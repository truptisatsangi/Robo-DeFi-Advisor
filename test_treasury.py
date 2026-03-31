"""
End-to-end test for the Treasury recommendation pipeline.
Run from project root:  python test_treasury.py
"""

import asyncio
import json
import sys

sys.path.insert(0, ".")

from agents.treasury_agent import run_treasury_recommendation


async def test_full_pipeline():
    """Run the full treasury recommendation with the test mandate."""
    print("=" * 70)
    print("  RDA Treasury Advisor — End-to-End Test")
    print("=" * 70)

    result = await run_treasury_recommendation(
        mandate_id="test-mandate-001",
        dao_id="test-dao",
        amount_usd=100_000,
    )

    print(f"\nSuccess: {result.get('success')}")
    print(f"Run ID:  {result.get('run_id')}")

    if not result.get("success"):
        print(f"ERROR:   {result.get('error')}")
        if result.get("renewal_required"):
            print("         Mandate expired — governance must renew.")
        return

    rec = result.get("recommendation") or {}

    # Allocation table
    allocations = rec.get("allocation") or []
    if allocations:
        print(f"\n{'─' * 70}")
        print(f"  MULTI-POOL ALLOCATION  (Portfolio APY: {rec.get('expected_portfolio_apy', 0)}%)")
        print(f"{'─' * 70}")
        print(f"  {'Protocol':<14} {'Chain':<12} {'Alloc':>6} {'Amount':>12} {'APY':>7} {'Risk':>6}")
        print(f"  {'─'*14} {'─'*12} {'─'*6} {'─'*12} {'─'*7} {'─'*6}")
        for a in allocations:
            print(
                f"  {a['protocol']:<14} {a['chain']:<12} {a['pct']:>5.1f}% "
                f"${a['amount_usd']:>10,.0f} {a['apy']:>6.2f}% {a['risk_score']:>5}/100"
            )
        print(f"\n  Total allocated: ${rec.get('total_allocated_usd', 0):,.0f}")
        print(f"  Portfolio APY:   {rec.get('expected_portfolio_apy', 0)}%")
    else:
        print("\n  No allocation produced.")

    # Proposal draft
    proposal = result.get("proposal_draft") or ""
    if proposal:
        print(f"\n{'=' * 70}")
        print("  GOVERNANCE PROPOSAL DRAFT")
        print(f"{'=' * 70}")
        print(proposal)

    # Full JSON (for debugging) — deepcopy to break shared references
    import copy
    print(f"\n{'=' * 70}")
    print("  FULL JSON RESPONSE")
    print(f"{'=' * 70}")
    try:
        safe_result = copy.deepcopy(result)
        print(json.dumps(safe_result, indent=2, default=str))
    except Exception as e:
        print(f"  (Could not serialize full JSON: {e})")
        print(f"  Keys: {list(result.keys())}")
        print(f"  Allocation count: {len((result.get('recommendation') or {}).get('allocation') or [])}")


async def test_modules_standalone():
    """Quick sanity checks for individual modules."""
    print(f"\n{'=' * 70}")
    print("  MODULE SANITY CHECKS")
    print(f"{'=' * 70}")

    # 1. Mandate
    from core.mandate import get_mandate
    m = get_mandate("test-mandate-001", "test-dao")
    print(f"\n  [Mandate]  Loaded: {m['mandate_id']} for {m['dao_name']}")
    print(f"             Approval: {m['approval_ref']}")

    # 2. Policy
    from core.treasury_policy import TreasuryPolicy
    p = TreasuryPolicy.model_validate(m["policy"])
    criteria = p.to_criteria_dict()
    print(f"\n  [Policy]   min_apy={p.min_apy}, preference={p.preference}")
    print(f"             allowed_protocols={p.allowed_protocols}")
    print(f"             risk={criteria.get('risk')}")

    # 3. Protocol registry
    from core.protocol_registry import validate_protocols, get_protocol
    valid, invalid = validate_protocols(["aave", "compound", "bogus-protocol"])
    print(f"\n  [Registry] valid={valid}, invalid={invalid}")
    aave = get_protocol("aave")
    print(f"             Aave chains: {aave.supported_chains}")

    # 4. Allocation engine (with fake data)
    from core.allocation import allocate_across_pools
    fake_pools = [
        {"id": "p1", "protocol": "Aave", "chain": "Ethereum", "apy": 6.2, "tvl": 3e9,
         "totalScore": 0.85, "riskData": {"riskScore": 82, "riskLevel": "low"}},
        {"id": "p2", "protocol": "Compound", "chain": "Ethereum", "apy": 5.8, "tvl": 1.5e9,
         "totalScore": 0.72, "riskData": {"riskScore": 78, "riskLevel": "low"}},
        {"id": "p3", "protocol": "Aave", "chain": "Arbitrum", "apy": 5.1, "tvl": 800e6,
         "totalScore": 0.65, "riskData": {"riskScore": 75, "riskLevel": "low"}},
    ]
    alloc = allocate_across_pools(fake_pools, 100_000, max_tvl_per_pool_pct=40.0)
    print(f"\n  [Allocation] Fake 3-pool split:")
    for a in alloc["allocations"]:
        print(f"    {a['protocol']:<12} {a['pct']:>5.1f}%  ${a['amount_usd']:>10,.0f}  APY {a['apy']}%")
    print(f"    Portfolio APY: {alloc['expected_portfolio_apy']}%")

    # 5. Explanation
    from core.explanation import explain_pool_selection
    reasons = explain_pool_selection(
        {"apy": 6.2, "tvl": 3e9, "protocol": "aave", "riskData": {"riskScore": 82, "riskLevel": "low"}},
        {"min_apy": 2.0, "min_pool_tvl_usd": 1e6, "allowed_protocols": ["aave"], "risk": {"max_level": "medium", "min_score": 40}},
    )
    print(f"\n  [Explanation] {reasons}")

    print(f"\n  All module checks passed.")


async def main():
    await test_modules_standalone()
    print("\n")
    await test_full_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
