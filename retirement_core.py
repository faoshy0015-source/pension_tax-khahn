"""2026 retirement/pension tax CONSULTATION ESTIMATES (not withholding engine).

Law references (accessed 2026-10-19):
- Income Tax Act Enforcement Decree articles 40-2, 40-3, 187-3
- Korean NTS retirement-income and private-pension income guidance

Explicit exclusions: retirement tax reconciliation, executive income limits,
mid-service severance settlements, tax exemption portions, multiple deferred-tax
lots, complex prior withdrawals, exceptional withdrawals, original-basis vs
investment-return allocation, pension-account transfers and succession.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN
from typing import Optional

ZERO = Decimal(0)
ONE = Decimal(1)
D = lambda x: Decimal(str(x))
LEGACY_CUTOFF = date(2013, 3, 1)


def floor_krw(v) -> int:
    return int(D(v).quantize(ONE, rounding=ROUND_DOWN))


def add_years(d: date, n: int) -> date:
    try:
        return d.replace(year=d.year+n)
    except ValueError:
        return d.replace(year=d.year+n, day=28)


def age_on(born: date, target: date) -> int:
    return target.year - born.year - ((target.month, target.day) < (born.month, born.day))


def service_years(entry: date, last_working_day: date) -> int:
    """Approximate whole-tax-years (fractional year counts as full year).

    For employee records with excluded periods, intermediate settlements etc.,
    use the service-years override from official withholding statement.
    """
    if last_working_day < entry:
        raise ValueError('퇴직일은 입사일 이후여야 합니다.')
    exclusive = last_working_day + timedelta(days=1)
    years = exclusive.year - entry.year
    if add_years(entry, years) > exclusive:
        years -= 1
    if add_years(entry, years) < exclusive:
        years += 1
    return max(1, years)


def service_deduction(years: int) -> Decimal:
    y = D(years)
    if years <= 5: return y * 1_000_000
    if years <= 10: return D(5_000_000) + (y-5)*2_000_000
    if years <= 20: return D(15_000_000) + (y-10)*2_500_000
    return D(40_000_000) + (y-20)*3_000_000


def converted_pay_deduction(pay: Decimal) -> Decimal:
    if pay <= 8_000_000: return pay
    if pay <= 70_000_000: return D(8_000_000) + (pay-8_000_000)*D('.60')
    if pay <= 100_000_000: return D(45_200_000) + (pay-70_000_000)*D('.55')
    if pay <= 300_000_000: return D(61_700_000) + (pay-100_000_000)*D('.45')
    return D(151_700_000) + (pay-300_000_000)*D('.35')


def income_tax_on_base(base: Decimal) -> Decimal:
    # Threshold, marginal rate, cumulative deduction (all official 2026 NTS).
    stages = [
        (14_000_000, '.06', 0),
        (50_000_000, '.15', 1_260_000),
        (88_000_000, '.24', 5_760_000),
        (150_000_000, '.35', 15_440_000),
        (300_000_000, '.38', 19_940_000),
        (500_000_000, '.40', 25_940_000),
        (1_000_000_000, '.42', 35_940_000),
        (float('inf'), '.45', 65_940_000),
    ]
    for ceiling, rate, credit in stages:
        if base <= ceiling:
            return max(ZERO, base*D(rate)-D(credit))
    raise AssertionError('Unreachable')


@dataclass(frozen=True)
class RetirementTax:
    gross: int
    tax_service_years: int
    service_deduction: int
    converted_pay: int
    converted_pay_deduction: int
    converted_tax_base: int
    income_tax: int
    local_income_tax: int
    total_tax: int


def estimate_retirement_tax(gross: int, years: int, non_taxable: int=0) -> RetirementTax:
    if gross < 0 or non_taxable < 0 or non_taxable > gross or years < 1:
        raise ValueError('퇴직금액·비과세액·근속연수를 확인해 주세요.')
    taxable = D(gross-non_taxable)
    deduction = service_deduction(years)
    pay = max(ZERO, taxable-deduction)*12/D(years)
    p_ded = converted_pay_deduction(pay)
    base = max(ZERO, pay-p_ded)
    income_tax = floor_krw(income_tax_on_base(base)*D(years)/12)
    local_tax = floor_krw(D(income_tax)*D('.10'))
    return RetirementTax(gross, years, floor_krw(deduction), floor_krw(pay),
                         floor_krw(p_ded), floor_krw(base), income_tax, local_tax, income_tax+local_tax)


def legacy_eligible(account_open: date, plan_type: str, plan_joined: date,
                    db_full_transfer: bool=False) -> bool:
    """Do not confer DB-transfer transitional treatment to DC transfers."""
    return (account_open < LEGACY_CUTOFF or
            (plan_type == 'DB' and db_full_transfer and plan_joined < LEGACY_CUTOFF))


def first_eligible_date(birth: date, account_open: date, deferred_retirement_funds: bool) -> date:
    # Personal-contribution-only accounts require >=5-year account history.
    qualifying = account_open if deferred_retirement_funds else add_years(account_open, 5)
    return max(add_years(birth, 55), qualifying)


def pension_limit(balance_at_period_open: int, qualifying_year: int,
                  calendar_year: int, legacy: bool) -> tuple[int, Optional[int]]:
    if balance_at_period_open < 0:
        raise ValueError('연금계좌 평가액은 음수일 수 없습니다.')
    if calendar_year < qualifying_year:
        return 0, None
    count = (6 if legacy else 1) + calendar_year-qualifying_year
    if count >= 11:
        return balance_at_period_open, count  # Full balance (no statutory cap).
    return floor_krw(D(balance_at_period_open)/D(11-count)*D('1.2')), count


def actual_receipt_year_from_history(received_calendar_years: list[int], calendar_year: int) -> int:
    """Distinct actual receipt tax years; gap years don't count (decree 187-3).

    User supplies previous paid years including any YTD payments. Current
    intended withdrawal is assumed to be a qualifying pension receipt.
    Account transfer historical combination must be entered as verified year
    history; this helper does not independently validate that transfer.
    """
    if any(y > calendar_year or y < 1980 for y in received_calendar_years):
        raise ValueError('실제 연금수령 연도에는 분석연도 이후의 연도를 넣을 수 없습니다.')
    return len(set(received_calendar_years) | {calendar_year})


def retirement_tax_multiplier(actual_receipt_year: int, calendar_year: int) -> Decimal:
    if actual_receipt_year < 1:
        raise ValueError('연금 실제수령연차는 1년 이상이어야 합니다.')
    if calendar_year < 2026:
        return D('.70') if actual_receipt_year <= 10 else D('.60')
    if actual_receipt_year <= 10: return D('.70')
    if actual_receipt_year <= 20: return D('.60')
    return D('.50')


def age_pension_tax_rate(age: int) -> Decimal:
    if age < 70: return D('.05')
    if age < 80: return D('.04')
    return D('.03')


@dataclass(frozen=True)
class WithdrawalRow:
    resource: str
    treatment: str
    gross: int
    income_tax_rate_percent: float
    income_tax: int
    local_income_tax: int
    total_tax: int
    net: int


@dataclass(frozen=True)
class WithdrawalResult:
    rows: list[WithdrawalRow]
    amount: int
    pension_amount: int
    nonpension_amount: int
    total_tax: int
    total_net: int
    hypothetical_all_lump_tax: int
    saving_vs_all_lump: int


def calculate_withdrawal(
        *, amount: int, prior_year_withdrawals: int, statutory_limit: int,
        excluded_balance: int, retirement_balance: int, taxable_balance: int,
        remaining_deferred_income_tax: int, actual_receipt_year: int,
        age: int, calendar_year: int, qualifies: bool=True) -> WithdrawalResult:
    """Allocation order: non-taxable basis -> deferred retirement -> taxable other.

    Assumes a single homogeneous deferred-retirement-income tax lot.
    `statutory_limit` is already determined from start-of-period balance.
    `prior_year_withdrawals` assumes all prior withdrawals consumed pension limit.
    """
    if min(amount, prior_year_withdrawals, statutory_limit, excluded_balance,
           retirement_balance, taxable_balance, remaining_deferred_income_tax) < 0:
        raise ValueError('금액은 음수일 수 없습니다.')
    if amount > excluded_balance+retirement_balance+taxable_balance:
        raise ValueError('신규 출금액이 현재 재원별 잔액 합계를 초과합니다.')
    pension_left = max(0, statutory_limit-prior_year_withdrawals) if qualifies else 0
    retirement_rate = (D(remaining_deferred_income_tax)/D(retirement_balance)) if retirement_balance else ZERO
    multiplier = retirement_tax_multiplier(actual_receipt_year, calendar_year)
    personal_rate = age_pension_tax_rate(age)
    left = amount
    rows = []
    all_lump_tax = 0
    pension_total = 0
    for source, balance in [('과세제외금액', excluded_balance),
                            ('이연퇴직소득', retirement_balance),
                            ('세액공제분·운용수익', taxable_balance)]:
        drawn = min(left, balance)
        left -= drawn
        pension_part = min(drawn, pension_left)
        nonpension_part = drawn - pension_part
        pension_left -= pension_part
        pension_total += pension_part
        for p_amount, is_pension in [(pension_part, True), (nonpension_part, False)]:
            if not p_amount: continue
            if source == '과세제외금액': rate = ZERO
            elif source == '이연퇴직소득': rate = retirement_rate*(multiplier if is_pension else ONE)
            else: rate = personal_rate if is_pension else D('.15')
            itax = floor_krw(D(p_amount)*rate)
            ltax = floor_krw(D(itax)*D('.1'))
            lump_rate = ZERO if source == '과세제외금액' else (retirement_rate if source == '이연퇴직소득' else D('.15'))
            lump_itax = floor_krw(D(p_amount)*lump_rate)
            all_lump_tax += lump_itax + floor_krw(D(lump_itax)*D('.1'))
            rows.append(WithdrawalRow(source, '연금수령' if is_pension else '연금외수령', p_amount,
                                      round(float(rate*100), 4), itax, ltax, itax+ltax,
                                      p_amount-itax-ltax))
    total_tax = sum(r.total_tax for r in rows)
    return WithdrawalResult(rows, amount, pension_total, amount-pension_total,
                            total_tax, amount-total_tax, all_lump_tax,
                            all_lump_tax-total_tax)
