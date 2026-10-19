from datetime import date
from retirement_core import *


def test_nts_case():
    t=estimate_retirement_tax(100_000_000,20)
    assert t.service_deduction == 40_000_000
    assert t.converted_pay == 36_000_000
    assert t.converted_pay_deduction == 24_800_000
    assert t.converted_tax_base == 11_200_000
    assert t.income_tax == 1_120_000
    assert t.local_income_tax == 112_000


def test_legacy_date_boundary():
    assert legacy_eligible(date(2013,2,28),'IRP',date(2013,2,28))
    assert not legacy_eligible(date(2013,3,1),'IRP',date(2013,3,1))
    assert legacy_eligible(date(2026,1,1),'DB',date(2010,1,1),True)
    assert not legacy_eligible(date(2026,1,1),'DC',date(2010,1,1),True)
    assert not legacy_eligible(date(2026,1,1),'DB',date(2010,1,1),False)


def test_pension_ceiling():
    old,old_yr = pension_limit(500_000_000, 2026, 2026, True)
    new,new_yr = pension_limit(500_000_000, 2026, 2026, False)
    assert (old,old_yr)==(120_000_000,6)
    assert (new,new_yr)==(60_000_000,1)
    assert pension_limit(500_000_000,2026,2031,True)[0]==500_000_000
    assert pension_limit(500_000_000,2026,2036,False)[0]==500_000_000


def test_split_and_discounts():
    old = calculate_withdrawal(amount=100_000_000,prior_year_withdrawals=0,statutory_limit=120_000_000,
        excluded_balance=0,retirement_balance=500_000_000,taxable_balance=0,
        remaining_deferred_income_tax=5_600_000,actual_receipt_year=1,age=60,calendar_year=2026)
    new = calculate_withdrawal(amount=100_000_000,prior_year_withdrawals=0,statutory_limit=60_000_000,
        excluded_balance=0,retirement_balance=500_000_000,taxable_balance=0,
        remaining_deferred_income_tax=5_600_000,actual_receipt_year=1,age=60,calendar_year=2026)
    assert old.pension_amount == 100_000_000 and old.nonpension_amount == 0
    assert new.pension_amount == 60_000_000 and new.nonpension_amount == 40_000_000
    assert old.total_tax == 862_400
    assert new.total_tax == 1_010_240
    assert new.saving_vs_all_lump == 221_760


def test_actual_receipt_history_gaps():
    assert actual_receipt_year_from_history([2022, 2024, 2024], 2026)==3
    assert actual_receipt_year_from_history([2022, 2024, 2026], 2026)==3
    assert actual_receipt_year_from_history([], 2026)==1


def test_actual_year_rates():
    assert retirement_tax_multiplier(10,2026) == D('.70')
    assert retirement_tax_multiplier(11,2026) == D('.60')
    assert retirement_tax_multiplier(20,2026) == D('.60')
    assert retirement_tax_multiplier(21,2026) == D('.50')


def test_order_and_tax():
    t=calculate_withdrawal(amount=30_000_000,prior_year_withdrawals=0,statutory_limit=20_000_000,
        excluded_balance=5_000_000, retirement_balance=15_000_000, taxable_balance=30_000_000,
        remaining_deferred_income_tax=1_500_000,actual_receipt_year=11,age=75,calendar_year=2026)
    assert sum(row.gross for row in t.rows)==30_000_000
    assert t.pension_amount == 20_000_000
    assert [row.resource for row in t.rows]==['과세제외금액','이연퇴직소득','세액공제분·운용수익']
    assert [row.total_tax for row in t.rows]==[0,990_000,1_650_000]


def test_service_year():
    assert service_years(date(2004,1,1),date(2023,12,31))==20
    assert service_years(date(2025,1,1),date(2025,12,31))==1
    assert service_years(date(2025,1,1),date(2026,1,1))==2


if __name__=='__main__':
    for n,x in list(globals().items()):
        if n.startswith('test_') and callable(x):
            x()
            print('PASS', n)
