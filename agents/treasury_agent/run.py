"""
Treasury entry point — runs the full recommendation pipeline (no execution in MVP).
Flow: load mandate → validate policy → discovery → risk → decision → explanation → proposal → audit → return.
"""

import asyncio
import copy
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Project root for imports
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from core.mandate import MandateExpiredError, MandateNotFoundError, get_mandate
from core.treasury_policy import TreasuryPolicy
from core.protocol_registry import validate_protocols
from core.audit import create_run_id, log_recommendation
from core.proposal_templates import format_snapshot_proposal
from core.explanation import explain_pool_selection
from core.allocation import allocate_across_pools

from agents.discovery_agent.discovery_logic import DiscoveryLogic
from agents.risk_agent.agent import analyze_pool
from agents.decision_agent.decision_logic import DecisionAgent

logger = logging.getLogger(__name__)

RISK_LEVEL_ORDER = ["very_low", "low", "medium", "high", "very_high"]


def _risk_level_rank(level: str) -> int:
    try:
        return RISK_LEVEL_ORDER.index((level or "").lower().replace(" ", "_"))
    except ValueError:
        return 2


def _policy_to_criteria(mandate_policy: Dict[str, Any]) -> Dict[str, Any]:
    """Build criteria dict from mandate policy (may be dict or need TreasuryPolicy)."""
    if not mandate_policy:
        return {}
    policy = TreasuryPolicy.model_validate(mandate_policy)
    return policy.to_criteria_dict()


