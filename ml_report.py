import pandas as pd
from io import BytesIO

EMOJI_GREEN = "🟢"
EMOJI_YELLOW = "🟡"
EMOJI_BLUE = "🔵"
EMOJI_RED = "🔴"


def load_organico(organico_file) -> pd.DataFrame:
    org = pd.read_excel(organico_file, header=4)
    org.columns = [
        "ID","Titulo","Status","Variacao","SKU",
        "Visitas","Qtd_Vendas","Compradores",
        "Unidades","Vendas_Brutas","Participacao",
        "Conv_Visitas_Vendas","Conv_Visitas_Compradores"
    ]
    org = org[org["ID"] != "ID do anúncio"].copy()

    for c in ["Visitas","Qtd_Vendas","Compradores","Unidades","Vendas_Brutas",
              "Participacao","Conv_Visitas_Vendas","Conv_Visitas_Compradores"]:
        org[c] = pd.to_numeric(org[c], errors="coerce")

    org["ID"] = org["ID"].astype(str).str.replace("MLB", "", regex=False)
    return org


def load_patrocinados(patrocinados_file) -> pd.DataFrame:
    pat = pd.read_excel(patrocinados_file, sheet_name="Relatório Anúncios patrocinados", header=1)
    pat["ID"] = pat["Código do anúncio"].astype(str).str.replace("MLB", "", regex=False)

    for c in ["Impressões","Cliques","Receita\n(Moeda local)","Investimento\n(Moeda local)",
              "Vendas por publicidade\n(Diretas + Indiretas)"]:
        if c in pat.columns:
            pat[c] = pd.to_numeric(pat[c], errors="coerce")
    return pat


def _coerce_campaign_numeric(df: pd.DataFrame) -> pd.DataFrame:
    cols_num = [
        "Impressões","Cliques","Receita\n(Moeda local)","Investimento\n(Moeda local)",
        "Vendas por publicidade\n(Diretas + Indiretas)","ROAS\n(Receitas / Investimento)",
        "CVR\n(Conversion rate)","% de impressões perdidas por orçamento",
        "% de impressões perdidas por classificação","ACOS"
    ]
    for c in cols_num:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_campanhas_diario(camp_file) -> pd.DataFrame:
    camp = pd.read_excel(camp_file, header=5)
    camp = _coerce_campaign_numeric(camp)
    camp = camp.rename(columns={"Nome da campanha": "Nome"})
    if "Nome" not in camp.columns and "Nome da campanha" in camp.columns:
        camp["Nome"] = camp["Nome da campanha"]
    return camp


def load_campanhas_consolidado(camp_file) -> pd.DataFrame:
    camp = pd.read_excel(camp_file, header=0)
    camp = _coerce_campaign_numeric(camp)
    camp = camp.rename(columns={"Nome da campanha": "Nome"})
    if "Nome" not in camp.columns and "Nome da campanha" in camp.columns:
        camp["Nome"] = camp["Nome da campanha"]
    return camp


def build_daily_from_diario(org: pd.DataFrame) -> pd.DataFrame:
    if org is None or org.empty:
        return pd.DataFrame(columns=["Desde", "Ate", "Faturamento_total", "Vendas_total"])

    daily = org.copy()
    # se vier sem datas, devolve so agregado
    if "Desde" not in daily.columns or "Ate" not in daily.columns:
        return pd.DataFrame([{
            "Desde": None,
            "Ate": None,
            "Faturamento_total": float(pd.to_numeric(daily.get("Vendas_Brutas", 0), errors="coerce").fillna(0).sum()),
            "Vendas_total": float(pd.to_numeric(daily.get("Qtd_Vendas", 0), errors="coerce").fillna(0).sum()),
        }])

    daily["Desde"] = pd.to_datetime(daily["Desde"], errors="coerce")
    daily["Ate"] = pd.to_datetime(daily["Ate"], errors="coerce")
    daily = daily.groupby(["Desde","Ate"], as_index=False).agg(
        Faturamento_total=("Vendas_Brutas","sum"),
        Vendas_total=("Qtd_Vendas","sum")
    )
    return daily.sort_values("Desde")


