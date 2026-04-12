"""
Treasury Policy Schema — single source of truth for treasury investment constraints.
Used by discovery, risk, and decision agents.
"""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from core.protocol_registry import validate_protocols


RISK_LEVELS = ("very_low", "low", "medium", "high", "very_high")


class RiskConstraints(BaseModel):
    """Risk band: only recommend pools at or safer than these limits."""

    max_level: Optional[Literal["very_low", "low", "medium", "high", "very_high"]] = Field(
        None,
        description="Only pools with risk_level in [very_low, ..., max_level]. One of: very_low, low, medium, high, very_high",
    )
    min_score: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Only pools with riskScore >= this (0-100, higher = safer)",
    )


class TreasuryPolicy(BaseModel):
    """
    Structured policy schema for DAO treasury investment constraints.
    Implement as Pydantic model; single source of truth for discovery, risk, decision.
    """

    min_apy: float = Field(0.0, description="Minimum acceptable APY (%)")
    max_apy: Optional[float] = Field(None, description="Maximum APY (e.g. for stable yield)")
    target_apy: Optional[float] = Field(None, description="Target APY for ranking")
    risk: Optional[Union[RiskConstraints, str]] = Field(
        None,
        description="Constraint: only pools in this risk band. 'low' or {max_level, min_score}",
    )
    allowed_protocols: List[str] = Field(
        default_factory=list,
        description="Whitelist (empty = use default trusted list). Validate via protocol_registry.validate_protocols.",
    )
    allowed_chains: List[str] = Field(
        default_factory=list,
        description="Whitelist e.g. ['ethereum', 'arbitrum']",
    )
    max_tvl_per_pool_pct: Optional[float] = Field(None, description="Max % of treasury in one pool")
    min_pool_tvl_usd: float = Field(0.0, description="Minimum pool TVL in USD")
    amount_usd: float = Field(0.0, description="Allocation amount in USD")
    rebalance_trigger_apy_drop_pct: Optional[float] = Field(
        None,
        description="Trigger rebalance if APY drops by this % (Phase 2 monitoring)",
    )
    preference: str = Field(
        "balanced",
        description="safest | highest_yield | balanced",
    )
    mandate_version: int = Field(1, description="Policy version for audit traceability")
    top_n: int = Field(10, description="Max number of pools to return from discovery")

    @field_validator("allowed_protocols", mode="before")
    @classmethod
    def _normalize_allowed_protocols(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("allowed_protocols must be a list of protocol names")
        normalized: List[str] = []
        for item in value:
            name = str(item or "").strip().lower()
            if name and name not in normalized:
                normalized.append(name)
        return normalized

    @field_validator("allowed_chains", mode="before")
    @classmethod
    def _normalize_allowed_chains(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("allowed_chains must be a list of chain names")
        normalized: List[str] = []
        for item in value:
            chain = str(item or "").strip().lower()
            if chain and chain not in normalized:
                normalized.append(chain)
        return normalized

    @model_validator(mode="after")
    def _validate_ranges_and_protocols(self) -> "TreasuryPolicy":
        if self.max_apy is not None and self.max_apy < self.min_apy:
            raise ValueError("max_apy must be greater than or equal to min_apy")

        if self.max_tvl_per_pool_pct is not None and not (0 < self.max_tvl_per_pool_pct <= 100):
            raise ValueError("max_tvl_per_pool_pct must be in the range (0, 100]")

        if self.allowed_protocols:
            valid, invalid = validate_protocols(self.allowed_protocols)
            if invalid:
                raise ValueError(
                    f"Unknown protocols in allowed_protocols: {invalid}. "
                    "Use canonical protocol registry names."
                )
            self.allowed_protocols = valid

        if isinstance(self.risk, str):
            risk_level = self.risk.strip().lower().replace(" ", "_")
            if risk_level not in RISK_LEVELS:
                raise ValueError(
                    f"Invalid risk level {self.risk!r}. "
                    f"Allowed values: {list(RISK_LEVELS)}."
                )
            self.risk = RiskConstraints(max_level=risk_level)

        return self

    def to_criteria_dict(self) -> Dict[str, Any]:
        """Convert to dict for discovery/risk/decision (min_apy, min_tvl, preference, risk, etc.)."""
        d: Dict[str, Any] = {
            "min_apy": self.min_apy,
            "max_apy": self.max_apy,
            "target_apy": self.target_apy,
            "preference": self.preference,
            "min_tvl": self.min_pool_tvl_usd,
            "amount_usd": self.amount_usd,
            "top_n": self.top_n,
        }
        if self.risk is not None:
            if isinstance(self.risk, str):
                d["risk"] = {"max_level": self.risk, "min_score": None}
            else:
                d["risk"] = {
                    "max_level": getattr(self.risk, "max_level", None),
                    "min_score": getattr(self.risk, "min_score", None),
                }
        else:
            d["risk"] = {"max_level": None, "min_score": None}
        d["allowed_protocols"] = self.allowed_protocols
        d["allowed_chains"] = self.allowed_chains
        d["max_tvl_per_pool_pct"] = self.max_tvl_per_pool_pct
        return d
