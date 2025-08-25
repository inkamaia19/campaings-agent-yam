import pandas as pd
import psycopg2
import settings

def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """
    Se conecta a la base de datos NeonDB (PostgreSQL), ejecuta una consulta SQL,
    y devuelve el resultado como un DataFrame de Pandas.
    """
    conn = None
    try:
        print(f"\n🔌 Connecting to NeonDB...")
        conn = psycopg2.connect(settings.DATABASE_URI)
        print(f"Executing query on NeonDB:\n---\n{sql_query}\n---")
        df = pd.read_sql_query(sql_query, conn)
        print("✅ Query executed successfully.")
        return df
    except Exception as e:
        print(f"❌ An error occurred while executing SQL query: {e}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            conn.close()
            print("🔌 Connection closed.")

def calculate_advanced_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Toma un DataFrame con datos de múltiples plataformas y calcula
    métricas relevantes para cada una, añadiéndolas como nuevas columnas.
    Esta función está inspirada en 'system_prompt_metrics'.
    """
    if df.empty:
        return df
        
    processed_df = df.copy()

    # Convertir a numérico para asegurar operaciones matemáticas
    # Lista de todas las posibles columnas de métricas
    metric_cols = [
        'fa_cost', 'fa_clicks_all', 'fa_impressions', 'fa_on_facebook_leads', 'fa_website_purchases', 'fa_link_clicks',
        'ga_cost', 'ga_clicks', 'ga_impressions', 'ga_conversions',
        'tt_cost', 'tt_clicks', 'tt_impressions', 'tt_conversions',
        'dv_revenue', 'dv_clicks', 'dv_impressions', 'dv_Post_Click_Conversions'
    ]
    for col in metric_cols:
        if col in processed_df.columns:
            # Rellenar valores nulos con 0 antes de convertir a numérico
            processed_df[col] = pd.to_numeric(processed_df[col].fillna(0), errors='coerce')

    # --- Calcular Métricas por Plataforma (si las columnas existen) ---
    
    # Meta Ads (Facebook) - OJO: usa fa_clicks_all o fa_link_clicks según lo que te devuelva el SQL
    if 'fa_cost' in processed_df and ('fa_clicks_all' in processed_df or 'fa_link_clicks' in processed_df):
        click_col = 'fa_clicks_all' if 'fa_clicks_all' in processed_df else 'fa_link_clicks'
        processed_df['fa_cpc'] = (processed_df['fa_cost'] / processed_df[click_col]).where(processed_df[click_col] > 0, 0).round(2)
    if ('fa_clicks_all' in processed_df or 'fa_link_clicks' in processed_df) and 'fa_impressions' in processed_df:
        click_col = 'fa_clicks_all' if 'fa_clicks_all' in processed_df else 'fa_link_clicks'
        processed_df['fa_ctr_%'] = (processed_df[click_col] / processed_df['fa_impressions'] * 100).where(processed_df['fa_impressions'] > 0, 0).round(2)
    if 'fa_cost' in processed_df and 'fa_website_purchases' in processed_df:
        processed_df['fa_cpa_purchase'] = (processed_df['fa_cost'] / processed_df['fa_website_purchases']).where(processed_df['fa_website_purchases'] > 0, 0).round(2)

    # Google Ads
    if 'ga_cost' in processed_df and 'ga_clicks' in processed_df:
        processed_df['ga_cpc'] = (processed_df['ga_cost'] / processed_df['ga_clicks']).where(processed_df['ga_clicks'] > 0, 0).round(2)
    if 'ga_clicks' in processed_df and 'ga_impressions' in processed_df:
        processed_df['ga_ctr_%'] = (processed_df['ga_clicks'] / processed_df['ga_impressions'] * 100).where(processed_df['ga_impressions'] > 0, 0).round(2)
    if 'ga_cost' in processed_df and 'ga_conversions' in processed_df:
        processed_df['ga_cpa'] = (processed_df['ga_cost'] / processed_df['ga_conversions']).where(processed_df['ga_conversions'] > 0, 0).round(2)

    print("📊 Advanced metrics calculated for available platforms.")
    return processed_df