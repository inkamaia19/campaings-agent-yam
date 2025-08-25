import pandas as pd
from workflow import create_workflow

print("⚙️ Compilando el workflow del agente por única vez...")
app = create_workflow()
print("✅ Workflow compilado y listo.")

def run_agent(question: str) -> dict:
    try:
        inputs = {"question": question}
        final_state = app.invoke(inputs)

        insights = final_state.get('insights', 'El agente no produjo un insight final.')
        df = final_state.get('processed_df')
        plot_path = final_state.get('plot_path')
        
        result = {
            "insights": insights,
            "dataframe": df if df is not None and not df.empty else pd.DataFrame(),
            "plot_path": plot_path
        }
        return result

    except Exception as e:
        print(f"❌ Ocurrió un error en el flujo del agente: {e}")
        return {"error": str(e)}

if __name__ == '__main__':
    # Esta sección es para probar el agente directamente desde la consola
    print("\n--- Modo de Prueba de Consola ---")
    while True:
        pregunta = input("> ")
        if pregunta.lower() in ["salir", "exit", "quit"]:
            break
        resultado = run_agent(pregunta)
        
        if "error" in resultado:
            print(f"Error: {resultado['error']}")
        else:
            print("\n--- Insights ---")
            print(resultado["insights"])
            if "dataframe" in resultado and not resultado["dataframe"].empty:
                print("\n--- DataFrame ---")
                print(resultado["dataframe"])
            if "plot_path" in resultado and resultado["plot_path"]:
                print(f"\n--- Gráfico Generado ---")
                print(f"Ruta: {resultado['plot_path']}")
        print("\n--------------------")