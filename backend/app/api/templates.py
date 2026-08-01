import html
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from jinja2 import BaseLoader, Environment, Undefined
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.matters import get_owned_matter
from app.database import get_db
from app.jurisdictions import jurisdiction_row_for_tenant
from app.deps import get_current_user
from app.models import Document, DocumentTemplate, Jurisdiction, Matter, MatterParty, User
from app.schemas.documents import (
    DocumentOut,
    RenderTemplateIn,
    RenderTemplateOut,
    RenderToMatterIn,
    TemplateOut,
)
from app.services import rag, storage
from app.services.audit import log_action
from app.services.docx_render import build_docx

router = APIRouter(prefix="/templates", tags=["templates"])


class _PlaceholderUndefined(Undefined):
    """A missing variable renders as a fill-in blank instead of failing —
    the lawyer completes it by hand, like on a paper form."""

    def __str__(self) -> str:  # noqa: D105
        return "__________"


# Sandboxed-ish: autoescape off (plain text legal docs).
_env = Environment(loader=BaseLoader(), undefined=_PlaceholderUndefined)


@router.get("", response_model=list[TemplateOut])
async def list_templates(
    jurisdiction_code: str | None = None,
    locale: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if jurisdiction_code:
        jurisdiction = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == jurisdiction_code))
        ).scalar_one_or_none()
        if jurisdiction is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Jurisdiction not found")
    else:
        jurisdiction = await jurisdiction_row_for_tenant(db, user.tenant_id)
    stmt = select(DocumentTemplate).where(
        DocumentTemplate.jurisdiction_id == jurisdiction.id,
        or_(
            DocumentTemplate.tenant_id.is_(None),
            DocumentTemplate.tenant_id == user.tenant_id,
        ),
    )
    if locale:
        stmt = stmt.where(DocumentTemplate.locale == locale)
    return (await db.execute(stmt.order_by(DocumentTemplate.code))).scalars().all()


async def _matter_variables(db: AsyncSession, user: User, matter: Matter) -> dict:
    """Auto-fill variables from the matter file."""
    variables: dict = {
        "lawyer_name": user.full_name,
        "date": date.today().strftime("%d.%m.%Y"),
        "city": "",
        "matter_reference": matter.reference,
        "client_name": "",
        "client_address": "",
        "opposing_name": "",
    }
    if matter.client:
        variables["client_name"] = matter.client.display_name
        variables["client_address"] = matter.client.address or ""
    parties = (
        await db.execute(
            select(MatterParty)
            .options(selectinload(MatterParty.contact))
            .where(MatterParty.matter_id == matter.id, MatterParty.role == "opposing_party")
        )
    ).scalars().all()
    if parties:
        variables["opposing_name"] = ", ".join(p.contact.display_name for p in parties)
    if matter.court_name:
        variables["court_name"] = matter.court_name
        # Administrative templates address an "authority"; default to the court
        variables.setdefault("authority", matter.court_name)
    if matter.court_case_number:
        variables["court_case_number"] = matter.court_case_number
    return variables


def _render(template: DocumentTemplate, variables: dict) -> tuple[str, list[str]]:
    """Render with placeholders for missing variables; report which were missing."""
    # template.variables is a list of {"name": ..., "label": {...}} dicts
    declared = [
        v.get("name") if isinstance(v, dict) else v for v in (template.variables or [])
    ]
    missing = [v for v in declared if v and not variables.get(v)]
    content = _env.from_string(template.body).render(**variables)
    return content, missing


