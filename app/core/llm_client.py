import json
import time
from typing import Tuple, Dict, Any

from openai import OpenAI
from langsmith import traceable

from app.core.config import get_settings

settings = get_settings()
_client = OpenAI(api_key=settings.openai_api_key or None)


@traceable(name="llm_verifier_call", run_type="llm")
def call_llm(system_prompt: str, user_prompt: str) -> Tuple[Dict[str, Any], float, str]:
    """Chama o LLM e retorna (dict_json, latency_ms, model_name).

    A função é instrumentada com LangSmith via o decorator @traceable, permitindo
    acompanhar os prompts, respostas, latência e eventuais erros em um projeto
    configurado via variáveis de ambiente LANGSMITH_API_KEY e LANGSMITH_PROJECT.

    Levanta ValueError se não conseguir decodificar JSON.
    """
    if not settings.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY não configurada. Defina a variável de ambiente antes de chamar o verificador."
        )

    start = time.time()
    response = _client.chat.completions.create(
        model=settings.llm_model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )
    elapsed_ms = (time.time() - start) * 1000.0

    content = response.choices[0].message.content
    if content is None:
        raise ValueError("LLM retornou conteúdo vazio")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        # Incluímos os primeiros caracteres do conteúdo para facilitar debug,
        # mas sem poluir demais os logs.
        snippet = content[:200]
        raise ValueError(f"LLM retornou conteúdo não-JSON: {e}: {snippet}")

    return data, elapsed_ms, settings.llm_model_name
