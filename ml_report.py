import pandas as pd
import numpy as np
from io import BytesIO
import unicodedata


def _norm(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\n", " ").replace("\r", " ").strip()
    s = " ".join(s.split())
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower()


def _to_number(series: pd.Series) -> pd.Series:
    if series is None:
        return series
    s = series.astype(str).str.strip()
    s = s.replace({"nan": np.nan, "None": np.nan})
    s = s.str.replace("R$", "", regex=False).str.replace("%", "", regex=False)
    s = s.str.replace("\u00a0", " ", regex=False)
    s = s.str.replace(" ", "", regex=False)
    s = s.str.replace(".", "", regex=False)
    s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _find_col(df: pd.DataFrame, keywords, avoid=None):
    avoid = avoid or []
    cols = list(df.columns)
    norm_cols = [_norm(c) for c in cols]
    for i, nc in enumerate(norm_cols):
        if any(k in nc for k in keywords) and not any(a in nc for a in avoid):
            return cols[i]
    return None


def _read_excel_first_sheet(xlsx_file, header=None, nrows=None, sheet_name=None):
    """
    Garantia: nunca devolve dict.
    Se sheet_name=None, lê somente a primeira aba.
    Se por algum motivo voltar dict, pega a primeira aba.
    """
    sh = 0 if sheet_name is None else sheet_name
    obj = pd.read_excel(xlsx_file, sheet_name=sh, header=header, nrows=nrows)

    if isinstance(obj, dict):
        # pega a primeira aba do dict
        first_key = next(iter(obj.keys()))
        return obj[first_key]
    return obj


def _detect_header_row(xlsx_file, required_keywords, max_rows=30, sheet_name=None):
    raw = _read_excel_first_sheet(xlsx_file, header=None, nrows=max_rows, sheet_name=sheet_name)

    for r in range(len(raw)):
        row_vals = [_norm(v) for v in raw.iloc[r].tolist()]
        hit = 0
        for kw in required_keywords:
            if any(kw in v for v in row_vals):
                hit += 1
        if hit >= max(2, int(len(required_keywords) * 0.6)):
            return r
    return None


def _coerce_campaign_numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        nc = _norm(c)
        if any(k in nc for k in [
            "invest", "gasto", "custo", "receit", "venda", "orc", "acos", "roas",
            "cvr", "impress", "clique", "perdid", "percent"
        ]):
            df[c] = _to_number(df[c])
    return df


def load_organico(organico_file) -> pd.DataFrame:
    header_row = _detect_header_row(
        organico_file,
        required_keywords=["id", "anuncio", "vendas"],
        max_rows=40,
        sheet_name=None
    )
    if header_row is None:
        header_row = 4

    org = _read_excel_first_sheet(organico_file, header=header_row, sheet_name=None)
    org.columns = [str(c).strip() for c in org.columns]

    col_id = _find_col(org, ["id do anuncio", "id", "codigo do anuncio", "mlb"])
    col_titulo = _find_col(org, ["anuncio", "titulo"])
    col_vendas_brutas = _find_col(org, ["vendas brutas", "vendas (brl)", "vendas"], avoid=["conversao", "particip"])
    col_visitas = _find_col(org, ["visitas"])
    col_qtd_vendas = _find_col(org, ["quantidade de vendas", "qtd"], avoid=["bruta", "brl"])
    col_compradores = _find_col(org, ["compradores"])
    col_unidades = _find_col(org, ["unidades"])

    out = pd.DataFrame()
    out["ID"] = org[col_id].astype(str).str.replace("MLB", "", regex=False).str.strip() if col_id else org.iloc[:, 0].astype(str)
    out["Titulo"] = org[col_titulo].astype(str) if col_titulo else ""
    out["Visitas"] = _to_number(org[col_visitas]) if col_visitas else np.nan
    out["Qtd_Vendas"] = _to_number(org[col_qtd_vendas]) if col_qtd_vendas else np.nan
    out["Compradores"] = _to_number(org[col_compradores]) if col_compradores else np.nan
    out["Unidades"] = _to_number(org[col_unidades]) if col_unidades else np.nan
    out["Vendas_Brutas"] = _to_number(org[col_vendas_brutas]) if col_vendas_brutas else np.nan

    out = out[out["ID"].notna()]
    out["ID"] = out["ID"].astype(str).str.replace("MLB", "", regex=False).str.strip()
    return out


def load_patrocinados(patrocinados_file) -> pd.DataFrame:
    sheet_try = [
        "Relatório Anúncios patrocinados",
        "Relatorio Anuncios patrocinados",
        "Anúncios patrocinados",
        "Anuncios patrocinados",
        "Sheet1"
    ]

    df = None
    for sh in sheet_try:
        try:
            header_row = _detect_header_row(
                patrocinados_file,
                required_keywords=["anuncio", "invest", "receit"],
                max_rows=40,
                sheet_name=sh
            )
            if header_row is None:
                header_row = 0
            df = _read_excel_first_sheet(patrocinados_file, header=header_row, sheet_name=sh)
            break
        except Exception:
            df = None

    if df is None:
        header_row = _detect_header_row(
            patrocinados_file,
            required_keywords=["anuncio", "invest", "receit"],
            max_rows=40,
            sheet_name=None
        )
        if header_row is None:
            header_row = 0
        df = _read_excel_first_sheet(patrocinados_file, header=header_row, sheet_name=None)

    df.columns = [str(c).strip() for c in df.columns]

    col_id = _find_col(df, ["codigo do anuncio", "id do anuncio", "id", "mlb"], avoid=["campanha"])
    if col_id is None:
        col_id = df.columns[0]

    df["ID"] = df[col_id].astype(str).str.replace("MLB", "", regex=False).str.strip()

    col_inv = _find_col(df, ["invest", "gasto", "custo"])
    col_rec = _find_col(df, ["receita", "vendas"], avoid=["quant"])
    col_vendas = _find_col(df, ["vendas"], avoid=["receita", "bruta", "brl"])
    col_imp = _find_col(df, ["impress"])
    col_clk = _find_col(df, ["clique"])
    col_camp = _find_col(df, ["campanha", "nome da campanha", "nome campanha"])

    out = pd.DataFrame()
    out["ID"] = df["ID"]
    out["Campanha"] = df[col_camp].astype(str) if col_camp else ""
    out["Impressões"] = _to_number(df[col_imp]) if col_imp else np.nan
    out["Cliques"] = _to_number(df[col_clk]) if col_clk else np.nan
    out["Receita"] = _to_number(df[col_rec]) if col_rec else np.nan
    out["Investimento"] = _to_number(df[col_inv]) if col_inv else np.nan
    out["Vendas"] = _to_number(df[col_vendas]) if col_vendas else np.nan

    return out


def load_campanhas_diario(camp_file) -> pd.DataFrame:
    header_row = _detect_header_row(
        camp_file,
        required_keywords=["campanha", "invest", "receit"],
        max_rows=50,
        sheet_name=None
    )
    if header_row is None:
        header_row = 0

    camp = _read_excel_first_sheet(camp_file, header=header_row, sheet_name=None)
    camp.columns = [str(c).strip() for c in camp.columns]
    camp = _coerce_campaign_numeric(camp)
    return camp


def load_campanhas_consolidado(camp_file) -> pd.DataFrame:
    sheet_try = ["Relatório de campanha", "Relatorio de campanha", "Campanhas", "Sheet1"]

    df = None
    for sh in sheet_try:
        try:
            header_row = _detect_header_row(
                camp_file,
                required_keywords=["campanha", "invest", "receit"],
                max_rows=50,
                sheet_name=sh
            )
            if header_row is None:
                header_row = 0
            df = _read_excel_first_sheet(camp_file, header=header_row, sheet_name=sh)
            break
        except Exception:
            df = None

    if df is None:
        header_row = _detect_header_row(
            camp_file,
            required_keywords=["campanha", "invest", "receit"],
            max_rows=50,
            sheet_name=None
        )
        if header_row is None:
            header_row = 0
        df = _read_excel_first_sheet(camp_file, header=header_row, sheet_name=None)

    df.columns = [str(c).strip() for c in df.columns]
    df = _coerce_campaign_numeric(df)
    return df


def build_campaign_agg(camp: pd.DataFrame, modo_key: str = "auto") -> pd.DataFrame:
    if camp is None or len(camp) == 0:
        return pd.DataFrame(columns=[
            "Nome","Status","Orçamento","ACOS Objetivo","Impressões","Cliques","Receita","Investimento","Vendas",
            "ROAS","CVR","Perdidas_Orc","Perdidas_Class"
        ])

    df = camp.copy()
    df.columns = [str(c).strip() for c in df.columns]

    col_nome = _find_col(df, ["nome da campanha", "nome campanha", "campanha"], avoid=["id"])
    col_status = _find_col(df, ["status"])
    col_orc = _find_col(df, ["orcamento", "orçamento"])
    col_acos_obj = _find_col(df, ["acos objetivo", "acos alvo", "acos"], avoid=["real"])
    col_imp = _find_col(df, ["impress"])
    col_clk = _find_col(df, ["clique"])
    col_receita = _find_col(df, ["receita", "vendas"], avoid=["quant", "clique", "impress"])
    col_invest = _find_col(df, ["invest", "gasto", "custo"])
    col_vendas = _find_col(df, ["vendas"], avoid=["receita", "bruta", "brl"])
    col_roas = _find_col(df, ["roas"])
    col_cvr = _find_col(df, ["cvr", "conversion"])
    col_perc_orc = _find_col(df, ["perdidas por orçamento", "perdidas por orcamento", "perdidas orc", "impressoes perdidas por orcamento"])
    col_perc_rank = _find_col(df, ["perdidas por classificação", "perdidas por classificacao", "perdidas rank", "impressoes perdidas por classificacao"])

    out = pd.DataFrame()
    out["Nome"] = df[col_nome] if col_nome else pd.NA
    out["Status"] = df[col_status] if col_status else pd.NA
    out["Orçamento"] = _to_number(df[col_orc]) if col_orc else np.nan
    out["ACOS Objetivo"] = _to_number(df[col_acos_obj]) if col_acos_obj else np.nan
    out["Impressões"] = _to_number(df[col_imp]) if col_imp else np.nan
    out["Cliques"] = _to_number(df[col_clk]) if col_clk else np.nan
    out["Receita"] = _to_number(df[col_receita]) if col_receita else np.nan
    out["Investimento"] = _to_number(df[col_invest]) if col_invest else np.nan
    out["Vendas"] = _to_number(df[col_vendas]) if col_vendas else np.nan
    out["ROAS"] = _to_number(df[col_roas]) if col_roas else np.nan
    out["CVR"] = _to_number(df[col_cvr]) if col_cvr else np.nan
    out["Perdidas_Orc"] = _to_number(df[col_perc_orc]) if col_perc_orc else np.nan
    out["Perdidas_Class"] = _to_number(df[col_perc_rank]) if col_perc_rank else np.nan

    if out["ROAS"].isna().all():
        inv = out["Investimento"].fillna(0)
        rec = out["Receita"].fillna(0)
        out["ROAS"] = np.where(inv > 0, rec / inv, np.nan)

    out = out[out["Nome"].notna()]
    out = out[out["Nome"].astype(str).str.strip().ne("")]
    return out


def _safe_div(a, b):
    a = float(a) if a is not None else 0.0
    b = float(b) if b is not None else 0.0
    if b == 0:
        return 0.0
    return a / b


def build_kpis(camp_agg: pd.DataFrame, pat: pd.DataFrame, org: pd.DataFrame | None):
    inv_ads = float(camp_agg["Investimento"].fillna(0).sum()) if camp_agg is not None and len(camp_agg) else 0.0
    rec_ads = float(camp_agg["Receita"].fillna(0).sum()) if camp_agg is not None and len(camp_agg) else 0.0
    vendas_ads = float(camp_agg["Vendas"].fillna(0).sum()) if camp_agg is not None and len(camp_agg) else 0.0

    roas = _safe_div(rec_ads, inv_ads)
    acos = _safe_div(inv_ads, rec_ads)

    camp_unicas = int(camp_agg["Nome"].nunique()) if camp_agg is not None and "Nome" in camp_agg else 0
    ids_patrocinados = int(pat["ID"].nunique()) if pat is not None and "ID" in pat else 0

    faturamento_total = None
    tacos = None
    if org is not None and len(org) and "Vendas_Brutas" in org:
        faturamento_total = float(org["Vendas_Brutas"].fillna(0).sum())
        tacos = _safe_div(inv_ads, faturamento_total)

    return {
        "Investimento Ads (R$)": inv_ads,
        "Receita Ads (R$)": rec_ads,
        "Vendas Ads (qtd)": vendas_ads,
        "ROAS": roas,
        "ACOS": acos,
        "Campanhas únicas": camp_unicas,
        "IDs patrocinados": ids_patrocinados,
        "Faturamento total estimado (R$)": faturamento_total,
        "TACOS (conta)": tacos,
    }


def build_tacos_ranking(pat: pd.DataFrame, org: pd.DataFrame, top_n=10):
    if pat is None or org is None or len(pat) == 0 or len(org) == 0:
        return pd.DataFrame(), pd.DataFrame()

    pat2 = pat.copy()
    org2 = org.copy()

    pat2["ID"] = pat2["ID"].astype(str).str.strip()
    org2["ID"] = org2["ID"].astype(str).str.strip()

    inv_por_id = (
        pat2.groupby("ID", as_index=False)["Investimento"]
        .sum()
        .rename(columns={"Investimento": "investimento_ads"})
    )

    base = org2.merge(inv_por_id, on="ID", how="left")
    base["investimento_ads"] = base["investimento_ads"].fillna(0)
    base["faturamento_total"] = base["Vendas_Brutas"].fillna(0)

    base["TACOS"] = np.where(
        base["faturamento_total"] > 0,
        base["investimento_ads"] / base["faturamento_total"],
        np.nan
    )

    cols_show = ["ID", "Titulo", "investimento_ads", "faturamento_total", "TACOS"]
    cols_show = [c for c in cols_show if c in base.columns]

    best = base.sort_values(["TACOS", "faturamento_total"], ascending=[True, False]).head(top_n)[cols_show]
    worst = base.sort_values(["TACOS", "faturamento_total"], ascending=[False, False]).head(top_n)[cols_show]

    return best, worst


def export_snapshot_excel(camp_agg: pd.DataFrame, pat: pd.DataFrame, org: pd.DataFrame | None, kpis: dict, periodo_label: str):
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        (camp_agg if camp_agg is not None else pd.DataFrame()).to_excel(writer, index=False, sheet_name="campanhas")
        (pat if pat is not None else pd.DataFrame()).to_excel(writer, index=False, sheet_name="patrocinados")
        (org if org is not None else pd.DataFrame()).to_excel(writer, index=False, sheet_name="organico")
        pd.DataFrame([{"periodo": periodo_label, **kpis}]).to_excel(writer, index=False, sheet_name="kpis")

    bio.seek(0)
    return bio.getvalue()


def read_snapshot_excel(snapshot_file):
    x = pd.read_excel(snapshot_file, sheet_name=None)
    camp = x.get("campanhas", pd.DataFrame())
    pat = x.get("patrocinados", pd.DataFrame())
    org = x.get("organico", pd.DataFrame())
    kpis = x.get("kpis", pd.DataFrame())
    return camp, pat, org, kpis
