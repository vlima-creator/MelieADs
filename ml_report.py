import pandas as pd
from io import BytesIO

EMOJI_GREEN = "\U0001F7E2"
EMOJI_YELLOW = "\U0001F7E1"
EMOJI_BLUE = "\U0001F535"
EMOJI_RED = "\U0001F534"


def load_organico(organico_file) -> pd.DataFrame:
    org = pd.read_excel(organico_file, header=4)
    org.columns = [
        "ID","Titulo","Status","Variacao","SKU",
        "Visitas","Qtd_Vendas","Compradores",
        "Unidades","Vendas_Brutas","Participacao",
        "Conv_Visitas_Vendas","Conv_Visitas_Compradores"
    ]
    org["ID"] = org["ID"].astype(str)
    for c in ["Visitas","Qtd_Vendas","Compradores","Unidades","Vendas_Brutas","Participacao","Conv_Visitas_Vendas","Conv_Visitas_Compradores"]:
        if c in org.columns:
            org[c] = pd.to_numeric(org[c], errors="coerce")
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
        "% de impressões perdidas por classificação","Orçamento","ACOS Objetivo",
        "Orçamento médio diário"
    ]
    for c in cols_num:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_campanhas_diario(campanhas_file) -> pd.DataFrame:
    camp = pd.read_excel(campanhas_file, sheet_name="Relatório de campanha", header=1)
    if "Desde" in camp.columns:
        camp["Desde"] = pd.to_datetime(camp["Desde"], errors="coerce")

    if "Nome da campanha" in camp.columns and "Nome" not in camp.columns:
        camp = camp.rename(columns={"Nome da campanha": "Nome"})

    camp = _coerce_campaign_numeric(camp)
    return camp


def load_campanhas_consolidado(campanhas_file) -> pd.DataFrame:
    camp = pd.read_excel(campanhas_file, sheet_name="Relatório de campanha", header=1)

    if "Nome da campanha" in camp.columns and "Nome" not in camp.columns:
        camp = camp.rename(columns={"Nome da campanha": "Nome"})

    camp = _coerce_campaign_numeric(camp)
    return camp


