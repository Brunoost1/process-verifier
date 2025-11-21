from typing import List

from app.core.config import get_settings
from app.core.llm_client import call_llm
from app.core.prompts import SYSTEM_PROMPT, build_user_prompt, retrieve_policy_snippets
from app.models.processo import ProcessoInput
from app.models.decision import DecisionOutput
from app.utils.logging_utils import log_decision

POLICY_IDS = {f"POL-{i}" for i in range(1, 9)}
settings = get_settings()


def _sanitize_policy_citations(citations: List[str]) -> List[str]:
    unique: List[str] = []
    for c in citations:
        if c in POLICY_IDS and c not in unique:
            unique.append(c)
    return unique


def verify_process(process: ProcessoInput) -> DecisionOutput:
    """Core do verificador: monta prompts, chama o LLM e normaliza a saída."""
    process_json = process.model_dump_json(ensure_ascii=False)
    policy_snippets = retrieve_policy_snippets()
    user_prompt = build_user_prompt(process_json, extra_policy_snippets=policy_snippets)

    raw, latency_ms, model_name = call_llm(SYSTEM_PROMPT, user_prompt)

    numero = raw.get("numeroProcesso") or process.numeroProcesso
    decision = raw.get("decision", "incomplete")
    rationale = raw.get("rationale") or "A decisão retornada pelo modelo estava incompleta."
    policy_citations = raw.get("policy_citations") or []
    metadata = raw.get("metadata") or {}

    if decision not in {"approved", "rejected", "incomplete"}:
        decision = "incomplete"

    policy_citations = _sanitize_policy_citations(policy_citations)

    metadata.setdefault("model_name", model_name)
    metadata.setdefault("prompt_version", settings.prompt_version)
    metadata.setdefault("latency_ms", round(latency_ms, 2))

    decision_output = DecisionOutput(
        numeroProcesso=numero,
        decision=decision,
        rationale=rationale,
        policy_citations=policy_citations,
        metadata=metadata,
    )

    log_decision(
        numero,
        decision_output.decision,
        decision_output.policy_citations,
        latency_ms,
        settings.prompt_version,
    )

    return decision_output
