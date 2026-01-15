# ml_report.py
import pandas as pd
from io import BytesIO

EMOJI_GREEN = "\U0001F7E2"
EMOJI_YELLOW = "\U0001F7E1"
EMOJI_BLUE = "\U0001F535"
EMOJI_RED = "\U0001F534"

def _read_any(file):
    name = getattr(file, "name", "") or ""
    if name.lower().endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)

def _normalize(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = s.replace("\n", " ").replace("\r", " ")
    s = " ".join(s.split())
    return s

def _auto_header_df(file, required_any=None, max_rows=30):
    raw = _read_any(file)
    if required_any is None or raw.empty:
        raw.columns = [str(c).strip() for c in raw.columns]
        return raw

    required_any_n = [_normalize(x) for x in required_any]
    header_row = None

    preview = raw.head(max_rows).copy()
    for i in range(len(preview)):
        row = preview.iloc[i].tolist()
        row_n = [_normalize(x) for x in row]
        hit = any(any(req in cell for cell in row_n) for req in required_any_n)
        if hit:
            header_row = i
            break

    if header_row is None:
        raw.columns = [str(c).strip() for c in raw.columns]
        return raw

    df = _read_any(file)
    df.columns = df.iloc[header_row].astype(str).tolist()
    df = df.iloc[header_row + 1 :].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def _to_num(series):
    s = series.astype(str).str.strip()
    s = s.str.replace("R$", "", regex=False)
    s = s.str.replace("%", "", regex=False)
    s = s.str.replace(".", "", regex=False)
    s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")

def _pick_col(cols, candidates):
    cols_n = {_normalize(c): c for c in cols}
    for cand in candidates:
        cn = _normalize(cand)
        for k, orig in cols_n.items():
            if cn == k:
                return orig
    for cand in candidates:
        cn = _normalize(cand)
        for k, orig in cols_n.items():
            if cn in k:
                return orig
    return None

# -----------------------------
# ID seguro (evita perder precisao)
# -----------------------------
def _clean_id_series(s: pd.Series) -> pd.Series:
    # Mantem somente digitos e retorna string
    x = s.astype(str).str.strip()
    x = x.str.replace(r"\.0$", "", regex=True)
    x = x.str.replace(r"[^\d]", "", regex=True)
    x = x.replace("", pd.NA)
    return x

def _detect_ad_id_col(df: pd.DataFrame):
    for cand in ["ID do anúncio", "Id do anúncio", "ID do anuncio", "Id do anuncio", "ID", "id_anuncio"]:
        if cand in df.columns:
            return cand
    return None

def _detect_campaign_col(df: pd.DataFrame):
    for cand in ["Nome da campanha", "Campanha", "campaign_name", "Nome Campanha"]:
        if cand in df.columns:
            return cand
    return None

# -----------------------------
# loaders
# -----------------------------
def load_organico(organico_file) -> pd.DataFrame:
    df = _auto_header_df(
        organico_file,
        required_any=["ID do anúncio", "Vendas brutas", "Unidades vendidas", "Visitas únicas"],
    )
    return df

def load_patrocinados(patro_file) -> pd.DataFrame:
    df = _auto_header_df(
        patro_file,
        required_any=["ID do anúncio", "Investimento", "Vendas brutas", "Quantidade de vendas"],
    )
    return df

def load_campanhas_consolidado(camp_file) -> pd.DataFrame:
    df = _auto_header_df(
        camp_file,
        required_any=["Nome da campanha", "Investimento", "Receita", "Vendas", "ACOS"],
    )
    return df

def load_campanhas_diario(camp_file) -> pd.DataFrame:
    df = _auto_header_df(
        camp_file,
        required_any=["Nome da campanha", "Desde", "Investimento", "Receita"],
    )
    return df

# -----------------------------
# build campaign agg
# -----------------------------
def build_campaign_agg(camp: pd.DataFrame, modo_key: str) -> pd.DataFrame:
    df = camp.copy()
    if df.empty:
        return pd.DataFrame(columns=["Nome", "Investimento", "Receita", "Vendas", "Orçamento", "ACOS_Objetivo", "Perdidas_Orc", "Perdidas_Class"])

    c_nome = _pick_col(df.columns, ["Nome da campanha", "Nome", "Campanha"])
    c_inv = _pick_col(df.columns, ["Investimento", "Gasto", "Spend"])
    c_rec = _pick_col(df.columns, ["Receita", "Vendas (R$)", "Sales", "Receita/Vendas"])
    c_vend = _pick_col(df.columns, ["Vendas", "Quantidade de vendas"])
    c_orc = _pick_col(df.columns, ["Orçamento médio diário", "Orçamento", "Budget"])
    c_acos_obj = _pick_col(df.columns, ["ACOS Objetivo", "ACOS alvo", "ACOS objetivo"])
    c_porc_orc = _pick_col(df.columns, ["Perda por orçamento", "% perda por orçamento", "Perdidas por orçamento"])
    c_porc_rank = _pick_col(df.columns, ["Perda por classificação", "% perda por classificação", "Perda por rank", "Perdidas por classificação"])

    if c_nome is None or c_inv is None or c_rec is None:
        raise ValueError("Campanhas: preciso de Nome da Campanha, Investimento e Receita.")

    df["Nome"] = df[c_nome].astype(str).str.strip()
    df["Investimento"] = _to_num(df[c_inv]).fillna(0)
    df["Receita"] = _to_num(df[c_rec]).fillna(0)

    if c_vend:
        df["Vendas"] = pd.to_numeric(df[c_vend], errors="coerce").fillna(0)
    else:
        df["Vendas"] = 0

    if c_orc:
        df["Orçamento"] = _to_num(df[c_orc]).fillna(0)
    else:
        df["Orçamento"] = 0

    if c_acos_obj:
        df["ACOS_Objetivo"] = _to_num(df[c_acos_obj]).fillna(0) / 100.0
    else:
        df["ACOS_Objetivo"] = 0

    if c_porc_orc:
        df["Perdidas_Orc"] = _to_num(df[c_porc_orc]).fillna(0) / 100.0
    else:
        df["Perdidas_Orc"] = 0

    if c_porc_rank:
        df["Perdidas_Class"] = _to_num(df[c_porc_rank]).fillna(0) / 100.0
    else:
        df["Perdidas_Class"] = 0

    agg = df.groupby("Nome", as_index=False).agg(
        Investimento=("Investimento", "sum"),
        Receita=("Receita", "sum"),
        Vendas=("Vendas", "sum"),
        Orçamento=("Orçamento", "mean"),
        ACOS_Objetivo=("ACOS_Objetivo", "mean"),
        Perdidas_Orc=("Perdidas_Orc", "mean"),
        Perdidas_Class=("Perdidas_Class", "mean"),
    )

    agg["ROAS_Real"] = agg.apply(lambda r: r["Receita"] / r["Investimento"] if r["Investimento"] > 0 else 0, axis=1)
    agg["ACOS_Real"] = agg.apply(lambda r: r["Investimento"] / r["Receita"] if r["Receita"] > 0 else 0, axis=1)
    return agg

def build_daily_from_diario(camp: pd.DataFrame) -> pd.DataFrame:
    df = camp.copy()
    if df.empty:
        return df

    c_date = _pick_col(df.columns, ["Desde", "Data", "Dia"])
    c_inv = _pick_col(df.columns, ["Investimento", "Gasto", "Spend"])
    c_rec = _pick_col(df.columns, ["Receita", "Vendas (R$)", "Sales"])

    if not (c_date and c_inv and c_rec):
        return pd.DataFrame()

    out = pd.DataFrame()
    out["Desde"] = pd.to_datetime(df[c_date], errors="coerce")
    out["Investimento"] = _to_num(df[c_inv]).fillna(0)
    out["Receita"] = _to_num(df[c_rec]).fillna(0)
    out = out.groupby("Desde", as_index=False)[["Investimento", "Receita"]].sum()
    return out.sort_values("Desde")

# -----------------------------
# strategy tables
# -----------------------------
def _classify_quadrant(r):
    roas = float(r.get("ROAS_Real", 0))
    perd_orc = float(r.get("Perdidas_Orc", 0))
    perd_rank = float(r.get("Perdidas_Class", 0))
    acos_real = float(r.get("ACOS_Real", 0))
    acos_obj = float(r.get("ACOS_Objetivo", 0))
    receita = float(r.get("Receita", 0))

    if roas > 7 and perd_orc > 0.40:
        return "ESCALA_ORCAMENTO"
    if receita > 0 and perd_rank > 0.50:
        return "COMPETITIVIDADE"
    if (roas > 0 and roas < 3) or (acos_obj > 0 and acos_real > acos_obj * 1.30):
        return "HEMORRAGIA"
    return "ESTAVEL"

def _action_from_quadrant(q):
    if q == "ESCALA_ORCAMENTO":
        return f"{EMOJI_GREEN} Aumentar Orçamento"
    if q == "COMPETITIVIDADE":
        return f"{EMOJI_YELLOW} Subir ACOS Alvo"
    if q == "HEMORRAGIA":
        return f"{EMOJI_RED} Revisar/Pausar"
    return f"{EMOJI_BLUE} Manter"

def _cpi_flag(df):
    if df.empty:
        df["CPI80"] = False
        return df
    d = df.sort_values("Receita", ascending=False).copy()
    total = d["Receita"].sum()
    if total <= 0:
        d["CPI80"] = False
        return d
    d["Share"] = d["Receita"] / total
    d["CumShare"] = d["Share"].cumsum()
    d["CPI80"] = d["CumShare"] <= 0.80
    return d

def build_tables(
    org: pd.DataFrame,
    camp_agg: pd.DataFrame,
    pat: pd.DataFrame,
    enter_visitas_min=50,
    enter_conv_min=0.05,
    pause_invest_min=100.0,
    pause_cvr_max=0.01,
):
    df = camp_agg.copy()
    if df.empty:
        kpis = {"Investimento": 0, "Receita": 0, "Vendas": 0, "ROAS": 0}
        empty = pd.DataFrame()
        return kpis, empty, empty, empty, empty, empty

    df = _cpi_flag(df)
    df["Quadrante"] = df.apply(_classify_quadrant, axis=1)
    df["Acao_Recomendada"] = df["Quadrante"].apply(_action_from_quadrant)

    kpis = {
        "Investimento": float(df["Investimento"].sum()),
        "Receita": float(df["Receita"].sum()),
        "Vendas": float(df["Vendas"].sum()),
        "ROAS": float(df["Receita"].sum() / df["Investimento"].sum()) if df["Investimento"].sum() > 0 else 0.0,
    }

    pause = df[(df["Investimento"] >= pause_invest_min) & (df["ROAS_Real"] < 3)].copy()
    pause = pause.sort_values("Investimento", ascending=False).head(30)

    enter = pd.DataFrame()
    if org is not None and not org.empty:
        c_id = _pick_col(org.columns, ["ID do anúncio", "Id do anúncio", "ID"])
        c_vis = _pick_col(org.columns, ["Visitas únicas", "Visitas"])
        c_vendas = _pick_col(org.columns, ["Quantidade de vendas", "Vendas"])
        if c_id and c_vis and c_vendas:
            o = org.copy()
            o["ID"] = _clean_id_series(o[c_id])
            o["Visitas"] = pd.to_numeric(o[c_vis], errors="coerce").fillna(0)
            o["Vendas"] = pd.to_numeric(o[c_vendas], errors="coerce").fillna(0)
            o["CVR"] = o.apply(lambda r: r["Vendas"] / r["Visitas"] if r["Visitas"] > 0 else 0, axis=1)
            enter = o[(o["Visitas"] >= enter_visitas_min) & (o["CVR"] >= enter_conv_min)].copy()
            enter = enter.sort_values(["CVR", "Visitas"], ascending=False).head(30)

    scale = df[df["Quadrante"] == "ESCALA_ORCAMENTO"].copy()
    acos = df[df["Quadrante"] == "COMPETITIVIDADE"].copy()
    camp_strat = df.copy()
    return kpis, pause, enter, scale, acos, camp_strat

def build_executive_diagnosis(camp_strat: pd.DataFrame, daily: pd.DataFrame = None) -> dict:
    inv = float(camp_strat["Investimento"].sum()) if not camp_strat.empty else 0.0
    rec = float(camp_strat["Receita"].sum()) if not camp_strat.empty else 0.0
    roas = rec / inv if inv > 0 else 0.0
    acos_real = inv / rec if rec > 0 else 0.0

    if inv > 0 and roas >= 7:
        ver = "Estamos deixando dinheiro na mesa."
    elif inv > 0 and roas < 3:
        ver = "Precisamos estancar sangria."
    else:
        ver = "Operacao estavel, priorize destravar gargalos."

    return {"ROAS": roas, "ACOS_real": acos_real, "Veredito": ver, "Tendencias": {}}

def build_opportunity_highlights(camp_strat: pd.DataFrame) -> dict:
    if camp_strat.empty:
        return {"Locomotivas": pd.DataFrame(), "Minas": pd.DataFrame()}
    loc = camp_strat[(camp_strat["CPI80"] == True) & (camp_strat["Perdidas_Class"] > 0.50)].copy()
    minas = camp_strat[(camp_strat["ROAS_Real"] > 7) & (camp_strat["Perdidas_Orc"] > 0.40)].copy()
    loc = loc.sort_values("Receita", ascending=False).head(10)
    minas = minas.sort_values("ROAS_Real", ascending=False).head(10)
    return {"Locomotivas": loc, "Minas": minas}

def build_control_panel(camp_strat: pd.DataFrame) -> pd.DataFrame:
    if camp_strat.empty:
        return pd.DataFrame()
    cols = ["Nome", "Orçamento", "ACOS_Objetivo", "ROAS_Real", "Perdidas_Orc", "Perdidas_Class", "Acao_Recomendada"]
    cols = [c for c in cols if c in camp_strat.columns]
    out = camp_strat[cols].copy()
    return out.sort_values("Receita", ascending=False)

def build_plan(camp_strat: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    df = camp_strat.copy()
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    if days <= 7:
        base = df[df["Quadrante"].isin(["ESCALA_ORCAMENTO", "COMPETITIVIDADE"])].copy()
        base["Dia"] = "Dia 1 a 7"
        base["Tarefa"] = base["Quadrante"].map({
            "ESCALA_ORCAMENTO": "Aumentar orcamento (+20% a +40%)",
            "COMPETITIVIDADE": "Subir ACOS objetivo e destravar rank",
        }).fillna("Monitorar")
        return base[["Dia", "Nome", "Tarefa", "Acao_Recomendada", "Investimento", "Receita", "ROAS_Real"]]
    base = df.copy()
    base["Dia"] = f"Dia 1 a {days}"
    base["Tarefa"] = base["Quadrante"].map({
        "ESCALA_ORCAMENTO": "Aumentar orcamento (+20% a +40%)",
        "COMPETITIVIDADE": "Subir ACOS objetivo e destravar rank",
        "HEMORRAGIA": "Cortar sangria, reduzir alvo ou pausar",
        "ESTAVEL": "Manter e monitorar",
    }).fillna("Monitorar")
    return base[["Dia", "Nome", "Tarefa", "Acao_Recomendada", "Investimento", "Receita", "ROAS_Real"]]

# -----------------------------
# TACOS
# -----------------------------
def count_unique_ad_ids(pat: pd.DataFrame) -> int:
    if pat is None or pat.empty:
        return 0
    c = _detect_ad_id_col(pat)
    if c is None:
        return 0
    ids = _clean_id_series(pat[c])
    return int(ids.dropna().nunique())

def compute_tacos_overall_from_org(camp_agg: pd.DataFrame, org: pd.DataFrame) -> dict:
    inv_ads = float(camp_agg["Investimento"].sum()) if camp_agg is not None and not camp_agg.empty else 0.0
    c_vbr = _pick_col(org.columns, ["Vendas brutas (BRL)", "Vendas brutas", "Receita", "Vendas (R$)"])
    fatur_total = float(_to_num(org[c_vbr]).fillna(0).sum()) if c_vbr else 0.0
    tacos = inv_ads / fatur_total if fatur_total > 0 else 0.0
    return {"Faturamento_total_estimado": fatur_total, "TACOS_conta": tacos}

def compute_tacos_by_product(org: pd.DataFrame, pat: pd.DataFrame, top_n: int = 10) -> dict:
    if org is None or org.empty:
        return {"best": pd.DataFrame(), "worst": pd.DataFrame()}

    c_org_id = _detect_ad_id_col(org)
    c_org_fat = _pick_col(org.columns, ["Vendas brutas (BRL)", "Vendas brutas", "Receita", "Vendas (R$)"])
    if c_org_id is None or c_org_fat is None:
        return {"best": pd.DataFrame(), "worst": pd.DataFrame()}

    o = org.copy()
    o["ID"] = _clean_id_series(o[c_org_id])
    o["Faturamento_total"] = _to_num(o[c_org_fat]).fillna(0)
    o = o.dropna(subset=["ID"]).groupby("ID", as_index=False)["Faturamento_total"].sum()

    spend = pd.DataFrame({"ID": [], "Investimento_ads": []})
    if pat is not None and not pat.empty:
        c_pat_id = _detect_ad_id_col(pat)
        c_pat_spend = _pick_col(pat.columns, ["Investimento", "Gasto", "Spend"])
        if c_pat_id and c_pat_spend:
            p = pat.copy()
            p["ID"] = _clean_id_series(p[c_pat_id])
            p["Investimento_ads"] = _to_num(p[c_pat_spend]).fillna(0)
            spend = p.dropna(subset=["ID"]).groupby("ID", as_index=False)["Investimento_ads"].sum()

    df = o.merge(spend, on="ID", how="left")
    df["Investimento_ads"] = pd.to_numeric(df["Investimento_ads"], errors="coerce").fillna(0)

    df["Origem"] = df["Investimento_ads"].apply(lambda x: "Orgânico puro" if float(x) == 0 else "Ads + Orgânico")
    df["TACOS"] = df.apply(lambda r: (r["Investimento_ads"] / r["Faturamento_total"]) if r["Faturamento_total"] > 0 else 0, axis=1)

    cols = ["ID", "Origem", "Investimento_ads", "Faturamento_total", "TACOS"]

    best = df.sort_values(["TACOS", "Faturamento_total"], ascending=[True, False]).head(top_n)[cols]
    worst = df.sort_values(["TACOS", "Faturamento_total"], ascending=[False, False]).head(top_n)[cols]
    return {"best": best, "worst": worst}

def compute_tacos_by_campaign(org: pd.DataFrame, pat: pd.DataFrame, top_n: int = 10) -> dict:
    if org is None or org.empty or pat is None or pat.empty:
        return {"best": pd.DataFrame(), "worst": pd.DataFrame(), "campaign_col": None}

    c_pat_campaign = _detect_campaign_col(pat)
    c_pat_id = _detect_ad_id_col(pat)
    c_pat_spend = _pick_col(pat.columns, ["Investimento", "Gasto", "Spend"])
    if c_pat_campaign is None or c_pat_id is None or c_pat_spend is None:
        return {"best": pd.DataFrame(), "worst": pd.DataFrame(), "campaign_col": None}

    c_org_id = _detect_ad_id_col(org)
    c_org_fat = _pick_col(org.columns, ["Vendas brutas (BRL)", "Vendas brutas", "Receita", "Vendas (R$)"])
    if c_org_id is None or c_org_fat is None:
        return {"best": pd.DataFrame(), "worst": pd.DataFrame(), "campaign_col": c_pat_campaign}

    o = org.copy()
    o["ID"] = _clean_id_series(o[c_org_id])
    o["Faturamento_total"] = _to_num(o[c_org_fat]).fillna(0)
    o = o.dropna(subset=["ID"]).groupby("ID", as_index=False)["Faturamento_total"].sum()

    p = pat.copy()
    p["ID"] = _clean_id_series(p[c_pat_id])
    p["Investimento_ads"] = _to_num(p[c_pat_spend]).fillna(0)
    p["Campanha"] = p[c_pat_campaign].astype(str).str.strip()

    p2 = p.dropna(subset=["ID"]).groupby(["Campanha", "ID"], as_index=False)["Investimento_ads"].sum()
    merged = p2.merge(o, on="ID", how="left")
    merged["Faturamento_total"] = pd.to_numeric(merged["Faturamento_total"], errors="coerce").fillna(0)

    camp = merged.groupby("Campanha", as_index=False).agg(
        Investimento_ads=("Investimento_ads", "sum"),
        Faturamento_total=("Faturamento_total", "sum"),
    )

    camp["Origem"] = camp["Investimento_ads"].apply(lambda x: "Orgânico puro" if float(x) == 0 else "Ads + Orgânico")
    camp["TACOS"] = camp.apply(lambda r: (r["Investimento_ads"] / r["Faturamento_total"]) if r["Faturamento_total"] > 0 else 0, axis=1)

    cols = ["Campanha", "Origem", "Investimento_ads", "Faturamento_total", "TACOS"]
    best = camp.sort_values(["TACOS", "Faturamento_total"], ascending=[True, False]).head(top_n)[cols]
    worst = camp.sort_values(["TACOS", "Faturamento_total"], ascending=[False, False]).head(top_n)[cols]
    return {"best": best, "worst": worst, "campaign_col": c_pat_campaign}

# -----------------------------
# export
# -----------------------------
def gerar_excel(kpis, camp_agg, pause, enter, scale, acos, camp_strat, daily=None) -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.DataFrame([kpis]).to_excel(writer, index=False, sheet_name="KPIS")
        (camp_agg if camp_agg is not None else pd.DataFrame()).to_excel(writer, index=False, sheet_name="CAMP_AGG")
        (camp_strat if camp_strat is not None else pd.DataFrame()).to_excel(writer, index=False, sheet_name="CAMP_STRAT")
        (pause if pause is not None else pd.DataFrame()).to_excel(writer, index=False, sheet_name="PAUSAR")
        (enter if enter is not None else pd.DataFrame()).to_excel(writer, index=False, sheet_name="ENTRAR")
        (scale if scale is not None else pd.DataFrame()).to_excel(writer, index=False, sheet_name="ESCALA")
        (acos if acos is not None else pd.DataFrame()).to_excel(writer, index=False, sheet_name="COMPETIR")
        if daily is not None:
            daily.to_excel(writer, index=False, sheet_name="DIARIO")
    out.seek(0)
    return out.read()