def build_campaign_agg(camp: pd.DataFrame, modo: str) -> pd.DataFrame:
    if modo == "diario":
        camp_agg = camp.groupby("Nome", as_index=False).agg(
            Status=("Status", "last"),
            Orçamento=("Orçamento", "last"),
            **{
                "ACOS Objetivo": ("ACOS Objetivo", "last"),
                "Impressões": ("Impressões", "sum"),
                "Cliques": ("Cliques", "sum"),
                "Receita": ("Receita\n(Moeda local)", "sum"),
                "Investimento": ("Investimento\n(Moeda local)", "sum"),
                "Vendas": ("Vendas por publicidade\n(Diretas + Indiretas)", "sum"),
                "ROAS": ("ROAS\n(Receitas / Investimento)", "mean"),
                "CVR": ("CVR\n(Conversion rate)", "mean"),
                "Perdidas_Orc": ("% de impressões perdidas por orçamento", "mean"),
                "Perdidas_Class": ("% de impressões perdidas por classificação", "mean"),
            }
        )
        return camp_agg

    camp_agg = camp.rename(columns={
        "Receita\n(Moeda local)": "Receita",
        "Investimento\n(Moeda local)": "Investimento",
        "Vendas por publicidade\n(Diretas + Indiretas)": "Vendas",
        "ROAS\n(Receitas / Investimento)": "ROAS",
        "CVR\n(Conversion rate)": "CVR",
        "% de impressões perdidas por orçamento": "Perdidas_Orc",
        "% de impressões perdidas por classificação": "Perdidas_Class",
    }).copy()

    needed = ["Nome","Investimento","Receita"]
    for c in needed:
        if c not in camp_agg.columns:
            camp_agg[c] = 0

    if "ROAS" not in camp_agg.columns:
        camp_agg["ROAS"] = camp_agg.apply(lambda r: (r["Receita"]/r["Investimento"]) if r["Investimento"] else 0, axis=1)

    if "ACOS Objetivo" not in camp_agg.columns:
        camp_agg["ACOS Objetivo"] = None

    if "Orçamento" not in camp_agg.columns:
        camp_agg["Orçamento"] = None

    if "Status" not in camp_agg.columns:
        camp_agg["Status"] = None

    if "Impressões" not in camp_agg.columns:
        camp_agg["Impressões"] = 0
    if "Cliques" not in camp_agg.columns:
        camp_agg["Cliques"] = 0
    if "Vendas" not in camp_agg.columns:
        camp_agg["Vendas"] = 0
    if "CVR" not in camp_agg.columns:
        camp_agg["CVR"] = 0
    if "Perdidas_Orc" not in camp_agg.columns:
        camp_agg["Perdidas_Orc"] = 0
    if "Perdidas_Class" not in camp_agg.columns:
        camp_agg["Perdidas_Class"] = 0

    return camp_agg


