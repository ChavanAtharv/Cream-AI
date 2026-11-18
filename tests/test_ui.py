"""Tests for SchemeSaathi Streamlit UI components and profile matching."""

from ui.app import evaluate_match


def test_evaluate_match_farmer_profile():
    pm_kisan_record = {
        "id": "PM_KISAN",
        "scheme_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "category": "Agriculture, Rural & Environment",
        "eligibility": "Eligible landholding farmer families; income-tax payers are excluded.",
    }

    # Match farmer
    is_match, why = evaluate_match(
        pm_kisan_record,
        age_band="All Ages",
        gender="All Genders",
        occupation="Farmer",
        income_band="All Incomes",
        category="All Categories",
        area="All Areas",
    )
    assert is_match is True
    assert "farmer" in why.lower()

    # Mismatch vendor
    is_match, why = evaluate_match(
        pm_kisan_record,
        age_band="All Ages",
        gender="All Genders",
        occupation="Street Vendor",
        income_band="All Incomes",
        category="All Categories",
        area="All Areas",
    )
    assert is_match is False


def test_evaluate_match_age_exclusion():
    apy_record = {
        "id": "APY",
        "scheme_name": "Atal Pension Yojana (APY)",
        "category": "Banking, Financial Services and Insurance",
        "eligibility": "Indian citizens aged 18–40 with a savings bank account.",
    }

    # 18-40 should match
    is_match, _ = evaluate_match(
        apy_record,
        age_band="18-40 (Youth/Working)",
        gender="All Genders",
        occupation="All Occupations",
        income_band="All Incomes",
        category="All Categories",
        area="All Areas",
    )
    assert is_match is True

    # 60+ should not match
    is_match, _ = evaluate_match(
        apy_record,
        age_band="60+ (Senior)",
        gender="All Genders",
        occupation="All Occupations",
        income_band="All Incomes",
        category="All Categories",
        area="All Areas",
    )
    assert is_match is False
