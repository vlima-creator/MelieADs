import pandas as pd
import numpy as np
from io import BytesIO

EMOJI_GREEN = "\U0001F7E2"
EMOJI_YELLOW = "\U0001F7E1"
EMOJI_BLUE = "\U0001F535"
EMOJI_RED = "\U0001F534"


def _safe_div(a, b):
    try:
        a = 0 if a is None else float(a)
        b = 0 if b is None else float(b)
        if b == 0:
            return 0.0
        return a / b
    except Exception:
        return 0.0


def _pct_to_float01(x):
    if pd.isna(x):
        return np.nan
    try:
        v = float(x)
        # se vier 40 significa 40%
        if v > 1.0:
            v = v / 100.0
        return v
    except Exception:
        return np.nan


# =========================
# LOADERS
# =========================

def load_organico(organico_file) -> pd.DataFrame:
    # normal: cabecalho comeca na linha 5 (header=4)
    org = pd.read_excel(organico_file, header=4)
    # padroniza nomes esperados
    org.columns = [
        "ID", "Titulo", "Status", "Variacao", "SKU",
        "Visitas", "Qtd_Vendas", "Compradores", "Unidades",
        "Vendas_Brutas", "Participacao",
        "Conv_Visitas_Vendas", "Conv_Visitas_Compradores"
    ]
    org["ID"] = org["ID"].astype(str)

    for c in ["Visitas","Qtd_Vendas","Compradores","Unidades","Vendas_Brutas","Participacao","Conv_Visitas_Vendas","Conv_Visitas_Compradores"]:
        if c in org.columns:
            org[c] = pd.to_numeric(org[c], errors="coerce")

    # conversoes em % podem vir como 2,3% ou 0,023
    for c in ["Conv_Visitas_Vendas","Conv_Visitas_Compradores","Participacao"]:
        if c in org.columns:
            org[c] = org[c].apply(_pct_to_float01)

    return org


def load_patrocinados(patrocinados_file) -> pd.DataFrame:
    pat = pd.read_excel(patrocinados_file, sheet_name="Relatório Anúncios patrocinados", header=1)

    if "Código do anúncio" in pat.columns:
        pat["ID"] = pat["Código do anúncio"].astype(str).str.replace("MLB", "", regex=False)
    elif "ID" not in pat.columns:
        pat["ID"] = pat.index.astype(str)

    cols_num = [
        "Impressões", "Cliques",
        "Receita\n(Moeda local)",
        "Investimento\n(Moeda local)",
        "Vendas por publicidade\n(Diretas + Indiretas)"
    ]
    for c in cols_num:
        if c in pat.columns:
            pat[c] = pd.to_numeric(pat[c], errors="coerce")

    return pat


def load_campanhas_consolidado(campanhas_file) -> pd.DataFrame:
    camp = pd.read_excel(campanhas_file, sheet_name="Relatório de campanha", header=1)

    if "Nome da campanha" in camp.columns and "Nome" not in camp.columns:
        camp = camp.rename(columns={"Nome da campanha": "Nome"})

    # normaliza nomes
    rename_map = {
        "Receita\n(Moeda local)": "Receita",
        "Investimento\n(Moeda local)": "Investimento",
        "Vendas por publicidade\n(Diretas + Indiretas)": "Vendas",
        "ROAS\n(Receitas / Investimento)": "ROAS",
        "CVR\n(Conversion rate)": "CVR",
        "% de impressões perdidas por orçamento": "Perdidas_Orc",
        "% de impressões perdidas por classificação": "Perdidas_Class",
        "Orçamento médio diário": "Orçamento",
    }
    camp = camp.rename(columns={k: v for k, v in rename_map.items() if k in camp.columns})

    # numericos
    for c in ["Receita","Investimento","Vendas","ROAS","CVR","Perdidas_Orc","Perdidas_Class","Orçamento","ACOS Objetivo","Impressões","Cliques"]:
        if c in camp.columns:
            camp[c] = pd.to_numeric(camp[c], errors="coerce")

    # percentuais
    for c in ["Perdidas_Orc","Perdidas_Class","CVR","ACOS Objetivo"]:
        if c in camp.columns:
            camp[c] = camp[c].apply(_pct_to_float01)

    return camp


