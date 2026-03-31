from agents.treasury_agent.run import _filter_risk_by_policy


def test_filter_risk_by_min_score_and_max_level():
    analyses = [
        {"poolId": "p1", "riskScore": 70, "riskLevel": "low"},
        {"poolId": "p2", "riskScore": 45, "riskLevel": "medium"},
        {"poolId": "p3", "riskScore": 35, "riskLevel": "high"},
    ]
    criteria = {"risk": {"min_score": 50, "max_level": "medium"}}

    filtered = _filter_risk_by_policy(analyses, criteria)
    assert [a["poolId"] for a in filtered] == ["p1"]


def test_filter_risk_by_string_level():
    analyses = [
        {"poolId": "p1", "riskScore": 80, "riskLevel": "very_low"},
        {"poolId": "p2", "riskScore": 75, "riskLevel": "low"},
        {"poolId": "p3", "riskScore": 65, "riskLevel": "medium"},
    ]
    criteria = {"risk": "low"}

    filtered = _filter_risk_by_policy(analyses, criteria)
    assert [a["poolId"] for a in filtered] == ["p1", "p2"]