def _filter_risk_by_policy(analyses: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Drop analyses that fail policy risk constraints (same logic as risk_agent)."""
    risk_cfg = criteria.get("risk") or {}
    if isinstance(risk_cfg, str):
        risk_cfg = {"max_level": risk_cfg, "min_score": None}
    min_score = risk_cfg.get("min_score")
    max_level = risk_cfg.get("max_level")
    if min_score is None and max_level is None:
        return analyses
    filtered = []
    for a in analyses:
        if min_score is not None and (a.get("riskScore") or 0) < min_score:
            continue
        if max_level is not None:
            pool_level = (a.get("riskLevel") or "medium").lower().replace(" ", "_")
            if _risk_level_rank(pool_level) > _risk_level_rank(max_level):
                continue
        filtered.append(a)
    return filtered


async def run_treasury_recommendation(
    mandate_id: str,
    amount_usd: Optional[float] = None,
    dao_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the full treasury recommendation pipeline. No execution; returns recommendation + proposal draft.
    Input: mandate_id, optional amount_usd override, optional dao_id to locate mandate.
    """
    run_id = create_run_id()
    started_at = datetime.now(timezone.utc)
    pipeline_stats: Dict[str, Any] = {
        "discovery": {
            "total_fetched": 0,
            "after_policy_filters": 0,
            "after_rank_top_n": 0,
            "after_apy_crosscheck": 0,
        },
        "risk": {
            "input_candidates": 0,
            "after_risk_policy_filters": 0,
        },
        "decision": {
            "scored_candidates": 0,
            "recommended_count": 0,
        },
        "timestamps": {
            "started_at_utc": started_at.isoformat(),
            "completed_at_utc": None,
        },
    }

    def _finalize_stats() -> Dict[str, Any]:
        pipeline_stats["timestamps"]["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
        return pipeline_stats
    try:
        # 1. Load mandate
        mandate = get_mandate(mandate_id, dao_id)
    except MandateNotFoundError as e:
        return {
            "success": False,
            "run_id": run_id,
            "mandate_id": mandate_id,
            "error": str(e),
            "renewal_required": False,
            "recommendation": None,
            "proposal_draft": None,
            "pipeline_stats": _finalize_stats(),
        }
    except MandateExpiredError as e:
        return {
            "success": False,
            "run_id": run_id,
            "mandate_id": mandate_id,
            "error": str(e),
            "renewal_required": True,
            "recommendation": None,
            "proposal_draft": None,
            "pipeline_stats": _finalize_stats(),
        }

    policy_dict = mandate.get("policy") or {}
    if amount_usd is not None:
        policy_dict = {**policy_dict, "amount_usd": amount_usd}
    try:
        criteria = _policy_to_criteria(policy_dict)
    except Exception as e:
        return {
            "success": False,
            "run_id": run_id,
            "mandate_id": mandate_id,
            "error": f"Invalid mandate policy: {e}",
            "recommendation": None,
            "proposal_draft": None,
            "pipeline_stats": _finalize_stats(),
        }

    # 2. Validate allowed_protocols
    allowed = policy_dict.get("allowed_protocols") or []
    if allowed:
        valid_names, invalid_names = validate_protocols(allowed)
        if invalid_names:
            return {
                "success": False,
                "run_id": run_id,
                "mandate_id": mandate_id,
                "error": f"Unknown protocols in policy: {invalid_names}. Use protocol registry names.",
                "recommendation": None,
                "proposal_draft": None,
                "pipeline_stats": _finalize_stats(),
            }

    # 3. Discovery
    discovery = DiscoveryLogic()
    discovery_result = await discovery.discover_pools_with_stats(criteria)
    pools = discovery_result.get("pools") or []
    pipeline_stats["discovery"] = discovery_result.get("stats") or pipeline_stats["discovery"]
    if not pools:
        out = {
            "success": True,
            "run_id": run_id,
            "mandate_id": mandate_id,
            "approval_ref": mandate.get("approval_ref", ""),
            "recommendation": {
                "recommended_pools": [],
                "expected_portfolio_apy": 0,
                "message": "No pools matched the mandate criteria.",
            },
            "proposal_draft": "## Treasury Allocation Proposal\n\nNo pools matched the mandate criteria. Adjust policy or try again later.",
            "pipeline_stats": _finalize_stats(),
        }
        log_recommendation(run_id, mandate_id, policy_dict, out)
        return out

    # 4. Risk analysis (in-process) — all pools analyzed concurrently
    pipeline_stats["risk"]["input_candidates"] = len(pools)
    normalized = [{"pool_id": p.get("id"), "metrics": p} for p in pools]
    raw_analyses = await asyncio.gather(*[analyze_pool(n) for n in normalized], return_exceptions=True)
    risk_analyses = [r for r in raw_analyses if isinstance(r, dict)]
    risk_analyses = _filter_risk_by_policy(risk_analyses, criteria)
    pipeline_stats["risk"]["after_risk_policy_filters"] = len(risk_analyses)
    # Only pass pools that passed risk policy to decision
    risk_pool_ids = {a["poolId"] for a in risk_analyses}
    pools = [p for p in pools if p.get("id") in risk_pool_ids]
    if not risk_analyses or not pools:
        out = {
            "success": True,
            "run_id": run_id,
            "mandate_id": mandate_id,
            "approval_ref": mandate.get("approval_ref", ""),
            "recommendation": {
                "recommended_pools": [],
                "expected_portfolio_apy": 0,
                "message": "All pools were filtered out by risk policy.",
            },
            "proposal_draft": "## Treasury Allocation Proposal\n\nAll candidate pools were filtered out by risk policy. Consider relaxing risk constraints or adding protocols.",
            "pipeline_stats": _finalize_stats(),
        }
        log_recommendation(run_id, mandate_id, policy_dict, out)
        return out

    # 5. Decision
    decision_agent = DecisionAgent()
    decision_response = await decision_agent.select_optimal_pool(criteria, pools, risk_analyses)
    if not decision_response.get("success") or not decision_response.get("optimalPool"):
        out = {
            "success": True,
            "run_id": run_id,
            "mandate_id": mandate_id,
            "approval_ref": mandate.get("approval_ref", ""),
            "recommendation": {
                "recommended_pools": [],
                "expected_portfolio_apy": 0,
                "message": decision_response.get("error") or "No pool selected.",
            },
            "proposal_draft": "## Treasury Allocation Proposal\n\n" + (decision_response.get("error") or "No pool selected."),
            "pipeline_stats": _finalize_stats(),
        }
        log_recommendation(run_id, mandate_id, policy_dict, out)
        return out

    # 6. Attach explanation to all scored pools
    all_scored = decision_response.get("allCandidates") or []
    optimal = decision_response["optimalPool"]
    for p in all_scored:
        p["explanation"] = explain_pool_selection(p, policy_dict)
        p["selection_reason"] = ". ".join(p["explanation"])
    optimal["explanation"] = explain_pool_selection(optimal, policy_dict)
    optimal["selection_reason"] = ". ".join(optimal["explanation"])

    # 7. Multi-pool allocation
    total_amount = criteria.get("amount_usd") or 0
    max_pool_pct = criteria.get("max_tvl_per_pool_pct")
    allocation_result = allocate_across_pools(all_scored, total_amount, max_pool_pct)

    recommended_pools = copy.deepcopy([optimal] + (decision_response.get("alternatives") or []))
    pipeline_stats["decision"]["scored_candidates"] = len(all_scored)
    pipeline_stats["decision"]["recommended_count"] = len(recommended_pools)
    recommendation = {
        "recommended_pools": recommended_pools,
        "allocation": allocation_result["allocations"],
        "expected_portfolio_apy": allocation_result["expected_portfolio_apy"],
        "total_allocated_usd": allocation_result["total_allocated_usd"],
        "reasoning_trace": decision_response.get("reasoningTrace", []),
    }

    # 8. Proposal draft (pass allocation into the template)
    proposal_draft = format_snapshot_proposal(
        decision_response,
        mandate_id,
        mandate.get("approval_ref", ""),
        allocation=allocation_result,
    )

    # 9. Audit
    log_recommendation(
        run_id,
        mandate_id,
        policy_dict,
        {
            "recommendation": recommendation,
            "proposal_draft": proposal_draft,
        },
    )

    # 10. Return
    return {
        "success": True,
        "run_id": run_id,
        "mandate_id": mandate_id,
        "approval_ref": mandate.get("approval_ref", ""),
        "recommendation": recommendation,
        "proposal_draft": proposal_draft,
        "pipeline_stats": _finalize_stats(),
    }
