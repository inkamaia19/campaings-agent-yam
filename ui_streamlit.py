import streamlit as st
import pandas as pd
from main import run_agent

# --- Configuración de la Página de Streamlit ---
st.set_page_config(page_title="Agente de Marketing YAM", layout="wide")
st.title("🤖 Agente de Marketing YAM")
st.caption("Interfaz de prueba con Streamlit. Lógica central en `main.py`.")

# --- Inicialización del Historial de Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Lógica de la Interfaz de Chat ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        container = st.container()
        content_dict = message["content"]
        if "insights" in content_dict:
            container.markdown(content_dict["insights"])
        if "plot_path" in content_dict and content_dict["plot_path"]:
            container.image(content_dict["plot_path"])
        if "dataframe" in content_dict and not content_dict["dataframe"].empty:
            container.dataframe(content_dict["dataframe"])

if prompt := st.chat_input("Pregunta sobre tendencias, comparaciones, etc."):
    st.chat_message("user").markdown(prompt)
    user_content = {"insights": prompt, "dataframe": pd.DataFrame(), "plot_path": None}
    st.session_state.messages.append({"role": "user", "content": user_content})

    with st.chat_message("assistant"):
        with st.spinner("El agente está planificando y ejecutando..."):
            result_dict = run_agent(prompt)
            response_container = st.container()
            
            if "error" in result_dict:
                error_message = f"Ocurrió un error:\n\n{result_dict['error']}"
                response_container.error(error_message)
                assistant_content = {"insights": error_message, "dataframe": pd.DataFrame(), "plot_path": None}
            else:
                insights_text = result_dict.get("insights", "No se generaron insights.")
                df_result = result_dict.get("dataframe")
                plot_path_result = result_dict.get("plot_path")

                response_container.markdown(insights_text)
                if plot_path_result:
                    response_container.image(plot_path_result)
                if df_result is not None and not df_result.empty:
                    response_container.dataframe(df_result)
                
                assistant_content = {
                    "insights": insights_text,
                    "dataframe": df_result,
                    "plot_path": plot_path_result
                }
            st.session_state.messages.append({"role": "assistant", "content": assistant_content})