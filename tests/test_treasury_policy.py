from pydantic import ValidationError

from core.treasury_policy import TreasuryPolicy


def test_policy_validates_and_canonicalizes_protocol_aliases():
    policy = TreasuryPolicy.model_validate(
        {
            "min_apy": 2.0,
            "allowed_protocols": ["AAVE-V3", "compound"],
            "allowed_chains": ["Ethereum", "Arbitrum"],
            "risk": "low",
            "max_tvl_per_pool_pct": 40.0,
        }
    )

    assert policy.allowed_protocols == ["aave", "compound"]
    assert policy.allowed_chains == ["ethereum", "arbitrum"]
    assert policy.risk is not None
    assert getattr(policy.risk, "max_level", None) == "low"


def test_policy_rejects_unknown_protocols():
    try:
        TreasuryPolicy.model_validate(
            {
                "min_apy": 1.0,
                "allowed_protocols": ["aave", "not-a-real-protocol"],
            }
        )
        assert False, "Expected ValidationError for unknown protocols"
    except ValidationError as exc:
        assert "Unknown protocols in allowed_protocols" in str(exc)


def test_policy_rejects_invalid_apy_range():
    try:
        TreasuryPolicy.model_validate(
            {
                "min_apy": 8.0,
                "max_apy": 4.0,
            }
        )
        assert False, "Expected ValidationError for invalid APY bounds"
    except ValidationError as exc:
        assert "max_apy must be greater than or equal to min_apy" in str(exc)
