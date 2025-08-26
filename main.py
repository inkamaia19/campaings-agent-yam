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
        show_table = final_state.get('plan', {}).get('show_table', True)
        calculation_log = final_state.get('calculation_log', [])
        
        result = {
            "insights": insights,
            "dataframe": df if df is not None and not df.empty else pd.DataFrame(),
            "plot_path": plot_path,
            "show_table": show_table,
            "calculation_log": calculation_log
        }
        return result

    except Exception as e:
        print(f"❌ Ocurrió un error en el flujo del agente: {e}")
        return {"error": str(e)}

if __name__ == '__main__':
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

            if resultado.get("calculation_log"):
                print("\n--- Fórmulas Utilizadas ---")
                for formula in resultado["calculation_log"]:
                    print(formula)
            
            if resultado.get("show_table", True) and not resultado.get("dataframe", pd.DataFrame()).empty:
                print("\n--- DataFrame ---")
                print(resultado["dataframe"])

            if resultado.get("plot_path"):
                print(f"\n--- Gráfico Generado ---")
                print(f"Ruta: {resultado['plot_path']}")
        print("\n--------------------")