import pandas as pd
from workflow import create_workflow

# Compilamos el grafo de LangGraph una sola vez cuando se importa este módulo.
# Esto es más eficiente que compilarlo en cada llamada.
print("⚙️ Compilando el workflow del agente por única vez...")
app = create_workflow()
print("✅ Workflow compilado y listo.")

def run_agent(question: str) -> dict:
    """
    Ejecuta el workflow completo del agente para una pregunta dada.

    Args:
        question: La pregunta del usuario en lenguaje natural.

    Returns:
        Un diccionario con los resultados, que puede contener 'insights',
        'dataframe', o una clave 'error' si algo falló.
    """
    try:
        # 1. Preparar el input para el grafo
        inputs = {"question": question}

        # 2. Invocar el workflow completo
        final_state = app.invoke(inputs)

        # 3. Extraer los resultados del estado final
        insights = final_state.get('insights', 'No se pudieron generar insights.')
        df = final_state.get('processed_df')

        # 4. Devolver un diccionario estructurado y limpio
        result = {
            "insights": insights,
            "dataframe": df if df is not None and not df.empty else pd.DataFrame()
        }
        return result

    except Exception as e:
        print(f"❌ Ocurrió un error en el flujo del agente: {e}")
        # 5. Devolver un diccionario de error si algo falla
        return {
            "error": str(e)
        }

if __name__ == '__main__':
    # Esta sección es para probar el agente directamente desde la consola
    # sin necesidad de la interfaz gráfica. Muy útil para depurar.
    print("\n--- Modo de Prueba de Consola ---")
    while True:
        pregunta = input("> ")
        if pregunta.lower() == "salir":
            break
        resultado = run_agent(pregunta)
        
        if "error" in resultado:
            print(f"Error: {resultado['error']}")
        else:
            print("\n--- Insights ---")
            print(resultado["insights"])
            if not resultado["dataframe"].empty:
                print("\n--- DataFrame ---")
                print(resultado["dataframe"])
        print("\n--------------------")