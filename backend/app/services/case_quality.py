"""Pre-publication quality check for citizen case requests.

Junk posts ("mkan rre,mkan rre,...") waste the lawyers' attention and lower
the marketplace's value. Two layers, both cheap:

1. Heuristics — catch obvious repetition/gibberish without any LLM call.
2. A single fast LLM classification (JSON: {"useful": bool, "reason": str}),
   through the provider abstraction. Fail-open: if the LLM is unreachable or
   returns garbage, the case is accepted with quality_flag="heuristic".

The check never blocks on legal merit — only on whether a lawyer could
possibly understand what is being asked.
"""
import json
import logging
import re

logger = logging.getLogger(__name__)

_CLASSIFY_PROMPT = (
    "Ti je filtri i cilësisë për një treg ligjor në Kosovë. Qytetari poston "
    "një rast që avokatët ta shohin. Vlerëso VETËM nëse përshkrimi është i "
    "kuptueshëm dhe i mjaftueshëm që një avokat ta kuptojë se çfarë kërkohet "
    "— JO meritën ligjore. Prano edhe përshkrime të shkurtra por të qarta. "
    "Refuzo vetëm tekst pa kuptim, përsëritje, testime ose sharje.\n\n"
    "Kategoria: {category}\nPërshkrimi:\n{description}\n\n"
    'Kthe VETËM JSON: {{"useful": true|false, "reason": "shpjegim i shkurtër"}}'
)


def heuristic_check(description: str) -> tuple[bool, str]:
    """Cheap local checks. Returns (ok, reason)."""
    words = re.findall(r"\w+", description.lower(), flags=re.UNICODE)
    if len(words) < 4:
        return False, "too_few_words"
    unique_ratio = len(set(words)) / len(words)
    # "mkan rre,mkan rre,mkan rre..." -> 2 unique words out of 14
    if len(words) >= 8 and unique_ratio < 0.3:
        return False, "repetitive"
    # Keyboard mash: no vowels at all in a long-enough text is not a language
    if not re.search(r"[aeiouëy]", description.lower()):
        return False, "gibberish"
    return True, "ok"


async def assess_case(description: str, category: str) -> tuple[bool, str]:
    """Full assessment. Returns (useful, quality_flag_or_reason).

    - (False, reason) -> reject with a friendly message
    - (True, "ok") -> LLM approved
    - (True, "heuristic") -> heuristics passed, LLM unavailable
    """
    ok, reason = heuristic_check(description)
    if not ok:
        return False, reason

    try:
        from app.llm.base import ChatMessage
        from app.llm.router import get_provider

        provider = get_provider(None, purpose="json")
        result = await provider.chat(
            [
                ChatMessage(
                    role="user",
                    content=_CLASSIFY_PROMPT.format(
                        category=category, description=description[:3000]
                    ),
                )
            ]
        )
        match = re.search(r"\{.*\}", result.content, flags=re.DOTALL)
        if match is None:
            return True, "heuristic"
        data = json.loads(match.group(0))
        if data.get("useful") is False:
            return False, str(data.get("reason", ""))[:200]
        return True, "ok"
    except Exception as exc:
        logger.warning("Case quality LLM check unavailable (fail-open): %s", exc)
        return True, "heuristic"