def build_tables(camp_agg: pd.DataFrame) -> dict:
    if camp_agg is None or camp_agg.empty:
        return {
            "Panel": pd.DataFrame(),
            "Locomotivas": pd.DataFrame(),
            "Minas": pd.DataFrame(),
            "Hemorragia": pd.DataFrame(),
            "Estavel": pd.DataFrame(),
        }

    df = camp_agg.copy()
    df["ROAS"] = pd.to_numeric(df.get("ROAS", 0), errors="coerce").fillna(0)
    df["Investimento"] = pd.to_numeric(df.get("Investimento", 0), errors="coerce").fillna(0)
    df["Receita"] = pd.to_numeric(df.get("Receita", 0), errors="coerce").fillna(0)
    df["Perdidas_Orc"] = pd.to_numeric(df.get("Perdidas_Orc", 0), errors="coerce").fillna(0)
    df["Perdidas_Class"] = pd.to_numeric(df.get("Perdidas_Class", 0), errors="coerce").fillna(0)

    # ACOS real (se quiser usar)
    df["ACOS_real"] = df.apply(lambda r: (r["Investimento"]/r["Receita"]) if r["Receita"] else 0, axis=1)

    # Acoes
    def action(row):
        if row["ROAS"] > 7 and row["Perdidas_Orc"] >= 0.40:
            return f"{EMOJI_GREEN} Aumentar Orçamento"
        if row["Receita"] > 0 and row["Perdidas_Class"] >= 0.50:
            return f"{EMOJI_YELLOW} Subir ACOS Alvo"
        if row["ROAS"] < 3 and row["Investimento"] > 0:
            return f"{EMOJI_RED} Revisar/Pausar"
        return f"{EMOJI_BLUE} Manter"

    df["AÇÃO"] = df.apply(action, axis=1)

    panel = df[[
        "Nome","Orçamento","ACOS Objetivo","ROAS","Perdidas_Orc","Perdidas_Class","AÇÃO",
        "Investimento","Receita"
    ]].copy()

    locomotivas = df[(df["Receita"] > 0) & (df["Perdidas_Class"] >= 0.50)].sort_values("Receita", ascending=False)
    minas = df[(df["ROAS"] > 7) & (df["Perdidas_Orc"] >= 0.40)].sort_values("ROAS", ascending=False)
    hemorragia = df[(df["ROAS"] < 3) & (df["Investimento"] > 0)].sort_values("Investimento", ascending=False)
    estavel = df[~df.index.isin(locomotivas.index) & ~df.index.isin(minas.index) & ~df.index.isin(hemorragia.index)].copy()

    return {
        "Panel": panel,
        "Locomotivas": locomotivas,
        "Minas": minas,
        "Hemorragia": hemorragia,
        "Estavel": estavel,
    }


def build_executive_diagnosis(camp_agg: pd.DataFrame) -> dict:
    if camp_agg is None or camp_agg.empty:
        return {
            "investimento": 0.0,
            "receita_ads": 0.0,
            "vendas_ads": 0.0,
            "roas": 0.0,
            "campanhas": 0,
            "texto": "Sem dados suficientes."
        }

    inv = float(pd.to_numeric(camp_agg.get("Investimento", 0), errors="coerce").fillna(0).sum())
    rec = float(pd.to_numeric(camp_agg.get("Receita", 0), errors="coerce").fillna(0).sum())
    vendas = float(pd.to_numeric(camp_agg.get("Vendas", 0), errors="coerce").fillna(0).sum())
    roas = (rec / inv) if inv > 0 else 0.0

    campanhas = int(camp_agg["Nome"].nunique()) if "Nome" in camp_agg.columns else 0

    veredito = "Estamos deixando dinheiro na mesa." if roas >= 5 else "Precisamos estancar sangria."
    txt = f"ROAS geral: {roas:.2f}. {veredito}"

    return {
        "investimento": inv,
        "receita_ads": rec,
        "vendas_ads": vendas,
        "roas": roas,
        "campanhas": campanhas,
        "texto": txt
    }


def build_opportunity_highlights(camp_agg: pd.DataFrame) -> dict:
    tabs = build_tables(camp_agg)
    return {
        "Locomotivas": tabs["Locomotivas"].head(5),
        "Minas": tabs["Minas"].head(5),
        "Hemorragia": tabs["Hemorragia"].head(5),
    }


def build_control_panel(camp_agg: pd.DataFrame) -> pd.DataFrame:
    return build_tables(camp_agg)["Panel"]


def build_7_day_plan(camp_agg: pd.DataFrame) -> pd.DataFrame:
    if camp_agg is None or camp_agg.empty:
        return pd.DataFrame(columns=["Dia", "Ação", "Campanha", "Justificativa"])

    tabs = build_tables(camp_agg)
    minas = tabs["Minas"].head(10)
    loco = tabs["Locomotivas"].head(10)
    hemo = tabs["Hemorragia"].head(10)

    rows = []
    for _, r in minas.iterrows():
        rows.append({
            "Dia": "Dia 1",
            "Ação": "Aumentar orçamento",
            "Campanha": r.get("Nome"),
            "Justificativa": "ROAS alto e perda por orçamento relevante."
        })
    for _, r in loco.iterrows():
        rows.append({
            "Dia": "Dia 2",
            "Ação": "Subir ACOS objetivo",
            "Campanha": r.get("Nome"),
            "Justificativa": "Receita relevante e perda por classificação alta."
        })
    for _, r in hemo.iterrows():
        rows.append({
            "Dia": "Dia 5",
            "Ação": "Revisar/pause",
            "Campanha": r.get("Nome"),
            "Justificativa": "ROAS baixo e gasto consumindo margem."
        })
    return pd.DataFrame(rows)


