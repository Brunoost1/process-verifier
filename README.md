# Verificador de Processos Judiciais (Case JusCash)

Aplicação de referência para análise automatizada de processos judiciais, com foco na
decisão de compra de créditos, utilizando **LLM** como componente obrigatório de decisão.

## Contexto de Negócio

A empresa compra créditos de processos judiciais contra a Fazenda Pública e precisa
avaliar se um processo é elegível com base em uma política interna (POL-1 a POL-8).
Este projeto recebe o JSON de um processo, chama um LLM para aplicar as regras e
retorna uma decisão estruturada:

- `approved`
- `rejected`
- `incomplete`

sempre com justificativa e citações às políticas utilizadas.

## Arquitetura (resumo)

```text
Cliente (UI Streamlit) ──► Serviço de Verificação (FastAPI)
                                  │
                                  ▼
                           Módulo de Verificação
                                  │
                                  ▼
                             Cliente LLM (OpenAI)
                                  │
                                  ▼
                          Decisão + Logs + Metadata
```

- Backend: Python + FastAPI
- UI: Streamlit
- LLM: OpenAI (modelo configurável por env)
- Observabilidade: logging estruturado, integração opcional com LangSmith
- Container: Docker (pronto para Railway/Render)

## Tecnologias

- Python 3.11
- FastAPI
- Streamlit
- Pydantic
- OpenAI API
- LangSmith (opcional)
- Docker
- Pytest

## Como Rodar Localmente (sem Docker)

1. Crie um ambiente virtual:

   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Exporte as variáveis de ambiente necessárias:

   ```bash
   export OPENAI_API_KEY="sua_chave_aqui"
   export LLM_MODEL_NAME="gpt-4.1-mini"
   ```

4. Suba a API:

   ```bash
   uvicorn app.api.main:app --reload
   ```

   A API ficará disponível em `http://localhost:8000`.

5. Suba a UI (opcional):

   ```bash
   streamlit run app/ui/app_streamlit.py
   ```

   A interface ficará disponível em `http://localhost:8501`.

## Como Rodar com Docker

```bash
docker build -t verificador-processos .
docker run -p 8000:8000 -e OPENAI_API_KEY="sua_chave" verificador-processos
```

Acesse:

- API: `http://localhost:8000`
- Documentação OpenAPI/Swagger: `http://localhost:8000/docs`

## Endpoints da API

- `GET /health`  
  Retorna `{ "status": "ok" }`.

- `POST /v1/process/verify`  
  Corpo (exemplo):

  ```json
  {
    "numeroProcesso": "0001234-56.2023.4.05.8100",
    "classe": "Cumprimento de Sentença contra a Fazenda Pública",
    "orgaoJulgador": "19ª VARA FEDERAL - SOBRAL/CE",
    "ultimaDistribuicao": "2024-11-18T23:15:44.130Z",
    "assunto": "Rural (Art. 48/51)",
    "segredoJustica": false,
    "justicaGratuita": true,
    "siglaTribunal": "TRF5",
    "esfera": "Federal",
    "documentos": [],
    "movimentos": []
  }
  ```

  Resposta (exemplo):

  ```json
  {
    "numeroProcesso": "0001234-56.2023.4.05.8100",
    "decision": "approved",
    "rationale": "Trânsito em julgado comprovado, fase de execução iniciada e valor de condenação adequado.",
    "policy_citations": ["POL-1", "POL-2"],
    "metadata": {
      "model_name": "gpt-4.1-mini",
      "prompt_version": "v1",
      "latency_ms": 1234.56
    }
  }
  ```

## Variáveis de Ambiente

- `OPENAI_API_KEY` (obrigatória)
- `LLM_MODEL_NAME` (opcional, default `gpt-4.1-mini`)
- `PROMPT_VERSION` (opcional, default `v1`)
- `LANGSMITH_API_KEY` e `LANGSMITH_PROJECT` (opcionais)

## Limitações e Próximos Passos

- RAG ainda é simplificado (uso direto do texto das políticas em memória).
- Não há autenticação/autorização na API.
- UI está focada em testes internos (poderia ser unificada com a API em produção).
- Poderíamos adicionar:
  - testes mais abrangentes;
  - cache de resultados;
  - monitoramento completo via LangSmith + dashboards.


## Observabilidade e Orquestração (LangSmith)

As chamadas ao LLM são instrumentadas com **LangSmith** por meio do decorator
`@traceable` aplicado à função `call_llm` (`app/core/llm_client.py`). Isso permite:

- rastrear cada decisão como um *run* em um projeto LangSmith;
- inspecionar prompts (system + user) e respostas do modelo;
- medir latência de ponta a ponta da chamada ao LLM;
- facilitar o debug de casos em que o modelo não respeite o formato JSON.

Para habilitar o LangSmith, basta configurar as variáveis de ambiente:

```bash (linux) / windows abaixo
export LANGSMITH_API_KEY="sua_chave_langsmith"
export LANGSMITH_PROJECT="verificador-processos"
ou 
$env:LANGSMITH_API_KEY  = "sua_chave_langsmith"
$env:LANGSMITH_PROJECT  = "verificador-processos"
$env:LANGSMITH_TRACING  = "true"
$env:LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
```
#OBS SOBRE O PROMPT
QUANTO MAIORES REQUISITOS, MAIS TOKENS DE ENTRADA PARA PRÉ PROCESSAMENTO.#


Sem essas variáveis a aplicação continua funcionando normalmente, apenas sem
registrar rastros das execuções no painel do LangSmith.

Um fluxo típico em produção poderia ser:

1. Sistema de origem envia o JSON do processo para a API `/v1/process/verify`.
2. A API chama o LLM, instrumentado pelo LangSmith.
3. O LangSmith registra o *run* contendo:
   - inputs (JSON do processo, prompt),
   - outputs (decision, rationale, policy_citations),
   - metadados (modelo, latência).
4. Painéis do LangSmith são utilizados para monitorar performance, erros e
   distribuição das decisões (`approved/rejected/incomplete`).