def build_daily_from_diario(camp_diario: pd.DataFrame) -> pd.DataFrame:
    daily = camp_diario.groupby("Desde", as_index=False).agg(
        Investimento=("Investimento\n(Moeda local)", "sum"),
        Receita=("Receita\n(Moeda local)", "sum"),
        Vendas=("Vendas por publicidade\n(Diretas + Indiretas)", "sum"),
        Cliques=("Cliques", "sum"),
        Impressoes=("Impressões", "sum"),
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
    else:
        camp_agg = camp.copy()

        if "ROAS\n(Receitas / Investimento)" in camp_agg.columns and "ROAS" not in camp_agg.columns:
            camp_agg["ROAS"] = camp_agg["ROAS\n(Receitas / Investimento)"]
        if "CVR\n(Conversion rate)" in camp_agg.columns and "CVR" not in camp_agg.columns:
            camp_agg["CVR"] = camp_agg["CVR\n(Conversion rate)"]
        if "% de impressões perdidas por orçamento" in camp_agg.columns and "Perdidas_Orc" not in camp_agg.columns:
            camp_agg["Perdidas_Orc"] = camp_agg["% de impressões perdidas por orçamento"]
        if "% de impressões perdidas por classificação" in camp_agg.columns and "Perdidas_Class" not in camp_agg.columns:
            camp_agg["Perdidas_Class"] = camp_agg["% de impressões perdidas por classificação"]

        camp_agg = camp_agg.rename(columns={
            "Receita\n(Moeda local)": "Receita",
            "Investimento\n(Moeda local)": "Investimento",
            "Vendas por publicidade\n(Diretas + Indiretas)": "Vendas",
        })

        if "Orçamento" not in camp_agg.columns and "Orçamento médio diário" in camp_agg.columns:
            camp_agg["Orçamento"] = camp_agg["Orçamento médio diário"]

        keep = [
            "Nome","Status","Orçamento","ACOS Objetivo","Impressões","Cliques","Receita","Investimento","Vendas","ROAS","CVR","Perdidas_Orc","Perdidas_Class"
        ]
        camp_agg = camp_agg[[c for c in keep if c in camp_agg.columns]].copy()

    return camp_agg


def _pct(x: float) -> float:
    if pd.isna(x):
        return 0.0
    return float(x) * 100.0 if float(x) <= 1.0 else float(x)


def _safe_div(a, b):
    try:
        a = 0 if a is None else float(a)
        b = 0 if b is None else float(b)
        if b == 0:
            return 0.0
        return a / b
    except Exception:
        return 0.0


def add_strategy_fields(
    camp_agg: pd.DataFrame,
    acos_over_pct: float = 0.30,
    roas_mina: float = 7.0,
    lost_budget_mina: float = 40.0,
    lost_rank_gigante: float = 50.0,
    roas_hemorragia: float = 3.0,
) -> pd.DataFrame:
    df = camp_agg.copy()

    for c in ["Receita","Investimento","Vendas","Cliques","Impressões","ROAS","CVR","Perdidas_Orc","Perdidas_Class","ACOS Objetivo","Orçamento"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df["ACOS_real"] = (df["Investimento"] / df["Receita"]).replace([pd.NA, pd.NaT], 0)
    df["ROAS_real"] = (df["Receita"] / df["Investimento"]).replace([pd.NA, pd.NaT], 0)

    if "ACOS Objetivo" in df.columns:
        df["ACOS Objetivo"] = df["ACOS Objetivo"].apply(lambda x: _pct(x)/100.0 if not pd.isna(x) else pd.NA)

    if "Perdidas_Orc" in df.columns:
        df["Perdidas_Orc"] = df["Perdidas_Orc"].apply(lambda x: _pct(x)/100.0 if not pd.isna(x) else pd.NA)
    else:
        df["Perdidas_Orc"] = pd.NA

    if "Perdidas_Class" in df.columns:
        df["Perdidas_Class"] = df["Perdidas_Class"].apply(lambda x: _pct(x)/100.0 if not pd.isna(x) else pd.NA)
    else:
        df["Perdidas_Class"] = pd.NA

    df = df.sort_values("Receita", ascending=False).reset_index(drop=True)
    total = df["Receita"].sum()
    df["CPI_share"] = df["Receita"] / total if total else 0
    df["CPI_cum"] = df["CPI_share"].cumsum()
    df["CPI_80"] = df["CPI_cum"] <= 0.80

    df["Quadrante"] = "ESTÁVEL"

    minas = (df["ROAS_real"] >= roas_mina) & (df["Perdidas_Orc"] >= (lost_budget_mina/100.0))
    df.loc[minas, "Quadrante"] = "ESCALA ORÇAMENTO"

    gigantes = df["CPI_80"] & (df["Perdidas_Class"] >= (lost_rank_gigante/100.0))
    df.loc[gigantes, "Quadrante"] = "COMPETITIVIDADE"

    if "ACOS Objetivo" in df.columns:
        hemo = (df["ROAS_real"] < roas_hemorragia) | (df["ACOS_real"] > (df["ACOS Objetivo"] * (1.0 + acos_over_pct)))
    else:
        hemo = (df["ROAS_real"] < roas_hemorragia)
    df.loc[hemo, "Quadrante"] = "HEMORRAGIA"

    df["AÇÃO"] = EMOJI_BLUE + " Manter"
    df.loc[df["Quadrante"] == "ESCALA ORÇAMENTO", "AÇÃO"] = EMOJI_GREEN + " Aumentar Orçamento"
    df.loc[df["Quadrante"] == "COMPETITIVIDADE", "AÇÃO"] = EMOJI_YELLOW + " Subir ACOS"
    df.loc[df["Quadrante"] == "HEMORRAGIA", "AÇÃO"] = EMOJI_RED + " Revisar/Pausar"

    df = df.rename(columns={
        "ROAS_real": "ROAS",
        "ACOS_real": "ACOS real",
    })
    return df


def build_enter_ads(org: pd.DataFrame, pat: pd.DataFrame, enter_visitas_min: int, enter_conv_min: float) -> pd.DataFrame:
    org2 = org.copy()
    org2["Codigo_MLB"] = "MLB" + org2["ID"].astype(str)

    pat_ids = set(pat["ID"].astype(str).unique()) if "ID" in pat.columns else set()
    org2["Ja_em_ads"] = org2["ID"].astype(str).isin(pat_ids)

    enter = org2[
        (~org2["Ja_em_ads"]) &
        (org2["Visitas"] >= enter_visitas_min) &
        (org2["Conv_Visitas_Vendas"] >= enter_conv_min)
    ].copy()

    enter["Ação"] = "Colocar em Ads"
    enter = enter.sort_values(["Vendas_Brutas","Visitas"], ascending=False)
    enter = enter[["ID","Codigo_MLB","Titulo","Conv_Visitas_Vendas","Visitas","Qtd_Vendas","Vendas_Brutas","Ação"]]
    return enter.head(50)


def build_pause_campaigns(camp_strat: pd.DataFrame, pause_invest_min: float, pause_cvr_max: float) -> pd.DataFrame:
    df = camp_strat.copy()
    if "CVR" in df.columns:
        df["CVR"] = pd.to_numeric(df["CVR"], errors="coerce")
    df["Investimento"] = pd.to_numeric(df["Investimento"], errors="coerce")

    pause = df[
        (df["Investimento"] >= pause_invest_min) &
        ((df["CVR"].fillna(0) <= pause_cvr_max) | (df["Quadrante"] == "HEMORRAGIA"))
    ].copy()

    pause = pause.sort_values(["Investimento","Receita"], ascending=[False, True])
    keep = ["Nome","Status","Investimento","Receita","ROAS","CVR","Quadrante","AÇÃO"]
    keep = [c for c in keep if c in pause.columns]
    return pause[keep].head(50)


def build_scale_budget(camp_strat: pd.DataFrame) -> pd.DataFrame:
    df = camp_strat.copy()
    scale = df[df["Quadrante"] == "ESCALA ORÇAMENTO"].copy()
    keep = ["Nome","Orçamento","Investimento","Receita","ROAS","Perdidas_Orc","AÇÃO"]
    keep = [c for c in keep if c in scale.columns]
    return scale[keep].sort_values("Receita", ascending=False)


def build_raise_acos(camp_strat: pd.DataFrame) -> pd.DataFrame:
    df = camp_strat.copy()
    acos = df[df["Quadrante"] == "COMPETITIVIDADE"].copy()
    keep = ["Nome","ACOS Objetivo","Investimento","Receita","ROAS","Perdidas_Class","AÇÃO"]
    keep = [c for c in keep if c in acos.columns]
    return acos[keep].sort_values("Receita", ascending=False)


def build_kpis(org: pd.DataFrame, camp_agg: pd.DataFrame, pat: pd.DataFrame) -> pd.DataFrame:
    receita = pd.to_numeric(camp_agg["Receita"], errors="coerce").sum() if "Receita" in camp_agg.columns else 0
    invest = pd.to_numeric(camp_agg["Investimento"], errors="coerce").sum() if "Investimento" in camp_agg.columns else 0
    roas = (receita / invest) if invest else 0

    return pd.DataFrame([{
        "Receita_total": receita,
        "Investimento_total": invest,
        "ROAS_conta": roas,
        "Qtd_campanhas": len(camp_agg),
        "Qtd_anuncios_ads": len(pat),
        "Qtd_itens_organico": len(org),
    }])


def build_executive_diagnosis(camp_strat: pd.DataFrame, daily: pd.DataFrame = None) -> dict:
    total_receita = pd.to_numeric(camp_strat["Receita"], errors="coerce").sum()
    total_inv = pd.to_numeric(camp_strat["Investimento"], errors="coerce").sum()
    roas = (total_receita / total_inv) if total_inv else 0
    acos_real = (total_inv / total_receita) if total_receita else 0

    veredito = "Conta intermediaria. Escale minas e destrave rank. Corte hemorragias."
    if roas >= 7:
        veredito = "Estamos deixando dinheiro na mesa. Escale orcamento e abra funil onde o rank trava."
    elif roas < 3:
        veredito = "Precisamos estancar sangria. Corte detratores e reequilibre o funil."

    tendencias = {}
    if daily is not None and len(daily) >= 14:
        d = daily.sort_values("Desde").copy()
        last7 = d.tail(7)
        prev7 = d.iloc[-14:-7]
        cpc_last = (last7["Investimento"].sum() / max(last7["Cliques"].sum(), 1))
        cpc_prev = (prev7["Investimento"].sum() / max(prev7["Cliques"].sum(), 1))
        ticket_last = (last7["Receita"].sum() / max(last7["Vendas"].sum(), 1))
        ticket_prev = (prev7["Receita"].sum() / max(prev7["Vendas"].sum(), 1))
        cm_last = (last7["Investimento"].sum() / max(last7["Receita"].sum(), 1))
        cm_prev = (prev7["Investimento"].sum() / max(prev7["Receita"].sum(), 1))

        tendencias = {
            "cpc_proxy_up": (cpc_last > cpc_prev),
            "ticket_down": (ticket_last < ticket_prev),
            "cm_piorou": (cm_last > cm_prev)
        }

    return {"ROAS": roas, "ACOS_real": acos_real, "Veredito": veredito, "Tendencias": tendencias}


def build_control_panel(camp_strat: pd.DataFrame) -> pd.DataFrame:
    keep = ["Nome","Status","Orçamento","ACOS Objetivo","ROAS","Receita","Investimento","Perdidas_Orc","Perdidas_Class","Quadrante","AÇÃO"]
    keep = [c for c in keep if c in camp_strat.columns]
    return camp_strat[keep].copy()


def build_opportunity_highlights(camp_strat: pd.DataFrame) -> dict:
    df = camp_strat.copy()
    locomotivas = df[(df["CPI_80"] == True) & (df["Quadrante"] == "COMPETITIVIDADE")].copy()
    minas = df[df["Quadrante"] == "ESCALA ORÇAMENTO"].copy()

    keep = ["Nome","Receita","Investimento","ROAS","Perdidas_Class","Perdidas_Orc","AÇÃO"]
    keep = [c for c in keep if c in df.columns]

    locomotivas = locomotivas[keep].head(10).reset_index(drop=True)
    minas = minas[keep].head(10).reset_index(drop=True)

    return {"Locomotivas": locomotivas, "Minas": minas}


def build_tables(
    org: pd.DataFrame,
    camp_agg: pd.DataFrame,
    pat: pd.DataFrame,
    enter_visitas_min: int = 40,
    enter_conv_min: float = 0.02,
    pause_invest_min: float = 30.0,
    pause_cvr_max: float = 0.006,
) -> tuple:
    camp_strat = add_strategy_fields(camp_agg)

    kpis = build_kpis(org, camp_agg, pat)
    enter = build_enter_ads(org, pat, enter_visitas_min=enter_visitas_min, enter_conv_min=enter_conv_min)
    pause = build_pause_campaigns(camp_strat, pause_invest_min=pause_invest_min, pause_cvr_max=pause_cvr_max)
    scale = build_scale_budget(camp_strat)
    acos = build_raise_acos(camp_strat)

    return kpis, pause, enter, scale, acos, camp_strat


def _impact_budget(df_row) -> float:
    receita = float(df_row.get("Receita", 0) or 0)
    lost = float(df_row.get("Perdidas_Orc", 0) or 0)
    if receita <= 0 or lost <= 0:
        return 0.0
    lost = max(0.0, min(lost, 0.90))
    bruto = receita * (lost / (1 - lost))
    return max(0.0, bruto * 0.50)


def _impact_rank(df_row) -> float:
    receita = float(df_row.get("Receita", 0) or 0)
    lost = float(df_row.get("Perdidas_Class", 0) or 0)
    if receita <= 0 or lost <= 0:
        return 0.0
    lost = max(0.0, min(lost, 0.90))
    bruto = receita * (lost / (1 - lost))
    return max(0.0, bruto * 0.30)


def _suggest_budget(df_row) -> str:
    orc = df_row.get("Orçamento", None)
    lost = float(df_row.get("Perdidas_Orc", 0) or 0)
    step = 0.30
    if lost > 0.4:
        step = 0.50
    elif lost > 0.2:
        step = 0.35

    if orc is None or pd.isna(orc):
        return f"Aumentar orcamento em {int(step*100)}%"

    try:
        orc = float(orc)
        novo = orc * (1.0 + step)
        return f"Orc atual {orc:.2f}, sugerido {novo:.2f}"
    except Exception:
        return f"Aumentar orcamento em {int(step*100)}%"


def _suggest_acos(df_row) -> str:
    alvo = df_row.get("ACOS Objetivo", None)
    if alvo is None or pd.isna(alvo):
        return "Subir ACOS alvo em +3 p.p."

    try:
        alvo = float(alvo)
        novo = min(alvo + 0.03, 0.60)
        return f"ACOS alvo {alvo*100:.1f}%, sugerido {novo*100:.1f}%"
    except Exception:
        return "Subir ACOS alvo em +3 p.p."


def build_action_impact_table(camp_strat: pd.DataFrame) -> pd.DataFrame:
    df = camp_strat.copy()

    for c in ["Receita","Investimento","Perdidas_Orc","Perdidas_Class","Orçamento","ACOS Objetivo","ROAS"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    out_rows = []

    for _, r in df.iterrows():
        quad = str(r.get("Quadrante", ""))
        nome = r.get("Nome", "")
        receita = float(r.get("Receita", 0) or 0)
        inv = float(r.get("Investimento", 0) or 0)

        if quad == "ESCALA ORÇAMENTO":
            impacto = _impact_budget(r)
            out_rows.append({
                "Campanha": nome,
                "Quadrante": quad,
                "Ação": EMOJI_GREEN + " Aumentar orcamento",
                "Ajuste sugerido": _suggest_budget(r),
                "Impacto estimado (R$)": round(impacto, 2),
                "Confiança": "Alta" if impacto > 0 else "Media",
                "Receita": round(receita, 2),
                "Investimento": round(inv, 2),
            })

        elif quad == "COMPETITIVIDADE":
            impacto = _impact_rank(r)
            out_rows.append({
                "Campanha": nome,
                "Quadrante": quad,
                "Ação": EMOJI_YELLOW + " Subir ACOS alvo",
                "Ajuste sugerido": _suggest_acos(r),
                "Impacto estimado (R$)": round(impacto, 2),
                "Confiança": "Media" if impacto > 0 else "Baixa",
                "Receita": round(receita, 2),
                "Investimento": round(inv, 2),
            })

        elif quad == "HEMORRAGIA":
            economia = max(0.0, inv * 0.70)
            out_rows.append({
                "Campanha": nome,
                "Quadrante": quad,
                "Ação": EMOJI_RED + " Revisar ou pausar",
                "Ajuste sugerido": "Reduzir verba e funil, ou pausar se nao houver recuperacao",
                "Impacto estimado (R$)": round(economia, 2),
                "Confiança": "Alta" if inv > 0 else "Media",
                "Receita": round(receita, 2),
                "Investimento": round(inv, 2),
            })

    out = pd.DataFrame(out_rows)

    if out.empty:
        return out

    out = out.sort_values(["Impacto estimado (R$)"], ascending=False).reset_index(drop=True)
    return out


def build_plan(camp_strat: pd.DataFrame, days: int = 15) -> pd.DataFrame:
    df = camp_strat.copy()
    df["Receita"] = pd.to_numeric(df.get("Receita", 0), errors="coerce").fillna(0)

    minas = df[df.get("Quadrante", "") == "ESCALA ORÇAMENTO"].sort_values("Receita", ascending=False).head(5)
    gigantes = df[df.get("Quadrante", "") == "COMPETITIVIDADE"].sort_values("Receita", ascending=False).head(5)
    hemo = df[df.get("Quadrante", "") == "HEMORRAGIA"].sort_values("Investimento", ascending=False).head(5)

    tasks = []

    tasks.append({"Quando": "Dia 1", "Ação": "Executar ajustes principais", "O que fazer": "Aplicar aumentos e abertura de funil nas campanhas prioritarias"})
    for _, r in minas.iterrows():
        tasks.append({"Quando": "Dia 1", "Ação": "Aumentar orcamento", "O que fazer": f"Campanha {r.get('Nome','')}"})
    for _, r in gigantes.iterrows():
        tasks.append({"Quando": "Dia 2", "Ação": "Subir ACOS alvo", "O que fazer": f"Campanha {r.get('Nome','')}"})

    tasks.append({"Quando": "Dia 3", "Ação": "Cortar detratores", "O que fazer": "Revisar hemorragias e pausar o que nao tem sinal de recuperacao"})
    for _, r in hemo.iterrows():
        tasks.append({"Quando": "Dia 3", "Ação": "Revisar ou pausar", "O que fazer": f"Campanha {r.get('Nome','')}"})

    tasks.append({"Quando": "Dia 5", "Ação": "Monitorar elasticidade", "O que fazer": "Checar CPC proxy, ticket medio e custo marginal"})

    if days >= 15:
        tasks.append({"Quando": "Dia 7", "Ação": "Ajuste fino", "O que fazer": "Reforcar minas que continuam perdendo orcamento e segurar hemorragias"})
        tasks.append({"Quando": "Dia 10", "Ação": "Reavaliar funil", "O que fazer": "Se rank continua alto, subir mais um passo de ACOS alvo nas gigantes"})
        tasks.append({"Quando": "Dia 15", "Ação": "Fechamento e decisao", "O que fazer": "Fechar ciclo, consolidar ganhos e definir proximo passo"})

    return pd.DataFrame(tasks)


def gerar_excel(
    kpis,
    camp_agg,
    pause,
    enter,
    scale,
    acos,
    camp_strat,
    daily=None,
    plan_df=None,
    actions_df=None,
    periodo_label: str = "",
    plano_dias: int = 15,
) -> bytes:
    diag = {
        "Periodo": [periodo_label],
        "Plano_dias": [plano_dias],
        "ROAS_media": [pd.to_numeric(camp_strat["ROAS"], errors="coerce").mean()],
        "Receita_total": [pd.to_numeric(camp_strat["Receita"], errors="coerce").sum()],
        "Invest_total": [pd.to_numeric(camp_strat["Investimento"], errors="coerce").sum()],
    }
    diag_df = pd.DataFrame(diag)

    panel = build_control_panel(camp_strat)
    highlights = build_opportunity_highlights(camp_strat)

    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        diag_df.to_excel(writer, index=False, sheet_name="DIAGNOSTICO_EXEC")
        kpis.to_excel(writer, index=False, sheet_name="RESUMO")
        panel.to_excel(writer, index=False, sheet_name="PAINEL_GERAL")
        camp_strat.to_excel(writer, index=False, sheet_name="MATRIZ_CPI")
        highlights["Locomotivas"].to_excel(writer, index=False, sheet_name="LOCOMOTIVAS")
        highlights["Minas"].to_excel(writer, index=False, sheet_name="MINAS_LIMITADAS")

        if plan_df is not None:
            plan_df.to_excel(writer, index=False, sheet_name=f"PLANO_{plano_dias}_DIAS")
        if actions_df is not None:
            actions_df.to_excel(writer, index=False, sheet_name="ACOES_IMPACTO_RS")

        pause.to_excel(writer, index=False, sheet_name="PAUSAR_CAMPANHAS")
        enter.to_excel(writer, index=False, sheet_name="ENTRAR_EM_ADS")
        scale.to_excel(writer, index=False, sheet_name="ESCALAR_ORCAMENTO")
        acos.to_excel(writer, index=False, sheet_name="SUBIR_ACOS")
        camp_agg.to_excel(writer, index=False, sheet_name="BASE_CAMPANHAS_AGG")

        if daily is not None:
            daily.to_excel(writer, index=False, sheet_name="SERIE_DIARIA")

    out.seek(0)
    return out.read()


# =========================
# Rankings
# =========================

def rank_campanhas(df_camp: pd.DataFrame, top_n: int = 10) -> dict:
    df = df_camp.copy()

    if "Receita" not in df.columns and "Receita\n(Moeda local)" in df.columns:
        df["Receita"] = df["Receita\n(Moeda local)"]
    if "Investimento" not in df.columns and "Investimento\n(Moeda local)" in df.columns:
        df["Investimento"] = df["Investimento\n(Moeda local)"]

    if "Receita" not in df.columns or "Investimento" not in df.columns:
        return {"best": df.head(0), "worst": df.head(0)}

    df["Receita"] = pd.to_numeric(df["Receita"], errors="coerce").fillna(0)
    df["Investimento"] = pd.to_numeric(df["Investimento"], errors="coerce").fillna(0)

    df["Lucro_proxy"] = df["Receita"] - df["Investimento"]
    df["ROAS_calc"] = df.apply(lambda r: _safe_div(r["Receita"], r["Investimento"]), axis=1)
    df["ACOS_calc"] = df.apply(lambda r: _safe_div(r["Investimento"], r["Receita"]), axis=1)

    best = df.sort_values(["Lucro_proxy", "ROAS_calc", "Receita"], ascending=[False, False, False]).head(top_n)

    worst_base = df[df["Investimento"] > 0].copy()
    worst_base["Zero_receita"] = (worst_base["Receita"] <= 0).astype(int)
    worst = worst_base.sort_values(
        ["Zero_receita", "Investimento", "ROAS_calc", "Lucro_proxy"],
        ascending=[False, False, True, True],
    ).head(top_n)

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

    best = df.sort_values(["Lucro_proxy", "ROAS_calc", "Receita"], ascending=[False, False, False]).head(top_n)

    worst_base = df[df["Investimento"] > 0].copy()
    worst_base["Zero_receita"] = (worst_base["Receita"] <= 0).astype(int)
    worst = worst_base.sort_values(["Zero_receita", "Investimento", "ROAS_calc"], ascending=[False, False, True]).head(top_n)

    camp_col = None
    for c in df.columns:
        if "campanh" in str(c).lower():
            camp_col = c
            break

    best_by_campaign = None
    if camp_col:
        best_by_campaign = (
            df.sort_values(["Lucro_proxy", "ROAS_calc"], ascending=[False, False])
              .groupby(camp_col, as_index=False)
              .head(top_n)
        )

    return {"best": best, "worst": worst, "best_by_campaign": best_by_campaign, "campaign_col": camp_col}
