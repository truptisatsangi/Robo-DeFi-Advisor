from agents.decision_agent.decision_logic import DecisionAgent


def test_decision_ranking_is_deterministic_for_same_input():
    agent = DecisionAgent()
    pools = [
        {"id": "p1", "apy": 7.0, "tvl": 200_000_000, "riskData": {"riskScore": 70}},
        {"id": "p2", "apy": 5.0, "tvl": 500_000_000, "riskData": {"riskScore": 85}},
        {"id": "p3", "apy": 9.0, "tvl": 120_000_000, "riskData": {"riskScore": 60}},
    ]

    run_one = agent.score_pools([dict(p) for p in pools], {})
    run_two = agent.score_pools([dict(p) for p in pools], {})

    assert [p["id"] for p in run_one] == [p["id"] for p in run_two]
    assert [p["totalScore"] for p in run_one] == [p["totalScore"] for p in run_two]


def test_decision_ranking_prefers_weighted_composite_score():
    agent = DecisionAgent()
    pools = [
        {"id": "balanced", "apy": 7.0, "tvl": 300_000_000, "riskData": {"riskScore": 80}},
        {"id": "high-apy-low-risk", "apy": 10.0, "tvl": 50_000_000, "riskData": {"riskScore": 45}},
        {"id": "safe-low-apy", "apy": 4.0, "tvl": 700_000_000, "riskData": {"riskScore": 95}},
    ]

    ranked = agent.score_pools([dict(p) for p in pools], {})
    assert len(ranked) == 3
    assert ranked[0]["totalScore"] >= ranked[1]["totalScore"] >= ranked[2]["totalScore"]
