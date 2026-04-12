"""
Single source of truth for supported DeFi protocol metadata.

All references to protocol names across discovery, risk, decision, and policy
validation must go through this registry. Do not use raw protocol name strings
elsewhere in the codebase.

To add a new protocol: add an entry to PROTOCOL_REGISTRY and ensure the
data/protocol_clients/ adapter exists or falls back to DeFiLlama.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ProtocolEntry:
    """Metadata for a supported DeFi protocol."""

    name: str  # canonical lowercase key e.g. "aave"
    display_name: str  # e.g. "Aave v3"
    supported_chains: List[str]  # e.g. ["ethereum", "arbitrum", "polygon"]
    protocol_type: str  # "lending" | "dex" | "yield_aggregator" | "restaking"
    audit_status: str  # "audited" | "unaudited" | "partial"
    audit_age_months: Optional[int]  # months since last audit; None if unaudited
    default_risk_category: str  # "very_low" | "low" | "medium" | "high" | "very_high"


PROTOCOL_REGISTRY: dict[str, ProtocolEntry] = {
    "aave": ProtocolEntry(
        name="aave",
        display_name="Aave v3",
        supported_chains=["ethereum", "arbitrum", "polygon", "optimism", "base", "avalanche"],
        protocol_type="lending",
        audit_status="audited",
        audit_age_months=12,
        default_risk_category="low",
    ),
    "compound": ProtocolEntry(
        name="compound",
        display_name="Compound v3",
        supported_chains=["ethereum", "arbitrum", "polygon", "base"],
        protocol_type="lending",
        audit_status="audited",
        audit_age_months=12,
        default_risk_category="low",
    ),
    "curve": ProtocolEntry(
        name="curve",
        display_name="Curve Finance",
        supported_chains=["ethereum", "arbitrum", "polygon", "optimism", "base", "avalanche", "fantom", "gnosis"],
        protocol_type="dex",
        audit_status="audited",
        audit_age_months=13,
        default_risk_category="medium",
    ),
    "yearn": ProtocolEntry(
        name="yearn",
        display_name="Yearn V3",
        supported_chains=["ethereum", "arbitrum", "polygon", "base"],
        protocol_type="yield_aggregator",
        audit_status="audited",
        audit_age_months=15,
        default_risk_category="medium",
    ),
}

# Aliases for common protocol name variants (DeFiLlama may return "aave-v3", etc.)
for _alias, _canonical in [
    ("aave-v2", "aave"),
    ("aave-v3", "aave"),
    ("compound-v2", "compound"),
    ("compound-v3", "compound"),
    ("curve-dex", "curve"),
    ("yearn-finance", "yearn"),
]:
    if _canonical in PROTOCOL_REGISTRY and _alias not in PROTOCOL_REGISTRY:
        PROTOCOL_REGISTRY[_alias] = PROTOCOL_REGISTRY[_canonical]


def get_protocol(name: str) -> ProtocolEntry:
    """
    Returns the ProtocolEntry for the given canonical name.
    Raises ValueError if the protocol is not in the registry.
    Use this instead of raw string comparisons anywhere in the codebase.
    """
    key = (name or "").strip().lower()
    if key not in PROTOCOL_REGISTRY:
        raise ValueError(f"Protocol not in registry: {name!r}")
    return PROTOCOL_REGISTRY[key]


def validate_protocols(names: List[str]) -> Tuple[List[str], List[str]]:
    """
    Given a list of protocol name strings, returns:
      (valid_names, invalid_names)
    valid_names: those found in PROTOCOL_REGISTRY (canonicalized)
    invalid_names: those not found (unknown protocols)
    Used by TreasuryPolicy validation.
    """
    valid: List[str] = []
    invalid: List[str] = []
    for n in names or []:
        key = (n or "").strip().lower()
        if not key:
            continue
        if key in PROTOCOL_REGISTRY:
            entry = PROTOCOL_REGISTRY[key]
            if entry.name not in valid:
                valid.append(entry.name)
        else:
            if n not in invalid:
                invalid.append(n)
    return (valid, invalid)
