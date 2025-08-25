from typing import TypedDict, Optional, Dict
import pandas as pd
from langchain_ollama import ChatOllama
from langchain_core.pydantic_v1 import BaseModel, Field
# StrOutputParser ya no es necesario para el nodo de insights
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from prompts import planner_prompt, insights_generation_prompt
from pc_utils import execute_sql_query, calculate_advanced_metrics, generate_plot
import settings

# 1. Definir el estado del grafo (sin cambios)
class GraphState(TypedDict):
    question: str
    plan: Optional[Dict]
    raw_df: Optional[pd.DataFrame]
    processed_df: Optional[pd.DataFrame]
    plot_path: Optional[str]
    insights: Optional[str]

# Modelo Pydantic para el plan completo (sin cambios)
class Plan(BaseModel):
    sql_query: str
    plot_info: Optional[Dict] = None

# 2. Definir los nodos del nuevo flujo (con el nodo de insights corregido)
def generate_plan_node(state: GraphState):
    """Genera el plan completo: SQL y visualización en un solo paso."""
    print(f"--- 1. GENERANDO PLAN DE ACCIÓN (con {settings.OLLAMA_MODEL_NAME}) ---")
    question = state["question"]
    structured_llm = ChatOllama(model=settings.OLLAMA_MODEL_NAME, format="json", temperature=0).with_structured_output(Plan)
    chain = planner_prompt | structured_llm
    plan_model = chain.invoke({"question": question})
    return {"plan": plan_model.dict()}

def execute_sql_node(state: GraphState):
    """Ejecuta el SQL del plan."""
    print("--- 2. EJECUTANDO CONSULTA SQL DEL PLAN ---")
    sql_query = state["plan"].get("sql_query")
    if not sql_query:
        raise ValueError("El plan no contiene una consulta SQL.")
    df = execute_sql_query(sql_query)
    return {"raw_df": df}

def process_data_node(state: GraphState):
    """Calcula métricas avanzadas si hay datos."""
    print("--- 3. CALCULANDO MÉTRICAS AVANZADAS ---")
    df = state["raw_df"]
    if df is None or df.empty:
        return {"processed_df": pd.DataFrame()}
    processed_df = calculate_advanced_metrics(df)
    return {"processed_df": processed_df}

def generate_plot_node(state: GraphState):
    """Genera el gráfico si el plan lo indica."""
    print("--- 4a. GENERANDO GRÁFICO DEL PLAN ---")
    df = state["processed_df"]
    plot_instructions = state["plan"].get("plot_info")
    file_path = generate_plot(df, plot_instructions)
    return {"plot_path": file_path}

def generate_insights_node(state: GraphState):
    """Genera el análisis final en texto, asegurando una salida limpia."""
    print("--- 4b/5. GENERANDO INSIGHTS ---")
    df = state["processed_df"]
    if df is None or df.empty:
        return {"insights": "No se encontraron datos para la consulta."}
    
    data_string = df.to_string()
    llm = ChatOllama(model=settings.OLLAMA_MODEL_NAME, temperature=0)
    
    # --- ¡ESTA ES LA CORRECCIÓN CLAVE! ---
    # 1. Creamos la cadena que va del prompt al LLM. El resultado será un objeto de mensaje.
    chain = insights_generation_prompt | llm
    # 2. Invocamos la cadena para obtener el objeto de mensaje completo.
    message_object = chain.invoke({"question": state["question"], "data": data_string})
    # 3. Extraemos SOLAMENTE el contenido de texto limpio del objeto.
    clean_insights = message_object.content
    # --- FIN DE LA CORRECCIÓN ---
    
    return {"insights": clean_insights}

# 3. Definir el router simple basado en el plan (sin cambios)
def should_generate_plot(state: GraphState) -> str:
    """Revisa si el plan incluye instrucciones para un gráfico."""
    print("--- ROUTER: ¿El plan incluye gráfico? ---")
    if state.get("plan") and state["plan"].get("plot_info"):
        print("--- DECISIÓN: SÍ, generar gráfico. ---")
        return "generate_plot"
    else:
        print("--- DECISIÓN: NO, ir a insights. ---")
        return "generate_insights"

# 4. Construir el grafo final (sin cambios)
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