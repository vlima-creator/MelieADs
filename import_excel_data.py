#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para extrair dados do template Excel e preparar para o app Streamlit
"""

import pandas as pd
import json
import os

def extract_data(file_path):
    results = {
        "cliente": {},
        "mercado_categoria": [],
        "mercado_subcategorias": []
    }
    
    # 1. Extrair Dados do Cliente
    try:
        df_cliente = pd.read_excel(file_path, sheet_name="Cliente", header=None)
        # Mapeamento baseado na estrutura observada
        results["cliente"] = {
            "empresa": df_cliente.iloc[4, 1],
            "categoria": df_cliente.iloc[5, 1],
            "ticket_medio": float(df_cliente.iloc[6, 1]),
            "margem": float(df_cliente.iloc[7, 1]),
            "faturamento_3m": float(df_cliente.iloc[8, 1]),
            "unidades_3m": int(df_cliente.iloc[9, 1]),
            "range_permitido": float(df_cliente.iloc[10, 1]),
            "ticket_custom": float(df_cliente.iloc[11, 1]) if pd.notna(df_cliente.iloc[11, 1]) else None
        }
    except Exception as e:
        print(f"Erro ao extrair dados do cliente: {e}")

    # 2. Extrair Mercado Categoria
    try:
        df_cat = pd.read_excel(file_path, sheet_name="Mercado_Categoria", skiprows=2)
        for _, row in df_cat.iterrows():
            if pd.notna(row['Periodo (texto)']):
                results["mercado_categoria"].append({
                    "periodo": str(row['Periodo (texto)']),
                    "faturamento": float(row['Faturamento (R$)']),
                    "unidades": int(row['Unidades'])
                })
    except Exception as e:
        print(f"Erro ao extrair mercado categoria: {e}")

    # 3. Extrair Mercado Subcategoria
    try:
        df_sub = pd.read_excel(file_path, sheet_name="Mercado_Subcategoria", skiprows=2)
        for _, row in df_sub.iterrows():
            if pd.notna(row['Subcategoria']):
                results["mercado_subcategorias"].append({
                    "subcategoria": row['Subcategoria'],
                    "faturamento_6m": float(row['Faturamento 6M (R$)']),
                    "unidades_6m": int(row['Unidades 6M'])
                })
    except Exception as e:
        print(f"Erro ao extrair mercado subcategoria: {e}")

    return results

if __name__ == "__main__":
    excel_path = "/home/ubuntu/upload/Template_Analise_Mercado_Marketplace_v8_Sheets(1).xlsx"
    if os.path.exists(excel_path):
        data = extract_data(excel_path)
        with open("/home/ubuntu/Tamanho-do-Mercado/initial_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("Dados extraídos com sucesso para initial_data.json")
    else:
        print(f"Arquivo não encontrado: {excel_path}")
