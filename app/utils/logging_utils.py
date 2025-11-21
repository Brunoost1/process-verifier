import json
import logging
from typing import List

logger = logging.getLogger("verificador")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)


def log_decision(
    numero_processo: str,
    decision: str,
    policy_citations: List[str],
    latency_ms: float,
    prompt_version: str,
) -> None:
    log_record = {
        "event": "decision",
        "numeroProcesso": numero_processo,
        "decision": decision,
        "policy_citations": policy_citations,
        "latency_ms": round(latency_ms, 2),
        "prompt_version": prompt_version,
    }
    logger.info(json.dumps(log_record, ensure_ascii=False))