def gerar_excel(kpis: dict, pause: pd.DataFrame, enter: pd.DataFrame, scale: pd.DataFrame, acos: pd.DataFrame, camp_strat: pd.DataFrame) -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        pd.DataFrame([kpis]).to_excel(writer, index=False, sheet_name="KPIS")
        pause.to_excel(writer, index=False, sheet_name="PAUSAR")
        enter.to_excel(writer, index=False, sheet_name="SUBIR_ACOS")
        scale.to_excel(writer, index=False, sheet_name="SUBIR_ORC")
        acos.to_excel(writer, index=False, sheet_name="ACOS")
        camp_strat.to_excel(writer, index=False, sheet_name="CAMPANHAS")
    out.seek(0)
    return out.read()


# -----------------------------
# TACOS helpers (nao alteram o que ja existe)
# -----------------------------
def compute_tacos_overall_from_org(camp_agg: pd.DataFrame, org: pd.DataFrame) -> dict:
    """
    TACOS conta = investimento_ads_total / faturamento_total (organico + pago).
    Aqui o faturamento_total vem do relatorio organico (Vendas_Brutas somado).
    """
    investimento_ads = float(pd.to_numeric(camp_agg.get("Investimento", 0), errors="coerce").fillna(0).sum()) if camp_agg is not None else 0.0
    faturamento_total = float(pd.to_numeric(org.get("Vendas_Brutas", 0), errors="coerce").fillna(0).sum()) if org is not None else 0.0

    tacos = (investimento_ads / faturamento_total) if faturamento_total > 0 else 0.0
    return {
        "Investimento_ads_total": investimento_ads,
        "Faturamento_total_estimado": faturamento_total,
        "TACOS_conta": tacos,
    }


def _detect_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    if df is None or df.empty:
        return None
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    return None


def compute_tacos_by_product(org: pd.DataFrame, pat: pd.DataFrame, top_n: int = 10) -> dict:
    """
    TACOS por produto (ID):
    investimento_ads (patrocinados) / faturamento_total (organico).
    Ajuste pedido:
      - quando investimento_ads == 0, sinaliza Origem = "Organico puro"
      - inclui Titulo no ranking (pra facilitar leitura)
      - mantem TACOS = 0 (correto) para leitura estrategica
    """
    if org is None or org.empty:
        return {"best": pd.DataFrame(), "worst": pd.DataFrame()}

    base = org.copy()
    if "ID" not in base.columns:
        return {"best": pd.DataFrame(), "worst": pd.DataFrame()}

    base["ID"] = base["ID"].astype(str)

    fat = (
        base.groupby("ID", as_index=False)
        .agg(
            Faturamento_total=("Vendas_Brutas", "sum"),
            Vendas_total=("Qtd_Vendas", "sum"),
            Visitas_total=("Visitas", "sum"),
            Titulo=("Titulo", "first"),
        )
    )

    inv = pd.DataFrame({"ID": fat["ID"], "Investimento_ads": 0.0})
    if pat is not None and not pat.empty:
        pid = "ID" if "ID" in pat.columns else _detect_col(pat, ["Código do anúncio", "Codigo do anuncio", "ID do anúncio", "Id do anúncio"])
        invest_col = _detect_col(pat, ["Investimento\n(Moeda local)", "Investimento (Moeda local)", "Investimento", "Gasto", "Spend"])
        if pid and invest_col:
            tmp = pat.copy()
            tmp[pid] = tmp[pid].astype(str).str.replace("MLB", "", regex=False)
            tmp[invest_col] = pd.to_numeric(tmp[invest_col], errors="coerce").fillna(0)
            inv = tmp.groupby(pid, as_index=False).agg(Investimento_ads=(invest_col, "sum")).rename(columns={pid: "ID"})

    df = fat.merge(inv, on="ID", how="left")
    df["Investimento_ads"] = pd.to_numeric(df["Investimento_ads"], errors="coerce").fillna(0.0)
    df["Faturamento_total"] = pd.to_numeric(df["Faturamento_total"], errors="coerce").fillna(0.0)

    # Ajuste: coluna de origem para evitar leitura errada do "0"
    df["Origem"] = df["Investimento_ads"].apply(lambda x: "Organico puro" if float(x) == 0.0 else "Ads + Organico")

    df["TACOS"] = df.apply(lambda r: (r["Investimento_ads"] / r["Faturamento_total"]) if r["Faturamento_total"] > 0 else 0.0, axis=1)

    cols = ["ID", "Titulo", "Origem", "Investimento_ads", "Faturamento_total", "TACOS"]
    df = df.sort_values(["TACOS", "Faturamento_total"], ascending=[True, False])

    best = df.head(int(top_n))[cols]
    worst = df.sort_values(["TACOS", "Faturamento_total"], ascending=[False, False]).head(int(top_n))[cols]

    return {"best": best, "worst": worst}


