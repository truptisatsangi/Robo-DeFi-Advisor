import asyncio

import pytest

from agents.treasury_agent.run import run_treasury_recommendation


def test_pipeline_stats_present_on_success(monkeypatch: pytest.MonkeyPatch):
    mandate = {
        "mandate_id": "m-1",
        "approval_ref": "Snapshot #1",
        "policy": {
            "min_apy": 2.0,
            "allowed_protocols": ["aave"],
            "allowed_chains": ["ethereum"],
            "amount_usd": 100_000,
            "risk": {"max_level": "medium", "min_score": 40},
        },
    }

    monkeypatch.setattr("agents.treasury_agent.run.get_mandate", lambda mandate_id, dao_id=None: mandate)

    class DummyDiscovery:
        async def discover_pools_with_stats(self, criteria):
            return {
                "pools": [{"id": "p1", "protocol": "aave-v3", "chain": "Ethereum", "apy": 4.2, "tvl": 1_000_000}],
                "stats": {
                    "total_fetched": 10,
                    "after_policy_filters": 4,
                    "after_rank_top_n": 3,
                    "after_apy_crosscheck": 1,
                },
            }

    async def fake_analyze_pool(payload):
        return {"poolId": "p1", "riskScore": 80, "riskLevel": "low"}

    class DummyDecisionAgent:
        async def select_optimal_pool(self, criteria, pools, risk_analysis):
            pool = dict(pools[0])
            pool["riskData"] = {"riskScore": 80, "riskLevel": "low"}
            return {
                "success": True,
                "optimalPool": pool,
                "alternatives": [],
                "allCandidates": [pool],
                "reasoningTrace": [],
                "criteria": criteria,
                "timestamp": "2026-03-31T00:00:00+00:00",
            }

    monkeypatch.setattr("agents.treasury_agent.run.DiscoveryLogic", DummyDiscovery)
    monkeypatch.setattr("agents.treasury_agent.run.analyze_pool", fake_analyze_pool)
    monkeypatch.setattr("agents.treasury_agent.run.DecisionAgent", DummyDecisionAgent)

    result = asyncio.run(run_treasury_recommendation("m-1"))
    assert result["success"] is True
    stats = result["pipeline_stats"]
    assert stats["discovery"]["total_fetched"] == 10
    assert stats["risk"]["input_candidates"] == 1
    assert stats["risk"]["after_risk_policy_filters"] == 1
    assert stats["decision"]["scored_candidates"] == 1
    assert stats["decision"]["recommended_count"] == 1
    assert stats["timestamps"]["started_at_utc"]
    assert stats["timestamps"]["completed_at_utc"]


def test_pipeline_stats_present_on_empty_discovery(monkeypatch: pytest.MonkeyPatch):
    mandate = {
        "mandate_id": "m-2",
        "approval_ref": "Snapshot #2",
        "policy": {"min_apy": 2.0, "allowed_protocols": ["aave"], "allowed_chains": ["ethereum"]},
    }
    monkeypatch.setattr("agents.treasury_agent.run.get_mandate", lambda mandate_id, dao_id=None: mandate)

    class DummyDiscovery:
        async def discover_pools_with_stats(self, criteria):
            return {
                "pools": [],
                "stats": {
                    "total_fetched": 10,
                    "after_policy_filters": 0,
                    "after_rank_top_n": 0,
                    "after_apy_crosscheck": 0,
                },
            }

    monkeypatch.setattr("agents.treasury_agent.run.DiscoveryLogic", DummyDiscovery)
    result = asyncio.run(run_treasury_recommendation("m-2"))
    assert result["success"] is True
    assert result["recommendation"]["recommended_pools"] == []
    stats = result["pipeline_stats"]
    assert stats["discovery"]["total_fetched"] == 10
    assert stats["timestamps"]["completed_at_utc"]
