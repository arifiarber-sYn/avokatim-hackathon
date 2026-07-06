from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from jinja2 import BaseLoader, Environment, StrictUndefined, UndefinedError
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.matters import get_owned_matter
from app.database import get_db
from app.deps import get_current_user
from app.models import DocumentTemplate, Jurisdiction, Matter, MatterParty, User
from app.schemas.documents import RenderTemplateIn, RenderTemplateOut, TemplateOut
from app.services.audit import log_action

router = APIRouter(prefix="/templates", tags=["templates"])

# Sandboxed-ish: autoescape off (plain text legal docs), StrictUndefined so a
# missing variable is an error the lawyer sees, not silent blank output.
_env = Environment(loader=BaseLoader(), undefined=StrictUndefined)


@router.get("", response_model=list[TemplateOut])
async def list_templates(
    jurisdiction_code: str = "XK",
    locale: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    jurisdiction = (
        await db.execute(select(Jurisdiction).where(Jurisdiction.code == jurisdiction_code))
    ).scalar_one_or_none()
    if jurisdiction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Jurisdiction not found")
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
    return variables


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
    variables.update(body.variables)

    try:
        content = _env.from_string(template.body).render(**variables)
    except UndefinedError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Missing template variable: {exc.message}"
        )

    await log_action(
        db, tenant_id=user.tenant_id, user_id=user.id, action="template.render",
        entity_type="template", entity_id=str(template.id),
        details={"code": template.code, "matter_id": str(body.matter_id) if body.matter_id else None},
    )
    await db.commit()
    name = template.name.get("sq") or template.code
    return RenderTemplateOut(content=content, filename=f"{name}.txt")
