import streamlit as st
import pandas as pd
import inspect

def _is_money_col(col_name: str) -> bool:
    c = str(col_name).strip().lower()
    if "receita proj" in c:
        return True
    if "potencial_receita" in c or "potencial receita" in c:
        return True
    if "orcamento" in c or "orçamento" in c:
        return True
    if "investimento" in c:
        return True
    if "vendas_brutas" in c or "vendas brutas" in c:
        return True
    if c == "receita" or c.startswith("receita "):
        return True
    return False

_PERCENT_COLS = {
    "acos real",
    "acos_real",
    "acos objetivo n",
    "acos_objetivo_n",
    "cpi_share",
    "cpi share",
    "cpi_cum",
    "cpi cum",
    "con_visitas_vendas",
    "con visitas vendas",
}

def _is_percent_col(col_name: str) -> bool:
    c = str(col_name).strip().lower().replace("__", "_")
    return c in _PERCENT_COLS

def _dataframe_accepts_column_config() -> bool:
    try:
        sig = inspect.signature(st.dataframe)
        return "column_config" in sig.parameters
    except Exception:
        return False

def show_df(df, **kwargs):
    # evita conflito se quem chamou já mandou column_config
    kwargs.pop("column_config", None)

    _st_dataframe = st.dataframe

    try:
        from pandas.io.formats.style import Styler
        if isinstance(df, Styler):
            return _st_dataframe(df, **kwargs)
    except Exception:
        pass

    if df is None:
        return st.info("Sem dados para exibir.")

    if not isinstance(df, pd.DataFrame):
        return _st_dataframe(df, **kwargs)

    if df.empty:
        return _st_dataframe(df, **kwargs)

    _df = df.copy()

    money_cols = [c for c in _df.columns if _is_money_col(c)]
    percent_cols = [c for c in _df.columns if _is_percent_col(c)]

    for c in percent_cols:
        ser = pd.to_numeric(_df[c], errors="coerce")
        try:
            vmax = ser.max(skipna=True)
            if pd.notna(vmax) and vmax <= 2:
                _df[c] = ser * 100
            else:
                _df[c] = ser
        except Exception:
            _df[c] = ser

    if not money_cols and not percent_cols:
        return _st_dataframe(_df, **kwargs)

    n_rows, n_cols = _df.shape
    n_special = len(money_cols) + len(percent_cols)

    # Só usa column_config se a sua versão do Streamlit suportar
    if _dataframe_accepts_column_config() and n_rows <= 5000 and n_cols <= 60 and n_special <= 30:
        try:
            col_config = {}
            for c in money_cols:
                col_config[c] = st.column_config.NumberColumn(format="R$ %.2f")
            for c in percent_cols:
                col_config[c] = st.column_config.NumberColumn(format="%.2f%%")
            return _st_dataframe(_df, column_config=col_config, **kwargs)
        except Exception:
            pass

    if n_rows <= 1500 and n_cols <= 40:
        try:
            fmt = {c: "R$ {:,.2f}" for c in money_cols}
            fmt.update({c: "{:.2f}%" for c in percent_cols})
            return _st_dataframe(_df.style.format(fmt), **kwargs)
        except Exception:
            pass

    for c in money_cols:
        _df[c] = pd.to_numeric(_df[c], errors="coerce")
        _df[c] = _df[c].map(lambda x: "" if pd.isna(x) else f"R$ {x:,.2f}")
    for c in percent_cols:
        _df[c] = pd.to_numeric(_df[c], errors="coerce")
        _df[c] = _df[c].map(lambda x: "" if pd.isna(x) else f"{x:.2f}%")

    return _st_dataframe(_df, **kwargs)
