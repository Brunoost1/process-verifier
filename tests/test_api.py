from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_verify_endpoint(monkeypatch):
    from app.services import verifier
    from app.models.decision import DecisionOutput

    def fake_verify_process(process):
        return DecisionOutput(
            numeroProcesso=process.numeroProcesso,
            decision="approved",
            rationale="Teste.",
            policy_citations=["POL-1"],
            metadata={"latency_ms": 1.0},
        )

    monkeypatch.setattr(verifier, "verify_process", fake_verify_process)

    payload = {
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

    resp = client.post("/v1/process/verify", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "approved"
    assert "POL-1" in body["policy_citations"]
