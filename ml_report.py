import pandas as pd
import numpy as np

# =========================
# Helpers
# =========================

def _safe_div(a, b):
    try:
        a = 0 if a is None else float(a)
        b = 0 if b is None else float(b)
        if b == 0:
            return 0.0
        return a / b
    except Exception:
        return 0.0


# =========================
# Estratégia de Campanhas
# =========================

def enrich_campaign_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["Receita"] = pd.to_numeric(out.get("Receita", 0), errors="coerce").fillna(0)
    out["Investimento"] = pd.to_numeric(out.get("Investimento", 0), errors="coerce").fillna(0)

    out["ROAS"] = out.apply(lambda r: _safe_div(r["Receita"], r["Investimento"]), axis=1)
    out["ACOS Real"] = out.apply(lambda r: _safe_div(r["Investimento"], r["Receita"]), axis=1)
    out["Lucro_proxy"] = out["Receita"] - out["Investimento"]

    return out


def classify_quadrants(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["Quadrante"] = "ESTÁVEL"

    out.loc[
        (out["ROAS"] >= 7) & (out.get("Perdidas_Orc", 0) >= 0.4),
        "Quadrante"
    ] = "ESCALA ORÇAMENTO"

    out.loc[
        (out["Receita"] > 0) & (out.get("Perdidas_Class", 0) >= 0.5),
        "Quadrante"
    ] = "COMPETITIVIDADE"

    out.loc[
        (out["ROAS"] < 3) & (out["Investimento"] > 0),
        "Quadrante"
    ] = "HEMORRAGIA"

    return out


# =========================
# Impacto Financeiro
# =========================

def estimate_impact(df: pd.DataFrame, horizon_days: int = 7) -> pd.DataFrame:
    out = df.copy()

    out["Impacto_R$"] = 0.0
    out["Ação"] = "Manter"

    # Minas
    minas = out["Quadrante"] == "ESCALA ORÇAMENTO"
    out.loc[minas, "Ação"] = "🟢 Aumentar orçamento"
    out.loc[minas, "Impacto_R$"] = (
        out.loc[minas, "Receita"]
        * out.loc[minas].get("Perdidas_Orc", 0)
        * 0.5
        * (horizon_days / 7)
    )

    # Competitividade
    comp = out["Quadrante"] == "COMPETITIVIDADE"
    out.loc[comp, "Ação"] = "🟡 Subir ACOS alvo"
    out.loc[comp, "Impacto_R$"] = (
        out.loc[comp, "Receita"]
        * 0.2
        * (horizon_days / 7)
    )

    # Hemorragia
    hem = out["Quadrante"] == "HEMORRAGIA"
    out.loc[hem, "Ação"] = "🔴 Reduzir ou pausar"
    out.loc[hem, "Impacto_R$"] = (
        -out.loc[hem, "Investimento"]
        * 0.3
        * (horizon_days / 7)
    )

    return out


# =========================
# Plano Tático
# =========================

def build_tactical_plan(camp_strat: pd.DataFrame, horizon_days: int = 7) -> pd.DataFrame:
    df = camp_strat.copy()

    actions = []

    for _, r in df.iterrows():
        if r["Quadrante"] == "ESCALA ORÇAMENTO":
            actions.append(
                f"Aumentar orçamento da campanha '{r['Nome']}' em 30%"
            )
        elif r["Quadrante"] == "COMPETITIVIDADE":
            actions.append(
                f"Subir ACOS alvo da campanha '{r['Nome']}' em +2pp"
            )
        elif r["Quadrante"] == "HEMORRAGIA":
            actions.append(
                f"Reduzir orçamento ou pausar campanha '{r['Nome']}'"
            )
        else:
            actions.append(
                f"Manter campanha '{r['Nome']}' e monitorar"
            )

    plan = pd.DataFrame({
        "Campanha": df["Nome"],
        "Ação recomendada": actions,
        "Horizonte (dias)": horizon_days
    })

    return plan


# =========================
# COMPATIBILIDADE (JEITO 1)
# =========================

def build_plan(camp_strat: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    return build_tactical_plan(camp_strat, horizon_days=int(days))


# =========================
# Rankings
# =========================

def rank_campanhas(df: pd.DataFrame, top_n: int = 10) -> dict:
    base = df.copy()
    base = base.sort_values(
        ["Lucro_proxy", "ROAS", "Receita"],
        ascending=[False, False, False]
    )

    best = base.head(top_n)

    worst = base.sort_values(
        ["Investimento", "ROAS"],
        ascending=[False, True]
    ).head(top_n)

    return {"best": best, "worst": worst}
