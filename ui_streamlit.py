import streamlit as st
import pandas as pd
# Importamos la función principal de nuestro agente desde main.py
from main import run_agent

# --- Configuración de la Página de Streamlit ---
st.set_page_config(page_title="Agente de Marketing YAM", layout="wide")
st.title("🤖 Agente de Marketing YAM")
st.caption("Interfaz de prueba con Streamlit. Lógica central en `main.py`.")

# --- Inicialización del Historial de Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Lógica de la Interfaz de Chat ---

# Mostrar mensajes antiguos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Usamos st.container para agrupar texto y datos
        container = st.container()
        if "insights" in message["content"]:
            container.markdown(message["content"]["insights"])
        if "dataframe" in message["content"] and not message["content"]["dataframe"].empty:
            container.dataframe(message["content"]["dataframe"])

# Obtener la nueva pregunta del usuario
if prompt := st.chat_input("¿Qué quieres analizar hoy?"):
    
    # 1. Mostrar la pregunta del usuario en la interfaz
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": {"insights": prompt, "dataframe": pd.DataFrame()}})

    # 2. Preparar la respuesta del bot
    with st.chat_message("assistant"):
        with st.spinner("El agente está analizando..."):
            
            # 3. Llamar a la función central del agente
            result_dict = run_agent(prompt)

            # 4. Mostrar los resultados
            response_container = st.container()
            if "error" in result_dict:
                response_container.error(f"Ocurrió un error:\n\n{result_dict['error']}")
                # Guardar el error en el historial
                st.session_state.messages.append({"role": "assistant", "content": {"insights": result_dict['error'], "dataframe": pd.DataFrame()}})
            else:
                insights_text = result_dict.get("insights", "No se generaron insights.")
                df_result = result_dict.get("dataframe")

                response_container.markdown(insights_text)
                if df_result is not None and not df_result.empty:
                    response_container.dataframe(df_result)
                
                # 5. Guardar la respuesta estructurada en el historial
                st.session_state.messages.append({"role": "assistant", "content": {"insights": insights_text, "dataframe": df_result}})