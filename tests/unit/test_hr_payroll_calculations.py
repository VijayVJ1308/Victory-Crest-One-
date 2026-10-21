"""Victory Crest One - Unit Tests for HR & Payroll Calculations
Statutory salary breakdown (Basic, HRA, PF, PT, TDS), unpaid leave deductions,
overtime pay, batch payroll run totals, and attendance percentages.
"""

from decimal import Decimal
from shared.calculations import (
    calculate_salary_breakdown,
    calculate_leave_deduction,
    calculate_overtime_pay,
    calculate_payroll_run_totals,
    calculate_attendance_rate
)


def test_calculate_salary_breakdown_standard():
    # Monthly gross = ₹50,000.00
    res = calculate_salary_breakdown(monthly_gross=Decimal("50000.00"))

    assert res["gross_salary"] == Decimal("50000.00")
    # Basic = 50% = 25,000.00
    assert res["basic"] == Decimal("25000.00")
    # HRA = 20% = 10,000.00
    assert res["hra"] == Decimal("10000.00")
    # Conveyance = 1,600.00
    assert res["conveyance"] == Decimal("1600.00")
    # Special Allowance = 50,000 - 36,600 = 13,400.00
    assert res["special_allowance"] == Decimal("13400.00")

    # Deductions:
    # PF = 12% of Basic = 12% of 25,000 = 3,000.00
    assert res["pf_deduction"] == Decimal("3000.00")
    # PT = 200.00
    assert res["professional_tax"] == Decimal("200.00")
    # TDS = 5% of Gross = 2,500.00
    assert res["tds_deduction"] == Decimal("2500.00")

    # Total Deductions = 3000 + 200 + 2500 = 5700.00
    assert res["total_deductions"] == Decimal("5700.00")
    # Net Salary = 50,000 - 5700 = 44,300.00
    assert res["net_salary"] == Decimal("44300.00")


def test_calculate_leave_deduction():
    # Gross = ₹60,000.00, 30 working days, 2 days unpaid leave (LWP)
    # Daily rate = 2,000.00, Deduction = 4,000.00, Adjusted Gross = 56,000.00
    res = calculate_leave_deduction(
        monthly_gross=Decimal("60000.00"),
        working_days=30,
        unpaid_leave_days=2
    )
    assert res["daily_rate"] == Decimal("2000.00")
    assert res["deduction_amount"] == Decimal("4000.00")
    assert res["adjusted_gross"] == Decimal("56000.00")

    # Zero unpaid leaves
    res_zero = calculate_leave_deduction(monthly_gross=Decimal("60000.00"), unpaid_leave_days=0)
    assert res_zero["deduction_amount"] == Decimal("0.00")
    assert res_zero["adjusted_gross"] == Decimal("60000.00")


def test_calculate_overtime_pay():
    # Monthly gross = 48,000.00, 240 standard hours/month => hourly rate = 200.00
    # Overtime hours = 10, multiplier = 1.5 => 200 * 10 * 1.5 = 3,000.00
    ot = calculate_overtime_pay(
        monthly_gross=Decimal("48000.00"),
        standard_monthly_hours=240,
        overtime_hours=10,
        ot_multiplier=Decimal("1.50")
    )
    assert ot == Decimal("3000.00")

    # Zero overtime hours
    assert calculate_overtime_pay(monthly_gross=Decimal("48000.00"), overtime_hours=0) == Decimal("0.00")


def test_calculate_payroll_run_totals():
    payslips = [
        {
            "gross_salary": Decimal("50000.00"),
            "pf_deduction": Decimal("3000.00"),
            "tds_deduction": Decimal("2500.00"),
            "professional_tax": Decimal("200.00"),
            "total_deductions": Decimal("5700.00"),
            "net_salary": Decimal("44300.00")
        },
        {
            "gross_salary": Decimal("80000.00"),
            "pf_deduction": Decimal("4800.00"),
            "tds_deduction": Decimal("4000.00"),
            "professional_tax": Decimal("200.00"),
            "total_deductions": Decimal("9000.00"),
            "net_salary": Decimal("71000.00")
        }
    ]
    totals = calculate_payroll_run_totals(payslips)

    assert totals["total_employees"] == 2
    assert totals["total_gross_earnings"] == Decimal("130000.00")
    assert totals["total_pf_liability"] == Decimal("7800.00")
    assert totals["total_tds_liability"] == Decimal("6500.00")
    assert totals["total_pt_liability"] == Decimal("400.00")
    assert totals["total_statutory_deductions"] == Decimal("14700.00")
    assert totals["total_net_disbursement"] == Decimal("115300.00")


def test_calculate_attendance_rate():
    # 20 rostered, 18 present = 90.00%
    rate = calculate_attendance_rate(total_rostered_shifts=20, present_shifts=18)
    assert rate == Decimal("90.00")

    # 0 rostered (empty day/safe division)
    zero_rate = calculate_attendance_rate(total_rostered_shifts=0, present_shifts=0)
    assert zero_rate == Decimal("100.00")
