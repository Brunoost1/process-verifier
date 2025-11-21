from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator


class DecisionOutput(BaseModel):
    numeroProcesso: str
    decision: str  # "approved" | "rejected" | "incomplete"
    rationale: str
    policy_citations: List[str]
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        allowed = {"approved", "rejected", "incomplete"}
        if v not in allowed:
            raise ValueError(f"decision must be one of {allowed}, got {v}")
        return v
