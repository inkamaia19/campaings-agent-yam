import pandas as pd
import psycopg2
import settings
import os
import matplotlib.pyplot as plt

def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """Se conecta a NeonDB, ejecuta SQL y devuelve un DataFrame."""
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

# --- LÓGICA DE CÁLCULO DE MÉTRICAS REFACTORIZADA ---

def _calculate_ctr(row):
    """Calcula el CTR (Click-Through Rate) para una fila de datos."""
    if 'clics' in row and 'impresiones' in row and row['impresiones'] > 0:
        return (row['clics'] / row['impresiones'] * 100)
    return 0

def _calculate_cpc(row):
    """Calcula el CPC (Costo por Clic) para una fila de datos."""
    if 'gasto' in row and 'clics' in row and row['clics'] > 0:
        return (row['gasto'] / row['clics'])
    return 0

def _calculate_cpa(row):
    """Calcula el CPA (Costo por Adquisición) para una fila de datos."""
    if 'gasto' in row and 'conversiones' in row and row['conversiones'] > 0:
        return (row['gasto'] / row['conversiones'])
    return 0

def calculate_advanced_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Función principal que orquesta el cálculo de todas las métricas de marketing.
    """
    if df.empty:
        return df
        
    processed_df = df.copy()
    
    # Asegurar que las columnas de métricas sean numéricas
    metric_cols = ['impresiones', 'clics', 'conversiones', 'gasto']
    for col in metric_cols:
        if col in processed_df.columns:
            processed_df[col] = pd.to_numeric(processed_df[col].fillna(0), errors='coerce')

    # Aplicar los cálculos y redondear
    if 'clics' in processed_df and 'impresiones' in processed_df:
        processed_df['ctr_%'] = processed_df.apply(_calculate_ctr, axis=1).round(2)
    
    if 'gasto' in processed_df and 'clics' in processed_df:
        processed_df['cpc'] = processed_df.apply(_calculate_cpc, axis=1).round(2)
        
    if 'gasto' in processed_df and 'conversiones' in processed_df:
        processed_df['cpa'] = processed_df.apply(_calculate_cpa, axis=1).round(2)
        
    print("📊 Advanced metrics calculated using modular functions.")
    return processed_df

def generate_plot(df: pd.DataFrame, plot_info: dict) -> str:
    """Genera un gráfico con Matplotlib y devuelve la ruta del archivo."""
    try:
        print(f"🎨 Generating plot: {plot_info.get('title', 'No Title')}")
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        plot_type = plot_info.get("plot_type", "bar")
        x_col = plot_info.get("x_col")
        y_col = plot_info.get("y_col")
        title = plot_info.get("title")

        if not all([x_col, y_col, title]):
             raise ValueError("Falta información para generar el gráfico (x_col, y_col, o title).")
        if x_col not in df.columns or y_col not in df.columns:
            raise ValueError(f"Las columnas '{x_col}' o '{y_col}' no se encontraron en los datos.")

        if plot_type == 'line':
            ax.plot(df[x_col], df[y_col], marker='o', linestyle='-')
        else:
            ax.bar(df[x_col], df[y_col])

        ax.set_title(title, fontsize=16)
        ax.set_xlabel(x_col.replace('_', ' ').title(), fontsize=12)
        ax.set_ylabel(y_col.replace('_', ' ').title(), fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            
        file_path = os.path.join('outputs', 'plot.png')
        plt.savefig(file_path)
        plt.close(fig)
        
        print(f"✅ Plot saved to {file_path}")
        return file_path
    except Exception as e:
        print(f"❌ Error generating plot: {e}")
        return None