# =========================
# AGG
# =========================

def build_campaign_agg(camp: pd.DataFrame, modo: str = "consolidado") -> pd.DataFrame:
    df = camp.copy()

    keep = ["Nome","Status","Orçamento","ACOS Objetivo","Impressões","Cliques","Receita","Investimento","Vendas","ROAS","CVR","Perdidas_Orc","Perdidas_Class"]
    keep = [c for c in keep if c in df.columns]
    df = df[keep].copy()

    # se vier duplicado por alguma quebra, agrupa por nome
    if df["Nome"].duplicated().any():
        agg = {
            "Status": "last",
            "Orçamento": "last",
            "ACOS Objetivo": "last",
            "Impressões": "sum",
            "Cliques": "sum",
            "Receita": "sum",
            "Investimento": "sum",
            "Vendas": "sum",
            "ROAS": "mean",
            "CVR": "mean",
            "Perdidas_Orc": "mean",
            "Perdidas_Class": "mean",
        }
        agg = {k: v for k, v in agg.items() if k in df.columns}
        df = df.groupby("Nome", as_index=False).agg(agg)

    return df


# =========================
# STRATEGY
# =========================

def add_strategy_fields(
    camp_agg: pd.DataFrame,
    roas_mina: float = 7.0,
    lost_budget_mina: float = 0.40,
    lost_rank_gigante: float = 0.50,
    roas_hemorragia: float = 3.0,
    acos_over_pct: float = 0.30
) -> pd.DataFrame:
    df = camp_agg.copy()

    for c in ["Receita","Investimento","Vendas","Cliques","Impressões","ROAS","CVR","Perdidas_Orc","Perdidas_Class","ACOS Objetivo","Orçamento"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df["ROAS_calc"] = df.apply(lambda r: _safe_div(r.get("Receita", 0), r.get("Investimento", 0)), axis=1)
    df["ACOS_calc"] = df.apply(lambda r: _safe_div(r.get("Investimento", 0), r.get("Receita", 0)), axis=1)
    df["Lucro_proxy"] = df.get("Receita", 0).fillna(0) - df.get("Investimento", 0).fillna(0)

    total = df["Receita"].sum() if "Receita" in df.columns else 0
    df = df.sort_values("Receita", ascending=False).reset_index(drop=True)
    df["CPI_share"] = df["Receita"] / total if total else 0
    df["CPI_cum"] = df["CPI_share"].cumsum()
    df["CPI_80"] = df["CPI_cum"] <= 0.80

    # quadrantes
    df["Quadrante"] = "ESTÁVEL"

    minas = (df["ROAS_calc"] >= roas_mina) & (df.get("Perdidas_Orc", 0).fillna(0) >= lost_budget_mina)
    df.loc[minas, "Quadrante"] = "ESCALA ORÇAMENTO"

    gigantes = (df["CPI_80"] == True) & (df.get("Perdidas_Class", 0).fillna(0) >= lost_rank_gigante)
    df.loc[gigantes, "Quadrante"] = "COMPETITIVIDADE"

    if "ACOS Objetivo" in df.columns:
        hemo = (df["ROAS_calc"] < roas_hemorragia) | (df["ACOS_calc"] > (df["ACOS Objetivo"] * (1.0 + acos_over_pct)))
    else:
        hemo = (df["ROAS_calc"] < roas_hemorragia)
    df.loc[hemo, "Quadrante"] = "HEMORRAGIA"

    df["AÇÃO"] = EMOJI_BLUE + " Manter"
    df.loc[df["Quadrante"] == "ESCALA ORÇAMENTO", "AÇÃO"] = EMOJI_GREEN + " Aumentar Orçamento"
    df.loc[df["Quadrante"] == "COMPETITIVIDADE", "AÇÃO"] = EMOJI_YELLOW + " Subir ACOS"
    df.loc[df["Quadrante"] == "HEMORRAGIA", "AÇÃO"] = EMOJI_RED + " Revisar/Pausar"

    # impacto R$
    df = add_impact_reais(df)
    return df


def add_impact_reais(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Receita_potencial_R$"] = 0.0
    out["Confianca"] = "Baixa"

    # Minas: projecao conservadora
    minas = (out["Quadrante"] == "ESCALA ORÇAMENTO") & (out["Receita"].fillna(0) > 0)
    if minas.any():
        perda = out.loc[minas, "Perdidas_Orc"].fillna(0).clip(0, 0.95)
        inc = out.loc[minas, "Receita"] * (perda / (1 - perda)) * 0.5
        out.loc[minas, "Receita_potencial_R$"] = inc.fillna(0).clip(lower=0)
        out.loc[minas, "Confianca"] = "Alta"

    # Competitividade
    comp = (out["Quadrante"] == "COMPETITIVIDADE") & (out["Receita"].fillna(0) > 0)
    if comp.any():
        perda = out.loc[comp, "Perdidas_Class"].fillna(0).clip(0, 0.95)
        inc = out.loc[comp, "Receita"] * (perda / (1 - perda)) * 0.25
        out.loc[comp, "Receita_potencial_R$"] = inc.fillna(0).clip(lower=0)
        out.loc[comp, "Confianca"] = "Media"

    # Hemorragia
    hemo = out["Quadrante"] == "HEMORRAGIA"
    out.loc[hemo, "Confianca"] = "Alta"

    out["Receita_potencial_R$"] = pd.to_numeric(out["Receita_potencial_R$"], errors="coerce").fillna(0).round(2)
    return out


# =========================
# TABLES
# =========================

def build_enter_ads(org: pd.DataFrame, pat: pd.DataFrame, enter_visitas_min: int, enter_conv_min: float) -> pd.DataFrame:
    if org is None or org.empty:
        return pd.DataFrame()

    org2 = org.copy()
    pat_ids = set(pat["ID"].astype(str).unique()) if pat is not None and not pat.empty and "ID" in pat.columns else set()
    org2["Ja_em_ads"] = org2["ID"].astype(str).isin(pat_ids)

    enter = org2[
        (~org2["Ja_em_ads"]) &
        (org2["Visitas"].fillna(0) >= enter_visitas_min) &
        (org2["Conv_Visitas_Vendas"].fillna(0) >= enter_conv_min)
    ].copy()

    enter["Ação"] = "Colocar em Ads"
    enter = enter.sort_values(["Vendas_Brutas","Visitas"], ascending=False)
    keep = ["ID","Titulo","Visitas","Conv_Visitas_Vendas","Qtd_Vendas","Vendas_Brutas","Ação"]
    keep = [c for c in keep if c in enter.columns]
    return enter[keep].head(50)


def build_pause_campaigns(camp_strat: pd.DataFrame, pause_invest_min: float, pause_cvr_max: float) -> pd.DataFrame:
    df = camp_strat.copy()
    df["Investimento"] = pd.to_numeric(df.get("Investimento", 0), errors="coerce").fillna(0)
    cvr = pd.to_numeric(df.get("CVR", np.nan), errors="coerce")

    pause = df[
        (df["Investimento"] >= pause_invest_min) &
        ((cvr.fillna(0) <= pause_cvr_max) | (df["Quadrante"] == "HEMORRAGIA"))
    ].copy()

    keep = ["Nome","Status","Investimento","Receita","ROAS_calc","CVR","Quadrante","AÇÃO","Confianca"]
    keep = [c for c in keep if c in pause.columns]
    return pause[keep].sort_values(["Investimento","Receita"], ascending=[False, True]).head(50)


def build_scale_budget(camp_strat: pd.DataFrame) -> pd.DataFrame:
    df = camp_strat[camp_strat["Quadrante"] == "ESCALA ORÇAMENTO"].copy()
    keep = ["Nome","Orçamento","Investimento","Receita","ROAS_calc","Perdidas_Orc","Receita_potencial_R$","Confianca","AÇÃO"]
    keep = [c for c in keep if c in df.columns]
    return df[keep].sort_values("Receita_potencial_R$", ascending=False)


def build_raise_acos(camp_strat: pd.DataFrame) -> pd.DataFrame:
    df = camp_strat[camp_strat["Quadrante"] == "COMPETITIVIDADE"].copy()
    keep = ["Nome","ACOS Objetivo","Investimento","Receita","ROAS_calc","Perdidas_Class","Receita_potencial_R$","Confianca","AÇÃO"]
    keep = [c for c in keep if c in df.columns]
    return df[keep].sort_values("Receita_potencial_R$", ascending=False)


def build_kpis(camp_agg: pd.DataFrame) -> pd.DataFrame:
    receita = pd.to_numeric(camp_agg.get("Receita", 0), errors="coerce").sum()
    invest = pd.to_numeric(camp_agg.get("Investimento", 0), errors="coerce").sum()
    roas = _safe_div(receita, invest)
    acos = _safe_div(invest, receita)

    return pd.DataFrame([{
        "Receita_total": receita,
        "Investimento_total": invest,
        "ROAS_conta": roas,
        "ACOS_conta": acos,
        "Qtd_campanhas": len(camp_agg),
    }])


def build_executive_diagnosis(camp_strat: pd.DataFrame, daily=None) -> dict:
    total_receita = pd.to_numeric(camp_strat.get("Receita", 0), errors="coerce").sum()
    total_inv = pd.to_numeric(camp_strat.get("Investimento", 0), errors="coerce").sum()
    roas = _safe_div(total_receita, total_inv)
    acos_real = _safe_div(total_inv, total_receita)

    veredito = "Conta intermediaria. Escale minas e destrave rank. Corte hemorragias."
    if roas >= 7:
        veredito = "Estamos deixando dinheiro na mesa. Escale orcamento e abra funil onde o rank trava."
    elif roas < 3:
        veredito = "Precisamos estancar sangria. Corte detratores e reequilibre o funil."

    return {"ROAS": roas, "ACOS_real": acos_real, "Veredito": veredito}


def build_control_panel(camp_strat: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "Nome","Status",
        "Orçamento","ACOS Objetivo",
        "Receita","Investimento","Vendas",
        "ROAS_calc","ACOS_calc",
        "Perdidas_Orc","Perdidas_Class",
        "Receita_potencial_R$","Confianca",
        "Quadrante","AÇÃO"
    ]
    keep = [c for c in keep if c in camp_strat.columns]
    return camp_strat[keep].copy()


def build_opportunity_highlights(camp_strat: pd.DataFrame) -> dict:
    df = camp_strat.copy()
    locomotivas = df[(df["CPI_80"] == True) & (df["Quadrante"] == "COMPETITIVIDADE")].copy()
    minas = df[df["Quadrante"] == "ESCALA ORÇAMENTO"].copy()

    keep = [
        "Nome","Receita","Investimento","ROAS_calc",
        "Perdidas_Class","Perdidas_Orc",
        "Receita_potencial_R$","Confianca","AÇÃO"
    ]
    keep = [c for c in keep if c in df.columns]

    locomotivas = locomotivas[keep].sort_values("Receita_potencial_R$", ascending=False).head(10).reset_index(drop=True)
    minas = minas[keep].sort_values("Receita_potencial_R$", ascending=False).head(10).reset_index(drop=True)
    return {"Locomotivas": locomotivas, "Minas": minas}


# =========================
# PLANO (e compatibilidade Jeito 1)
# =========================

def build_tactical_plan(camp_strat: pd.DataFrame, horizon_days: int = 7) -> pd.DataFrame:
    df = camp_strat.copy()

    minas = df[df["Quadrante"] == "ESCALA ORÇAMENTO"].sort_values("Receita_potencial_R$", ascending=False).head(8)
    comp = df[df["Quadrante"] == "COMPETITIVIDADE"].sort_values("Receita_potencial_R$", ascending=False).head(8)
    hemo = df[df["Quadrante"] == "HEMORRAGIA"].sort_values(["Investimento","Receita"], ascending=[False, True]).head(8)

    tasks = []

    dia_mina = 1
    dia_comp = 2
    dia_hemo = 3
    dia_monitor = 5 if horizon_days <= 7 else 10
    dia_fechamento = 7 if horizon_days <= 7 else 15

    for _, r in minas.iterrows():
        tasks.append({
            "Dia": dia_mina,
            "Tipo": "Orcamento",
            "Campanha": r.get("Nome"),
            "Acao": "Aumentar orcamento (prioridade)",
            "Impacto_R$": r.get("Receita_potencial_R$"),
            "Confianca": r.get("Confianca"),
            "Motivo": "ROAS alto e perda por orcamento"
        })

    for _, r in comp.iterrows():
        tasks.append({
            "Dia": dia_comp,
            "Tipo": "ACOS",
            "Campanha": r.get("Nome"),
            "Acao": "Subir ACOS objetivo (abrir funil)",
            "Impacto_R$": r.get("Receita_potencial_R$"),
            "Confianca": r.get("Confianca"),
            "Motivo": "Receita relevante e perda por classificacao"
        })

    for _, r in hemo.iterrows():
        tasks.append({
            "Dia": dia_hemo,
            "Tipo": "Corte",
            "Campanha": r.get("Nome"),
            "Acao": "Revisar e pausar ou reduzir",
            "Impacto_R$": 0.0,
            "Confianca": "Alta",
            "Motivo": "Hemorragia ou performance ruim"
        })

    tasks.append({
        "Dia": dia_monitor,
        "Tipo": "Monitoramento",
        "Campanha": "Conta",
        "Acao": "Monitorar ROAS, ACOS real e os detratores",
        "Impacto_R$": "",
        "Confianca": "Media",
        "Motivo": "Validar se ajustes estao funcionando"
    })

    tasks.append({
        "Dia": dia_fechamento,
        "Tipo": "Fechamento",
        "Campanha": "Conta",
        "Acao": "Fechar ciclo e preparar proximo plano",
        "Impacto_R$": "",
        "Confianca": "Media",
        "Motivo": "Decisao do proximo ciclo"
    })

    plan = pd.DataFrame(tasks)
    if not plan.empty:
        plan["Dia"] = pd.to_numeric(plan["Dia"], errors="coerce")
        plan = plan.sort_values(["Dia","Tipo"], ascending=[True, True]).reset_index(drop=True)
        if "Impacto_R$" in plan.columns:
            plan["Impacto_R$"] = pd.to_numeric(plan["Impacto_R$"], errors="coerce")
    return plan


def build_plan(camp_strat: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    return build_tactical_plan(camp_strat, horizon_days=int(days))


# =========================
# MAIN BUILD
# =========================

def build_tables(
    org: pd.DataFrame,
    camp_agg: pd.DataFrame,
    pat: pd.DataFrame,
    enter_visitas_min: int = 40,
    enter_conv_min: float = 0.02,
    pause_invest_min: float = 30.0,
    pause_cvr_max: float = 0.006,
):
    camp_strat = add_strategy_fields(camp_agg)

    kpis = build_kpis(camp_agg)
    pause = build_pause_campaigns(camp_strat, pause_invest_min=pause_invest_min, pause_cvr_max=pause_cvr_max)
    enter = build_enter_ads(org, pat, enter_visitas_min=enter_visitas_min, enter_conv_min=enter_conv_min)
    scale = build_scale_budget(camp_strat)
    acos = build_raise_acos(camp_strat)

    return kpis, pause, enter, scale, acos, camp_strat


# =========================
# EXPORT EXCEL
# =========================

def gerar_excel(kpis, camp_agg, pause, enter, scale, acos, camp_strat, daily=None, plan_df=None) -> bytes:
    panel = build_control_panel(camp_strat)
    highlights = build_opportunity_highlights(camp_strat)

    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        kpis.to_excel(writer, index=False, sheet_name="RESUMO")
        panel.to_excel(writer, index=False, sheet_name="PAINEL_GERAL")
        camp_strat.to_excel(writer, index=False, sheet_name="MATRIZ_CPI")
        highlights["Locomotivas"].to_excel(writer, index=False, sheet_name="LOCOMOTIVAS")
        highlights["Minas"].to_excel(writer, index=False, sheet_name="MINAS_LIMITADAS")

        if plan_df is not None:
            plan_df.to_excel(writer, index=False, sheet_name="PLANO_TATICO")

        pause.to_excel(writer, index=False, sheet_name="PAUSAR_CAMPANHAS")
        if enter is not None and not enter.empty:
            enter.to_excel(writer, index=False, sheet_name="ENTRAR_EM_ADS")

        scale.to_excel(writer, index=False, sheet_name="ESCALAR_ORCAMENTO")
        acos.to_excel(writer, index=False, sheet_name="SUBIR_ACOS")
        camp_agg.to_excel(writer, index=False, sheet_name="BASE_CAMPANHAS_AGG")

    out.seek(0)
    return out.read()


# =========================
# RANKINGS
# =========================

def rank_campanhas(df_camp: pd.DataFrame, top_n: int = 10) -> dict:
    df = df_camp.copy()

    df["Receita"] = pd.to_numeric(df.get("Receita", 0), errors="coerce").fillna(0)
    df["Investimento"] = pd.to_numeric(df.get("Investimento", 0), errors="coerce").fillna(0)
    df["Lucro_proxy"] = df["Receita"] - df["Investimento"]
    df["ROAS_calc"] = df.apply(lambda r: _safe_div(r["Receita"], r["Investimento"]), axis=1)

    best = df.sort_values(["Lucro_proxy","ROAS_calc","Receita"], ascending=[False, False, False]).head(top_n)

    worst_base = df[df["Investimento"] > 0].copy()
    worst_base["Zero_receita"] = (worst_base["Receita"] <= 0).astype(int)
    worst = worst_base.sort_values(["Zero_receita","Investimento","ROAS_calc"], ascending=[False, False, True]).head(top_n)

    return {"best": best, "worst": worst}


def rank_anuncios_patrocinados(pat: pd.DataFrame, top_n: int = 10) -> dict:
    df = pat.copy()

    rec = "Receita\n(Moeda local)"
    inv = "Investimento\n(Moeda local)"

    if rec not in df.columns or inv not in df.columns:
        return {"best": df.head(0), "worst": df.head(0), "best_by_campaign": None, "campaign_col": None}

    df["Receita"] = pd.to_numeric(df[rec], errors="coerce").fillna(0)
    df["Investimento"] = pd.to_numeric(df[inv], errors="coerce").fillna(0)
    df["Lucro_proxy"] = df["Receita"] - df["Investimento"]
    df["ROAS_calc"] = df.apply(lambda r: _safe_div(r["Receita"], r["Investimento"]), axis=1)
    df["ACOS_calc"] = df.apply(lambda r: _safe_div(r["Investimento"], r["Receita"]), axis=1)

    best = df.sort_values(["Lucro_proxy","ROAS_calc","Receita"], ascending=[False, False, False]).head(top_n)

    worst_base = df[df["Investimento"] > 0].copy()
    worst_base["Zero_receita"] = (worst_base["Receita"] <= 0).astype(int)
    worst = worst_base.sort_values(["Zero_receita","Investimento","ROAS_calc"], ascending=[False, False, True]).head(top_n)

    camp_col = None
    for c in df.columns:
        if "campanh" in str(c).lower():
            camp_col = c
            break

    best_by_campaign = None
    if camp_col:
        best_by_campaign = (
            df.sort_values(["Lucro_proxy","ROAS_calc"], ascending=[False, False])
              .groupby(camp_col, as_index=False)
              .head(top_n)
        )

    return {"best": best, "worst": worst, "best_by_campaign": best_by_campaign, "campaign_col": camp_col}
