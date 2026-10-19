"""HanaV Pension Tax Lab - Streamlit consultation prototype, Oct 2026."""
from datetime import date
import hashlib
import hmac
import pandas as pd
import streamlit as st
from retirement_core import (
    age_on, actual_receipt_year_from_history, calculate_withdrawal, estimate_retirement_tax, first_eligible_date,
    legacy_eligible, pension_limit, service_years, floor_krw,
)

st.set_page_config(page_title='HanaV Pension Tax Lab', page_icon='🧾', layout='wide')
# The CSS is intentionally embedded in app.py so a GitHub update to this file
# alone still provides readable colors. .streamlit/config.toml supplies a matching
# native Streamlit dark theme (including dataframe/editor internals and popovers).
st.markdown('''<style>
/* HanaV Pension Tax Lab v3: high contrast across native widgets. */
:root {
  --hv-bg:#0B1521; --hv-side:#102333; --hv-card:#172B3A;
  --hv-field:#213C50; --hv-field-border:#6A8BA0;
  --hv-line:#416073; --hv-text:#FFFFFF; --hv-soft:#E3EDF4;
  --hv-muted:#BED2DF; --hv-green:#48E4AD; --hv-green-dark:#007C61;
}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{
  background:var(--hv-bg)!important; color:var(--hv-text)!important;
}
[data-testid="stHeader"]{background:rgba(11,21,33,.94)!important}
[data-testid="stSidebar"],[data-testid="stSidebarContent"]{
  background:var(--hv-side)!important; color:var(--hv-text)!important;
}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6{
  color:var(--hv-text)!important;
}
.stApp h1{font-size:2.15rem;font-weight:850;letter-spacing:-.04em;margin-bottom:.55rem}
.stApp h3{font-weight:800;letter-spacing:-.025em;margin-top:1.15rem}
[data-testid="stSidebar"] h3{font-size:1.03rem;margin-top:.8rem}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li{line-height:1.5}
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label,
[data-testid="stSidebar"] label{
  color:var(--hv-text)!important;font-weight:700!important;opacity:1!important;
}
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
.stApp small{color:var(--hv-muted)!important;opacity:1!important}
/* Crucial: fix BOTH the input and its enclosing BaseWeb wrapper. Previously
   some date pickers retained a pale wrapper with nearly-white input text. */
.stApp [data-baseweb="input"],
.stApp [data-baseweb="input"]>div,
.stApp [data-baseweb="select"],
.stApp [data-baseweb="select"]>div,
.stApp [data-baseweb="textarea"],
.stApp [data-baseweb="textarea"]>div,
.stApp [data-testid="stDateInput"] [data-baseweb="input"],
.stApp [data-testid="stDateInput"] [data-baseweb="input"]>div,
.stApp [data-testid="stNumberInput"] [data-baseweb="input"],
.stApp [data-testid="stNumberInput"] [data-baseweb="input"]>div{
  background-color:var(--hv-field)!important;
  color:var(--hv-text)!important;
  border-color:var(--hv-field-border)!important;
}
.stApp input,.stApp textarea,
.stApp [data-baseweb="input"] input,
.stApp [data-baseweb="select"] input,
.stApp [data-testid="stDateInput"] input,
.stApp [data-testid="stNumberInput"] input{
  background:var(--hv-field)!important;
  color:var(--hv-text)!important;
  -webkit-text-fill-color:var(--hv-text)!important;
  caret-color:var(--hv-green)!important;
  font-size:.95rem!important;font-weight:650!important;
  opacity:1!important;
  color-scheme:dark;
}
.stApp input::placeholder,.stApp textarea::placeholder{
  color:var(--hv-muted)!important;-webkit-text-fill-color:var(--hv-muted)!important;opacity:1!important;
}
.stApp input:disabled,.stApp input[disabled],.stApp [aria-disabled="true"] input{
  color:var(--hv-soft)!important;-webkit-text-fill-color:var(--hv-soft)!important;opacity:1!important;
}
.stApp [data-baseweb="input"]:focus-within,
.stApp [data-baseweb="select"]:focus-within{
  outline:2px solid var(--hv-green)!important;outline-offset:1px;
}
.stApp [data-baseweb="input"] svg,
.stApp [data-baseweb="select"] svg,
.stApp [data-testid="stDateInput"] svg{
  fill:var(--hv-soft)!important;color:var(--hv-soft)!important;
}
.stApp [data-baseweb="select"] [role="combobox"],
.stApp [data-baseweb="select"] [role="combobox"] *,
.stApp [data-testid="stSelectbox"] *[aria-selected]{color:var(--hv-text)!important}
/* Dropdowns / date calendar overlays: native dark theme colors. */
[data-baseweb="popover"],[data-baseweb="menu"],
[data-baseweb="calendar"],[role="listbox"],
