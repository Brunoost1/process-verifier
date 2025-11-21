from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.processo import ProcessoInput
from app.models.decision import DecisionOutput
from app.services.verifier import verify_process

app = FastAPI(
    title="Verificador de Processos Judiciais",
    version="1.0.0",
    description="API para decidir compra de créditos de processos judiciais usando LLM.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/process/verify", response_model=DecisionOutput)
def verify(processo: ProcessoInput) -> DecisionOutput:
    try:
        return verify_process(processo)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
