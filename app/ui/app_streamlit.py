import json
import streamlit as st
from pydantic import ValidationError

from app.models.processo import ProcessoInput
from app.services.verifier import verify_process

st.set_page_config(page_title="Verificador de Processos Judiciais", layout="wide")

st.title("🔍 Verificador de Processos Judiciais")
st.markdown(
    """
Cole abaixo o JSON de um processo judicial no formato esperado
ou use um dos exemplos. Em seguida, clique em **Analisar**.
"""
)

EXEMPLOS = {
    "Exemplo 1 (federal, típico)": """
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
""",
}


if "json_input" not in st.session_state:
    st.session_state["json_input"] = ""

col1, col2 = st.columns(2)

with col1:
    exemplo_nome = st.selectbox("Carregar exemplo:", ["(nenhum)"] + list(EXEMPLOS.keys()))
    if exemplo_nome != "(nenhum)":
        st.session_state["json_input"] = EXEMPLOS[exemplo_nome]

json_input = st.text_area(
    "JSON do processo:",
    value=st.session_state.get("json_input", ""),
    height=400,
)

if st.button("Analisar"):
    if not json_input.strip():
        st.error("Por favor, informe um JSON de processo.")
    else:
        try:
            data = json.loads(json_input)
            processo = ProcessoInput(**data)
            decision = verify_process(processo)
        except (json.JSONDecodeError, ValidationError) as e:
            st.error(f"Erro ao interpretar JSON: {e}")
        except Exception as e:  # noqa: BLE001
            st.error(f"Erro interno ao verificar processo: {e}")
        else:
            with col2:
                st.subheader("Resultado")

                color = {
                    "approved": "green",
                    "rejected": "red",
                    "incomplete": "orange",
                }.get(decision.decision, "gray")

                st.markdown(
                    f"**Decisão:** "
                    f"<span style='color:{color}; font-weight:bold;'>{decision.decision.upper()}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Número do processo:** `{decision.numeroProcesso}`")
                st.markdown("**Justificativa:**")
                st.write(decision.rationale)

                st.markdown("**Regras citadas:**")
                if decision.policy_citations:
                    st.write(", ".join(decision.policy_citations))
                else:
                    st.write("_Nenhuma regra citada._")

                if decision.metadata:
                    st.markdown("**Metadata:**")
                    st.json(decision.metadata)
