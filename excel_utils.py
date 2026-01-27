import pandas as pd
from io import BytesIO

def _is_money_col(col_name: str) -> bool:
    c = str(col_name).strip().lower()
    keywords = ["receita", "investimento", "orcamento", "orçamento", "vendas_brutas", "vendas brutas", "custo", "despesas", "gmv", "crédito"]
    return any(kw in c for kw in keywords)

def _is_percent_col(col_name: str) -> bool:
    c = str(col_name).strip().lower()
    keywords = ["acos", "roas", "ctr", "taxa", "cpi_share", "cpi share", "cpi_cum", "cpi cum", "con_visitas_vendas", "con visitas vendas", "%"]
    # ROAS is usually a multiplier (e.g. 5.0x), but sometimes people want it as percent. 
    # For now, let's treat ROAS separately if needed, or just as a number.
    return any(kw in c for kw in keywords) and "roas" not in c

def _is_roas_col(col_name: str) -> bool:
    c = str(col_name).strip().lower()
    return "roas" in c

def save_to_excel(dfs_dict: dict) -> bytes:
    """
    Gera um arquivo Excel formatado a partir de um dicionário de DataFrames.
    
    Args:
        dfs_dict: Dicionário onde a chave é o nome da aba e o valor é o DataFrame.
        
    Returns:
        bytes: Conteúdo do arquivo Excel.
    """
    output = BytesIO()
    # Usando xlsxwriter para maior controle de formatação
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Definição de formatos
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        money_format = workbook.add_format({'num_format': 'R$ #,##0.00', 'border': 1})
        percent_format = workbook.add_format({'num_format': '0.00%', 'border': 1})
        roas_format = workbook.add_format({'num_format': '0.00"x"', 'border': 1})
        default_format = workbook.add_format({'border': 1})
        
        for sheet_name, df in dfs_dict.items():
            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                continue
                
            # Limitar nome da aba a 31 caracteres (limite do Excel)
            sheet_name = sheet_name[:31]
            
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            
            # Formatar cabeçalho
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Ajustar largura das colunas e aplicar formatos
            for i, col in enumerate(df.columns):
                # Encontrar a maior largura (nome da coluna ou dados)
                column_len = max(df[col].astype(str).map(len).max(), len(str(col))) + 2
                column_len = min(column_len, 50) # Limite máximo de largura
                
                # Definir formato baseado no nome da coluna
                fmt = default_format
                if _is_money_col(col):
                    fmt = money_format
                elif _is_percent_col(col):
                    fmt = percent_format
                    # Se os dados estiverem em 0-100 (ex: 15.5 em vez de 0.155), 
                    # precisamos ajustar para o formato de porcentagem do Excel funcionar
                    try:
                        ser = pd.to_numeric(df[col], errors='coerce')
                        if ser.max() > 2:
                            # Reescreve a coluna na planilha com valores divididos por 100
                            # para que o formato de % do Excel (que multiplica por 100) funcione
                            for row_num, value in enumerate(ser):
                                if pd.notna(value):
                                    worksheet.write(row_num + 1, i, value / 100, fmt)
                                else:
                                    worksheet.write(row_num + 1, i, None, fmt)
                            # Pula o set_column padrão pois já escrevemos os dados
                            worksheet.set_column(i, i, column_len, fmt)
                            continue
                    except:
                        pass
                elif _is_roas_col(col):
                    fmt = roas_format
                
                worksheet.set_column(i, i, column_len, fmt)
                
            # Congelar a primeira linha
            worksheet.freeze_panes(1, 0)
            
    return output.getvalue()