def compute_tacos_by_campaign(org: pd.DataFrame, pat: pd.DataFrame, top_n: int = 10) -> dict:
    """
    TACOS por campanha (quando existir coluna de campanha no relatorio de patrocinados):
    investimento_ads_da_campanha / faturamento_total_dos_IDs_da_campanha (organico).
    """
    if org is None or org.empty or pat is None or pat.empty:
        return {"best": pd.DataFrame(), "worst": pd.DataFrame(), "campaign_col": None}

    camp_col = _detect_col(pat, ["Nome da campanha", "Campanha", "Campaign", "campaign_name", "Nome da Campanha"])
    if not camp_col:
        return {"best": pd.DataFrame(), "worst": pd.DataFrame(), "campaign_col": None}

    pid = "ID" if "ID" in pat.columns else _detect_col(pat, ["Código do anúncio", "Codigo do anuncio", "ID do anúncio", "Id do anúncio"])
    invest_col = _detect_col(pat, ["Investimento\n(Moeda local)", "Investimento (Moeda local)", "Investimento", "Gasto", "Spend"])
    if not pid or not invest_col:
        return {"best": pd.DataFrame(), "worst": pd.DataFrame(), "campaign_col": camp_col}

    tmp = pat.copy()
    tmp[pid] = tmp[pid].astype(str).str.replace("MLB", "", regex=False)
    tmp[invest_col] = pd.to_numeric(tmp[invest_col], errors="coerce").fillna(0)

    inv_camp = tmp.groupby(camp_col, as_index=False).agg(Investimento_ads=(invest_col, "sum"))

    org2 = org.copy()
    org2["ID"] = org2["ID"].astype(str)
    fat_id = org2.groupby("ID", as_index=False).agg(Faturamento_total=("Vendas_Brutas", "sum"))

    camp_ids = tmp[[camp_col, pid]].dropna().drop_duplicates().rename(columns={pid: "ID"})

    fat_camp = camp_ids.merge(fat_id, on="ID", how="left")
    fat_camp["Faturamento_total"] = pd.to_numeric(fat_camp["Faturamento_total"], errors="coerce").fillna(0)
    fat_camp = fat_camp.groupby(camp_col, as_index=False).agg(Faturamento_total=("Faturamento_total", "sum"))

    df = inv_camp.merge(fat_camp, on=camp_col, how="left").fillna(0)
    df["TACOS"] = df.apply(lambda r: (r["Investimento_ads"] / r["Faturamento_total"]) if r["Faturamento_total"] > 0 else 0.0, axis=1)

    cols = [camp_col, "Investimento_ads", "Faturamento_total", "TACOS"]
    best = df.sort_values(["TACOS", "Faturamento_total"], ascending=[True, False]).head(int(top_n))[cols]
    worst = df.sort_values(["TACOS", "Faturamento_total"], ascending=[False, False]).head(int(top_n))[cols]

    return {"best": best, "worst": worst, "campaign_col": camp_col}
