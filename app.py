"""HanaV Pension Tax Lab - Streamlit consultation prototype, Oct 2026."""
from datetime import date
from decimal import Decimal
from html import escape
import hashlib
import hmac
import math
import pandas as pd
import streamlit as st
from retirement_core import (
    age_on, actual_receipt_year_from_history, calculate_withdrawal, estimate_retirement_tax, first_eligible_date,
    legacy_eligible, pension_limit, service_years, floor_krw,
    converted_pay_deduction, income_tax_on_base, retirement_tax_multiplier, age_pension_tax_rate,
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
[data-baseweb="popover"] [role="dialog"]{
  background:var(--hv-card)!important;color:var(--hv-text)!important;
  border-color:var(--hv-field-border)!important;
}
[data-baseweb="popover"] *,[data-baseweb="menu"] *,
[data-baseweb="calendar"] *,[role="listbox"] *{color:var(--hv-text)}
[role="option"][aria-selected="true"],[role="option"]:hover{
  background-color:#275842!important;
}
/* Step buttons, downloads, and selected controls */
.stButton button,.stDownloadButton button,
[data-testid="stNumberInput"] button{
  background:var(--hv-green-dark)!important;color:#FFFFFF!important;
  border:1px solid #3AE1B0!important;font-weight:750!important;border-radius:8px!important;
}
.stButton button *,.stDownloadButton button *,
[data-testid="stNumberInput"] button *{color:#FFFFFF!important}
.stButton button:hover,.stDownloadButton button:hover,
[data-testid="stNumberInput"] button:hover{background:#029775!important}
.stApp [data-baseweb="checkbox"] [aria-checked="true"]{
  background:var(--hv-green-dark)!important;border-color:var(--hv-green)!important;
}
.stApp [data-baseweb="radio"] [aria-checked="true"]{
  border-color:var(--hv-green)!important;
}
[data-testid="stDataFrame"],[data-testid="stTable"],
[data-testid="stExpander"]{
  background:var(--hv-card)!important;border:1px solid var(--hv-line)!important;
  border-radius:11px;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary *{color:var(--hv-text)!important}
[data-testid="stAlert"]{border-radius:11px}
[data-testid="stAlert"] p,[data-testid="stAlert"] li{color:var(--hv-text)!important}
.stApp hr{border-color:var(--hv-line)!important}
.stApp a{color:#62F0C4!important}
/* Custom KPI replaces st.metric, whose value and label ellipsize at 4 columns. */
.hv-kpi-grid{
  display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:8px 0 19px;
}
.hv-kpi{
  min-width:0;background:var(--hv-card);
  border:1px solid var(--hv-line);border-top:3px solid #16BE8B;
  border-radius:12px;padding:14px 13px 12px;
  display:flex;flex-direction:column;justify-content:space-between;gap:8px;
}
.hv-kpi-label{color:var(--hv-soft);font-weight:700;font-size:.85rem;
  line-height:1.45;min-height:2.55em;overflow-wrap:anywhere;
}
.hv-kpi-value{color:#FFFFFF;font-weight:850;letter-spacing:-.04em;
  font-size:clamp(1.22rem,1.72vw,1.68rem);line-height:1.25;
  font-variant-numeric:tabular-nums;overflow-wrap:anywhere;word-break:keep-all;
}
.hv-kpi-detail{color:var(--hv-muted);font-size:.76rem;line-height:1.3;
  font-variant-numeric:tabular-nums;overflow-wrap:anywhere;
}
.hv-kpi--green{border-top-color:var(--hv-green)}
.hv-kpi--green .hv-kpi-value{color:#75F5CA}
.hv-kpi-grid--solo{grid-template-columns:minmax(0,1fr);max-width:100%}
.hv-kpi-grid--solo .hv-kpi{min-height:92px}
@media (max-width:1050px){
  .hv-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .hv-kpi-grid--solo{grid-template-columns:1fr}
  .hv-kpi-label{min-height:0}
  .hv-kpi-value{font-size:1.42rem}
}
@media (max-width:570px){
  .hv-kpi{padding:11px 10px;gap:5px}
  .hv-kpi-label{font-size:.78rem}
  .hv-kpi-value{font-size:1.15rem}
  .hv-kpi-detail{font-size:.7rem}
  .stApp h1{font-size:1.7rem}
}

/* Limit formula popover trigger: fix white-on-white default Streamlit button.
   st.popover does not inherit the .stButton styles above. */
.stApp [data-testid="stPopover"] button,
.stApp [data-testid="stPopover"] [data-testid^="stBaseButton"] {
  background:#173849!important;
  background-color:#173849!important;
  color:#F7FFFC!important;
  -webkit-text-fill-color:#F7FFFC!important;
  border:1px solid #48E4AD!important;
  border-radius:9px!important;
  box-shadow:0 0 0 1px rgba(72,228,173,.09)!important;
  min-height:42px!important;
  padding:9px 16px!important;
  font-size:.93rem!important;
  font-weight:800!important;
  opacity:1!important;
}
.stApp [data-testid="stPopover"] button *,
.stApp [data-testid="stPopover"] [data-testid^="stBaseButton"] * {
  color:#F7FFFC!important;
  -webkit-text-fill-color:#F7FFFC!important;
  opacity:1!important;
}
.stApp [data-testid="stPopover"] button:hover,
.stApp [data-testid="stPopover"] button[aria-expanded="true"] {
  background:#006E59!important;
  background-color:#006E59!important;
  border-color:#73F7CD!important;
}
.stApp [data-testid="stPopover"] button:focus-visible {
  outline:2px solid #73F7CD!important;
  outline-offset:2px!important;
}
/* Open formula content retains dark text contrast even without config.toml. */
[data-testid="stPopoverBody"],
[data-baseweb="popover"] [data-testid="stPopoverBody"] {
  background:#172B3A!important;
  color:#FFFFFF!important;
  border:1px solid #416073!important;
}
[data-testid="stPopoverBody"] p,
[data-testid="stPopoverBody"] h4,
[data-testid="stPopoverBody"] strong,
[data-testid="stPopoverBody"] span {color:#F7FFFC!important}

/* Hover/focus explanation table: replaces Streamlit's pale dataframe inside expander. */
.hv-calc-intro{color:#C9DEE8;font-size:.86rem;margin:2px 0 12px}
.hv-calc-scroll{width:100%;overflow:visible}
.hv-calc-table{border-collapse:separate;border-spacing:0;width:100%;
  background:#152939;border:1px solid #496E81;border-radius:11px;
  color:#F7FBFF;font-variant-numeric:tabular-nums}
.hv-calc-table th{background:#20394B;color:#EBF8FE;text-align:left;
  font-size:.86rem;padding:12px 14px;border-bottom:1px solid #496E81}
.hv-calc-table th:last-child{text-align:right;min-width:142px}
.hv-calc-table td{padding:11px 14px;border-bottom:1px solid #355369;
  vertical-align:top;font-size:.92rem;line-height:1.6}
.hv-calc-table tr:last-child td{border-bottom:0}
.hv-calc-row:hover,.hv-calc-row:focus,.hv-calc-row:focus-within{
  background:#234559;outline:0}
.hv-calc-label{font-weight:730;color:#FFF}
.hv-calc-help{margin-left:8px;color:#64F5C7;font-size:.82rem;
  cursor:help;border:1px solid #28896F;border-radius:999px;
  display:inline-flex;width:20px;height:20px;align-items:center;justify-content:center}
.hv-calc-help:focus{outline:2px solid #64F5C7;outline-offset:2px}
.hv-calc-amount{text-align:right;white-space:nowrap;color:#E7FFF7;font-weight:740}
.hv-calc-steps{display:none;margin-top:9px;background:#102636;
  border:1px solid #3E7880;border-left:3px solid #48E4AD;
  padding:11px 13px;border-radius:8px;line-height:1.65;
  font-size:.85rem;color:#E5F3F9;overflow-wrap:anywhere;word-break:keep-all}
.hv-calc-row:hover .hv-calc-steps,
.hv-calc-row:focus .hv-calc-steps,
.hv-calc-row:focus-within .hv-calc-steps{display:block}
.hv-calc-formula{color:#91F6D3;font-weight:760;margin-bottom:5px}
.hv-calc-numbers{color:#FFFFFF}
.hv-calc-note{color:#BCD7E3;font-size:.79rem;margin-top:5px}
@media(max-width:600px){
 .hv-calc-table th,.hv-calc-table td{padding:10px 8px;font-size:.8rem}
 .hv-calc-table th:last-child{min-width:102px}
 .hv-calc-steps{font-size:.78rem;padding:9px}
}

/* Breakdown for individual pension / non-pension withdrawal tax routes. */
.hv-tax-summary{
  margin:4px 0 16px;padding:15px 18px;background:#132A3A;
  border:1px solid #467488;border-left:4px solid #48E4AD;
  border-radius:11px;line-height:1.8;color:#F4FCFF;
}
.hv-tax-summary strong{color:#83F6CF}
.hv-tax-steps{
  background:#132939;border:1px solid #3E6979;
  border-radius:10px;overflow:hidden;margin:10px 0 15px;
}
.hv-tax-step{
  padding:14px 16px;border-bottom:1px solid #355667;color:#EFF9FD;
}
.hv-tax-step:last-child{border-bottom:0}
.hv-tax-step-title{color:#77F4C8;font-weight:800;line-height:1.45;overflow-wrap:anywhere}
.hv-tax-step-formula{color:#FFFFFF;line-height:1.75;font-size:.90rem;
  margin-top:8px;overflow-wrap:anywhere;word-break:keep-all}
.hv-tax-step-foot{color:#BFD8E5;margin-top:6px;font-size:.85rem;
  line-height:1.6;overflow-wrap:anywhere}
.hv-tax-two-col{
  display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:12px 0 20px
}
.hv-tax-result{background:#172B3A;border:1px solid #416073;
  border-top:3px solid #48E4AD;border-radius:11px;padding:14px 16px}
.hv-tax-result--excess{border-top-color:#F2BC73}
.hv-tax-result-name{color:#DCEEF7;font-weight:750;font-size:.9rem;line-height:1.6}
.hv-tax-result-value{color:#FFFFFF;font-size:1.3rem;font-weight:850;
  margin-top:7px;overflow-wrap:anywhere}
.hv-tax-result-detail{color:#BED2DF;line-height:1.65;font-size:.81rem;margin-top:5px}
@media(max-width:650px){.hv-tax-two-col{grid-template-columns:1fr}}

/* Automatically-linked ledger balances and highlighted customer withdrawal. */
.hv-linked-hint{
  color:#8AEBC7;font-size:.79rem;font-weight:730;
  letter-spacing:-.01em;margin:0 0 .22rem;
}
.hv-customer-withdrawal-label{
  font-size:.99rem;font-weight:850;color:#FFE29D;
  letter-spacing:-.015em;margin:0 0 7px;
}
.hv-customer-withdrawal-hint{color:#F4DCA4;font-size:.78rem;margin:8px 0 0}
/* Streamlit container(key=...) emits the st-key- class. Scope the amber palette
   to this one input so every other number field retains its Hana-green theme. */
.st-key-hv_withdrawal_highlight{
  background:#2B2D29!important;
  border:1.5px solid #E9B760!important;
  border-left:5px solid #F9C86E!important;
  border-radius:12px!important;
  padding:12px 13px 10px!important;
  margin-top:7px!important;
}
.st-key-hv_withdrawal_highlight [data-testid="stNumberInput"] [data-baseweb="input"],
.st-key-hv_withdrawal_highlight [data-testid="stNumberInput"] [data-baseweb="input"] > div{
  background:#493B29!important;border-color:#F4CD7E!important;
}
.st-key-hv_withdrawal_highlight [data-testid="stNumberInput"] input{
  background:#493B29!important;
  color:#FFF5DA!important;
  -webkit-text-fill-color:#FFF5DA!important;
  font-weight:850!important;
  font-size:1.13rem!important;
  caret-color:#FFF5DA!important;
}
.st-key-hv_withdrawal_highlight [data-testid="stNumberInput"] button{
  background:#986A1D!important;border-color:#F5C66B!important;
}
.st-key-hv_withdrawal_highlight [data-testid="stNumberInput"] button:hover{
  background:#B6832A!important;
}
</style>''', unsafe_allow_html=True)


def _short_krw(value: int) -> str:
    # Readable headline; exact won value always appears below.
    n = int(value)
    if n < 10_000:
        return f'{n:,}원'
    if n < 100_000_000:
        units = n / 10_000
        if n % 10_000 == 0:
            return f'{int(units):,}만원'
        return f'약 {units:,.1f}만원'
    eok, rest = divmod(n, 100_000_000)
    man = rest // 10_000
    if man:
        result = f'{eok:,}억 {man:,}만원'
    else:
        result = f'{eok:,}억원'
    return ('약 ' if n % 10_000 else '') + result


def _kpis(items: list[tuple[str, str, str]], *, green_last: bool = False) -> None:
    # item: title, large display, exact/detail, no truncation.
    from html import escape
    cards = []
    for idx, (title, amount, detail) in enumerate(items):
        class_name = 'hv-kpi hv-kpi--green' if green_last and idx == len(items) - 1 else 'hv-kpi'
        cards.append(
            f'<div class="{class_name}">'
            f'<div class="hv-kpi-label">{escape(title)}</div>'
            f'<div class="hv-kpi-value">{escape(str(amount))}</div>'
            f'<div class="hv-kpi-detail">{escape(detail)}</div>'
            '</div>'
        )
    solo = ' hv-kpi-grid--solo' if len(cards) == 1 else ''
    st.markdown(f'<div class="hv-kpi-grid{solo}">{"".join(cards)}</div>', unsafe_allow_html=True)


def _won_kpi(title: str, amount: int) -> tuple[str, str, str]:
    return title, _short_krw(amount), f'{int(amount):,}원'



def _retirement_tax_steps(tax, non_taxable: int, years: int):
    """Mirror retirement_core's math for explanatory hovers (do not change tax logic).

    Intermediate values are recomputed with Decimal and ONLY floored for display;
    rounding displayed intermediate fields first would cause occasional 1-won errors.
    """
    y = int(years)
    taxable = int(tax.gross) - int(non_taxable)
    net_after_service = max(0, taxable - int(tax.service_deduction))
    exact_pay = Decimal(net_after_service) * Decimal(12) / Decimal(y)
    exact_deduction = converted_pay_deduction(exact_pay)
    exact_base = max(Decimal(0), exact_pay - exact_deduction)
    exact_converted_tax = income_tax_on_base(exact_base)

    if y <= 5:
        service_formula = f'{y}년 × 1,000,000원'
    elif y <= 10:
        service_formula = f'5,000,000원 + ({y}년 − 5년) × 2,000,000원'
    elif y <= 20:
        service_formula = f'15,000,000원 + ({y}년 − 10년) × 2,500,000원'
    else:
        service_formula = f'40,000,000원 + ({y}년 − 20년) × 3,000,000원'

    if exact_pay <= 8_000_000:
        converted_ded_formula = '환산급여 800만원 이하: 환산급여 전액 공제'
        converted_ded_calc = f'{exact_pay:,.2f}원 × 100%'
    elif exact_pay <= 70_000_000:
        converted_ded_formula = '800만원 + (환산급여 − 800만원) × 60%'
        converted_ded_calc = f'8,000,000 + ({exact_pay:,.2f} − 8,000,000) × 60%'
    elif exact_pay <= 100_000_000:
        converted_ded_formula = '4,520만원 + (환산급여 − 7,000만원) × 55%'
        converted_ded_calc = f'45,200,000 + ({exact_pay:,.2f} − 70,000,000) × 55%'
    elif exact_pay <= 300_000_000:
        converted_ded_formula = '6,170만원 + (환산급여 − 1억원) × 45%'
        converted_ded_calc = f'61,700,000 + ({exact_pay:,.2f} − 100,000,000) × 45%'
    else:
        converted_ded_formula = '1억 5,170만원 + (환산급여 − 3억원) × 35%'
        converted_ded_calc = f'151,700,000 + ({exact_pay:,.2f} − 300,000,000) × 35%'

    tax_rates = [
        (14_000_000, '6%', 0),
        (50_000_000, '15%', 1_260_000),
        (88_000_000, '24%', 5_760_000),
        (150_000_000, '35%', 15_440_000),
        (300_000_000, '38%', 19_940_000),
        (500_000_000, '40%', 25_940_000),
        (1_000_000_000, '42%', 35_940_000),
        (Decimal('Infinity'), '45%', 65_940_000),
    ]
    rate, quick_deduction = next((rate, credit) for ceiling, rate, credit in tax_rates
                                 if exact_base <= ceiling)
    converted_tax_note = f'환산산출세액: {exact_base:,.2f}원 × {rate} − {quick_deduction:,}원 = {exact_converted_tax:,.2f}원'

    # label, result, formula, number substitution, extra note
    return [
        ('퇴직급여 총액', tax.gross,
         '퇴직 시 지급받는 퇴직급여의 총합',
         f'퇴직급여 {tax.gross:,}원 − 비과세 {non_taxable:,}원 = 과세대상 {taxable:,}원',
         '이후 계산은 비과세 퇴직소득을 제외한 금액에 적용합니다.'),
        ('근속연수공제', tax.service_deduction,
         '근속연수에 따라 구간별 누진 공제액 산출',
         f'{service_formula} = {tax.service_deduction:,}원',
         f'적용 근속연수: {y}년 (세법상 근속연수 기준)'),
        ('환산급여', tax.converted_pay,
         'MAX(0, 과세대상 퇴직소득 − 근속연수공제) × 12 ÷ 근속연수',
         f'MAX(0, {taxable:,} − {tax.service_deduction:,}) × 12 ÷ {y} = {tax.converted_pay:,}원',
         f'원 단위 표시 전 실제 계산값: {exact_pay:,.2f}원'),
        ('환산급여공제', tax.converted_pay_deduction,
         converted_ded_formula,
         f'{converted_ded_calc} = {tax.converted_pay_deduction:,}원',
         '환산급여 원미만 미절사 계산값을 사용하며, 최종 결과는 원 단위로 표시합니다.'),
        ('환산과세표준', tax.converted_tax_base,
         'MAX(0, 환산급여 − 환산급여공제)',
         f'{exact_pay:,.2f} − {exact_deduction:,.2f} = {tax.converted_tax_base:,}원',
         f'원 단위 표시 전 실제 계산값: {exact_base:,.2f}원'),
        ('퇴직소득세', tax.income_tax,
         '(환산과세표준 × 적용세율 − 누진공제) × 근속연수 ÷ 12',
         f'{converted_tax_note} → × {y} ÷ 12 = {tax.income_tax:,}원',
         '국세 기준 금액이며, 원 미만 절사 결과입니다.'),
        ('지방소득세', tax.local_income_tax,
         '퇴직소득세(국세) × 10%',
         f'{tax.income_tax:,}원 × 10% = {tax.local_income_tax:,}원',
         '지방소득세 원 미만 절사 결과입니다.'),
    ]


def _render_retirement_tax_route(tax, non_taxable: int, years: int) -> None:
    """CSS-only hover formula panel; keyboard focus and touchscreen tap supported."""
    rows = _retirement_tax_steps(tax, non_taxable, years)
    html_rows = []
    for title, amount, formula, substitution, note in rows:
        formula_html = escape(formula)
        substitution_html = escape(substitution)
        note_html = escape(note)
        tooltip = escape(f'{formula} | {substitution}', quote=True)
        html_rows.append(
            f'<tr class="hv-calc-row" tabindex="0" title="{tooltip}">'
            '<td>'
            f'<span class="hv-calc-label">{escape(title)}</span>'
            '<span class="hv-calc-help" tabindex="0" aria-label="계산식 보기">ⓘ</span>'
            '<div class="hv-calc-steps">'
            f'<div class="hv-calc-formula">계산식: {formula_html}</div>'
            f'<div class="hv-calc-numbers">대입: {substitution_html}</div>'
            f'<div class="hv-calc-note">{note_html}</div>'
            '</div></td>'
            f'<td class="hv-calc-amount">{amount:,}원</td>'
            '</tr>'
        )
    st.markdown(
        '<div class="hv-calc-intro">각 계산 항목에 마우스를 올리면 산식과 숫자 대입 과정이 표시됩니다. '
        '모바일에서는 <b>ⓘ</b>를 터치하세요.</div>'
        '<div class="hv-calc-scroll"><table class="hv-calc-table">'
        '<thead><tr><th>계산 항목</th><th>금액(원)</th></tr></thead>'
        '<tbody>' + ''.join(html_rows) + '</tbody></table></div>',
        unsafe_allow_html=True,
    )



def _detail_formula_for_withdrawal_row(row, *, deferred_tax: int, def_balance: int,
                                      age: int, receipt_year: int, calendar_year: int) -> tuple[str, str]:
    """Expose the same Decimal arithmetic and won flooring as retirement_core.

    Returns (tax formula, result and local-tax formula) for each existing result row.
    No independent tax calculation is used to replace the engine output.
    """
    amount = int(row.gross)
    pension = row.treatment == '연금수령'
    if row.resource == '과세제외금액':
        formula = '과세제외 재원: 소득세 0원 (비과세)'
        substitution = f'{amount:,}원 × 0% = 0원'
    elif row.resource == '이연퇴직소득':
        factor = retirement_tax_multiplier(receipt_year, calendar_year) if pension else Decimal('1')
        factor_percent = factor * 100
        if pension:
            formula = ('국세 = ⌊수령액 × (잔여 이연퇴직소득세 ÷ 잔여 이연퇴직소득 원금)'
                       f' × {factor_percent:,.0f}%⌋')
        else:
            formula = '국세 = ⌊수령액 × (잔여 이연퇴직소득세 ÷ 잔여 이연퇴직소득 원금) × 100%⌋'
        substitution = (f'⌊{amount:,}원 × ({deferred_tax:,}원 ÷ {def_balance:,}원)'
                        f' × {factor_percent:,.0f}%⌋ = {row.income_tax:,}원')
    else:
        personal_percent = (age_pension_tax_rate(age) * 100) if pension else Decimal('15')
        desc = '연령별 연금소득세' if pension else '연금외수령 기타소득세'
        formula = f'국세 = ⌊수령액 × {personal_percent:,.0f}%⌋ ({desc})'
        substitution = f'⌊{amount:,}원 × {personal_percent:,.0f}%⌋ = {row.income_tax:,}원'
    local_text = (f'지방소득세: ⌊국세 {row.income_tax:,}원 × 10%⌋ = {row.local_income_tax:,}원'
                  f' | 합계 {row.total_tax:,}원 | 실수령 {row.net:,}원')
    return formula, substitution + ' | ' + local_text


def _render_withdrawal_route(title: str, treatment: str, result, *,
                             deferred_tax: int, def_balance: int, age: int,
                             receipt_year: int, calendar_year: int) -> None:
    """One-click breakdown of the taxes for every withdrawal source in the category."""
    matching = [r for r in result.rows if r.treatment == treatment]
    total_amount = sum(r.gross for r in matching)
    total_income = sum(r.income_tax for r in matching)
    total_local = sum(r.local_income_tax for r in matching)
    total_tax = total_income + total_local
    total_net = total_amount - total_tax
    label = (f'{title} — {total_amount:,}원 | 세금 {total_tax:,}원 | 계산식 펼치기')
    with st.expander(label, expanded=False):
        if not matching:
            st.info('이번 신청금액 중 해당 분류로 인출되는 금액은 없습니다.')
            return
        html_rows = []
        for idx, row in enumerate(matching, 1):
            formula, applied = _detail_formula_for_withdrawal_row(
                row, deferred_tax=deferred_tax, def_balance=def_balance,
                age=age, receipt_year=receipt_year, calendar_year=calendar_year)
            html_rows.append(
                '<div class="hv-tax-step">'
                f'<div class="hv-tax-step-title">{idx}. {escape(row.resource)} · {row.gross:,}원</div>'
                f'<div class="hv-tax-step-formula">{escape(formula)}</div>'
                f'<div class="hv-tax-step-formula">숫자 대입: {escape(applied)}</div>'
                '</div>'
            )
        st.markdown('<div class="hv-tax-steps">' + ''.join(html_rows) + '</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="hv-tax-summary"><b>소득세(국세)</b> {total_income:,}원 '
            f'+ <b>지방소득세</b> {total_local:,}원 = '
            f'<strong>세금 합계 {total_tax:,}원</strong><br>'
            f'수령액 {total_amount:,}원 − 세금 {total_tax:,}원 = '
            f'<strong>실수령액 {total_net:,}원</strong></div>',
            unsafe_allow_html=True)
        st.caption('⌊ ⌋ 기호는 원 미만 절사를 뜻합니다. 분류는 재원별 법정 인출순서를 반영했습니다.')


# ===== BA II PLUS-style standalone financial / annuity calculator =====
# TVM math is intentionally self-contained: only app.py is needed on GitHub.
def _tvm_period_rate(annual_percent: float, payments_per_year: int,
                     compounds_per_year: int) -> float:
    """Nominal annual I/Y (%) -> effective rate for each PAYMENT period."""
    py, cy = int(payments_per_year), int(compounds_per_year)
    if py <= 0 or cy <= 0:
        raise ValueError('P/Y와 C/Y는 모두 1 이상이어야 합니다.')
    nominal_compound_rate = float(annual_percent) / (100.0 * cy)
    if nominal_compound_rate <= -1:
        raise ValueError('이율이 복리 회차당 -100% 이하입니다.')
    return math.expm1(math.log1p(nominal_compound_rate) * cy / py)


def _tvm_annuity_factor(rate: float, periods: float, beginning: bool) -> float:
    """Growth of a level-payment annuity for fractional n too (TI TVM model)."""
    if periods < 0 or periods > 1200:
        raise ValueError('N은 0부터 1,200회 사이에서 계산합니다.')
    if rate <= -1:
        raise ValueError('회차 이자율은 -100%를 초과해야 합니다.')
    a = periods if abs(rate) < 1e-12 else math.expm1(periods * math.log1p(rate)) / rate
    return a * (1.0 + rate if beginning else 1.0)


def _tvm_fv(pv: float, pmt: float, rate: float, periods: float,
            beginning: bool) -> float:
    growth = math.exp(periods * math.log1p(rate))
    result = -float(pv) * growth - float(pmt) * _tvm_annuity_factor(rate, periods, beginning)
    if not math.isfinite(result):
        raise ValueError('계산 결과가 표현 가능한 범위를 넘었습니다. N 또는 이율을 줄여 주세요.')
    return result


def _tvm_residual(rate: float, n: float, pv: float, pmt: float,
                  fv: float, beginning: bool) -> float:
    return _tvm_fv(pv, pmt, rate, n, beginning) - fv


def _tvm_solve_unknown(key: str, *, n: float, iy: float, pv: float,
                       pmt: float, fv: float, py: int = 1, cy: int = 1,
                       beginning: bool = False) -> tuple[float, str]:
    """Solve CPT [N/I-Y/PV/PMT/FV], with cashflow sign convention.

    PV negative means the customer's initial investment is money OUT;
    FV positive means the eventual money received IN.
    """
    if not all(math.isfinite(float(v)) for v in (n, iy, pv, pmt, fv)):
        raise ValueError('입력값은 유한한 숫자여야 합니다.')
    if key != 'N' and not (0 <= n <= 1200):
        raise ValueError('N은 0~1,200 사이여야 합니다.')
    if key != 'I/Y' and (iy < -99 or iy > 1000):
        raise ValueError('I/Y는 -99%~1,000% 범위에서 입력해 주세요.')
    if key != 'I/Y':
        r = _tvm_period_rate(iy, py, cy)
    else:
        r = None
    if key == 'FV':
        ans = _tvm_fv(pv, pmt, r, n, beginning)
    elif key == 'PV':
        growth = math.exp(n * math.log1p(r))
        ans = -(fv + pmt * _tvm_annuity_factor(r, n, beginning)) / growth
    elif key == 'PMT':
        factor = _tvm_annuity_factor(r, n, beginning)
        if abs(factor) <= 1e-14:
            raise ValueError('N이 0회이므로 PMT를 계산할 수 없습니다.')
        growth = math.exp(n * math.log1p(r))
        ans = -(fv + pv * growth) / factor
    elif key == 'N':
        if abs(r) < 1e-12:
            if abs(pmt) < 1e-12:
                raise ValueError('이율과 PMT가 0인 경우에는 N을 결정할 수 없습니다.')
            ans = -(pv + fv) / pmt
        else:
            coeff = pmt * (1 + r if beginning else 1) / r
            denom = pv + coeff
            if abs(denom) < 1e-12:
                raise ValueError('지급 흐름상 N을 하나의 값으로 결정할 수 없습니다.')
            ratio = (coeff - fv) / denom
            if ratio <= 0:
                raise ValueError('현재 PV·PMT·FV 조합은 양의 기간으로 성립하지 않습니다.')
            ans = math.log(ratio) / math.log1p(r)
        if not (0 <= ans <= 1200):
            raise ValueError('계산된 N이 0~1,200회 범위를 벗어났습니다. 현금흐름 부호를 확인하세요.')
    elif key == 'I/Y':
        if abs(pv) < 1e-12 and abs(pmt) < 1e-12 and abs(fv) < 1e-12:
            raise ValueError('모든 현금흐름이 0원이면 이율을 결정할 수 없습니다.')
        if not (0 < n <= 1200):
            raise ValueError('I/Y를 구하려면 N은 0보다 커야 합니다.')
        # Find all sign-changing intervals on a -99% to 1000% annual-nominal
        # grid; prefer the solution near zero if more than one mathematical root.
        candidates = [-99.0 + i * 0.5 for i in range(199)]  # -99~0
        candidates += [i * .25 for i in range(1, 801)]  # .25~200
        candidates += [200.0 + i * 2.0 for i in range(1, 401)]  # 202~1000
        roots = []
        prior_point, prior_value = None, None
        for x in candidates:
            try:
                rr = _tvm_period_rate(x, py, cy)
                value = _tvm_residual(rr, n, pv, pmt, fv, beginning)
                if not math.isfinite(value):
                    continue
            except (OverflowError, ValueError):
                continue
            if abs(value) <= 1e-8 * max(1.0, abs(fv), abs(pv), abs(pmt)):
                roots.append(x)
            elif prior_value is not None and value * prior_value < 0:
                lo, hi, f_lo = prior_point, x, prior_value
                for _ in range(85):
                    mid = (lo + hi) / 2
                    try:
                        f_mid = _tvm_residual(_tvm_period_rate(mid, py, cy),
                                              n, pv, pmt, fv, beginning)
                    except (OverflowError, ValueError):
                        break
                    if f_mid == 0 or abs(hi - lo) < 1e-12:
                        lo = hi = mid
                        break
                    if (f_mid > 0) == (f_lo > 0):
                        lo, f_lo = mid, f_mid
                    else:
                        hi = mid
                roots.append((lo + hi) / 2)
            prior_point, prior_value = x, value
        roots = sorted(set(round(x, 10) for x in roots))
        if not roots:
            raise ValueError('이 현금흐름에서는 -99%~1,000% 구간에 이율 해가 없습니다. PV·PMT·FV의 +/- 부호와 N을 확인하세요.')
        ans = min(roots, key=lambda v: abs(v))
        if len(roots) > 1:
            return ans, f'주의: 이율 해가 {len(roots)}개 발견되었습니다. 절댓값이 가장 작은 이율을 표시합니다. 다른 해: {roots}'
    else:
        raise ValueError('알 수 없는 CPT 항목입니다.')
    if not math.isfinite(ans):
        raise ValueError('계산 결과가 유한하지 않습니다.')
    explanation = f'P/Y={py}, C/Y={cy}, 납입시점={"BGN" if beginning else "END"}'
    return ans, explanation


def _tvm_money(value: float) -> str:
    return f'{value:,.0f}원'


def _tvm_clear_registers() -> None:
    # 2ND + CLR TVM must preserve P/Y, C/Y, and BGN/END, per the TI manual.
    for k in ('N', 'IY', 'PV', 'PMT', 'FV'):
        st.session_state['hv_tvm_' + k] = 0.0
    st.session_state['hv_tvm_result'] = None


def _tvm_portfolio_projection(initial: int, monthly_net: int, years: int,
                               annual_return: float, annual_fee: float) -> tuple[float, list[float]]:
    """Approximate annualized effective return net of fee, with monthly cashflows."""
    if annual_return - annual_fee <= -100:
        raise ValueError('보수 차감 후 수익률은 -100%를 초과해야 합니다.')
    net_annual = (annual_return - annual_fee) / 100.0
    monthly_rate = math.expm1(math.log1p(net_annual) / 12)
    sequence = [float(initial)]
    for y in range(1, years + 1):
        # Compare at end-of-month contributions / withdrawals.
        sequence.append(_tvm_fv(-initial, -monthly_net, monthly_rate, y * 12, False))
    return sequence[-1], sequence


def _tvm_draw_page() -> None:
    st.markdown("""<style>
    .hv-tvm-hero{background:linear-gradient(110deg,#132E3C,#0B1C2A);
      border:1px solid #3F716E;border-left:5px solid #48E4AD;border-radius:14px;
      padding:18px 20px;margin-bottom:18px}
    .hv-tvm-hero h3{margin:0 0 6px!important;color:#FFFFFF;font-size:1.3rem}
    .hv-tvm-hero p{color:#CEDFE7;font-size:.93rem;margin:0}
    .hv-tvm-key{color:#B6EBD8;font-weight:800;letter-spacing:.08em}
    .hv-tvm-output{background:#143646;border:1px solid #69DAB8;
      border-radius:12px;padding:16px;margin:13px 0}
    .hv-tvm-output .caption{color:#C6E9E0;font-size:.84rem}
    .hv-tvm-output .value{color:#7FFFD2;font-size:clamp(1.6rem,3vw,2.5rem);
      font-weight:850;overflow-wrap:anywhere}
    .st-key-hv_tvm_go button{background:#078C6E!important;
      border-color:#7FFFD2!important;font-size:1.03rem!important;
      padding:12px!important}
    </style>""", unsafe_allow_html=True)
    st.markdown("""<div class="hv-tvm-hero"><h3>연금상품 금융계산기 · CPT</h3>
      <p>BA II Plus 방식의 화폐 시간가치(TVM) 계산과 은행·증권사 운용 시나리오 비교</p></div>""",
      unsafe_allow_html=True)
    tab_calculator, tab_compare = st.tabs(['🧮 CPT · N / I/Y / PV / PMT / FV', '📈 은행 vs 증권 · 운용 비교'])
    with tab_calculator:
        st.markdown('#### 금융계산기 — 계산할 키 선택 후 CPT')
        st.caption('연 단위 납입은 P/Y=1, 월 단위 납입은 P/Y=12. 이자 복리회수(C/Y)와 지급시점(END/BGN)도 설정합니다.')
        for name, default in {
            'N': 15.0, 'IY': 10.0, 'PV': -63_570_000.0,
            'PMT': -9_000_000.0, 'FV': 0.0,
        }.items():
            st.session_state.setdefault('hv_tvm_'+name, default)
        st.session_state.setdefault('hv_tvm_py', 1)
        st.session_state.setdefault('hv_tvm_cy', 1)
        st.session_state.setdefault('hv_tvm_when', 'END')
        st.session_state.setdefault('hv_tvm_2nd_open', False)
        st.session_state.setdefault('hv_tvm_result', None)

        button_settings, button_clear, status = st.columns([1.05, 1.3, 1.8])
        with button_settings:
            if st.button('2ND · 설정 열기/닫기', use_container_width=True, key='hv_tvm_second'):
                st.session_state['hv_tvm_2nd_open'] = not st.session_state['hv_tvm_2nd_open']
        with button_clear:
            st.button('2ND → CLR TVM', use_container_width=True,
                      key='hv_tvm_clear', on_click=_tvm_clear_registers)
        with status:
            st.caption(f'P/Y {st.session_state["hv_tvm_py"]}  ·  C/Y {st.session_state["hv_tvm_cy"]}  ·  {st.session_state["hv_tvm_when"]}')

        if st.session_state['hv_tvm_2nd_open']:
            with st.container(border=True):
                st.markdown('**2ND 추가 설정 · 연금현가/미래가치 계산에 적용**')
                setting1, setting2, setting3 = st.columns(3)
                with setting1:
                    st.selectbox('P/Y · 연간 납입 횟수', [1, 2, 4, 12, 52, 365], key='hv_tvm_py')
                with setting2:
                    st.selectbox('C/Y · 연간 복리 횟수', [1, 2, 4, 12, 52, 365], key='hv_tvm_cy')
                with setting3:
                    st.radio('납입 시점', ['END','BGN'], key='hv_tvm_when', horizontal=True,
                             help='END: 매 회차 말 납입 / BGN: 매 회차 초 납입')
        target = st.radio('**CPT · 계산할 미지수 선택**',
                          ['FV', 'PV', 'PMT', 'N', 'I/Y'],
                          horizontal=True, key='hv_tvm_target',
                          help='선택한 값은 입력하지 않아도 됩니다. 다른 네 값을 사용해 계산합니다.')
        with st.form('hv_tvm_form', border=True):
            left, middle, right = st.columns(3)
            with left:
                n = st.number_input('N · 총 납입/수령 횟수', step=1.0, format='%.4f',
                                    key='hv_tvm_N', disabled=target == 'N',
                                    help='연수 자체가 아니라 지급 횟수입니다. 매월 10년이면 N=120')
                iy = st.number_input('I/Y · 연이율 (%)', step=0.1, format='%.5f',
                                     key='hv_tvm_IY', disabled=target == 'I/Y',
                                     help='예: 5%면 5 입력. P/Y와 C/Y 설정을 별도로 확인하세요.')
            with middle:
                pv = st.number_input('PV · 현재가치 (원)', step=1_000_000.0, format='%.0f',
                                     key='hv_tvm_PV', disabled=target == 'PV')
                pmt = st.number_input('PMT · 회차별 수령/납입액 (원)', step=100_000.0,
                                      format='%.0f', key='hv_tvm_PMT', disabled=target == 'PMT')
            with right:
                fv = st.number_input('FV · 미래가치 (원)', step=1_000_000.0, format='%.0f',
                                     key='hv_tvm_FV', disabled=target == 'FV')
                st.caption('**현금흐름 부호**: 고객이 납입하는 금액은 음수(−), 나중에 받는 금액은 양수(+).')
                st.caption('상환·연금 인출을 계산할 때는 돈이 들어오는 방향과 나가는 방향을 반대로 넣습니다.')
            submitted = st.form_submit_button('CPT ▶ 선택한 값 계산',
                                              type='primary', use_container_width=True)
        if submitted:
            try:
                val, note = _tvm_solve_unknown(target, n=n, iy=iy, pv=pv,
                    pmt=pmt, fv=fv, py=st.session_state['hv_tvm_py'],
                    cy=st.session_state['hv_tvm_cy'],
                    beginning=st.session_state['hv_tvm_when'] == 'BGN')
                st.session_state['hv_tvm_result'] = (target, val, note)
            except (ValueError, ZeroDivisionError, OverflowError) as exc:
                st.session_state['hv_tvm_result'] = None
                st.error(str(exc))
        if st.session_state.get('hv_tvm_result') is not None:
            solved, value, explanation = st.session_state['hv_tvm_result']
            formatted = (f'{value:,.6f}%' if solved == 'I/Y' else
                         f'{value:,.4f}회 (약 {value/st.session_state["hv_tvm_py"]:,.2f}년)'
                         if solved == 'N' else _tvm_money(value))
            st.markdown(
                '<div class="hv-tvm-output"><div class="caption">CPT ▶ '+escape(solved)+'</div>'
                '<div class="value">'+escape(formatted)+'</div></div>', unsafe_allow_html=True)
            st.caption(explanation)
            if st.button('계산 결과를 ' + solved + ' 레지스터에 저장',
                         key='hv_tvm_store', use_container_width=True,
                         help='BA II Plus처럼 계산 결과를 해당 키에 저장합니다. 이후 다른 키를 CPT로 다시 구할 때 활용할 수 있습니다.'):
                field = 'IY' if solved == 'I/Y' else solved
                st.session_state['hv_tvm_' + field] = float(value)
                st.session_state['hv_tvm_result'] = None
                st.rerun()
            with st.expander('ⓘ 계산 원리 및 수식 보기'):
                st.markdown('**현금흐름 현재가치/미래가치 공식**')
                st.latex(r'0=PV(1+r)^N+PMT\times\frac{(1+r)^N-1}{r}\times\begin{cases}1&\mathrm{END}\\1+r&\mathrm{BGN}\end{cases}+FV')
                st.markdown('연 지급 횟수 **P/Y**, 연 복리 횟수 **C/Y**일 때 지급 회차별 이율:')
                st.latex(r'r=\left(1+\frac{I/Y}{100\times C/Y}\right)^{C/Y\,/\,P/Y}-1')
                st.caption('이율 0%는 연금현가/미래가치의 극한값으로 처리합니다. N 또는 I/Y 역산에는 해가 없거나 여러 개일 수 있습니다.')
        with st.expander('BA II Plus와 결과가 다를 때 점검할 항목'):
            st.markdown('**① P/Y** 연간 납입 횟수 · **② C/Y** 복리 횟수 · **③ END/BGN** 회차 말/초 납입 · '
                        '**④ PV/PMT 부호** · **⑤ N은 연수가 아니라 회차 수** · **⑥ 소수점 표시만 다른지 확인.')
            st.markdown('[TI 공식 금융계산기 TVM 키 안내](https://education.ti.com/en/customer-support/knowledge-base/financial-calculators/general-information/11254)')

    with tab_compare:
        st.markdown('#### 은행형 vs 증권사 퇴직연금 운용 비교')
        st.caption('동일한 원금·기간·납입 방식에 서로 다른 연 수익률·비용 가정만 적용하는 비교입니다. 특정 금융사의 확정 성과를 의미하지 않습니다.')
        current_case = int(st.session_state.get('hv_tvm_case_principal', 0))
        st.session_state.setdefault('hv_tvm_initial', current_case if current_case > 0 else 1_088_894_913)
        if current_case > 0:
            if st.button('최근 퇴직금 상담의 잔여 IRP 원금 불러오기', key='hv_tvm_from_case'):
                st.session_state['hv_tvm_initial'] = current_case
                st.rerun()
        a, b, c = st.columns(3)
        with a:
            principal = int(st.number_input('운용 시작금액 (원)', min_value=0,
                                            step=10_000_000, format='%d', key='hv_tvm_initial'))
        with b:
            duration = int(st.number_input('운용기간 (년)', min_value=1, max_value=40,
                                           value=10, step=1, key='hv_tvm_duration'))
        with c:
            monthly = int(st.number_input('매월 추가납입(+) / 인출(−) (원)',
                                          step=100_000, value=0, format='%d', key='hv_tvm_monthly'))
        bank, securities = st.columns(2)
        with bank:
            with st.container(border=True):
                st.markdown('**🏦 은행형 운용 시나리오**')
                bank_rate = st.number_input('가정 연 수익률 (%) · 은행',
                    value=3.0, min_value=-50.0, max_value=100.0,
                    step=0.1, format='%.2f', key='hv_tvm_bank_rate')
                bank_fee = st.number_input('연 수수료·비용률 (%) · 은행',
                    value=0.1, min_value=0.0, max_value=30.0, step=0.1,
                    format='%.2f', key='hv_tvm_bank_fee')
        with securities:
            with st.container(border=True):
                st.markdown('**📈 하나증권 운용 시나리오**')
                securities_rate = st.number_input('가정 연 수익률 (%) · 증권',
                    value=5.5, min_value=-50.0, max_value=100.0,
                    step=0.1, format='%.2f', key='hv_tvm_stock_rate')
                securities_fee = st.number_input('연 수수료·비용률 (%) · 증권',
                    value=0.5, min_value=0.0, max_value=30.0, step=0.1,
                    format='%.2f', key='hv_tvm_stock_fee')
        try:
            bank_final, bank_path = _tvm_portfolio_projection(principal, monthly, duration,
                                                               bank_rate, bank_fee)
            stock_final, stock_path = _tvm_portfolio_projection(principal, monthly, duration,
                                                                 securities_rate, securities_fee)
            if monthly < 0 and (min(bank_path) < -1e-7 or min(stock_path) < -1e-7):
                st.warning('중도에 운용자금이 소진되는 시나리오입니다. 인출금액 또는 기간을 조정해 주세요. 음수 잔액을 실제 운용금액으로 보아서는 안 됩니다.')
            bank_net, stock_net = bank_rate-bank_fee, securities_rate-securities_fee
            difference = stock_final-bank_final
            gross_contributed = principal + monthly*duration*12
            _kpis([
                ('은행형 순수익률 가정', f'{bank_net:.2f}%', f'{bank_rate:.2f}% − {bank_fee:.2f}%p'),
                ('증권사 순수익률 가정', f'{stock_net:.2f}%', f'{securities_rate:.2f}% − {securities_fee:.2f}%p'),
                _won_kpi('은행형 예상 미래가치', round(bank_final)),
                _won_kpi('증권사 예상 미래가치', round(stock_final)),
            ], green_last=True)
            if difference > 0:
                st.success(f'이 **가정**에서 증권사 운용안의 {duration}년 뒤 평가금액이 은행형보다 **{difference:,.0f}원 많습니다**.')
            elif difference < 0:
                st.info(f'이 **가정**에서는 은행형 운용안이 증권사 운용안보다 **{abs(difference):,.0f}원 많습니다**.')
            else:
                st.info('입력한 가정에서는 두 운용안의 미래가치가 같습니다.')
            yearly = pd.DataFrame({
                '경과연도': list(range(duration+1)),
                '은행형 잔액(원)': [round(x) for x in bank_path],
                '하나증권 잔액(원)': [round(x) for x in stock_path],
            })
            st.line_chart(yearly.set_index('경과연도'))
            with st.expander('📋 연도별 잔액 및 수익 계산식 보기'):
                st.dataframe(yearly, hide_index=True, use_container_width=True)
                st.markdown('**순수익률(단순 가정)** = 연 기대수익률 − 연 수수료·비용률')
                st.markdown('**월 유효이율** = (1 + 연 순수익률)^(1/12) − 1')
                st.markdown('**미래가치** = 시작금액 × (1+r)^개월수 + 매월 납입액 × {[(1+r)^개월수−1]/r}')
                st.caption('납입은 매월 말(END) 기준입니다. 실제 IRP 수수료 체계와 투자상품 보수는 단순 연율 차감 방식과 다를 수 있습니다.')
            st.download_button('비교 결과 CSV 다운로드', yearly.to_csv(index=False).encode('utf-8-sig'),
                               file_name='HanaV_퇴직연금_운용비교.csv', mime='text/csv')
            st.caption('**비교 유의사항:** 수익률·수수료는 사용자가 입력한 가정입니다. 일반예금은 약정금리·예금자보호 조건을 확인하고, '
                '펀드·ETF·채권 등은 가격변동·원금손실·상품별 투자제한을 고려하세요. 은행 IRP와 증권사 IRP는 동일한 세법상 조건에서 세율 혜택이 같습니다. '
                '미래가치에는 향후 연금수령세금·인플레이션·세법 변경·실제 운용 제약을 반영하지 않았습니다.')
        except (ValueError, OverflowError) as exc:
            st.error(f'운용 비교 계산을 완료할 수 없습니다: {exc}')


# ===== Client-facing IRP acquisition proposal generator (assumption-driven) =====
def _proposal_annual_paths(principal: int, years: int, monthly_flow: int,
                           gross_return_percent: float, annual_cost_percent: float) -> tuple[list[int], int | None]:
    """Balance at each anniversary; do not let a spending model borrow below zero."""
    if principal < 0 or years < 1 or years > 40:
        raise ValueError('운용 원금 또는 기간 입력을 확인해 주세요.')
    if annual_cost_percent < 0 or not (-99.0 < gross_return_percent - annual_cost_percent <= 200):
        raise ValueError('비용 차감 후 수익률은 -99% 초과~200% 이하여야 합니다.')
    annual_net = (gross_return_percent - annual_cost_percent) / 100
    monthly_return = math.expm1(math.log1p(annual_net) / 12)
    balance = float(principal)
    output = [int(principal)]
    depleted_month = None
    for month in range(1, years * 12 + 1):
        next_value = balance * (1 + monthly_return) + monthly_flow
        if next_value <= 0:
            if depleted_month is None and (balance > 0 or monthly_flow < 0):
                depleted_month = month
            balance = 0.0
        else:
            balance = next_value
        if month % 12 == 0:
            output.append(round(balance))
    return output, depleted_month


def _proposal_won(amount: int | float) -> str:
    return f'{round(amount):,}원'


def _proposal_interpretation(bank_final: int, sec_final: int, risk: str,
                             strategy_risk: str, is_sec_guaranteed: bool) -> str:
    diff = sec_final - bank_final
    if diff > 0:
        base = ('제시된 수익률·비용 가정이 실현될 때 하나증권 운용안의 예상 평가액이 '
                f'{_proposal_won(diff)} 높습니다. 이는 세제 우위가 아니라 가정한 운용 성과 차이입니다.')
    elif diff < 0:
        base = ('현재 입력 조건에서는 은행 IRP 운용안의 예상 평가액이 '
                f'{_proposal_won(-diff)} 높아, 수익률만으로 하나증권 이전을 권유할 근거가 없습니다.')
    else:
        base = '현재 입력 조건에서는 두 IRP의 예상 평가액이 같습니다. 상품 특성·수수료·서비스를 비교해야 합니다.'
    if risk == '원금보전 최우선' and not is_sec_guaranteed:
        base += ' 고객이 원금보전을 최우선으로 하므로, 실적배당상품 확대보다 원금보장형 대안과 위험자산 편입 한도를 우선 검토하세요.'
    elif strategy_risk == '실적배당형 비중 높음':
        base += ' 하나증권 운용안은 실적배당형 비중이 높아 손실 가능성과 적합성·위험설명이 필요합니다.'
    return base


def _proposal_html(data: dict, rows: list[dict], decision: str) -> bytes:
    """Print-ready, self-contained HTML. Customers can save it as PDF using Ctrl+P."""
    def e(value):
        return escape(str(value), quote=True)
    bank_end = int(data['bank_final'])
    hana_end = int(data['hana_final'])
    diff = hana_end - bank_end
    conclusion = ('하나증권 우세(가정)' if diff > 0 else
                  '은행 IRP 우세(가정)' if diff < 0 else '예상 평가액 동일')
    body_rows = ''.join(
        '<tr><td>'+e(x['경과연도'])+'년</td><td>'+e(_proposal_won(x['은행 IRP 예상잔액']))+'</td>'
        '<td>'+e(_proposal_won(x['하나증권 IRP 예상잔액']))+'</td>'
        '<td>'+e(_proposal_won(x['차이(하나증권-은행)']))+'</td></tr>' for x in rows)

    html = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>HanaV IRP 운용 제안서</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@page{size:A4;margin:14mm}*{box-sizing:border-box}body{font-family:"Malgun Gothic","Apple SD Gothic Neo",Arial,sans-serif;color:#152636;background:white;margin:0 auto;max-width:850px;font-size:12px;line-height:1.5}
header{border-bottom:3px solid #00816b;padding:8px 0 13px;display:flex;justify-content:space-between;align-items:end}h1{margin:0;font-size:24px;color:#093c39}h2{font-size:16px;color:#00785c;margin:23px 0 8px}p{margin:7px 0}.muted{color:#657586}.summary{margin-top:14px;padding:14px;background:#eff9f6;border:1px solid #bee0d4;border-radius:9px}.summary b{font-size:18px;color:#08674f}.cards{display:flex;gap:9px;margin-top:14px}.card{flex:1;border:1px solid #cbdad9;border-radius:8px;padding:11px}.card span{font-size:11px;color:#556775}.card strong{display:block;font-size:17px;color:#133b42;margin-top:5px}table{border-collapse:collapse;width:100%;font-size:11px;margin-top:8px}th,td{border:1px solid #dae2e7;padding:6px 8px;text-align:right}th:first-child,td:first-child{text-align:left}th{background:#eef5f5;color:#184745}.notes{padding:12px;border-left:4px solid #ad733a;background:#fffaf0;margin:10px 0}.small{font-size:10px;color:#687b88}footer{margin-top:20px;border-top:1px solid #cbdad9;padding:9px 0;font-size:10px;color:#64747b}.print-bar{background:#13394b;color:white;padding:12px;margin:0 0 15px;text-align:center}@media print{.print-bar{display:none}body{max-width:initial}h2{break-after:avoid}table{break-inside:avoid}}</style></head><body>
<div class="print-bar">이 문서는 브라우저의 인쇄(Ctrl+P) 기능으로 PDF 저장이 가능합니다.</div>
<header><div><h1>HanaV IRP 운용 제안서</h1><div class="muted">고객 맞춤형 연금자산 운용 비교 · 상담용</div></div><div class="muted">작성일: @DATE@<br>고객 식별: @CUSTOMER@</div></header>
<div class="summary"><div>제안 요약 · @SUMMARY@</div><p><b>@YEARS@년 예상 평가액 차이: @DIFF@</b></p><p>@DECISION@</p></div>
<h2>① 고객 자금 계획</h2><table><tbody>
<tr><th>퇴직급여(참고)</th><td>@GROSS@</td><th>우선 확보할 현금(참고)</th><td>@CASH@</td></tr>
<tr><th>비교대상 IRP 운용 시작원금</th><td>@PRINCIPAL@</td><th>운용기간</th><td>@YEARS@년</td></tr>
<tr><th>매월 추가납입(+)·인출(-)</th><td>@MONTHLY@</td><th>고객 투자성향</th><td>@RISK@</td></tr>
<tr><th>별도 연금저축(참고)</th><td>@SAVINGS@</td><th>별도 기존 IRP(참고)</th><td>@OTHERIRP@</td></tr>
</tbody></table>
<h2>② 금융기관별 운용 시나리오</h2><table><thead><tr><th>항목</th><th>은행 IRP</th><th>하나증권 IRP</th></tr></thead><tbody>
<tr><td>검토 상품/전략</td><td>@BANKPRODUCT@</td><td>@HANAPRODUCT@</td></tr>
<tr><td>연 가정수익률</td><td>@BANKGROSS@%</td><td>@HANAGROSS@%</td></tr>
<tr><td>연 총비용 가정</td><td>@BANKFEE@%</td><td>@HANAFEE@%</td></tr>
<tr><td>단순 차감 순수익률 가정</td><td>@BANKNET@%</td><td>@HANANET@%</td></tr>
<tr><td>@YEARS@년 후 세전 예상 평가액</td><td>@BANKFINAL@</td><td>@HANAFINAL@</td></tr>
<tr><td>시장 악화 가정 시 평가액</td><td>@BANKSTRESS@</td><td>@HANASTRESS@</td></tr>
<tr><td>원금보장 여부</td><td>@BANKGUAR@</td><td>@HANAGUAR@</td></tr>
</tbody></table>
<div class="cards"><div class="card"><span>은행 IRP 평가액(기본)</span><strong>@BANKFINAL@</strong></div>
<div class="card"><span>하나증권 IRP 평가액(기본)</span><strong>@HANAFINAL@</strong></div>
<div class="card"><span>평가액 차이 (하나증권−은행)</span><strong>@DIFF@</strong></div></div>
<h2>③ 연도별 예상 평가액 · 매년 말</h2><table><thead><tr><th>경과연도</th><th>은행 IRP</th><th>하나증권 IRP</th><th>차이</th></tr></thead><tbody>@ROWS@</tbody></table>
<h2>④ 상담 결론 및 후속 확인</h2><div class="notes"><b>현재 가정에 대한 결론</b><p>@DECISION@</p>
<p>은행 IRP와 하나증권 IRP는 동일한 조건에서 세법상 IRP 과세·감면 기준이 같습니다. 금융회사별 운용상품, 실제 적용 보수, 위험수준, 거래 제약, 연금지급 서비스를 확인한 후 비교해야 합니다.</p></div>
<h2>⑤ 반드시 확인할 사항</h2><p>① 실제 이용 가능한 상품·금리·총비용(운용관리/자산관리/상품보수 포함) ② 원리금보장 여부·예금자보호 적용 범위 ③ 투자성향·위험자산 비중 제한 및 원금손실 가능성 ④ 연금계좌 이전 절차, 인출 계획 및 향후 인출 시 세액 ⑤ 연금자산 인출에 따른 현금흐름·유동성</p>
<footer>본 자료는 고객이 입력한 가정에 따른 <b>조건부 시뮬레이션</b>이며 확정수익·세후 실수령 보장·금융회사 고유 세제혜택을 뜻하지 않습니다. 연 수익률에서 연 비용률을 단순 차감하여 일정하게 유지하고, 월말 납입/인출·월 유효수익률 복리로 계산합니다. 운용 중 손실, 수익률 변동, 상품별 기타 비용, 거래 제한, 향후 인출 시 퇴직소득세·연금소득세 및 물가변동은 별도로 확인해야 합니다. 본 자료의 원금·기존 계좌 정보는 중복 합산하지 않았습니다. 개인정보를 포함한 자료는 별도 관리하세요.</footer></body></html>"""
    replacements = {
        '@DATE@': data['date'], '@CUSTOMER@': data['customer'] or '익명 고객',
        '@SUMMARY@': conclusion, '@YEARS@': data['years'],
        '@DIFF@': ('+' if diff>0 else '') + _proposal_won(diff),
        '@DECISION@': decision, '@ROWS@': body_rows,
        '@GROSS@': _proposal_won(data['gross']), '@CASH@': _proposal_won(data['cash']),
        '@PRINCIPAL@': _proposal_won(data['principal']),
        '@MONTHLY@': _proposal_won(data['monthly']), '@RISK@': data['risk'],
        '@SAVINGS@': _proposal_won(data['savings']), '@OTHERIRP@': _proposal_won(data['other_irp']),
        '@BANKPRODUCT@': data['bank_product'], '@HANAPRODUCT@': data['hana_product'],
        '@BANKGROSS@': f"{data['bank_rate']:.2f}", '@HANAGROSS@': f"{data['hana_rate']:.2f}",
        '@BANKFEE@': f"{data['bank_fee']:.2f}", '@HANAFEE@': f"{data['hana_fee']:.2f}",
        '@BANKNET@': f"{data['bank_rate']-data['bank_fee']:.2f}",
        '@HANANET@': f"{data['hana_rate']-data['hana_fee']:.2f}",
        '@BANKFINAL@': _proposal_won(bank_end), '@HANAFINAL@': _proposal_won(hana_end),
        '@BANKSTRESS@': _proposal_won(data['bank_stress_final']),
        '@HANASTRESS@': _proposal_won(data['hana_stress_final']),
        '@BANKGUAR@': '원리금보장형 가정' if data['bank_guaranteed'] else '비보장형/혼합형',
        '@HANAGUAR@': '원리금보장형 가정' if data['hana_guaranteed'] else '비보장형/혼합형',
    }
    for keyword, val in replacements.items():
        html = html.replace(keyword, val if keyword == '@ROWS@' else e(val))
    return html.encode('utf-8-sig')


def _proposal_load_sample() -> None:
    st.session_state.update({
        'hv_prop_gross': 1_700_000_000,
        'hv_prop_cash': 500_000_000,
        'hv_prop_principal': 1_088_894_913,
        'hv_prop_savings': 70_000_000,
        'hv_prop_other_irp': 40_000_000,
        'hv_prop_customer': '고액 퇴직금 상담 예시',
        'hv_prop_monthly': 0,
    })


def _proposal_draw_page() -> None:
    st.markdown("""<style>
    .hv-tvm-hero{background:linear-gradient(110deg,#132E3C,#0B1C2A);
      border:1px solid #3F716E;border-left:5px solid #48E4AD;border-radius:14px;
      padding:18px 20px;margin-bottom:18px}
    .hv-tvm-hero h3{margin:0 0 6px!important;color:#FFFFFF!important;font-size:1.3rem}
    .hv-tvm-hero p{color:#CEDFE7!important;font-size:.93rem;margin:0}
    </style>""", unsafe_allow_html=True)
    st.markdown("""<div class="hv-tvm-hero"><h3>📄 IRP 유치 제안서 자동 생성기</h3>
    <p>은행 IRP와 하나증권 IRP를 같은 조건으로 비교하고, 수익·비용·하락위험·고객 적합성을 포함한 상담 자료를 생성합니다.</p></div>""",
    unsafe_allow_html=True)
    st.caption('세제는 금융회사에 따라 달라지지 않습니다. 예상수익률은 직접 입력하는 가정이며, 상품 추천 전 실제 취급 여부·투자성향을 확인하세요.')
    a, b = st.columns([1,2])
    with a:
        st.button('🎯 퇴직금 17억원 실습사례 채우기', on_click=_proposal_load_sample,
                  use_container_width=True, key='hv_prop_sample')
    with b:
        current_case = st.session_state.get('hv_tvm_case_principal', 0)
        if current_case:
            if st.button(f'현재 퇴직세금 상담의 잔여 운용원금 {_proposal_won(current_case)} 불러오기',
                         use_container_width=True, key='hv_prop_fetch'):
                st.session_state['hv_prop_principal'] = int(current_case)
                st.rerun()
    st.markdown('#### ① 상담 대상 및 자금 계획')
    for k, default in {
        'hv_prop_customer': '상담 고객', 'hv_prop_principal': 1_000_000_000,
        'hv_prop_gross': 0, 'hv_prop_cash': 0, 'hv_prop_monthly': 0,
        'hv_prop_savings': 0, 'hv_prop_other_irp': 0,
    }.items():
        st.session_state.setdefault(k, default)
    cx1, cx2, cx3 = st.columns(3)
    with cx1:
        customer = st.text_input('고객 구분명 (선택·실명 입력 지양)', key='hv_prop_customer')
        gross = int(st.number_input('퇴직급여 총액 · 참고(원)', min_value=0, step=10_000_000, key='hv_prop_gross'))
        cash = int(st.number_input('우선 확보 현금 · 참고(원)', min_value=0, step=10_000_000, key='hv_prop_cash'))
    with cx2:
        principal = int(st.number_input('비교할 IRP 운용 시작원금(원)', min_value=0, step=10_000_000,
                                         format='%d', key='hv_prop_principal'))
        years = int(st.number_input('운용기간(년)', min_value=1, max_value=40, value=10, step=1, key='hv_prop_years'))
        monthly = int(st.number_input('매월 추가납입(+) / 인출(−)(원)', step=100_000,
                                      format='%d', key='hv_prop_monthly'))
    with cx3:
        risk = st.selectbox('고객 투자성향 (상담 가정)',
            ['원금보전 최우선','안정추구','위험중립','적극투자'], key='hv_prop_risk')
        savings = int(st.number_input('별도 기존 연금저축(원) · 합산 제외', min_value=0,
                                      step=1_000_000, key='hv_prop_savings'))
        other_irp = int(st.number_input('별도 기존 IRP(원) · 합산 제외', min_value=0,
                                        step=1_000_000, key='hv_prop_other_irp'))
    st.info('**입력 유의:** 실습사례의 잔여 운용원금은 앞선 상담의 단순 시뮬레이션값이며 확정 잔액이 아닙니다. 비교 시작원금은 실제 운용 예정 IRP 잔액을 입력하세요. 퇴직급여·결혼자금·별도 기존 계좌는 설명용 참고값으로, 시작원금에 자동 합산하지 않습니다. 시작원금이 이연퇴직소득이라면 향후 인출세액은 별도입니다.')
    st.markdown('#### ② 은행 IRP vs 하나증권 IRP · 실제 제안 상품 기준')
    ba, ha = st.columns(2)
    with ba:
        with st.container(border=True):
            st.markdown('**🏦 기존 은행 IRP 운용안**')
            bank_product = st.text_input('은행 IRP 검토 상품·전략', value='원리금보장형 상품 또는 실제 운용상품', key='hv_prop_bank_product')
            bank_rate = st.number_input('은행 연 기대/약정수익률 가정(%)', min_value=-50.0, max_value=200.0,
                                        value=3.0, step=0.1, key='hv_prop_bank_rate')
            bank_fee = st.number_input('은행 연간 총비용률 가정(%)', min_value=0.0, max_value=20.0,
                                       value=0.0, step=0.05, key='hv_prop_bank_fee')
            bank_stress = st.number_input('은행 시장악화 시 연 수익률 가정(%)', min_value=-95.0, max_value=100.0,
                                         value=1.0, step=0.5, key='hv_prop_bank_stress')
            bank_guaranteed = st.checkbox('비교상품을 원리금보장형으로 가정', value=True, key='hv_prop_bank_guaranteed')
    with ha:
        with st.container(border=True):
            st.markdown('**📈 하나증권 IRP 제안 운용안**')
            hana_product = st.text_input('하나증권 검토 상품·전략', value='원리금보장형 + 채권/ETF 등 조합 검토',
                                         key='hv_prop_hana_product')
            hana_rate = st.number_input('하나증권 연 기대수익률 가정(%)', min_value=-50.0, max_value=200.0,
                                        value=5.0, step=0.1, key='hv_prop_hana_rate')
            hana_fee = st.number_input('하나증권 연간 총비용률 가정(%)', min_value=0.0, max_value=20.0,
                                       value=0.0, step=0.05, key='hv_prop_hana_fee')
            hana_stress = st.number_input('하나증권 시장악화 시 연 수익률 가정(%)', min_value=-95.0, max_value=100.0,
                                         value=-10.0, step=0.5, key='hv_prop_hana_stress')
            hana_guaranteed = st.checkbox('비교상품을 원리금보장형으로 가정', value=False, key='hv_prop_hana_guaranteed')
    strategy_risk = st.radio('하나증권 제안안의 위험구성 (설명용)',
        ['원리금보장형 중심', '혼합형', '실적배당형 비중 높음'], horizontal=True, key='hv_prop_mix')
    try:
        bank_path, b_depleted = _proposal_annual_paths(principal, years, monthly, bank_rate, bank_fee)
        hana_path, h_depleted = _proposal_annual_paths(principal, years, monthly, hana_rate, hana_fee)
        bank_bad, b_bad_depleted = _proposal_annual_paths(principal, years, monthly, bank_stress, bank_fee)
        hana_bad, h_bad_depleted = _proposal_annual_paths(principal, years, monthly, hana_stress, hana_fee)
    except (ValueError, OverflowError) as exc:
        st.error(f'운용 시뮬레이션 입력을 확인해 주세요: {exc}')
        return
    bank_final, hana_final = bank_path[-1], hana_path[-1]
    diff = hana_final - bank_final
    st.markdown('#### ③ 예상 결과 및 시장악화 시나리오')
    _kpis([
        ('은행 IRP 가정 순수익률', f'{bank_rate-bank_fee:.2f}%', '세전 수익률 − 연간 비용률'),
        ('하나증권 가정 순수익률', f'{hana_rate-hana_fee:.2f}%', '세전 수익률 − 연간 비용률'),
        _won_kpi(f'은행 IRP {years}년 후 평가액', bank_final),
        _won_kpi(f'하나증권 IRP {years}년 후 평가액', hana_final),
    ], green_last=diff>0)
    if diff > 0:
        st.success(f'같은 현금흐름과 가정하에서 하나증권 예상 평가액이 **{_proposal_won(diff)} 더 높습니다.** 확정수익이나 세제 혜택 차이는 아닙니다.')
    elif diff < 0:
        st.info(f'현재 가정에서는 은행 IRP의 예상 평가액이 **{_proposal_won(-diff)} 더 높습니다.**')
    else:
        st.info('현재 입력 조건에서는 두 IRP의 예상 평가액이 같습니다.')
    path_rows = [{'경과연도': year,
                  '은행 IRP 예상잔액': bank_path[year],
                  '하나증권 IRP 예상잔액': hana_path[year],
                  '차이(하나증권-은행)': hana_path[year]-bank_path[year]}
                 for year in range(0, years+1)]
    st.line_chart(pd.DataFrame({
        '연도': list(range(years+1)),
        '은행 IRP': bank_path,
        '하나증권 IRP': hana_path,
    }).set_index('연도'), height=300)
    stress_df = pd.DataFrame([
        {'구분':'은행 IRP', '기본 시나리오 평가액':bank_final,
         '시장 악화 가정 평가액':bank_bad[-1], '악화 시 감소액':bank_final-bank_bad[-1]},
        {'구분':'하나증권 IRP', '기본 시나리오 평가액':hana_final,
         '시장 악화 가정 평가액':hana_bad[-1], '악화 시 감소액':hana_final-hana_bad[-1]},
    ])
    st.markdown('**하락·시장악화 가정 (연 수익률이 기간 내 일정하게 지속되는 스트레스 테스트)**')
    st.dataframe(stress_df, hide_index=True, use_container_width=True,
                 column_config={x: st.column_config.NumberColumn(format='%d') for x in stress_df.columns[1:]})
    if any(x is not None for x in (b_depleted,h_depleted,b_bad_depleted,h_bad_depleted)):
        st.error('일부 시나리오는 계획 기간 중 잔액이 소진됩니다. 결과를 확정 지급액으로 설명하지 마세요.')
    with st.expander('ⓘ 운용 비교 계산식 · 연도별 예상금액'):
        st.markdown('**순수익률 가정:** `연 기대수익률(%) − 연 총비용률(%)`')
        st.markdown('**월 유효수익률:** `(1 + 연 순수익률/100)^(1/12) − 1`')
        st.markdown('**매월 말 잔액:** `MAX(0, 전달 잔액 × (1+월 유효수익률) + 월 납입/인출액)`')
        st.dataframe(pd.DataFrame(path_rows), hide_index=True, use_container_width=True)
        st.caption('각 연도 표는 반올림 표시합니다. 매월 말 현금흐름이며 수익률·비용률은 상수로 가정합니다.')
    st.markdown('#### ④ 자동 영업 결론 및 고객 제안서')
    conclusion = _proposal_interpretation(bank_final, hana_final, risk, strategy_risk, hana_guaranteed)
    st.markdown(f'**상담용 결론:** {conclusion}')
    st.caption('금융회사별 IRP 과세이연·연금수령세액은 동일 법 규정이 적용됩니다. 실제 제안 상품 확인, 투자성향 적합성, 원리금보장 여부, 운용/자산관리 수수료·상품별 보수 확인은 필수입니다.')
    doc = {
        'date': date.today().isoformat(), 'customer': customer, 'years': years,
        'gross': gross, 'cash': cash, 'principal': principal, 'monthly': monthly,
        'risk': risk, 'savings': savings, 'other_irp': other_irp,
        'bank_product': bank_product, 'hana_product': hana_product,
        'bank_rate': bank_rate, 'hana_rate': hana_rate,
        'bank_fee': bank_fee, 'hana_fee': hana_fee,
        'bank_guaranteed': bank_guaranteed, 'hana_guaranteed': hana_guaranteed,
        'bank_final': bank_final, 'hana_final': hana_final,
        'bank_stress_final': bank_bad[-1], 'hana_stress_final': hana_bad[-1],
    }
    doc_bytes = _proposal_html(doc, path_rows, conclusion)
    d1,d2=st.columns(2)
    with d1:
        st.download_button('📄 고객 제안서 다운로드 (인쇄용 HTML)', data=doc_bytes,
                           file_name='HanaV_IRP_고객제안서.html', mime='text/html',
                           use_container_width=True, key='hv_prop_html')
    with d2:
        st.download_button('📊 연도별 비교표 CSV 다운로드',
                           data=pd.DataFrame(path_rows).to_csv(index=False).encode('utf-8-sig'),
                           file_name='HanaV_IRP_운용비교.csv', mime='text/csv',
                           use_container_width=True, key='hv_prop_csv')
    st.caption('제안서 파일을 브라우저로 열어 **Ctrl+P → 프린터: PDF로 저장**을 선택하면 고객용 PDF가 됩니다. 고객정보는 앱 세션에서만 사용하며, 내려받은 파일의 보관·공유에 주의하세요.')
    st.warning('예상 평가액은 향후 인출 시 세금·미래 상품 변경·물가·변동성·원금 손실·투자한도 등을 모두 반영한 확정 세후금액이 아닙니다. 증권사 이전 자체로 높은 수익률이 보장되지는 않습니다.')


# ===== First-visit password gate (same APP_PASSWORD secret as HanaV Trading) =====
def _app_password_from_secrets() -> str | None:
    """Fail closed if the deployment has no valid secret configured."""
    try:
        password = st.secrets["APP_PASSWORD"]
    except (KeyError, FileNotFoundError):
        return None
    return password if isinstance(password, str) and password.strip() else None


def _require_login() -> None:
    configured_password = _app_password_from_secrets()
    if configured_password is None:
        st.error('앱 비밀번호가 설정되지 않았습니다. Streamlit 앱 Settings → Secrets에 APP_PASSWORD를 등록해 주세요.')
        st.code('APP_PASSWORD = "여기에_본인이_정한_비밀번호"', language='toml')
        st.stop()

    # Existing sessions are invalidated if the secret is rotated.
    password_fingerprint = hashlib.sha256(configured_password.encode('utf-8')).hexdigest()
    if st.session_state.get('_hv_auth_fingerprint') != password_fingerprint:
        st.session_state['_hv_logged_in'] = False
        st.session_state.pop('_hv_auth_fingerprint', None)

    if st.session_state.get('_hv_logged_in'):
        return

    # Do not construct any app data widgets until the user is authenticated.
    st.markdown('''<style>
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
       display:none!important;
    }
    [data-testid="stMainBlockContainer"] {
       max-width:610px!important;
       padding-top:clamp(4rem,13vh,7rem)!important;
    }
    .hv-login-head { text-align:center; margin-bottom:28px; }
    .hv-login-mark {
       display:inline-flex;align-items:center;justify-content:center;
       width:61px;height:61px;border-radius:17px;
       color:#073128;background:#51E7B3;
       box-shadow:0 0 35px rgba(72,228,173,.16);
       font-size:2.15rem;font-weight:900;margin:0 auto 18px;
    }
    .hv-login-title {font-size:clamp(1.75rem,3.7vw,2.4rem)!important;
       color:#fff;font-weight:850;letter-spacing:-.055em;line-height:1.3;}
    .hv-login-sub {color:#BBD0DC;font-size:1rem;margin-top:10px;}
    .hv-login-owner {color:#7EA69C;font-size:.8rem;margin-top:8px;}
    div[data-testid="stForm"] {
       padding:25px 27px 19px!important;
       background:#172B3A!important;
       border:1px solid #416073!important;
       border-top:3px solid #48E4AD!important;
       border-radius:17px!important;
       box-shadow:0 16px 52px rgba(0,0,0,.17);
    }
    div[data-testid="stForm"] [data-testid="stWidgetLabel"] p {
       color:#FFFFFF!important;font-weight:750!important;
    }
    div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
       width:100%!important;min-height:45px!important;
       color:#fff!important;background:#007C61!important;
       border:1px solid #48E4AD!important;
       font-size:1rem!important;font-weight:800!important;
    }
    .hv-login-foot {text-align:center;margin-top:19px;color:#A3BECC;font-size:.85rem;}
    @media(max-width:600px){
      div[data-testid="stForm"]{padding:20px 16px 16px!important}
    }
    </style>''', unsafe_allow_html=True)
    st.markdown(
       '<div class="hv-login-head">'
       '<div class="hv-login-mark">H</div>'
       '<div class="hv-login-title">HanaV Pension Tax Lab</div>'
       '<div class="hv-login-sub">Private Pension Tax Dashboard</div>'
       '<div class="hv-login-owner">Designed &amp; Built by K.H. Ahn</div>'
       '</div>', unsafe_allow_html=True,
    )
    with st.form('hv_pension_login', clear_on_submit=True):
        st.markdown('**접속 비밀번호**')
        typed_password = st.text_input(
            '접속 비밀번호', type='password', placeholder='비밀번호를 입력하세요',
            label_visibility='collapsed',
        )
        submitted = st.form_submit_button('로그인', use_container_width=True)
    if submitted:
        if hmac.compare_digest(typed_password, configured_password):
            st.session_state['_hv_logged_in'] = True
            st.session_state['_hv_auth_fingerprint'] = password_fingerprint
            st.rerun()
        else:
            st.error('비밀번호가 일치하지 않습니다. 다시 입력해 주세요.')
    st.markdown(
        '<div class="hv-login-foot">인가된 사용자만 이용할 수 있는 내부 연금 상담용 프로그램입니다.</div>',
        unsafe_allow_html=True,
    )
    st.stop()


_require_login()

# Top of sidebar: voluntary logout also clears customer inputs from session state.
with st.sidebar:
    st.caption('🔒 로그인됨 · HanaV Pension Tax Lab')
    if st.button('로그아웃', key='hv_pension_logout', use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()

st.title('HanaV Pension Tax Lab')
st.caption('2026년 세법 기반 퇴직소득세·IRP 연금수령 비교 | 내부 상담용 시뮬레이터 (실제 원천징수 확정세액 아님)')
with st.sidebar:
    choice = st.radio('업무 메뉴', ['퇴직·연금 유치 상담', '🧮 금융계산기 · CPT / 운용비교', '📄 IRP 유치 제안서'],
                      key='hv_main_menu', label_visibility='visible')
    st.divider()
if choice.startswith('🧮'):
    _tvm_draw_page()
    st.stop()
if choice.startswith('📄'):
    _proposal_draw_page()
    st.stop()


# Streamlit session_state keys make values update immediately when the left
# sidebar retirement payment changes. Ledger balance/valuation may differ from
# original severance: both automatic links can be individually disabled.
_DEFAULT_GROSS = 100_000_000
for _state_key, _initial in {
    'hv_gross_retirement': _DEFAULT_GROSS,
    'hv_non_taxable_retirement': 0,
    'hv_def_balance': _DEFAULT_GROSS,
    'hv_excluded_balance': 0,
    'hv_taxable_balance': 0,
    'hv_evaluated_balance': _DEFAULT_GROSS,
    'hv_auto_def_balance': True,
    'hv_auto_evaluated_balance': True,
}.items():
    if _state_key not in st.session_state:
        st.session_state[_state_key] = _initial


def _sync_evaluated_from_balances():
    if st.session_state.get('hv_auto_evaluated_balance', True):
        st.session_state['hv_evaluated_balance'] = sum(
            int(st.session_state.get(name, 0))
            for name in ('hv_def_balance', 'hv_excluded_balance', 'hv_taxable_balance')
        )


def _sync_from_retirement_payment():
    if st.session_state.get('hv_auto_def_balance', True):
        gross = int(st.session_state.get('hv_gross_retirement', 0))
        nontax = int(st.session_state.get('hv_non_taxable_retirement', 0))
        st.session_state['hv_def_balance'] = max(0, gross - nontax)
    _sync_evaluated_from_balances()


def _load_advisory_case() -> None:
    """Load only non-identifying scenario numbers; individual values stay editable."""
    values = {
        'hv_customer_birth': date(1969, 3, 16),
        'hv_plan_type': 'DB',
        'hv_plan_joined': date(2015, 1, 1),
        'hv_receiving_irp_open': date(2026, 10, 30),
        'hv_service_entry': date(1996, 11, 23),
        'hv_service_retirement': date(2026, 10, 30),
        'hv_gross_retirement': 1_700_000_000,
        'hv_non_taxable_retirement': 0,
        'hv_auto_def_balance': True,
        'hv_auto_evaluated_balance': True,
        'hv_def_balance': 1_700_000_000,
        'hv_evaluated_balance': 1_700_000_000,
        'hv_excluded_balance': 0,
        'hv_taxable_balance': 0,
        'hv_legacy_db_full_transfer': False,
        'hv_analysis_year': 2026,
        'hv_advice_year': 2026,
        'hv_planned_receipt_day': date(2026, 10, 30),
        'hv_new_withdrawal': 500_000_000,
        'hv_advice_old_savings': 70_000_000,
        'hv_advice_bank_irp': 40_000_000,
        'hv_advice_cash': 500_000_000,
        'hv_advice_cash_mode': '세후 실제 필요액',
    }
    for key, val in values.items():
        st.session_state[key] = val


with st.sidebar:
    st.subheader('고객·퇴직연금 정보')
    st.button('🎯 실전사례 불러오기 · 퇴직금 17억원', on_click=_load_advisory_case,
              key='hv_case_load', use_container_width=True,
              help='퇴직급여 17억원, 기존 연금저축 7천만원·H은행 IRP 4천만원(모두 퇴직금과 별도), 세후 결혼자금 목표 5억원을 불러옵니다.')
    birth = st.date_input('생년월일', value=date(1966, 6, 1), min_value=date(1920,1,1), max_value=date(2010,12,31), key='hv_customer_birth')
    plan_type = st.selectbox('퇴직연금 종류', ['DB', 'DC', 'IRP'], key='hv_plan_type')
    plan_joined = st.date_input('기존 퇴직연금제도 가입일', value=date(2010,1,1), min_value=date(1970,1,1), max_value=date(2026,12,31), key='hv_plan_joined',
                                help='현재 수령계좌가 IRP라도 최초 DB형 퇴직연금 가입일을 입력합니다. 가입이력을 확인한 날짜를 사용하세요.')
    account_open = st.date_input('연금계좌 가입일/IRP 개설일', value=date(2026,1,1), min_value=date(1970,1,1), max_value=date(2026,12,31), key='hv_receiving_irp_open')
    # IRP is the receiving-account type, so it must NOT disable a prior-DB
    # full-transfer confirmation. Do not auto-check based on the date alone.
    db_full = st.checkbox(
        '2013.3.1 이전 DB 가입 + 퇴직소득 전액 신규 IRP 이체',
        value=False,
        disabled=plan_type == 'DC',
        key='hv_legacy_db_full_transfer',
        help='현재 유형이 IRP라도, 과거 DB형 가입자이고 퇴직소득 전액을 신규 IRP로 이체한 사실이 확인되면 체크합니다. '
             'DB 최초 가입일이 2013.3.1 이후라면 체크해도 특례가 적용되지 않습니다.',
    )
    if plan_type == 'DC':
        db_full = False
    if db_full and plan_joined >= date(2013,3,1):
        st.warning('DB 최초 가입일이 2013.3.1 이후여서 이전 DB 가입자 특례를 적용할 수 없습니다.')
    st.divider()
    st.subheader('근속·퇴직소득')
    entry = st.date_input('입사일', value=date(2007,1,1), min_value=date(1950,1,1), max_value=date(2026,12,31), key='hv_service_entry')
    retirement_day = st.date_input('퇴직일(마지막 근무일)', value=date(2026,12,31), min_value=date(2000,1,1), max_value=date(2035,12,31), key='hv_service_retirement')
    manual_years = st.checkbox('공식 원천징수영수증의 근속연수 직접 입력', value=False)
    try: computed_years = service_years(entry, retirement_day)
    except ValueError: computed_years = None
    years = int(st.number_input('세법상 근속연수(년)', min_value=1, max_value=80, value=computed_years or 20,
                                disabled=not manual_years)) if manual_years else computed_years
    gross_retirement = st.number_input(
        '퇴직급여 총액(원)', min_value=0, step=1_000_000, format='%d',
        key='hv_gross_retirement', on_change=_sync_from_retirement_payment,
        help='퇴직급여를 변경하면 자동 연동 중인 이연퇴직소득 잔액과 한도산정용 평가액도 변경됩니다.',
    )
    non_taxable = st.number_input(
        '비과세 퇴직소득(원)', min_value=0, step=100_000,
        key='hv_non_taxable_retirement', on_change=_sync_from_retirement_payment,
    )
    st.caption(f'입력 퇴직급여: {gross_retirement:,}원 · 비과세: {non_taxable:,}원')

if years is None:
    st.error('입사일과 퇴직일의 순서를 확인해 주세요.')
    st.stop()
if non_taxable > gross_retirement:
    st.error('비과세금액은 퇴직급여 총액을 초과할 수 없습니다.')
    st.stop()

ret_tax = estimate_retirement_tax(int(gross_retirement), int(years), int(non_taxable))

# ===== Additional high-value retirement-consultation screen (new-account model) =====
def _new_retirement_withdrawal_amount(gross_requested: int, account_value: int,
                                      tax_income: int, annual_limit: int,
                                      tax_year: int, actual_year: int):
    """Use the existing vetted pension withdrawal engine (single deferred-tax lot)."""
    return calculate_withdrawal(
        amount=int(gross_requested), prior_year_withdrawals=0,
        statutory_limit=int(annual_limit), excluded_balance=0,
        retirement_balance=int(account_value), taxable_balance=0,
        remaining_deferred_income_tax=int(tax_income),
        actual_receipt_year=int(actual_year), age=age_on(birth, retirement_day),
        calendar_year=int(tax_year), qualifies=True,
    )


def _gross_for_net_cash(net_target: int, total_money: int,
                        income_tax: int, annual_limit: int, tax_year: int) -> int | None:
    """Binary search for MINIMUM gross payment achieving after-tax target."""
    if net_target < 0 or net_target > total_money:
        return None
    if net_target == 0:
        return 0
    if _new_retirement_withdrawal_amount(
            total_money, total_money, income_tax, annual_limit, tax_year, 1).total_net < net_target:
        return None
    lo, hi = 0, total_money
    while lo < hi:
        mid = (lo + hi) // 2
        calc = _new_retirement_withdrawal_amount(mid, total_money, income_tax, annual_limit, tax_year, 1)
        if calc.total_net >= net_target:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _direct_retirement_lump_tax(gross_part: int, retirement_income: int, full_income_tax: int) -> int:
    """Partial direct severance payment: proportional share of total national tax."""
    if retirement_income <= 0 or not (0 <= gross_part <= retirement_income):
        raise ValueError('퇴직금 분할 지급액 범위를 확인해 주세요.')
    national = floor_krw(Decimal(full_income_tax)*Decimal(gross_part)/Decimal(retirement_income))
    return national + floor_krw(Decimal(national)*Decimal('0.1'))


def _direct_retirement_gross_for_net(net_cash: int, retirement_income: int,
                                     full_income_tax: int) -> int | None:
    """Gross up partial immediate severance payout (not via pension account)."""
    if net_cash < 0 or net_cash > retirement_income:
        return None
    if retirement_income-_direct_retirement_lump_tax(retirement_income, retirement_income, full_income_tax) < net_cash:
        return None
    lo,hi=0,retirement_income
    while lo < hi:
        mid=(lo+hi)//2
        if mid-_direct_retirement_lump_tax(mid,retirement_income,full_income_tax) >= net_cash:
            hi=mid
        else:
            lo=mid+1
    return lo


# ===== Advisor comparison helper: old pension savings plus new IRP =====
def _old_pension_savings_tax(amount: int, non_deducted_basis: int,
                             annual_pension_room: int, age: int,
                             other_pension_taxable_year: int=0) -> dict:
    """Tax estimate for an OLD pension savings account, NOT for deferred severance.

    Excluded (non-deducted) contributions are drawn first, and do NOT exhaust
    the statutory pension withdrawal room. The remaining taxable portion is
    eligible for age-bracket pension tax inside the room; outside = other income.
    All amounts are independent of the new retirement-income IRP tax lot.
    This is an illustration: provider's actual tax-source ledger is definitive.
    """
    if min(amount, non_deducted_basis, annual_pension_room, age, other_pension_taxable_year) < 0:
        raise ValueError('연금저축 재원과 인출금액을 확인하세요.')
    excluded = min(int(amount), int(non_deducted_basis))
    taxable = int(amount) - excluded
    pension_taxable = min(taxable, int(annual_pension_room))
    nonpension_taxable = taxable - pension_taxable
    p_rate = age_pension_tax_rate(age)
    pension_national = floor_krw(Decimal(pension_taxable)*p_rate)
    pension_local = floor_krw(Decimal(pension_national)*Decimal('0.1'))
    other_national = floor_krw(Decimal(nonpension_taxable)*Decimal('0.15'))
    other_local = floor_krw(Decimal(other_national)*Decimal('0.1'))
    # The age rate above is withholding. For ordinary taxable pension savings,
    # > 15m won in annual private-pension income requires election of comprehensive
    # taxation or 16.5% separate taxation. Conservatively model the latter,
    # across the WHOLE taxable pension amount (not just the excess).
    withheld_pension = pension_national+pension_local
    threshold_exceeded = (int(other_pension_taxable_year)+pension_taxable > 15_000_000)
    if threshold_exceeded:
        # 15% national income tax + 10% local tax on that tax
        pension_national = floor_krw(Decimal(pension_taxable)*Decimal('0.15'))
        pension_local = floor_krw(Decimal(pension_national)*Decimal('0.1'))
    total_tax = pension_national+pension_local+other_national+other_local
    return {
        'gross':int(amount), 'excluded':excluded,
        'pension_taxable':pension_taxable, 'nonpension_taxable':nonpension_taxable,
        'pension_tax':pension_national+pension_local,
        'withheld_pension_tax':withheld_pension,
        'pension_over_15m':threshold_exceeded,
        'final_tax_extra':pension_national+pension_local-withheld_pension,
        'nonpension_tax':other_national+other_local,
        'total_tax':total_tax, 'net':int(amount)-total_tax,
    }


def _optimize_combined_funding(net_goal: int, *, old_balance: int,
                               old_excluded: int, old_room: int, old_age: int,
                               new_retirement_balance: int, retirement_national_tax: int,
                               retirement_pension_limit: int, calendar_year: int,
                               other_pension_taxable_year: int=0):
    """Minimum *current* tax (not minimum lifetime tax), conserving annual room.

    Search discrete 250k-won legacy withdrawals plus exact endpoints; each
    candidate gross-ups the new IRP withdrawal to the same wedding cash.
    No post-2013 account is moved into a pre-2013 pension savings account.
    """
    if net_goal < 0:
        raise ValueError('목표 실수령액은 음수일 수 없습니다.')
    # Tax-exempt basis is not included in the pension-withdrawal ceiling.
    max_old = min(int(old_balance), int(old_excluded)+int(old_room))
    candidates = set(range(0, max_old+1, 250_000))
    candidates.add(max_old)
    candidates.add(min(max_old, int(old_excluded)))
    best = None
    for old_gross in sorted(candidates):
        old_result = _old_pension_savings_tax(old_gross, old_excluded, old_room, old_age,
                                              other_pension_taxable_year)
        if old_result['net'] > net_goal:
            continue
        irp_needed = _gross_for_net_cash(
            net_goal-old_result['net'], new_retirement_balance,
            retirement_national_tax, retirement_pension_limit, calendar_year)
        if irp_needed is None:
            continue
        new_draw = _new_retirement_withdrawal_amount(
            irp_needed, new_retirement_balance, retirement_national_tax,
            retirement_pension_limit, calendar_year, 1)
        combined_tax = old_result['total_tax']+new_draw.total_tax
        result = {'old':old_result,'irp_gross':irp_needed,'irp_draw':new_draw,
                  'combined_tax':combined_tax,'net':old_result['net']+new_draw.total_net}
        if (best is None or (result['combined_tax'],old_gross) <
                         (best['combined_tax'],best['old']['gross'])):
            best=result
    return best


st.subheader('🎯 고액 퇴직금 유치 상담 · 은행 예금 / 은행 IRP / 하나증권 IRP')
st.caption('상담 시나리오별 당장의 세금, 연금계좌에 남는 자금, 금융회사별 운용조건을 분리해 비교합니다.')
with st.container(border=True):
    st.markdown(
        f'#### 고객 사례 분석 · {_short_krw(int(st.session_state.get("hv_advice_cash", 500_000_000)))} '
        '결혼자금 마련 후 잔여자금 운용'
    )
    # 왼쪽 사이드바의 17억원 퇴직금을 오른쪽에서도 즉시 확인할 수 있도록 표시.
    # 기존 연금저축과 기존 H은행 IRP는 신규 퇴직금에 합산하지 않는다.
    _kpis([
        _won_kpi('이번 퇴직급여 · 신규 유치 대상', int(gross_retirement)),
        _won_kpi('기존 연금저축 · 별도 자산', int(st.session_state.get('hv_advice_old_savings', 70_000_000))),
        _won_kpi('기존 H은행 IRP · 별도 자산', int(st.session_state.get('hv_advice_bank_irp', 40_000_000))),
        _won_kpi('결혼자금 목표 · 퇴직금에서 인출', int(st.session_state.get('hv_advice_cash', 500_000_000))),
    ])
    st.caption(
        f'✅ 자금 구분: 이번 퇴직급여 **{_short_krw(int(gross_retirement))}** · '
        f'별도 기존 연금저축 **{_short_krw(int(st.session_state.get("hv_advice_old_savings", 70_000_000)))}** · '
        f'별도 기존 H은행 IRP **{_short_krw(int(st.session_state.get("hv_advice_bank_irp", 40_000_000)))}**. '
        '기존 계좌는 퇴직금에 합산하지 않습니다. '
        f'결혼자금 목표 **{_short_krw(int(st.session_state.get("hv_advice_cash", 500_000_000)))}**을 '
        '세후 기준으로 마련할 경우 실제 인출원금은 목표액보다 클 수 있습니다.'
    )
    sleft, sright = st.columns([1.04, 1])
    with sleft:
        st.markdown('**다른 금융기관에 보유한 연금계좌 — 퇴직금 17억원과 별도 관리**')
        existing_savings = int(st.number_input(
            '연금저축 평가액(원) · 2009년 12월 가입', min_value=0,
            step=1_000_000, key='hv_advice_old_savings',
            value=70_000_000,
            help='2009년 12월 가입일은 월만 알려져 있으므로 해당 월 가입으로 취급합니다. 기존 납입액의 세액공제 여부는 별도 확인해야 합니다.'))
        existing_bank_irp = int(st.number_input(
            '기존 H은행 IRP 평가액(원) · 2021.10.19 가입', min_value=0,
            step=1_000_000, key='hv_advice_bank_irp', value=40_000_000,
            help='기존 H은행 IRP는 신규 퇴직금 유치 IRP와 별도 계좌로 가정합니다. 두 계좌를 합산해 인출하는 경우 재계산해야 합니다.'))
    with sright:
        st.markdown('**자녀 결혼자금 — 세전·세후 입력을 명확히 선택**')
        mode_wedding = st.radio(
            '5억원의 의미', ['세후 실제 필요액', '세전 인출신청액'],
            key='hv_advice_cash_mode', horizontal=True,
            help='세후 필요액은 실제 결혼자금 5억원을 받기 위한 인출 원금까지 역산합니다.')
        wanted = int(st.number_input(
            '결혼자금 목표액(원)', min_value=0,
            step=10_000_000, key='hv_advice_cash', value=500_000_000))
        compare_year = st.number_input(
            '퇴직금 인출 예정 연도', min_value=2026, max_value=2050,
            value=2026, step=1, key='hv_advice_year',
            help='신규 IRP에 퇴직금이 입금된 뒤 해당 연도 연금개시 및 수령한다고 가정합니다.')
        st.caption('이 분석은 새 연금계좌에 퇴직소득이 **전액 이체**되고, 기존 연금저축·기존 IRP에서는 인출하지 않는 경우입니다.')

    st.markdown('##### ① 퇴직소득세 및 최초 연금수령한도')
    original_retirement = int(gross_retirement - non_taxable)
    receipt_date = max(retirement_day, account_open)
    first_allowed = first_eligible_date(birth, account_open, True)
    # This is new retirement money, not 2021 bank IRP or 2009 annuity.
    applicable = (original_retirement > 0 and compare_year >= max(first_allowed.year, retirement_day.year))
    if account_open < retirement_day:
        st.info('수령 IRP 개설일은 퇴직일 이전이어도 됩니다. 퇴직금이 해당 IRP로 들어와 연금개시되는 날짜는 퇴직일 이후로 가정합니다.')
    if compare_year < retirement_day.year:
        st.error('분석 연도가 퇴직 연도보다 빠릅니다. 결혼자금 인출 예정 연도를 다시 설정하세요.')
    elif not applicable:
        st.warning('해당 분석 연도에는 이 사례의 신규 퇴직금에 대한 연금수령 요건을 충족하지 못합니다. 계좌 개설일과 퇴직일을 확인하세요.')
    else:
        # Old DB pre-2013 rule matters ONLY if qualifying full transfer is verified.
        sales_legacy = bool(
            legacy_eligible(account_open, plan_type, plan_joined, db_full)
            or (plan_type == 'IRP' and db_full and plan_joined < date(2013, 3, 1)))
        first_year = max(first_allowed.year, retirement_day.year)
        annual_limit, limit_year = pension_limit(original_retirement, first_year, int(compare_year), sales_legacy)
        if limit_year >= 11:
            annual_limit = original_retirement
        # Actual receipt count 1 is the conservative default for this new IRP tax lot.
        if mode_wedding.startswith('세후'):
            gross_cash = _gross_for_net_cash(wanted, original_retirement,
                                             ret_tax.income_tax, annual_limit, int(compare_year))
        else:
            gross_cash = wanted if wanted <= original_retirement else None
        if gross_cash is None:
            st.error('목표 결혼자금을 이 퇴직금만으로 마련할 수 없습니다. 세금 차감과 퇴직금 총액을 확인하세요.')
        else:
            draw = _new_retirement_withdrawal_amount(
                gross_cash, original_retirement, ret_tax.income_tax, annual_limit, int(compare_year), 1)
            full_lump = int(ret_tax.total_tax)
            deferral_remaining_principal = original_retirement-gross_cash
            st.session_state['hv_tvm_case_principal'] = int(deferral_remaining_principal)
            # Remaining tax is an estimate based on deferred-income basis consumption, not 'savings'.
            all_lump_draw_tax = draw.hypothetical_all_lump_tax
            saving_per_draw = draw.saving_vs_all_lump
            future_base_income_tax = max(0, ret_tax.income_tax -
                floor_krw(Decimal(ret_tax.income_tax)*Decimal(gross_cash)/Decimal(original_retirement)))
            future_base_local = floor_krw(Decimal(future_base_income_tax)*Decimal('0.1'))
            remaining_total_future_lump_tax = future_base_income_tax+future_base_local
            # Benchmarked at the SAME NET wedding spending (not same gross withdrawal).
            cash_for_wedding = draw.total_net
            bank_lump_bank_balance = original_retirement-full_lump-cash_for_wedding
            actual_immediate_tax_deferred = full_lump-draw.total_tax
            # Alternative: separate immediate cash payment from retirement benefit,
            # with only remaining severance contributed to a new IRP. Actual
            # feasibility is conditional on payer/provider procedures.
            direct_lump_gross = _direct_retirement_gross_for_net(
                cash_for_wedding, original_retirement, ret_tax.income_tax)
            direct_lump_paid_tax = _direct_retirement_lump_tax(
                direct_lump_gross, original_retirement, ret_tax.income_tax) if direct_lump_gross is not None else None
            direct_lump_irp_rest = (original_retirement-direct_lump_gross
                                    if direct_lump_gross is not None else None)
            # Lead the consultation with the defensible recommendation.
            st.markdown('##### 이번 고객 1차 유치 결론')
            st.info(
                f'**H은행 일반예금으로 퇴직금 전액 현금화** 시 퇴직소득세 **{full_lump:,}원**. '
                f'**하나증권 신규 IRP 전액 이체 후 결혼자금만 인출** 시 이번 인출세금 '
                f'**{draw.total_tax:,}원**, IRP 잔여원금(세전) **{deferral_remaining_principal:,}원**. '
                f'즉시 납부 세금 차이 **{actual_immediate_tax_deferred:,}원**에는 '
                '향후 납부할 세금의 과세이연분이 포함됩니다. '
                '**H은행 IRP로 같은 전략을 실행하면 세법상 세금 차이는 0원**입니다. '
                '아래 ⑥에서 기존 연금저축 활용, 수수료와 수익률까지 반영한 추천안을 확인하세요.'
            )
            st.markdown(f'**퇴직 후 신규 IRP 가정:** {compare_year}년 **{limit_year}년차**, '
                        f'연금수령한도 **{_short_krw(annual_limit)}** · 예상 퇴직소득세 '
                        f'**{_short_krw(full_lump)}** (국세+지방세)')
            _kpis([
                _won_kpi('결혼자금 세전 인출액', gross_cash),
                _won_kpi('결혼자금 세후 실수령액', cash_for_wedding),
                _won_kpi('이번 인출 세금', draw.total_tax),
                _won_kpi('이번 인출분 예상 세율감면 효과', saving_per_draw),
            ], green_last=True)
            st.markdown('##### ② 연금수령한도 내·초과 금액과 세율')
            f1, f2 = st.columns(2)
            with f1:
                _kpis([_won_kpi('한도 내 인출 (연금소득 과세)', draw.pension_amount)])
            with f2:
                _kpis([_won_kpi('한도 초과 인출 (퇴직소득 과세)', draw.nonpension_amount)])
            with st.expander('ⓘ 이 사례의 연금한도·퇴직소득세 계산식 모두 펼치기'):
                st.markdown('**퇴직소득세(2026년, 국세)**')
                st.markdown(f'퇴직소득세 = 환산산출세액 × 근속연수 / 12 = **{ret_tax.income_tax:,}원**; '
                            f'지방소득세 = **{ret_tax.local_income_tax:,}원**')
                st.markdown('**연금수령한도(신규 IRP 평가액이 퇴직금 전액과 같다는 가정)**')
                if limit_year < 11:
                    st.markdown(f'{original_retirement:,}원 ÷ (11 − {limit_year}) × 120% = **{annual_limit:,}원**')
                else:
                    st.markdown('11년차 이후 법정 연간 수령한도 제한 없음')
                st.markdown(f'**연금수령 인정액:** MIN({gross_cash:,}, {annual_limit:,}) = **{draw.pension_amount:,}원**')
                st.markdown(f'**연금외수령액:** {gross_cash:,} − {draw.pension_amount:,} = **{draw.nonpension_amount:,}원**')
                st.markdown(f'**이연퇴직소득 국세 유효세율:** {ret_tax.income_tax:,} ÷ {original_retirement:,} '
                            f'= {ret_tax.income_tax/original_retirement*100:.4f}%')
                st.markdown('**한도 내:** 위 유효세율 × 70% (신규 실제수령 1년차) / **한도 초과:** 위 유효세율 × 100%')
                for row in draw.rows:
                    st.markdown(f'**{row.treatment} {row.gross:,}원:** 국세 {row.income_tax:,}원 '
                                f'+ 지방소득세 {row.local_income_tax:,}원 = **{row.total_tax:,}원** '
                                f'(국세 유효세율 {row.income_tax_rate_percent:.4f}%)')
                st.markdown(f'**이번 인출 총세금:** {draw.total_tax:,}원 / '
                            f'**수령 현금:** {gross_cash:,} − {draw.total_tax:,} = {cash_for_wedding:,}원')
                if mode_wedding.startswith('세후'):
                    st.caption('세후 목표액을 충족하는 최소 세전 인출액은 1원 단위 이분탐색으로 역산합니다.')
                st.caption('이 계좌에 이미 다른 과세 재원·이연퇴직소득 입금 이력·기인출이 있으면 금융기관 원장 기준으로 재계산해야 합니다.')

            st.markdown('##### ③ 은행 예금과 IRP 운용 시나리오 (결혼자금 동일 실수령 기준)')
            compared_rows = [
                {'경로':'H은행 일반예금 (퇴직금 전액 일시금 수령 후)',
                 '현재 퇴직금 관련 납부세금(원)':full_lump,
                 '결혼자금 지급(세후,원)':cash_for_wedding,
                 '계좌에 남는 잔액(원)':bank_lump_bank_balance,
                 '잔액의 세금 상태':'퇴직소득세 납부 완료'},
                {'경로':'일부 현금 지급 + 잔액 신규 IRP 이체 (가능 여부 확인)',
                 '현재 퇴직금 관련 납부세금(원)':direct_lump_paid_tax if direct_lump_paid_tax is not None else 0,
                 '결혼자금 지급(세후,원)':cash_for_wedding,
                 '계좌에 남는 잔액(원)':direct_lump_irp_rest if direct_lump_irp_rest is not None else 0,
                 '잔액의 세금 상태':'잔여 IRP 세금 이연 · 지급기관 절차 확인'},
                {'경로':'H은행 신규 IRP (퇴직금 전액 이전 후 일부 인출)',
                 '현재 퇴직금 관련 납부세금(원)':draw.total_tax,
                 '결혼자금 지급(세후,원)':cash_for_wedding,
                 '계좌에 남는 잔액(원)':deferral_remaining_principal,
                 '잔액의 세금 상태':'향후 인출 시 이연퇴직소득세 발생'},
                {'경로':'하나증권 신규 IRP (퇴직금 전액 이전 후 일부 인출)',
                 '현재 퇴직금 관련 납부세금(원)':draw.total_tax,
                 '결혼자금 지급(세후,원)':cash_for_wedding,
                 '계좌에 남는 잔액(원)':deferral_remaining_principal,
                 '잔액의 세금 상태':'향후 인출 시 이연퇴직소득세 발생'},
            ]
            if direct_lump_gross is None:
                compared_rows=[row for row in compared_rows if not row['경로'].startswith('일부 현금')]
            display = pd.DataFrame(compared_rows)
            st.dataframe(display, hide_index=True, use_container_width=True,
                         column_config={
                            '현재 퇴직금 관련 납부세금(원)':st.column_config.NumberColumn(format='%d'),
                            '결혼자금 지급(세후,원)':st.column_config.NumberColumn(format='%d'),
                            '계좌에 남는 잔액(원)':st.column_config.NumberColumn(format='%d'),
                         })
            _kpis([
                _won_kpi('일반예금 방식 대비 현재 세금 납부 차이', actual_immediate_tax_deferred),
                _won_kpi('이 중 이번 인출분의 세율감면 효과', saving_per_draw),
                _won_kpi('IRP 잔여 이연퇴직소득 세전 잔액', deferral_remaining_principal),
                _won_kpi('잔여액 전부 연금외수령 가정 시 잠재세금', remaining_total_future_lump_tax),
            ], green_last=False)
            if direct_lump_gross is not None:
                with st.expander('ⓘ 일부 현금지급 후 나머지 IRP vs 전액 IRP 후 인출'):
                    st.markdown(f'**부분 현금지급 방식:** 결혼자금 순수령액 {cash_for_wedding:,}원 확보를 위해 '
                                f'퇴직금 **{direct_lump_gross:,}원** 즉시 지급, '
                                f'비례 퇴직소득세 **{direct_lump_paid_tax:,}원** 원천징수, '
                                f'잔여 퇴직급여 **{direct_lump_irp_rest:,}원**을 IRP로 이체하는 가정입니다.')
                    st.markdown(f'**전액 IRP 후 인출 방식:** 결혼자금 순수령액 {cash_for_wedding:,}원 확보에 '
                                f'세전 인출 **{gross_cash:,}원**, 세금 **{draw.total_tax:,}원**, '
                                f'잔여 IRP **{deferral_remaining_principal:,}원**입니다.')
                    st.markdown(f'**같은 현금 확보 후 잔여 IRP 원금 차이:** '
                                f'**{deferral_remaining_principal-direct_lump_irp_rest:+,}원** '
                                '(전액 IRP 후 인출 − 일부 현금 직접지급).')
                    st.caption('중간 일부 현금지급 가능 여부 및 지급기관 처리방식, 연금개시 승인·부분 인출 가능 여부는 '
                               '퇴직연금사업자와 퇴직급여 지급기관에 반드시 확인해야 합니다.')
            st.warning('**현재 납부세금 차이 전체를 절세액으로 홍보하면 안 됩니다.** 잔여 IRP의 퇴직소득세가 미래로 이연된 금액이 포함됩니다. '
                       '확정된 방식 간 세율 차이는 이번 인출분의 연금수령 인정액에 대한 감면분입니다. '
                       '미래에도 연금 한도 내에서 나눠 받으면 추가 감면이 가능하지만, 실제 일정·수익·세법에 따라 달라집니다.')
            if bank_lump_bank_balance < 0:
                st.error('일시금 방식으로는 동일한 세후 결혼자금을 충당하지 못하는 조건입니다.')

            st.markdown('##### ④ 은행 일반예금·은행 IRP·하나증권 IRP — 운용조건 직접 비교')
            y1,y2,y3,y4 = st.columns(4)
            with y1:
                bank_irp_rate = st.number_input('H은행 IRP 가정 수익률(연 %)',min_value=-30.,max_value=30.,value=0.,step=.1, key='hv_bank_irp_rate')
            with y2:
                hana_irp_rate = st.number_input('하나증권 IRP 가정 수익률(연 %)',min_value=-30.,max_value=30.,value=0.,step=.1, key='hv_hana_irp_rate')
            with y3:
                bank_irp_fee = st.number_input('H은행 IRP 가정 총비용(연 %)',min_value=0.,max_value=10.,value=0.,step=.05, key='hv_bank_irp_fee')
            with y4:
                hana_irp_fee = st.number_input('하나증권 IRP 가정 총비용(연 %)',min_value=0.,max_value=10.,value=0.,step=.05, key='hv_hana_irp_fee')
            bank_deposit_rate = st.number_input(
                'H은행 일반예금 금리 가정(연 %, 실제 견적 입력)',
                min_value=0.,max_value=30.,value=0.,step=.1,key='hv_bank_deposit_rate')
            two_years = st.slider('운용 기간(년) · 단순 연복리 가정',1,20,5,key='hv_projection_years')
            bank_deposit_proj = int(round(max(0,bank_lump_bank_balance)*((1+bank_deposit_rate/100)**two_years)))
            bank_proj = int(round(deferral_remaining_principal*((1+(bank_irp_rate-bank_irp_fee)/100)**two_years)))
            hana_proj = int(round(deferral_remaining_principal*((1+(hana_irp_rate-hana_irp_fee)/100)**two_years)))
            projections=pd.DataFrame([
                {'운용':'H은행 일반예금', '순가정 연수익률(%)':bank_deposit_rate,
                 '세전 예상 평가액(원)':bank_deposit_proj, '평가액 과세상태':'퇴직소득세 납부 후 원금 / 예금이자소득세 아직 미반영'},
                {'운용':'H은행 IRP','순가정 연수익률(%)':bank_irp_rate-bank_irp_fee,
                 '세전 예상 평가액(원)':bank_proj, '평가액 과세상태':'향후 연금 인출세액 미차감'},
                {'운용':'하나증권 IRP','순가정 연수익률(%)':hana_irp_rate-hana_irp_fee,
                 '세전 예상 평가액(원)':hana_proj, '평가액 과세상태':'향후 연금 인출세액 미차감'},
            ])
            st.dataframe(projections,hide_index=True,use_container_width=True)
            st.markdown(f'**{two_years}년 후 세전 평가액 차이(하나증권 − H은행):** '
                        f'**{hana_proj-bank_proj:+,}원**')
            st.caption('수익률·수수료는 입력한 가정값이지 해당 금융기관의 실제 공시값이나 확정 금리가 아닙니다. '
                       '향후 인출세금·환매비용·원금손실·복리 중간인출·수수료 부과기준은 단순화했습니다. '
                       '일반예금의 이자소득세와 금융소득종합과세, IRP의 미래 인출세금은 이 운용 비교에서 미반영입니다. ')

            st.markdown('##### ⑤ 기존 계좌 확인 및 고객 상담 포인트')
            old_pension_can = max(date(birth.year+55,birth.month,birth.day), date(2009,12,1))
            old_pension_count = 6+int(compare_year)-old_pension_can.year
            old_lim = pension_limit(existing_savings, old_pension_can.year, int(compare_year), True)[0] if int(compare_year)>=old_pension_can.year else 0
            bank_irp_open = date(2021,10,19)
            bank_irp_first = first_eligible_date(birth,bank_irp_open,False)
            bank_irp_lim,bank_irp_year = pension_limit(existing_bank_irp,bank_irp_first.year,int(compare_year),False)
            st.markdown(
                f'- **2009년 12월 연금저축 {_short_krw(existing_savings)}:** '
                f'{compare_year}년 계산상 {old_pension_count}년차, 별도 계좌의 단순 한도 {_short_krw(old_lim)}. '
                '세액공제 납입분·운용수익·과세제외 재원 원장을 확인하기 전에는 인출세액을 확정할 수 없습니다.\n'
                f'- **2021.10.19 H은행 기존 IRP {_short_krw(existing_bank_irp)}:** '
                f'개인 납입금만 있다는 가정에서 최초 가능일 {bank_irp_first:%Y.%m.%d}, '
                f'{compare_year}년 {bank_irp_year or "미산정"}년차, 별도 단순 한도 {_short_krw(bank_irp_lim)}. '
                '과거 퇴직금 입금·계좌 이전·기수령 이력이 있으면 연차·세율 재확인 필요.\n'
                '- **고객 유치 방향:** 세금은 은행 IRP와 하나증권 IRP에서 동일하므로, '
                '실제 선택 가능한 원리금보장 상품·ETF·채권·수수료·유동성·연금지급 서비스의 차이를 '
                '실제 제안서로 비교합니다. IRP 내부 원리금보장상품 편입과 IRP 밖 은행예금 가입은 과세시점이 다릅니다.'
            )
            st.info('**설명 멘트:** “퇴직금 전액을 일반예금으로 옮기기 전에 IRP로 세금을 이연한 뒤, '
                    '자녀 결혼자금만 인출하는 방식을 검토할 수 있습니다. 하나증권이 은행 IRP보다 세율이 낮은 것은 아닙니다. '
                    '동일한 절세 구조에서 원금보장 상품과 운용상품 선택, 비용과 사후 관리를 함께 비교해 드리겠습니다.”')
            # ===== ⑥ Sales recommendation with numeric, apples-to-apples tax results =====
            st.markdown('##### ⑥ 추천 인출 전략 · H은행 대비 하나증권 유치 결론')
            st.caption('서로 다른 경로의 세금 차이와 금융회사별 세금 차이를 구분해 자동으로 결론을 제시합니다.')
            aa,bb,cc=st.columns(3)
            with aa:
                old_partial_assumed=st.checkbox(
                    '2009년 연금저축 부분인출 가능 가정', value=True,
                    key='hv_strategy_old_partial',
                    help='약관 및 현재 연금개시 상태에 따라 부분인출이 불가능할 수 있습니다. '
                         '체크 시 조건부 시나리오로만 계산합니다.')
            with bb:
                old_tax_exempt=int(st.number_input(
                    '연금저축 세액공제 받지 않은 원금(원)',min_value=0,
                    max_value=int(existing_savings),value=0,step=1_000_000,
                    key='hv_strategy_old_exempt',
                    help='원장으로 확인한 금액만 넣습니다. 모르면 0원으로 두고 과세대상으로 보수적 가정합니다.'))
            with cc:
                old_taken_ytd=int(st.number_input(
                    '올해 연금저축 기존 인출액(원)',min_value=0,
                    value=0,step=1_000_000,key='hv_strategy_old_ytd',
                    help='이미 같은 해 연금으로 인출해 한도를 사용한 금액입니다. '
                         '과세제외금액 등의 한도불산입 인출은 금융기관 원장 기준으로 조정하세요.'))
            other_pension_annual=int(st.number_input(
                '올해 다른 사적연금 과세대상 수령액(원) · 퇴직소득 연금수령분 제외',
                min_value=0,value=0,step=1_000_000,key='hv_strategy_other_pension',
                help='연금저축/IRP의 세액공제 납입분과 운용수익 중 정상 연금수령한 과세재원. '
                     '이연퇴직소득을 연금으로 받는 금액은 1,500만원 기준에서 제외됩니다.'))
            old_draw_date=st.date_input(
                '결혼자금 인출예정일(연금저축 연령별 세율 확인용)',
                value=date(int(compare_year),10,30),min_value=date(2026,1,1),
                max_value=date(2050,12,31),key='hv_strategy_draw_date')
            pension_room=max(0,int(old_lim)-old_taken_ytd)
            if old_draw_date.year != int(compare_year):
                st.warning('인출예정일의 연도와 퇴직금 인출 예정 연도가 다릅니다. 같은 연도로 지정해야 조합 전략을 비교합니다.')
            else:
                old_age=age_on(birth,old_draw_date)
                old_funds= int(existing_savings) if old_partial_assumed else 0
                best_combo=_optimize_combined_funding(
                    cash_for_wedding,old_balance=old_funds,
                    old_excluded=old_tax_exempt if old_partial_assumed else 0,
                    old_room=pension_room,old_age=old_age,
                    new_retirement_balance=original_retirement,
                    retirement_national_tax=ret_tax.income_tax,
                    retirement_pension_limit=annual_limit,
                    calendar_year=int(compare_year),
                    other_pension_taxable_year=old_taken_ytd+other_pension_annual)
                if best_combo is None:
                    st.error('지정된 목표 현금액을 충족할 수 없습니다. 계좌별 잔액 및 세후 목표액을 조정하세요.')
                else:
                    old_draw=best_combo['old']
                    new_draw=best_combo['irp_draw']
                    blended_tax=best_combo['combined_tax']
                    blended_new_irp_left=original_retirement-best_combo['irp_gross']
                    blended_old_left=existing_savings-old_draw['gross']
                    ordinary_reduction=full_lump-blended_tax
                    vs_single_irp=draw.total_tax-blended_tax
                    # H은행이 똑같은 2계좌 전략을 실행하는 경우에는 세금차이가 없습니다.
                    st.markdown('**결론 A — 기존 계획이 “퇴직금 전액 현금화 → H은행 일반예금”이라면**')
                    _kpis([
                        _won_kpi('H은행 일반예금 · 퇴직소득세(전액 과세)',full_lump),
                        _won_kpi('하나증권 IRP 단독 · 해당 연도 총세금 추정',draw.total_tax),
                        _won_kpi('연금저축+하나증권 IRP 조합 · 해당 연도 총세금 추정',blended_tax),
                        _won_kpi('일시금 전액 과세 대비 해당 연도 총세금 추정 감소',ordinary_reduction),
                    ],green_last=True)
                    st.success(
                        f'**계산상 제안 경로:** 기존 연금저축 **{_short_krw(old_draw["gross"])}**에서 '
                        f'세후 **{_short_krw(old_draw["net"])}** 확보 + 하나증권 신규 IRP '
                        f'**{_short_krw(best_combo["irp_gross"])}** 인출(세후 '
                        f'**{_short_krw(new_draw.total_net)}**) → 결혼자금 '
                        f'**{_short_krw(best_combo["net"])}** 확보. '
                        '단, 연금저축 부분인출 가능·재원별 세금 가정이 충족될 때의 조건부 제안입니다.'
                    )
                    _kpis([
                        _won_kpi('신규 IRP에 남는 퇴직금 · 세전',blended_new_irp_left),
                        _won_kpi('기존 연금저축 잔액 · 세전',blended_old_left),
                        _won_kpi('기존 H은행 IRP 잔액 · 세전(미인출)',existing_bank_irp),
                        _won_kpi('IRP 단독 인출 대비 올해 총세금 추정 차이',vs_single_irp),
                    ])
                    st.markdown('**결론 B — H은행에서도 동일하게 IRP를 활용한다면**')
                    st.markdown(
                        '**H은행 IRP와 하나증권 IRP의 세법상 납부세금 차이: 0원.** '
                        f'동일한 연금저축+IRP 조합의 현재 납부세금은 양사 모두 '
                        f'**{blended_tax:,}원**으로 계산됩니다. '
                        '하나증권의 우위는 실제 약정금리, 수수료, 상품 선택과 서비스 비교로 입증해야 합니다.'
                    )
                    difference=hana_proj-bank_proj
                    if difference>0:
                        st.info(f'입력한 수익률·비용 가정대로라면 {two_years}년 후 '
                                f'하나증권 IRP 평가액이 H은행보다 **{difference:,}원** 높습니다. '
                                '이는 세금 차이가 아니라 운용 가정 차이이며 세전·미래 과세 미반영입니다.')
                    elif difference<0:
                        st.warning(f'현재 입력 가정에서는 {two_years}년 후 H은행 IRP가 '
                                   f'**{abs(difference):,}원** 유리합니다. '
                                   '하나증권 이전을 더 유리하다고 결론 낼 근거가 아직 없습니다.')
                    else:
                        st.info('현재 수익률과 수수료 가정으로는 하나증권 IRP와 H은행 IRP 사이의 '
                                '운용금액 차이가 0원입니다. 실제 상품 금리와 계약별 비용 입력 후 판단하세요.')
                    st.markdown('**고객 상담용 전략 비교표 — 결혼자금 세후 실수령액 동일**')
                    breakdown_rows=[
                        {'수령·운용 전략':'H은행 일반예금 · 전액 일시금',
                         '올해 총세금 추정(원)':full_lump,
                         '신규퇴직금 잔액(원)':bank_lump_bank_balance,
                         '기존 연금저축 잔액(원)':existing_savings,
                         '기존 H은행 IRP 잔액(원)':existing_bank_irp,
                         '세금 성격':'퇴직금 전액 과세 완료'},
                        {'수령·운용 전략':'H은행 IRP · 퇴직금만 부분인출',
                         '올해 총세금 추정(원)':draw.total_tax,
                         '신규퇴직금 잔액(원)':deferral_remaining_principal,
                         '기존 연금저축 잔액(원)':existing_savings,
                         '기존 H은행 IRP 잔액(원)':existing_bank_irp,
                         '세금 성격':'나머지 퇴직금 이연세금 잔존'},
                        {'수령·운용 전략':'하나증권 IRP · 퇴직금만 부분인출',
                         '올해 총세금 추정(원)':draw.total_tax,
                         '신규퇴직금 잔액(원)':deferral_remaining_principal,
                         '기존 연금저축 잔액(원)':existing_savings,
                         '기존 H은행 IRP 잔액(원)':existing_bank_irp,
                         '세금 성격':'나머지 퇴직금 이연세금 잔존'},
                        {'수령·운용 전략':'하나증권 IRP + 기존 연금저축 조합',
                         '올해 총세금 추정(원)':blended_tax,
                         '신규퇴직금 잔액(원)':blended_new_irp_left,
                         '기존 연금저축 잔액(원)':blended_old_left,
                         '기존 H은행 IRP 잔액(원)':existing_bank_irp,
                         '세금 성격':'두 연금계좌의 세금 + 향후 이연세금'},
                        {'수령·운용 전략':'H은행 IRP + 기존 연금저축 동일 조합',
                         '올해 총세금 추정(원)':blended_tax,
                         '신규퇴직금 잔액(원)':blended_new_irp_left,
                         '기존 연금저축 잔액(원)':blended_old_left,
                         '기존 H은행 IRP 잔액(원)':existing_bank_irp,
                         '세금 성격':'은행·증권사 IRP 세제 동일'},
                    ]
                    st.dataframe(pd.DataFrame(breakdown_rows),hide_index=True,use_container_width=True)
                    with st.expander('ⓘ 최적 조합의 인출·과세 계산식과 전제 확인'):
                        st.markdown('**기존 연금저축 한도 및 과세(2009년 가입)**')
                        st.markdown(f'올해 기존 연금저축 한도 **{old_lim:,}원** − 이미 인출한 연금한도 사용액 '
                                    f'**{old_taken_ytd:,}원** = **{pension_room:,}원** '
                                    f'(한도 외 과세제외 원금은 별도 분리).')
                        st.markdown(f'기존 연금저축 인출 **{old_draw["gross"]:,}원** = '
                                    f'과세제외 원금 **{old_draw["excluded"]:,}원** + '
                                    f'한도 내 과세대상 **{old_draw["pension_taxable"]:,}원** + '
                                    f'한도 초과 **{old_draw["nonpension_taxable"]:,}원**.')
                        if old_draw['pension_over_15m']:
                            st.warning('**연간 사적연금소득 1,500만원 초과:** 한도 내 연금저축 인출분의 '
                                       '원천징수는 연령별 세율이지만, 여기서는 종합과세 대신 '
                                       '16.5% 선택 분리과세를 가정해 연간 최종세액에 반영했습니다. '
                                       '다른 종합소득에 따라 종합과세가 유리할 수 있으므로 별도 검산이 필요합니다.')
                        st.markdown(f'{old_age}세 기준 한도 내 과세재원 원천징수세율 '

                                    f'**{float(age_pension_tax_rate(old_age))*110:.2f}% (지방세 포함 개산)** · '
                                    '한도 외 과세재원 16.5%(지방세 포함).')
                        st.markdown(f'연금저축 연금수령분 원천징수세액 '
                                    f'**{old_draw["withheld_pension_tax"]:,}원**, '
                                    f'1,500만원 초과에 따른 연말 과세액 증가분(16.5% 선택 시) '
                                    f'**{old_draw["final_tax_extra"]:,}원**.')
                        st.markdown(f'연금저축 세금 = 한도 내 **{old_draw["pension_tax"]:,}원** '
                                    f'+ 한도 초과 **{old_draw["nonpension_tax"]:,}원** '
                                    f'= **{old_draw["total_tax"]:,}원**. '
                                    f'실수령액 {old_draw["gross"]:,} − {old_draw["total_tax"]:,} '
                                    f'= **{old_draw["net"]:,}원**.')
                        st.markdown('**신규 퇴직소득 IRP 인출**')
                        st.markdown(f'필요 세후 결혼자금 **{cash_for_wedding:,}원** − '
                                    f'기존 연금저축 실수령액 **{old_draw["net"]:,}원** = '
                                    f'IRP에서 세후 **{new_draw.total_net:,}원** 필요.')
                        st.markdown(f'IRP 세전 **{best_combo["irp_gross"]:,}원** 인출 = '
                                    f'연금수령 인정액 **{new_draw.pension_amount:,}원** + '
                                    f'초과액 **{new_draw.nonpension_amount:,}원**.')
                        for taxrow in new_draw.rows:
                            st.markdown(f'{taxrow.treatment} {taxrow.gross:,}원 × '
                                        f'국세 유효세율 {taxrow.income_tax_rate_percent:.4f}% '
                                        f'→ 국세 {taxrow.income_tax:,}원 + 지방소득세 '
                                        f'{taxrow.local_income_tax:,}원 = **{taxrow.total_tax:,}원**')
                        st.markdown(f'IRP 인출세금 **{new_draw.total_tax:,}원** + '
                                    f'연금저축 인출세금 **{old_draw["total_tax"]:,}원** '
                                    f'= 이번 인출 합계세금 **{blended_tax:,}원**.')
                        st.markdown(f'일시금 전액 과세 **{full_lump:,}원** − 올해 총세금 추정 '
                                    f'**{blended_tax:,}원** = **{ordinary_reduction:,}원** '
                                    '(이연 세금이 포함된 **해당 연도 세금 부담액 차이**, 영구 절세액 아님).')
                        st.caption('최적화 기준은 “연금저축 한도 내 인출만 사용하면서 올해 총세금 추정 최소화”입니다. '
                                   '250,000원 간격으로 비교한 추정치이며 평생 누적 세금의 최소화는 아닙니다. '
                                   '노후 연금 고갈, 계좌별 유동성 제약, 기 수령·기납부세금 원장은 반영하지 않았습니다. ' 
                                   '다른 종합소득과 연금소득공제에 따른 실제 종합과세는 계산하지 않았습니다.')
                    st.warning('**계좌 이전 유의:** 2021년 가입 IRP를 2009년 가입 연금저축으로 '
                               '옮겨 2013년 이전 가입 특례를 적용하는 방식은 정상적인 비과세 계좌이체로 '
                               '가정하지 않습니다. 일반적으로 2013년 이후 가입 계좌 → 이전 가입 계좌로의 '
                               '이체는 과세 문제가 있어 별도 확인이 필요합니다. '
                               'H은행 IRP 4천만원은 재원(개인납입·이연퇴직소득) 확인 후 '
                               '동일 계좌유형의 금융회사 간 **전액 이전** 가능 여부와 승계정보를 확인하십시오.')
                    st.warning('**조건부 세액 주의:** 기존 연금저축 7천만원 중 세액공제 미신청 원금·'
                               '과세재원·연금개시 상태·부분수령 가능 여부를 알 수 없습니다. '
                               '여기서는 미확인 금액을 과세재원으로 계산하고 연간 1,500만원 초과 시 16.5% 선택 분리과세를 가정했습니다. '
                               '같은 절세 조합을 H은행에서도 실행할 수 있으므로 하나증권만의 독점 절세혜택이 아닙니다.')
                    st.download_button('추천 인출전략·양사비교표 CSV 다운로드',
                        pd.DataFrame(breakdown_rows).to_csv(index=False).encode('utf-8-sig'),
                        file_name=f'HanaV_추천전략_H은행대비_{compare_year}.csv',
                        mime='text/csv',key='hv_strategy_csv')

            st.download_button(
                '상담 시나리오 비교표 CSV 다운로드',
                display.to_csv(index=False).encode('utf-8-sig'),
                file_name=f'HanaV_연금유치상담_{compare_year}.csv',
                mime='text/csv', key='hv_advice_csv',
            )
            st.caption('⚠ **자료 확인 필요:** 원천징수영수증(근속기간·기납부세액), 17억원의 세법상 퇴직소득 여부, '
                       '신규 IRP 입금일 및 연금개시 가능일, 기존 IRP 4천만원의 재원·계좌 이전 여부, '
                       '2009년 연금저축 원장, 5억원의 세전/세후 의미, 비교상품 금리·수수료. '
                       '임원 퇴직소득 제한·이전 근속기간 정산·부분 인출 처리방식은 별도 확인하십시오. ')

st.divider()

st.subheader('① 퇴직소득세 — 2026년 기본 산식')
_kpis([
    ('세법상 근속연수', f'{years}년', f'입사 {entry:%Y.%m.%d} · 퇴직 {retirement_day:%Y.%m.%d}'),
    _won_kpi('퇴직소득세', ret_tax.income_tax),
    _won_kpi('지방소득세', ret_tax.local_income_tax),
    _won_kpi('일시금 수령 시 추정 합계세금', ret_tax.total_tax),
], green_last=True)
with st.expander('퇴직소득세 계산 경로 펼치기'):
    _render_retirement_tax_route(ret_tax, int(non_taxable), int(years))

st.subheader('② IRP 연금수령한도·연차 확인')
col_a,col_b,col_c = st.columns(3)
with col_a:
    year = st.number_input('분석 연도', min_value=2026, max_value=2050, value=2026, step=1, key='hv_analysis_year')
    planned_date = st.date_input('연금개시/수령예정일', value=date(2026,10,19),
                                 min_value=date(2026,1,1), max_value=date(2050,12,31), key='hv_planned_receipt_day')
with col_b:
    st.checkbox('퇴직급여와 잔액 자동 연동', key='hv_auto_def_balance',
                on_change=_sync_from_retirement_payment,
                help='기본적으로 퇴직급여 총액에서 비과세 퇴직소득을 제외한 금액이 자동 반영됩니다. '
                     '기인출·계좌이체 등으로 현재 잔액이 다르면 체크를 해제해 직접 입력하세요.')
    def_balance = st.number_input(
        '현재 이연퇴직소득 재원 잔액(원)', min_value=0, step=1_000_000,
        key='hv_def_balance', disabled=st.session_state['hv_auto_def_balance'],
        on_change=_sync_evaluated_from_balances,
        help='퇴직금 원금 중 아직 인출하지 않은 이연퇴직소득 잔액입니다. 자동 연동 해제 시 직접 조정할 수 있습니다.',
    )
    if st.session_state['hv_auto_def_balance']:
        st.markdown('<div class="hv-linked-hint">↳ 왼쪽 퇴직급여 입력과 연동 중</div>', unsafe_allow_html=True)
    excluded = st.number_input(
        '과세제외 재원 잔액(원)', min_value=0, step=1_000_000,
        key='hv_excluded_balance', on_change=_sync_evaluated_from_balances,
    )
    taxable = st.number_input(
        '세액공제 납입액·운용수익 잔액(원)', min_value=0, step=1_000_000,
        key='hv_taxable_balance', on_change=_sync_evaluated_from_balances,
    )
with col_c:
    st.checkbox('재원별 잔액과 평가액 자동 연동', key='hv_auto_evaluated_balance',
                on_change=_sync_evaluated_from_balances,
                help='기본적으로 이연퇴직소득·과세제외·세액공제 납입액/수익 잔액을 합산합니다. '
                     '연금수령한도 계산의 기준일 평가액이 현재 잔액과 다르면 체크를 해제해 정확한 평가액을 입력하세요.')
    evaluated = st.number_input(
        '해당 연도 한도산정용 평가액(원)', min_value=0, step=1_000_000,
        key='hv_evaluated_balance', disabled=st.session_state['hv_auto_evaluated_balance'],
        help='한도산정용 평가액은 현재 인출 전 잔액과 다를 수 있습니다. '
             '최초 수령일 및 이후 과세연도의 적용 기준일은 금융기관 자료로 확인하세요.',
    )
    if st.session_state['hv_auto_evaluated_balance']:
        st.markdown('<div class="hv-linked-hint">↳ 재원별 잔액 합계 자동 반영</div>', unsafe_allow_html=True)
    withdrawn_ytd = st.number_input('해당 연도 이미 수령한 금액(원)', min_value=0, value=0, step=1_000_000,
                                    help='본 프로토타입은 이전 수령분 모두 한도를 소진했다고 가정합니다.')
    with st.container(key='hv_withdrawal_highlight'):
        st.markdown('<div class="hv-customer-withdrawal-label">✦ 이번 수령신청금액(원)</div>',
                    unsafe_allow_html=True)
        new_withdrawal = st.number_input(
            '이번 수령신청금액(원)', min_value=0, value=50_000_000,
            step=1_000_000, label_visibility='collapsed', key='hv_new_withdrawal',
            help='이번에 새로 신청하는 금액입니다. 기존 수령분과 구분해 입력하세요.',
        )
        st.markdown('<div class="hv-customer-withdrawal-hint">수령신청액을 입력하면 아래에서 한도 내·초과 세액을 자동 계산합니다.</div>',
                    unsafe_allow_html=True)

# Current account type IRP can still carry qualifying *prior DB* history.
# retirement_core.legacy_eligible only understands a DB current-plan flag,
# so explicitly include the IRP receiving-account case here (app.py-only fix).
legacy = (legacy_eligible(account_open, plan_type, plan_joined, db_full)
          or (plan_type == 'IRP' and db_full and plan_joined < date(2013,3,1)))
qualifying = first_eligible_date(birth, account_open, deferred_retirement_funds=def_balance>0)
limit, count = pension_limit(evaluated, qualifying.year, int(year), legacy)
eligible_now = (year >= qualifying.year and planned_date >= qualifying)
if planned_date.year != year:
    st.warning('분석 연도와 수령예정일의 연도를 동일하게 설정해 주세요.')
    st.stop()
if not eligible_now:
    st.warning(f'일반적인 연금수령 요건을 아직 충족하지 않습니다. 최초 가능일: {qualifying.isoformat()} (특례 수령은 별도 검토)')

_kpis([
    ('수령예정일 만 나이', f'{age_on(birth,planned_date)}세', f'{planned_date:%Y.%m.%d} 기준'),
    ('한도 산정 기산연차', '6년차' if legacy else '1년차', '경과규정 적용' if legacy else '일반 산정'),
    ('금년도 한도 산정 연차', f'{count}년차' if count else '수령자격 전', f'{year}년 기준'),
    ('올해 연금수령한도', '한도 제한 없음' if count and count >= 11 else _short_krw(limit),
     '법정 한도 제한 없음' if count and count >= 11 else f'{limit:,}원'),
], green_last=True)
# A click (not a hover) opens the exact statutory calculation alongside
# the displayed limit. Match the data and year count used by pension_limit().
with st.popover('ⓘ 올해 연금수령한도 계산식 보기'):
    st.markdown('#### 연금수령한도 계산 과정')
    st.markdown(f'**최초 연금수령 요건 충족일:** {qualifying:%Y.%m.%d}')
    first_count = 6 if legacy else 1
    if count is not None:
        st.markdown(
            f'**수령연차 계산:** {qualifying.year}년을 {first_count}년차로 기산'
            f' → {year}년은 **{first_count} + ({year} − {qualifying.year})'
            f' = {count}년차**'
        )
    else:
        st.markdown('**수령연차:** 아직 최초 연금수령 요건 충족 전입니다.')
    st.markdown(f'**한도산정용 평가액:** {evaluated:,}원')
    if count is None:
        st.warning(f'{year}년은 최초 연금수령 가능연도({qualifying.year}년) 이전이므로 한도를 산출하지 않습니다.')
    elif count >= 11:
        st.success('**11년차 이상: 연금수령한도의 법정 제한 없음**')
        st.caption('단, 계좌의 실제 잔액을 초과하여 인출할 수는 없습니다.')
    else:
        st.markdown('**법정 계산식**')
        st.markdown('연금수령한도 = 한도산정용 평가액 ÷ (11 − 한도 산정 연차) × 120%')
        st.markdown(
            f'**숫자 대입:** {evaluated:,}원 ÷ (11 − {count}) × 1.2'
            f' = **{limit:,}원**'
        )
        st.caption('최종 금액은 원 단위로 표시하며, 계산 결과의 원 미만은 절사합니다.')
    st.caption('한도 계산용 연차는 이연퇴직소득세 감면에 쓰이는 실제 연금수령연차와 별개입니다.')
if legacy and plan_type in ('DB', 'IRP') and db_full and plan_joined < date(2013,3,1):
    st.info('2013.3.1 이전 DB 가입 및 퇴직소득 전액 신규 IRP 이체 확인에 따른 특례를 적용했습니다.')
elif legacy:
    st.info('2013.3.1 이전 연금계좌 가입 경과규정을 적용했습니다.')
else:
    st.info('일반 가입으로 1년차부터 적용했습니다. 단, 가입일만으로 기존 계좌 이전 등의 승계특례가 확정되는 것은 아닙니다.')

st.subheader('③ 실제 수령연차 — 한도 계산 연차와 별도')
history_method = st.radio('실제수령연차 산정', ['과거 수령연도 입력해 자동 계산', '금융기관 확인 연차 직접 입력'], horizontal=True)
if history_method.startswith('과거'):
    history_str = st.text_input('과거 실제 연금 수령 연도(쉼표 구분, 없으면 공란)', value='',
                                placeholder='예: 2022, 2023, 2025',
                                help='연금을 받지 않은 과세연도는 건너뛰고, 수령한 과세연도마다 1년씩 셉니다. 적격 계좌이체 연차 승계는 별도 확인 필요.')
    try:
        historical_years = [int(x.strip()) for x in history_str.split(',') if x.strip()]
        actual_year = actual_receipt_year_from_history(historical_years, int(year))
        st.caption(f'이연퇴직소득 감면용 실제수령연차: **{actual_year}년차** (과거 {len(set(historical_years))}개 수령연도 + 해당연도)')
    except ValueError as exc:
        st.error(f'연금수령연도 입력 형식을 확인해 주세요. {exc}')
        st.stop()
else:
    actual_year = st.number_input('금융기관 확인 연금 실제수령연차', min_value=1, max_value=60, value=1, step=1,
                                  help='위 연금수령한도 계산 연차를 그대로 입력하면 안 됩니다.')
mode = st.radio('이연퇴직소득세 원본', ['입력 퇴직금·근속연수로 추정', '원천징수영수증/금융기관 확인 세액 직접 입력'], horizontal=True)
if mode.startswith('원천징수'):
    deferred_tax = st.number_input('현재 잔여 이연퇴직소득세(국세, 원)', min_value=0, value=ret_tax.income_tax, step=10_000,
                                    help='연금외수령 시 국세 기준 잔여 이연퇴직소득세. 지방소득세를 합산하지 마세요.')
else:
    if def_balance != gross_retirement-non_taxable:
        st.warning('현재 퇴직금 재원 잔액과 입력 퇴직소득금액이 다릅니다. 신규·수익·기인출 등 이력에 따라 세율이 달라질 수 있으므로 실제 세액을 직접 입력하는 것이 안전합니다.')
    deferred_tax = ret_tax.income_tax

if new_withdrawal > excluded+def_balance+taxable:
    st.error('이번 수령신청금액이 현재 재원별 잔액 합계보다 큽니다.')
    st.stop()
if evaluated != excluded+def_balance+taxable:
    st.caption('한도 산정 평가액과 인출 직전 재원별 잔액은 기준일이 달라 서로 다를 수 있습니다. 확인 후 사용하세요.')
# 11년차 이후는 법정 연간한도 제한이 없으므로, 평가액이나 당해
# 기수령액 때문에 적격 연금 인출액이 연금외수령으로 오분류되지 않도록 합니다.
current_available = int(excluded + def_balance + taxable)
if eligible_now and count is not None and count >= 11:
    effective_limit = int(withdrawn_ytd) + current_available
    limit_remaining = current_available
else:
    effective_limit = int(limit)
    limit_remaining = max(0, effective_limit - int(withdrawn_ytd)) if eligible_now else 0

result = calculate_withdrawal(
    amount=int(new_withdrawal), prior_year_withdrawals=int(withdrawn_ytd), statutory_limit=effective_limit,
    excluded_balance=int(excluded), retirement_balance=int(def_balance), taxable_balance=int(taxable),
    remaining_deferred_income_tax=int(deferred_tax), actual_receipt_year=int(actual_year),
    age=age_on(birth, planned_date), calendar_year=int(year), qualifies=eligible_now)

st.subheader('④ 수령신청금액별 세금 계산 — 한도 내 vs 초과')
if count is not None and count >= 11 and eligible_now:
    how_limit = '연금수령연차 11년차 이상으로 법정 한도 제한 없음'
else:
    how_limit = (f'올해 연금수령한도 {limit:,}원 − 기수령액 {withdrawn_ytd:,}원'
                 f' = 남은 한도 {limit_remaining:,}원')
st.markdown(
    '<div class="hv-tax-summary">'
    f'<b>수령신청금액</b> {new_withdrawal:,}원 · '
    f'<b>한도 내 인정금액</b> {result.pension_amount:,}원 · '
    f'<b>한도 초과/연금외수령</b> {result.nonpension_amount:,}원<br>'
    f'{escape(how_limit)}'
    '</div>', unsafe_allow_html=True)
if eligible_now and count is not None and count >= 11:
    separation_formula = (f'**한도 내 인정액:** 법정 연간 한도 없음 → 신청액 {new_withdrawal:,}원 전액 연금수령 인정 가능'
                          f'\n\n**한도 초과액:** 0원')
elif eligible_now:
    separation_formula = (
        f'**한도 내 인정액:** MIN(이번 신청액, MAX(연간 한도 − 기수령액, 0))'
        f' = MIN({new_withdrawal:,}원, MAX({limit:,}원 − {withdrawn_ytd:,}원, 0))'
        f' = **{result.pension_amount:,}원**'
        f'\n\n**한도 초과액:** 신청액 − 한도 내 인정액'
        f' = {new_withdrawal:,}원 − {result.pension_amount:,}원'
        f' = **{result.nonpension_amount:,}원**'
    )
else:
    separation_formula = (
        '**연금수령 요건 미충족:** 이번 신청액은 연금외수령으로 분류합니다.'
        f'\n\n**한도 내 인정액:** 0원'
        f'\n\n**연금외수령액:** {new_withdrawal:,}원'
    )
with st.expander('ⓘ 한도 내·초과 금액 분리 계산식 보기'):
    st.markdown(separation_formula)
    st.caption('한도 계산은 수령 예정일의 연금수령 요건 충족 및 해당 연도 기수령액을 반영합니다.')

_kpis([
    _won_kpi('이번 수령신청금액', int(new_withdrawal)),
    _won_kpi('한도 내 연금수령 인정액', result.pension_amount),
    _won_kpi('한도 초과·연금외수령액', result.nonpension_amount),
    _won_kpi('세후 실수령액', result.total_net),
], green_last=True)

pension_rows = [r for r in result.rows if r.treatment == '연금수령']
nonpension_rows = [r for r in result.rows if r.treatment == '연금외수령']
pension_tax = sum(r.total_tax for r in pension_rows)
nonpension_tax = sum(r.total_tax for r in nonpension_rows)
pension_net = sum(r.net for r in pension_rows)
nonpension_net = sum(r.net for r in nonpension_rows)

st.markdown(
    '<div class="hv-tax-two-col">'
    '<div class="hv-tax-result">'
    '<div class="hv-tax-result-name">① 한도 내 · 연금수령 인정액</div>'
    f'<div class="hv-tax-result-value">{result.pension_amount:,}원</div>'
    f'<div class="hv-tax-result-detail">예상 세금 <strong>{pension_tax:,}원</strong><br>'
    f'세후 수령액 {pension_net:,}원</div></div>'
    '<div class="hv-tax-result hv-tax-result--excess">'
    '<div class="hv-tax-result-name">② 한도 초과 · 연금외수령액</div>'
    f'<div class="hv-tax-result-value">{result.nonpension_amount:,}원</div>'
    f'<div class="hv-tax-result-detail">예상 세금 <strong>{nonpension_tax:,}원</strong><br>'
    f'세후 수령액 {nonpension_net:,}원</div></div></div>',
    unsafe_allow_html=True,
)
st.markdown('**각 구분을 클릭하면 소득세·지방소득세의 계산식을 금액 대입과 함께 확인할 수 있습니다.**')
_render_withdrawal_route('① 한도 내 연금수령 계산식', '연금수령', result,
                         deferred_tax=int(deferred_tax), def_balance=int(def_balance),
                         age=age_on(birth, planned_date), receipt_year=int(actual_year),
                         calendar_year=int(year))
_render_withdrawal_route('② 한도 초과·연금외수령 계산식', '연금외수령', result,
                         deferred_tax=int(deferred_tax), def_balance=int(def_balance),
                         age=age_on(birth, planned_date), receipt_year=int(actual_year),
                         calendar_year=int(year))

st.markdown(
    '<div class="hv-tax-summary">'
    f'<b>이번 수령 총세금</b> = 한도 내 {pension_tax:,}원 + 초과분 {nonpension_tax:,}원'
    f' = <strong>{result.total_tax:,}원</strong><br>'
    f'<b>최종 실수령액</b> = 신청액 {new_withdrawal:,}원 − 총세금 {result.total_tax:,}원'
    f' = <strong>{result.total_net:,}원</strong>'
    '</div>', unsafe_allow_html=True)

st.caption('세율 판단 기준: 이연퇴직소득은 잔여 이연퇴직소득세/잔여 원금 × (연금수령 70·60·50% / 연금외수령 100%). '
           '세액공제 납입금·운용수익은 적격 연금수령 시 연령별 국세 3~5%, 연금외수령 시 국세 15%; '
           '지방소득세는 국세의 10%로 별도 계산합니다. 과세제외 재원은 비과세입니다.')
st.caption('※ 연금수령한도는 올해 남은 한도만 고려합니다. 연간 과거 수령액 입력은 기수령분이 모두 한도를 소진한 것으로 가정합니다. '
           '퇴직소득세 분모·분자는 해당 계좌의 원천징수 자료에 맞춰 확인해 주세요.')

output = pd.DataFrame([{
    '재원': r.resource, '인출 분류':r.treatment, '수령금액(원)':r.gross,
    '국세 적용세율(%)':r.income_tax_rate_percent,'소득세(원)':r.income_tax,
    '지방소득세(원)':r.local_income_tax,'합계세금(원)':r.total_tax, '실수령액(원)':r.net,
} for r in result.rows])
with st.expander('재원별 과세 명세표 펼치기'):
    if not output.empty:
        st.dataframe(output, use_container_width=True, hide_index=True)
    else:
        st.info('수령신청금액을 입력하면 재원별 과세 명세가 표시됩니다.')
if not output.empty:
    st.download_button('수령 세율별 결과 CSV 다운로드', output.to_csv(index=False).encode('utf-8-sig'),
                       file_name=f'연금세액비교_{year}.csv', mime='text/csv')
_kpis([_won_kpi('전액 연금외수령 가정 대비 추정 절세액', result.saving_vs_all_lump)], green_last=True)
st.caption(f'비교기준: 전액 연금외수령시 약 {result.hypothetical_all_lump_tax:,}원 vs 현재 계획 {result.total_tax:,}원. 자산운용수익·물가·세법변경 미반영.')

st.divider()
st.warning('주의: 본 앱은 2026년 세법으로 만든 상담용 시뮬레이터입니다. 임원 퇴직금 한도, 중간정산·세액정산·기납부세액, 다수 이연퇴직소득 입금분, 자산 수익률과 원본 분리, 복잡한 계좌 이전/상속, 의료비·부득이한 인출, 기존 연도별 한도 소진 등은 단순화했습니다. 실제 원천징수는 금융기관 원장·퇴직소득 원천징수영수증·홈택스 모의계산을 기준으로 검증해야 합니다.')
st.markdown('**공식 근거:** [소득세법 시행령 제40조의2·제40조의3](https://www.law.go.kr/lumLsLinkPop.do?chrClsCd=010202&lspttninfSeq=126416) · [국세청 퇴직소득세 계산방법](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7880&mi=6444) · [국세청 연금소득세 안내](https://webtv.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6452)')
