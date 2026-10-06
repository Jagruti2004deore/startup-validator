from app.agents.critic import (
    numbers_missing, names_missing, quote_in_source, compute_gaps,
)

SOURCE = (
    "Premia raised approximately $1.0M in a first round on August 18, 2026. "
    "The India edtech market grew from USD 3.63 Billion in 2025 to USD 4.60 Billion "
    "in 2026, a CAGR of 27.94%. The app has 1 million members. Quizlet charges $10 a month."
)


def test_correct_numbers_pass():
    assert numbers_missing("Premia raised $1.0M on August 18, 2026", SOURCE) == []


def test_glued_date_still_matches():
    assert numbers_missing("Premia raised money on August 18,2026", SOURCE) == []


def test_decimals_and_percentages():
    claim = "The market grew to USD 4.60 Billion at a CAGR of 27.94%"
    assert numbers_missing(claim, SOURCE) == []


def test_invented_number_is_caught():
    assert numbers_missing("Quizlet charges $49 a month", SOURCE) == ["49"]


def test_invented_one_digit_amount_is_caught():
    assert numbers_missing("The market is worth $5 billion", SOURCE) == ["5"]


def test_one_digit_with_unit_present_passes():
    assert numbers_missing("The app has 1 million members", SOURCE) == []


def test_wrong_company_is_caught():
    assert names_missing("Duolingo charges $10 a month", SOURCE) == ["Duolingo"]


def test_right_company_passes():
    assert names_missing("Quizlet charges $10 a month", SOURCE) == []


def test_quote_must_be_real():
    assert quote_in_source("Quizlet charges $10 a month", SOURCE)
    assert not quote_in_source("Quizlet charges $20 a month for premium", SOURCE)
    assert not quote_in_source("too short", SOURCE)


def test_gaps_are_listed():
    verified = (
        [{"category": "competitor"}] * 3
        + [{"category": "pricing"}] * 2
        + [{"category": "market_size"}, {"category": "demand_signal"}]
    )
    assert compute_gaps(verified) == ["recent_activity", "failure_or_risk"]
    assert "competitor" in compute_gaps([{"category": "competitor"}])



def test_names_ignore_spacing_and_punctuation():
    assert names_missing("MoocLab lists Middle-High groups", "Mooclab: Middle/High school groups") == []


def test_quote_ignores_spacing_noise():
    assert quote_in_source(
        "India edtech market size increased to USD 4.60 Billion in 2026",
        "The India edtech market size increased to USD 4.60Billion in2026",
    )