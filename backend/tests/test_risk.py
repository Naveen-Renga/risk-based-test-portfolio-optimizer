"""
test_risk.py — Risk Score Formula Validation Tests

Tests verify:
  - Risk score is always in [0.0, 10.0]
  - Weighted formula produces deterministic output
  - Priority categories are correctly assigned
  - Efficiency score is risk_score / execution_time
  - Maximum input values produce score ≤ 10.0
  - Minimum input values produce score ≥ 0.0
  - Historical defect count normalization behaves correctly
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock
from routers.risk import calculate_risk_score, WEIGHTS


def make_tc(**kwargs):
    """Create a minimal mock TestCase with provided overrides."""
    tc = MagicMock()
    tc.test_case_id = kwargs.get("test_case_id", "TC_TEST")
    tc.business_criticality = kwargs.get("business_criticality", 5.0)
    tc.historical_defect_count = kwargs.get("historical_defect_count", 2)
    tc.historical_critical_defect_count = kwargs.get("historical_critical_defect_count", 1)
    tc.production_usage = kwargs.get("production_usage", 5.0)
    tc.change_risk = kwargs.get("change_risk", 5.0)
    tc.network_risk = kwargs.get("network_risk", 5.0)
    tc.unusual_behaviour_risk = kwargs.get("unusual_behaviour_risk", 5.0)
    tc.execution_time_minutes = kwargs.get("execution_time_minutes", 5.0)
    return tc


class TestRiskScoreRange:
    def test_risk_score_in_range_for_average_values(self):
        tc = make_tc()
        result = calculate_risk_score(tc, actual_critical_count=1)
        assert 0.0 <= result["risk_score"] <= 10.0

    def test_risk_score_maximum_inputs(self):
        tc = make_tc(business_criticality=10.0, production_usage=10.0,
                     change_risk=10.0, network_risk=10.0, unusual_behaviour_risk=10.0)
        result = calculate_risk_score(tc, actual_critical_count=25)
        assert result["risk_score"] <= 10.0

    def test_risk_score_minimum_inputs(self):
        tc = make_tc(business_criticality=0.0, production_usage=0.0,
                     change_risk=0.0, network_risk=0.0, unusual_behaviour_risk=0.0)
        result = calculate_risk_score(tc, actual_critical_count=0)
        assert result["risk_score"] >= 0.0

    def test_risk_score_is_deterministic(self):
        tc = make_tc(business_criticality=7.0, change_risk=8.0, production_usage=6.0)
        r1 = calculate_risk_score(tc, actual_critical_count=3)
        r2 = calculate_risk_score(tc, actual_critical_count=3)
        assert r1["risk_score"] == r2["risk_score"]


class TestPriorityCategory:
    def test_critical_category_at_8_plus(self):
        # Max inputs guaranteed to produce ≥ 8.0
        tc = make_tc(business_criticality=10.0, production_usage=10.0,
                     change_risk=10.0, network_risk=10.0, unusual_behaviour_risk=10.0)
        result = calculate_risk_score(tc, actual_critical_count=25)
        assert result["priority_category"] == "Critical"
        assert result["risk_score"] >= 8.0

    def test_low_category_at_below_4(self):
        tc = make_tc(business_criticality=0.0, production_usage=0.0,
                     change_risk=0.0, network_risk=0.0, unusual_behaviour_risk=0.0)
        result = calculate_risk_score(tc, actual_critical_count=0)
        assert result["priority_category"] == "Low"
        assert result["risk_score"] < 4.0


class TestRiskFormulaWeights:
    def test_weights_sum_to_one(self):
        total = sum(WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9, f"Weights do not sum to 1.0: {total}"

    def test_higher_business_criticality_raises_score(self):
        tc_low = make_tc(business_criticality=1.0)
        tc_high = make_tc(business_criticality=9.0)
        r_low = calculate_risk_score(tc_low, actual_critical_count=1)
        r_high = calculate_risk_score(tc_high, actual_critical_count=1)
        assert r_high["risk_score"] > r_low["risk_score"]

    def test_higher_defect_count_raises_score(self):
        tc = make_tc()
        r_low = calculate_risk_score(tc, actual_critical_count=0)
        r_high = calculate_risk_score(tc, actual_critical_count=7)
        assert r_high["risk_score"] >= r_low["risk_score"]


class TestEfficiencyScore:
    def test_efficiency_score_equals_risk_over_time(self):
        tc = make_tc(execution_time_minutes=4.0)
        result = calculate_risk_score(tc, actual_critical_count=2)
        expected = round(result["risk_score"] / 4.0, 2)
        assert result["efficiency_score"] == expected

    def test_efficiency_score_higher_for_shorter_test(self):
        tc_short = make_tc(execution_time_minutes=2.0)
        tc_long = make_tc(execution_time_minutes=10.0)
        r_short = calculate_risk_score(tc_short, actual_critical_count=2)
        r_long = calculate_risk_score(tc_long, actual_critical_count=2)
        assert r_short["efficiency_score"] > r_long["efficiency_score"]


class TestRiskApiEndpoint:
    def test_risk_scores_endpoint_returns_list(self, client, tokens):
        r = client.get(f"/api/risk/scores?token={tokens['tester']}")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_all_returned_risk_scores_in_range(self, client, tokens):
        r = client.get(f"/api/risk/scores?token={tokens['tester']}")
        assert r.status_code == 200
        for tc in r.json():
            assert 0.0 <= tc["risk_score"] <= 10.0

    def test_weights_endpoint_returns_correct_keys(self, client, tokens):
        r = client.get(f"/api/risk/weights?token={tokens['tester']}")
        assert r.status_code == 200
        weights = r.json()
        for key in ["business_criticality", "historical_defect_risk", "change_risk",
                    "production_usage", "network_risk", "unusual_behaviour_risk"]:
            assert key in weights
