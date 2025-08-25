from typing import TypedDict, Optional
import pandas as pd
from langchain_ollama import ChatOllama
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langgraph.graph import StateGraph, END
from prompts import sql_generation_prompt, insights_generation_prompt
from pc_utils import execute_sql_query, calculate_advanced_metrics
import settings

# El GraphState ya no necesita 'final_response', usaremos 'insights' y 'processed_df' directamente
class GraphState(TypedDict):
    question: str
    sql_query: Optional[str]
    raw_df: Optional[pd.DataFrame]
    processed_df: Optional[pd.DataFrame]
    insights: Optional[str]

class SQLQuery(BaseModel):
    query: str = Field(description="La consulta SQL a ejecutar en PostgreSQL.")

# Nodos generate_sql_node, execute_sql_node, process_data_node no cambian
def generate_sql_node(state: GraphState):
    print(f"--- 1. GENERANDO CONSULTA SQL (con {settings.OLLAMA_MODEL_NAME}) ---")
    question = state["question"]
    llm = ChatOllama(model=settings.OLLAMA_MODEL_NAME, format="json", temperature=0)
    chain = sql_generation_prompt | llm | JsonOutputParser(pydantic_object=SQLQuery)
    sql_query_model = chain.invoke({"question": question})
    return {"sql_query": sql_query_model['query']}

def execute_sql_node(state: GraphState):
    print("--- 2. EJECUTANDO CONSULTA EN NEONDB ---")
    sql_query = state["sql_query"]
    if not sql_query:
        raise ValueError("No se generó una consulta SQL para ejecutar.")
    df = execute_sql_query(sql_query)
    return {"raw_df": df}

def process_data_node(state: GraphState):
    print("--- 3. CALCULANDO MÉTRICAS AVANZADAS ---")
    df = state["raw_df"]
    if df is None or df.empty:
        return {"processed_df": pd.DataFrame()}
    processed_df = calculate_advanced_metrics(df)
    return {"processed_df": processed_df}

# El nodo generate_insights ahora es el último
def generate_insights_node(state: GraphState):
    print(f"--- 4. GENERANDO INSIGHTS (con {settings.OLLAMA_MODEL_NAME}) ---")
    question = state["question"]
    df = state["processed_df"]
    if df is None or df.empty:
        return {"insights": "No se encontraron datos para la consulta. Por favor, intenta con otra pregunta."}
    data_string = df.to_string()
    llm = ChatOllama(model=settings.OLLAMA_MODEL_NAME, temperature=0)
    parser = StrOutputParser()
    chain = insights_generation_prompt | llm | parser
    insights = chain.invoke({"question": question, "data": data_string})
    return {"insights": insights}

# Construimos el grafo sin el nodo de formateo final
def create_workflow():
    workflow = StateGraph(GraphState)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("process_data", process_data_node)
    workflow.add_node("generate_insights", generate_insights_node)

    workflow.set_entry_point("generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("execute_sql", "process_data")
    workflow.add_edge("process_data", "generate_insights")
    workflow.add_edge("generate_insights", END) # 'generate_insights' ahora es el final

    app = workflow.compile()
    return app