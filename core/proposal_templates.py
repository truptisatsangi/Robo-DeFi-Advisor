"""
Governance proposal templates — Snapshot / Tally / Commonwealth compatible markdown.
Returned as proposal_draft (no auto-submit in MVP).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _pool_verify_link(a: Dict[str, Any]) -> str:
    """Return a markdown link for pool verification, or a plain pool_id fallback."""
    url = (a.get("url") or "").strip()
    pool_id = a.get("pool_id", "")
    if url:
        return f"[View ↗]({url})"
    if pool_id:
        return f"[DeFiLlama ↗](https://defillama.com/yields/pool/{pool_id})"
    return "—"


def _format_allocation_table(allocation: Dict[str, Any]) -> str:
    """Build a markdown table for the multi-pool allocation split."""
    allocs = allocation.get("allocations") or []
    if not allocs:
        return ""
    lines = [
        "| Pool / Protocol | Chain | Allocation | Amount | APY | Risk | Verify |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for a in allocs:
        protocol = a.get("protocol", "—")
        chain = a.get("chain", "—")
        pct = a.get("pct", 0)
        amt = a.get("amount_usd", 0)
        apy = round(a.get("apy", 0), 2)
        risk = a.get("risk_score", "—")
        link = _pool_verify_link(a)
        lines.append(f"| {protocol} | {chain} | {pct}% | ${amt:,.0f} | {apy}% | {risk}/100 | {link} |")
    return "\n".join(lines)


def _format_human_timestamps(raw_timestamp: str) -> tuple[str, str]:
    """
    Convert ISO timestamp into human-friendly UTC and local labels.
    Returns (utc_label, local_label).
    """
    try:
        dt = datetime.fromisoformat(str(raw_timestamp).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt_local = dt.astimezone()
        else:
            dt_local = dt.astimezone()
        dt_utc = dt_local.astimezone(timezone.utc)
        utc_label = dt_utc.strftime("%d %b %Y, %H:%M UTC")
        local_tz = dt_local.tzname() or dt_local.strftime("UTC%z")
        local_label = dt_local.strftime("%d %b %Y, %H:%M") + f" {local_tz}"
        return utc_label, local_label
    except (ValueError, TypeError):
        return str(raw_timestamp), str(raw_timestamp)


def format_snapshot_proposal(
    decision_response: Dict[str, Any],
    mandate_id: str,
    approval_ref: str,
    allocation: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Format a treasury allocation recommendation as a Snapshot-ready markdown proposal.
    When `allocation` is provided, renders a multi-pool split table with portfolio APY.
    """
    if not decision_response.get("success") or not decision_response.get("optimalPool"):
        return "## Treasury Allocation Proposal\n\nNo pool selected. " + (
            decision_response.get("error") or "Decision did not return a recommendation."
        )

    criteria = decision_response.get("criteria") or decision_response.get("user_intent") or {}
    amount = criteria.get("amount_usd") or criteria.get("amount") or "—"
    generated_at = decision_response.get("timestamp") or datetime.now(timezone.utc).isoformat()
    generated_utc, generated_local = _format_human_timestamps(generated_at)

    has_allocation = allocation and allocation.get("allocations")

    if has_allocation:
        portfolio_apy = allocation.get("expected_portfolio_apy", 0)
        total_alloc = allocation.get("total_allocated_usd", 0)
        alloc_table = _format_allocation_table(allocation)
        n_pools = len(allocation["allocations"])
        top = allocation["allocations"][0]

        body = f"""## Treasury Allocation Proposal

Allocate **${amount:,.0f}** from treasury across **{n_pools} pool{"s" if n_pools > 1 else ""}**.

### Portfolio summary
- **Total allocated:** ${total_alloc:,.0f}
- **Expected portfolio APY:** {portfolio_apy}%
- **Number of pools:** {n_pools}

### Allocation breakdown

{alloc_table}
"""
        # Per-pool explanations
        body += "\n### Selection rationale\n"
        for a in allocation["allocations"]:
            expl = a.get("explanation") or ""
            if isinstance(expl, list):
                expl = ". ".join(expl)
            protocol = a.get("protocol", "—")
            pct = a.get("pct", 0)
            body += (
                f"- **{protocol} ({pct}%):** {expl or 'Met policy thresholds and ranking criteria.'}\n"
                f"  _Mandate: `{mandate_id}` | Generated (UTC): `{generated_utc}` | Local: `{generated_local}`_\n"
                "---\n"
            )
    else:
        # Fallback: single-pool format
        pool = decision_response["optimalPool"]
        protocol = pool.get("protocol", "Unknown")
        chain = pool.get("chain", "Unknown")
        apy = pool.get("apy", 0)
        risk_score = (pool.get("riskData") or {}).get("riskScore", "—")
        risk_level = (pool.get("riskData") or {}).get("riskLevel", "—")
        tvl = pool.get("tvl", 0)
        pool_id = pool.get("id", "—")
        explanation = pool.get("explanation") or pool.get("selection_reason")
        if isinstance(explanation, list):
            explanation = ". ".join(explanation)
        link = (pool.get("url") or "").strip() or "—"

        body = f"""## Treasury Allocation Proposal

Allocate **${amount}** from treasury to **{protocol}** on **{chain}**.

### Recommended pool
- **Pool / Market:** `{pool_id}`
- **Expected APY:** {apy}%
- **Risk Score:** {risk_score}/100 ({risk_level})
- **TVL:** ${tvl:,.0f}
- **Link:** {link}

### Why this pool was selected
{explanation or "Met policy thresholds and ranking criteria."}
"""

    body += f"""
### Mandate & approval
- **Mandate ID:** {mandate_id}
- **Approval Ref:** {approval_ref}
- **Generated At (UTC):** {generated_utc}
- **Generated At (Local):** {generated_local}
"""

    alternatives = decision_response.get("alternatives") or []
    if alternatives and not has_allocation:
        body += "\n### Alternative options\n"
        for i, alt in enumerate(alternatives[:3], 1):
            a_protocol = alt.get("protocol", "—")
            a_apy = alt.get("apy", 0)
            a_risk = (alt.get("riskData") or {}).get("riskScore", "—")
            body += f"- **Option {i}:** {a_protocol} — APY {a_apy}%, Risk {a_risk}/100\n"

    body += "\n---\n*Generated by RDA Treasury Advisor. Review before publishing.*"
    return body


def format_tally_proposal(
    decision_response: Dict[str, Any],
    mandate_id: str,
    approval_ref: str,
    allocation: Optional[Dict[str, Any]] = None,
) -> str:
    """Tally-compatible proposal (same structure as Snapshot for MVP)."""
    return format_snapshot_proposal(decision_response, mandate_id, approval_ref, allocation)
