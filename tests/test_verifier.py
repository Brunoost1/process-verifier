import pytest

from app.models.processo import ProcessoInput
from app.services import verifier


def _build_base_process(**overrides):
    base = {
        "numeroProcesso": "0001234-56.2023.4.05.8100",
        "classe": "Cumprimento de Sentença",
        "orgaoJulgador": "Vara Federal",
        "ultimaDistribuicao": "2024-01-01T00:00:00Z",
        "assunto": "Benefício previdenciário",
        "segredoJustica": False,
        "justicaGratuita": True,
        "siglaTribunal": "TRF5",
        "esfera": "Federal",
        "documentos": [],
        "movimentos": [],
    }
    base.update(overrides)
    return ProcessoInput(**base)


def test_verifier_forces_valid_decision(monkeypatch):
    def fake_call_llm(system_prompt, user_prompt):
        return {
            "numeroProcesso": "0001234-56.2023.4.05.8100",
            "decision": "foo",
            "rationale": "Teste.",
            "policy_citations": ["POL-1"],
            "metadata": {},
        }, 10.0, "fake-model"

    monkeypatch.setattr("app.services.verifier.call_llm", fake_call_llm)

    proc = _build_base_process()
    decision = verifier.verify_process(proc)

    assert decision.decision == "incomplete"
    assert "POL-1" in decision.policy_citations


def test_trabalhista_rejected(monkeypatch):
    def fake_call_llm(system_prompt, user_prompt):
        return {
            "numeroProcesso": "0100001-11.2023.5.02.0001",
            "decision": "rejected",
            "rationale": "Processo trabalhista.",
            "policy_citations": ["POL-4"],
            "metadata": {},
        }, 15.0, "fake-model"

    monkeypatch.setattr("app.services.verifier.call_llm", fake_call_llm)

    proc = _build_base_process(
        numeroProcesso="0100001-11.2023.5.02.0001",
        esfera="Trabalhista",
    )
    decision = verifier.verify_process(proc)

    assert decision.decision == "rejected"
    assert "POL-4" in decision.policy_citations
