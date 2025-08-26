from typing import TypedDict, Optional, Dict, List
import pandas as pd
from langchain_ollama import ChatOllama
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, END
from prompts import planner_prompt, insights_generation_prompt
from pc_utils import execute_sql_query, calculate_advanced_metrics, generate_plot
import settings

# 1. Definir el estado del grafo
class GraphState(TypedDict):
    question: str
    plan: Optional[Dict]
    raw_df: Optional[pd.DataFrame]
    processed_df: Optional[pd.DataFrame]
    calculation_log: Optional[List[str]]
    plot_path: Optional[str]
    insights: Optional[str]

# Modelo Pydantic para el plan completo
class Plan(BaseModel):
    sql_query: str
    show_table: bool = True
    plot_info: Optional[Dict] = None

# 2. Definir los nodos del flujo
def generate_plan_node(state: GraphState):
    """Genera, VALIDA y LIMPIA el plan de acción completo."""
    print(f"--- 1. GENERANDO PLAN DE ACCIÓN (con {settings.OLLAMA_MODEL_NAME}) ---")
    question = state["question"]
    structured_llm = ChatOllama(model=settings.OLLAMA_MODEL_NAME, format="json", temperature=0).with_structured_output(Plan)
    chain = planner_prompt | structured_llm
    plan_model = chain.invoke({"question": question})
    plan = plan_model.dict()

    # --- SUPERVISOR DE PLANES (POST-PROCESAMIENTO) ---
    plot_info = plan.get("plot_info")
    if plot_info:
        sql_query = plan.get("sql_query", "").lower()
        x_col = plot_info.get("x_col")
        y_col = plot_info.get("y_col")
        title = plot_info.get("title")

        # Regla 1: Si el gráfico está incompleto, se descarta.
        if not all([x_col, y_col, title]):
            print(f"⚠️ SUPERVISOR: Plan de gráfico incompleto. Descartando.")
            plan["plot_info"] = None
        # Regla 2: Si las columnas del gráfico no están en el SQL, se descarta.
        elif x_col.lower() not in sql_query or y_col.lower() not in sql_query:
            print(f"⚠️ SUPERVISOR: Plan incoherente. Columnas del gráfico ('{x_col}', '{y_col}') no están en el SQL. Descartando.")
            plan["plot_info"] = None
    # --- FIN DEL SUPERVISOR ---

    return {"plan": plan}


def execute_sql_node(state: GraphState):
    """Ejecuta el SQL del plan."""
    print("--- 2. EJECUTANDO CONSULTA SQL DEL PLAN ---")
    sql_query = state["plan"].get("sql_query")
    if not sql_query:
        raise ValueError("El plan no contiene una consulta SQL.")
    df = execute_sql_query(sql_query)
    return {"raw_df": df}

def process_data_node(state: GraphState):
    """Calcula métricas y captura el log de cálculos."""
    print("--- 3. CALCULANDO MÉTRICAS AVANZADAS ---")
    df = state["raw_df"]
    if df is None or df.empty:
        return {"processed_df": pd.DataFrame(), "calculation_log": []}
    processed_df, calc_log = calculate_advanced_metrics(df)
    return {"processed_df": processed_df, "calculation_log": calc_log}

def generate_plot_node(state: GraphState):
    """Genera el gráfico si el plan lo indica."""
    print("--- 4a. GENERANDO GRÁFICO DEL PLAN ---")
    df = state["processed_df"]
    plot_instructions = state["plan"].get("plot_info")
    file_path = generate_plot(df, plot_instructions)
    return {"plot_path": file_path}

def generate_insights_node(state: GraphState):
    """Genera el análisis final, ahora con el log de cálculos."""
    print("--- 4b/5. GENERANDO INSIGHTS ---")
    df = state["processed_df"]
    if df is None or df.empty:
        return {"insights": "No se encontraron datos para la consulta."}
    
    data_string = df.to_string()
    llm = ChatOllama(model=settings.OLLAMA_MODEL_NAME, temperature=0)
    
    chain = insights_generation_prompt | llm
    message_object = chain.invoke({
        "question": state["question"], 
        "data": data_string,
        "calculation_log": state.get("calculation_log", [])
    })
    clean_insights = message_object.content
    return {"insights": clean_insights}

# 3. Definir el router simple basado en el plan
def should_generate_plot(state: GraphState) -> str:
    """Revisa si el plan incluye instrucciones para un gráfico."""
    print("--- ROUTER: ¿El plan incluye gráfico? ---")
    if state.get("plan") and state["plan"].get("plot_info"):
        print("--- DECISIÓN: SÍ, generar gráfico. ---")
        return "generate_plot"
    else:
        print("--- DECISIÓN: NO, ir a insights. ---")
        return "generate_insights"

# 4. Construir el grafo final
def create_workflow():
    workflow = StateGraph(GraphState)
    workflow.add_node("generate_plan", generate_plan_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("process_data", process_data_node)
    workflow.add_node("generate_plot", generate_plot_node)
    workflow.add_node("generate_insights", generate_insights_node)

    workflow.set_entry_point("generate_plan")
    workflow.add_edge("generate_plan", "execute_sql")
    workflow.add_edge("execute_sql", "process_data")
    
    workflow.add_conditional_edges(
        "process_data",
        should_generate_plot,
        {
            "generate_plot": "generate_plot",
            "generate_insights": "generate_insights"
        }
    )
    
    workflow.add_edge("generate_plot", "generate_insights")
    workflow.add_edge("generate_insights", END)
    
    app = workflow.compile()
    return app