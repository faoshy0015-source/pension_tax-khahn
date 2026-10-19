"""HanaV Pension Tax Lab - Streamlit consultation prototype, Oct 2026."""
from datetime import date
from decimal import Decimal
from html import escape
import hashlib
import hmac
import pandas as pd
import streamlit as st
from retirement_core import (
    age_on, actual_receipt_year_from_history, calculate_withdrawal, estimate_retirement_tax, first_eligible_date,
    legacy_eligible, pension_limit, service_years, floor_krw,
    converted_pay_deduction, income_tax_on_base,
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
    st.subheader('고객·퇴직연금 정보')
    birth = st.date_input('생년월일', value=date(1966, 6, 1), min_value=date(1920,1,1), max_value=date(2010,12,31))
    plan_type = st.selectbox('퇴직연금 종류', ['DB', 'DC', 'IRP'])
    plan_joined = st.date_input('기존 퇴직연금제도 가입일', value=date(2010,1,1), min_value=date(1970,1,1), max_value=date(2026,12,31),
                                help='현재 수령계좌가 IRP라도 최초 DB형 퇴직연금 가입일을 입력합니다. 가입이력을 확인한 날짜를 사용하세요.')
    account_open = st.date_input('연금계좌 가입일/IRP 개설일', value=date(2026,1,1), min_value=date(1970,1,1), max_value=date(2026,12,31))
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
    entry = st.date_input('입사일', value=date(2007,1,1), min_value=date(1950,1,1), max_value=date(2026,12,31))
    retirement_day = st.date_input('퇴직일(마지막 근무일)', value=date(2026,12,31), min_value=date(2000,1,1), max_value=date(2035,12,31))
    manual_years = st.checkbox('공식 원천징수영수증의 근속연수 직접 입력', value=False)
    try: computed_years = service_years(entry, retirement_day)
    except ValueError: computed_years = None
    years = int(st.number_input('세법상 근속연수(년)', min_value=1, max_value=80, value=computed_years or 20,
                                disabled=not manual_years)) if manual_years else computed_years
    gross_retirement = st.number_input('퇴직급여 총액(원)', min_value=0, value=100_000_000, step=1_000_000, format='%d')
    non_taxable = st.number_input('비과세 퇴직소득(원)', min_value=0, value=0, step=100_000)
    st.caption(f'입력 퇴직급여: {gross_retirement:,}원 · 비과세: {non_taxable:,}원')

if years is None:
    st.error('입사일과 퇴직일의 순서를 확인해 주세요.')
    st.stop()
if non_taxable > gross_retirement:
    st.error('비과세금액은 퇴직급여 총액을 초과할 수 없습니다.')
    st.stop()

ret_tax = estimate_retirement_tax(int(gross_retirement), int(years), int(non_taxable))

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
    year = st.number_input('분석 연도', min_value=2026, max_value=2050, value=2026, step=1)
    planned_date = st.date_input('연금개시/수령예정일', value=date(2026,10,19),
                                 min_value=date(2026,1,1), max_value=date(2050,12,31))
with col_b:
    def_balance = st.number_input('현재 이연퇴직소득 재원 잔액(원)', min_value=0, value=100_000_000, step=1_000_000)
    excluded = st.number_input('과세제외 재원 잔액(원)', min_value=0, value=0, step=1_000_000)
    taxable = st.number_input('세액공제 납입액·운용수익 잔액(원)', min_value=0, value=0, step=1_000_000)
with col_c:
    evaluated = st.number_input('해당 연도 한도산정용 평가액(원)', min_value=0, value=100_000_000, step=1_000_000,
                                help='연금개시 신청연도는 신청시점 평가액, 그 이후는 1월 1일 기준. 현재 잔액과 다를 수 있음.')
    withdrawn_ytd = st.number_input('해당 연도 이미 수령한 금액(원)', min_value=0, value=0, step=1_000_000,
                                    help='본 프로토타입은 이전 수령분 모두 한도를 소진했다고 가정합니다.')
    new_withdrawal = st.number_input('이번/남은 연도 수령 계획액(원)', min_value=0, value=50_000_000, step=1_000_000)

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
    st.error('이번 수령 계획액이 현재 재원별 잔액 합계보다 큽니다.')
    st.stop()
if evaluated != excluded+def_balance+taxable:
    st.caption('한도 산정 평가액과 인출 직전 재원별 잔액은 기준일이 달라 서로 다를 수 있습니다. 확인 후 사용하세요.')
result = calculate_withdrawal(
    amount=int(new_withdrawal), prior_year_withdrawals=int(withdrawn_ytd), statutory_limit=int(limit),
    excluded_balance=int(excluded), retirement_balance=int(def_balance), taxable_balance=int(taxable),
    remaining_deferred_income_tax=int(deferred_tax), actual_receipt_year=int(actual_year),
    age=age_on(birth, planned_date), calendar_year=int(year), qualifies=eligible_now)

st.subheader('④ 수령금액별 과세 결과')
_kpis([
    _won_kpi('연금수령 인정금액', result.pension_amount),
    _won_kpi('연금외수령 금액', result.nonpension_amount),
    _won_kpi('이번 수령 예상 세금(지방세 포함)', result.total_tax),
    _won_kpi('이번 수령 세후 실수령액', result.total_net),
], green_last=True)

output = pd.DataFrame([{
    '재원': r.resource, '인출 분류':r.treatment, '수령금액(원)':r.gross,
    '국세 적용세율(%)':r.income_tax_rate_percent,'소득세(원)':r.income_tax,
    '지방소득세(원)':r.local_income_tax,'합계세금(원)':r.total_tax, '실수령액(원)':r.net,
} for r in result.rows])
if not output.empty:
    st.dataframe(output, use_container_width=True, hide_index=True)
    st.download_button('수령 세율별 결과 CSV 다운로드', output.to_csv(index=False).encode('utf-8-sig'),
                       file_name=f'연금세액비교_{year}.csv', mime='text/csv')
_kpis([_won_kpi('동일 금액 전액 연금외수령 가정 대비 추정 절세액', result.saving_vs_all_lump)], green_last=True)
st.caption(f'비교기준: 전액 연금외수령시 약 {result.hypothetical_all_lump_tax:,}원 vs 현재 계획 {result.total_tax:,}원. 자산운용수익·물가·세법변경 미반영.')

st.divider()
st.warning('주의: 본 앱은 2026년 세법으로 만든 상담용 시뮬레이터입니다. 임원 퇴직금 한도, 중간정산·세액정산·기납부세액, 다수 이연퇴직소득 입금분, 자산 수익률과 원본 분리, 복잡한 계좌 이전/상속, 의료비·부득이한 인출, 기존 연도별 한도 소진 등은 단순화했습니다. 실제 원천징수는 금융기관 원장·퇴직소득 원천징수영수증·홈택스 모의계산을 기준으로 검증해야 합니다.')
st.markdown('**공식 근거:** [소득세법 시행령 제40조의2·제40조의3](https://www.law.go.kr/lumLsLinkPop.do?chrClsCd=010202&lspttninfSeq=126416) · [국세청 퇴직소득세 계산방법](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7880&mi=6444) · [국세청 연금소득세 안내](https://webtv.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6452)')
