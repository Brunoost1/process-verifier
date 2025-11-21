# Verificador de Processos Judiciais – Documentação do Case

## 1. Resumo Executivo

Este projeto implementa um verificador automático de processos judiciais, voltado
à decisão de compra de créditos, utilizando um Large Language Model (LLM) como
componente central de decisão.

A aplicação recebe o JSON de um processo no formato definido pelo case, aplica
a política interna (POL-1 a POL-8) e retorna uma decisão:

- `approved`
- `rejected`
- `incomplete`

sempre acompanhada de justificativa textual e citações às regras utilizadas.

## 2. Fluxo Ponta a Ponta

1. **Recebimento do JSON**  
   A API (`POST /v1/process/verify`) recebe um objeto `Processo` com dados gerais,
   documentos e movimentos.

2. **Validação de Entrada**  
   O corpo é validado via Pydantic (`ProcessoInput`). Em caso de erros de formato
   ou campos obrigatórios ausentes, a requisição é rejeitada com erro HTTP.

3. **Montagem do Contexto e Prompt**  
   O módulo de verificação (`verify_process`) serializa o processo em JSON,
   injeta o texto da política (POL-1 a POL-8) e constrói prompts de sistema e de
   usuário, impondo um formato estrito de resposta em JSON.

4. **Chamada ao LLM**  
   O cliente LLM (`llm_client`) envia os prompts para o modelo configurado
   (por exemplo, `gpt-4.1-mini` via OpenAI API), registra o tempo de resposta
   e tenta decodificar o conteúdo retornado como JSON.

5. **Pós-Processamento da Resposta**  
   A resposta do LLM é normalizada e validada:
   - `decision` deve ser uma das três opções;
   - `policy_citations` é filtrada para manter apenas IDs POL-1…POL-8;
   - `metadata` é preenchida com modelo, latência e versão do prompt.

6. **Retorno ao Cliente**  
   A API devolve um `DecisionOutput` em JSON, pronto para consumo por sistemas
   internos ou pela interface visual.

## 3. Papel do LLM

O LLM não é utilizado apenas como classificador, mas como componente de raciocínio,
responsável por:

- Ler textos livres dos documentos e movimentos;
- Identificar menções a trânsito em julgado, fase de execução, valores e eventos
  processuais relevantes;
- Aplicar as regras POL-1 a POL-8 de forma combinada;
- Produzir uma decisão explicada e alinhada à política da empresa.

O prompt foi desenhado para:

- Explicitar as regras de negócio;
- Definir regras de fallback (por exemplo, quando falta valor de condenação);
- Forçar a saída em JSON (sem texto fora do objeto);
- Indicar como lidar com entradas malformadas ou incompletas.

## 4. Aplicação das Regras da Política

- **POL-1**: O LLM verifica se há prova de trânsito em julgado (ex.: “Certidão de
  Trânsito em Julgado”) e indicações de fase de execução (movimentos como “início
  do cumprimento definitivo”).

- **POL-2**: Procura um campo `valorCondenacao` ou menções claras a valores nos
  documentos (planilhas de cálculos, requisições, precatórios). Se não encontrar,
  a saída tende a ser `incomplete`.

- **POL-3**: Quando um valor de condenação é identificado, o LLM compara com o
  limiar de R$ 1.000,00 e, se inferior, recomenda `rejected`.

- **POL-4**: A partir da esfera (por exemplo, “Trabalhista”) ou do próprio texto,
  identifica processos trabalhistas e aponta `rejected`.

- **POL-5**: Detecta menções a óbito do autor e ausência de habilitação em inventário,
  retornando `rejected` quando presente.

- **POL-6**: Ao detectar “substabelecimento sem reserva de poderes” em documentos
  ou movimentos, indica `rejected`.

- **POL-7**: Registra, quando existentes, honorários contratuais, periciais e
  sucumbenciais, permitindo que a decisão considere esses valores na justificativa.

- **POL-8**: Sempre que faltar um documento essencial (por exemplo, prova de trânsito
  em julgado), a saída deve ser `incomplete`, com rationale explicando o ponto.

## 5. Exemplo de Caso

Para um processo típico federal, com:

- Sentença de mérito transitada em julgado;
- Início de cumprimento definitivo;
- Valor de condenação acima de R$ 1.000,00;
- Ausência de eventos impeditivos (óbito sem habilitação, substabelecimento sem
  reserva, esfera trabalhista);

o sistema tende a retornar:

- `decision`: `approved`
- `rationale`: explicação mencionando trânsito em julgado, fase de execução e valor
  compatível com a política financeira.
- `policy_citations`: por exemplo, `["POL-1", "POL-2", "POL-7"]`.

## 6. Explicabilidade e Robustez

- **Explicabilidade**: o `rationale` é redigido em português claro, de forma curta,
  porém suficiente para justificar a decisão com base nos fatos relevantes do
  processo e nas políticas aplicadas.

- **Robustez**:
  - Validação de entrada via Pydantic impede formatos inválidos.
  - O cliente LLM força resposta em JSON e rejeita saídas malformadas.
  - Em caso de erros do LLM ou ambiguidades, a decisão tende a `incomplete`, com
    justificativas adequadas.
  - Logs estruturados registram decisões, regras citadas e latência, permitindo
    auditoria e monitoramento em produção.


## 6. Observabilidade e Monitoramento

Para observabilidade das chamadas ao LLM e do fluxo de decisão, a solução utiliza
integração com o **LangSmith**.

A função `call_llm` em `app/core/llm_client.py` é decorada com `@traceable` do
LangSmith, o que permite:

- registrar cada execução como um *run* no projeto configurado;
- inspecionar prompts (system e user) e respostas;
- medir latência e acompanhar erros nas chamadas ao modelo.

A configuração é feita via variáveis de ambiente:

- `LANGSMITH_API_KEY`: chave de API do LangSmith;
- `LANGSMITH_PROJECT`: nome do projeto onde os *runs* serão registrados.

Quando essas variáveis não estão definidas, a instrumentação se comporta de forma
*não intrusiva*, permitindo que a aplicação seja executada normalmente, apenas
sem registrar os rastros das execuções.
