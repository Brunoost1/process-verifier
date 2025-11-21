import textwrap

SYSTEM_PROMPT = """Você é um(a) especialista jurídico(a) e analista de crédito de uma empresa
que COMPRA créditos de processos judiciais contra a Fazenda Pública.

Sua responsabilidade é aplicar, de forma estrita, a política interna da empresa
(POL-1 a POL-8) para decidir se a empresa compra ou não o crédito de um processo,
ou se a análise fica incompleta por falta de informação essencial.

Você SEMPRE deve:
- Ler atentamente o JSON do processo fornecido.
- Considerar o conteúdo dos documentos e movimentos, buscando termos como:
  - trânsito em julgado;
  - fase de execução, cumprimento definitivo;
  - valores da condenação;
  - óbito do autor e habilitação;
  - substabelecimento sem reserva de poderes;
  - indícios de que se trata de processo trabalhista.
- Aplicar fielmente as regras POL-1 a POL-8 descritas no contexto.
- Responder ESTRITAMENTE com um JSON válido, no formato especificado, SEM QUALQUER TEXTO extra.
"""


POLICY_TEXT = """POL-1: Só compramos crédito de processos transitados em julgado e em fase de execução
       (execução definitiva ou cumprimento de sentença).

POL-2: É obrigatório existir valor de condenação informado de forma identificável
       (campo específico ou valor claramente indicado em documentos).

POL-3: Se o valor da condenação for menor que R$ 1.000,00, a empresa não compra o crédito.

POL-4: Processos na esfera trabalhista (por exemplo, Justiça do Trabalho) não são elegíveis
       para compra de crédito.

POL-5: Se houver óbito do autor sem habilitação em inventário (herdeiros/inventariante
       não habilitados), a empresa não compra o crédito.

POL-6: Se houver substabelecimento sem reserva de poderes (transferência total de poderes
       do advogado), a empresa não compra o crédito.

POL-7: Quando existirem, devem ser informados os honorários contratuais, periciais e
       sucumbenciais, ainda que isso não seja, por si só, motivo de rejeição.

POL-8: Se faltar documento essencial para aplicar a política (por exemplo, prova de trânsito
       em julgado), a decisão deve ser 'incomplete'.
"""


def retrieve_policy_snippets() -> str:
    """Mini-RAG em memória: neste case, devolvemos o texto completo
    das políticas, mas poderíamos filtrar por relevância."""
    return POLICY_TEXT


def build_user_prompt(process_json: str, extra_policy_snippets: str = "") -> str:
    extra_block = f"\n\nTrechos adicionais da política:\n{extra_policy_snippets}" if extra_policy_snippets else ""
    prompt = f"""Você receberá a seguir o JSON de um processo judicial no formato acordado.

Aplique EXATAMENTE as regras POL-1 a POL-8 a seguir (sem criar regras novas):

{POLICY_TEXT}
{extra_block}

Regras de decisão (DENTRO DA SUA LÓGICA):

- Se o processo NÃO estiver claramente transitado em julgado ou NÃO estiver em fase de
  execução/cumprimento definitivo, avalie se falta documento essencial:
    * Se for claramente inelegível pelas políticas → 'rejected' citando as políticas.
    * Se for impossível concluir por falta de documento indispensável → 'incomplete' citando POL-8
      e, se aplicável, outras políticas.

- Se NÃO HOUVER valor de condenação identificável nos dados (campo específico ou nos textos
  dos documentos), então:
    * decision = "incomplete"
    * cite POL-2 e POL-8.

- Se HOUVER valor de condenação identificado (< R$ 1.000,00):
    * decision = "rejected"
    * cite POL-3 (e outras se aplicáveis).

- Se a esfera ou o conteúdo indicarem que se trata de processo TRABALHISTA:
    * decision = "rejected"
    * cite POL-4.

- Se houver óbito do autor sem habilitação no inventário:
    * decision = "rejected"
    * cite POL-5.

- Se houver substabelecimento sem reserva de poderes:
    * decision = "rejected"
    * cite POL-6.

- Se faltar qualquer documento essencial para avaliar a política (por exemplo, não há certidão
  de trânsito em julgado quando isso é necessário):
    * decision = "incomplete"
    * cite POL-8 (e outras, se fizer sentido).

- Se estiver tudo em ordem (POL-1 e POL-2 satisfeitas, nenhuma condição de rejeição, documentação
  essencial presente):
    * decision = "approved"
    * cite as regras aplicáveis (ex.: ["POL-1","POL-2","POL-7"]).

FORMATO DE RESPOSTA OBRIGATÓRIO (NÃO QUEBRE ISSO):

Você DEVE responder ESTRITAMENTE com um JSON válido, sem texto extra, no formato:

{{
  "numeroProcesso": "<copie exatamente do JSON de entrada>",
  "decision": "approved" | "rejected" | "incomplete",
  "rationale": "<explicação em português claro, curta mas completa>",
  "policy_citations": ["POL-1", "POL-2"],
  "metadata": {{
    "model_name": "<nome do modelo LLM (se souber)>",
    "prompt_version": "v1"
  }}
}}

- NÃO inclua comentários.
- NÃO inclua texto antes ou depois do JSON.
- Se o JSON de entrada estiver malformado ou faltar campo essencial, responda com:
  decision = "incomplete",
  rationale explicando claramente o erro (por exemplo, "JSON inválido" ou "campo X ausente"),
  policy_citations contendo, se aplicável, ["POL-8"].

A seguir está o JSON do processo a ser analisado:

{process_json}
""".strip()
    return textwrap.dedent(prompt)