@router.post("/render", response_model=RenderTemplateOut)
async def render_template(
    body: RenderTemplateIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = await db.get(DocumentTemplate, body.template_id)
    if template is None or (
        template.tenant_id is not None and template.tenant_id != user.tenant_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    variables: dict = {}
    if body.matter_id:
        matter = await get_owned_matter(db, user, body.matter_id)
        variables.update(await _matter_variables(db, user, matter))
    else:
        variables.update(
            {"lawyer_name": user.full_name, "date": date.today().strftime("%d.%m.%Y")}
        )
    variables.update({k: v for k, v in body.variables.items() if v})

    content, _missing = _render(template, variables)

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="template.render",
        entity_type="template", entity_id=str(template.id),
        details={"code": template.code, "matter_id": str(body.matter_id) if body.matter_id else None},
    )
    await db.commit()
    name = template.name.get("sq") or template.code
    return RenderTemplateOut(content=content, filename=f"{name}.txt")


class AiAssistIn(BaseModel):
    draft: str = Field(min_length=20, max_length=60000)
    instruction: str = Field(min_length=3, max_length=2000)
    provider: str | None = None


@router.post("/ai-assist")
async def ai_assist(
    body: AiAssistIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Spellbook-style clause help: Ava rewrites the draft per the lawyer's
    instruction and flags legal risks. Respects the tenant's external-AI gate."""
    from app.api.assistant import _effective_provider
    from app.services.assistant import ai_assist_template

    provider_name = await _effective_provider(db, user, body.provider)
    try:
        result = await ai_assist_template(body.draft, body.instruction, provider_name)
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    if result is None:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "AI reply could not be parsed; try again"
        )
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="template.ai_assist",
        entity_type="template", entity_id=None,
        details={"instruction": body.instruction[:200]},
    )
    await db.commit()
    return result


@router.post("/render-docx")
async def render_docx(
    body: RenderToMatterIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Render (or take the lawyer's edited text) as a styled Word document —
    for lawyers who finish their drafting in Word."""
    template = await db.get(DocumentTemplate, body.template_id)
    if template is None or (
        template.tenant_id is not None and template.tenant_id != user.tenant_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    if body.content:
        content = body.content
    else:
        variables: dict = {}
        if body.matter_id:
            matter = await get_owned_matter(db, user, body.matter_id)
            variables.update(await _matter_variables(db, user, matter))
        else:
            variables.update(
                {"lawyer_name": user.full_name, "date": date.today().strftime("%d.%m.%Y")}
            )
        variables.update({k: v for k, v in body.variables.items() if v})
        content, _ = _render(template, variables)

    name = template.name.get("sq") or template.code
    docx_bytes = build_docx(content, title=name)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="template.render_docx",
        entity_type="template", entity_id=str(template.id), details={"code": template.code},
    )
    await db.commit()
    filename = f"{name}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


_DOC_PAGE = """<!DOCTYPE html>
<html lang="sq"><head><meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 2.5cm; }}
  body {{ font-family: "DejaVu Serif", serif; font-size: 12px;
         line-height: 1.65; color: #111; white-space: pre-wrap; }}
</style></head><body>{content}</body></html>"""


@router.post("/render-to-matter", response_model=DocumentOut, status_code=201)
async def render_to_matter(
    body: RenderToMatterIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Render (or take the lawyer's edited text) and file it into the matter
    as a PDF document — versioned, searchable and shareable like any upload."""
    from weasyprint import HTML

    template = await db.get(DocumentTemplate, body.template_id)
    if template is None or (
        template.tenant_id is not None and template.tenant_id != user.tenant_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")
    if body.matter_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "matter_id is required")
    matter = await get_owned_matter(db, user, body.matter_id)

    if body.content:
        content = body.content
    else:
        variables = await _matter_variables(db, user, matter)
        variables.update({k: v for k, v in body.variables.items() if v})
        content, _ = _render(template, variables)

    pdf = HTML(string=_DOC_PAGE.format(content=html.escape(content))).write_pdf()
    rel_path, sha, encrypted = storage.save_file(pdf, user.tenant_id)

    name = template.name.get("sq") or template.code
    filename = f"{name} - {matter.reference}.pdf"
    doc = Document(
        tenant_id=user.tenant_id,
        matter_id=matter.id,
        family_id=uuid.uuid4(),
        version=1,
        is_latest=True,
        filename=filename,
        mime_type="application/pdf",
        size_bytes=len(pdf),
        sha256=sha,
        storage_path=rel_path,
        encrypted=encrypted,
        category="draft",
        uploaded_by_id=user.id,
        text_content=content,
        ocr_status="none",
    )
    db.add(doc)
    await db.flush()
    await rag.index_document_chunks(db, doc)
    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="template.render_to_matter",
        entity_type="document", entity_id=str(doc.id),
        details={"code": template.code, "matter": matter.reference},
    )
    await db.commit()
    await db.refresh(doc)
    out = DocumentOut.model_validate(doc)
    out.has_text = True
    return out
