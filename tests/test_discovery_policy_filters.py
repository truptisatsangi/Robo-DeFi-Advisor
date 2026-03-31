from agents.discovery_agent.discovery_logic import DiscoveryLogic, Pool


def test_discovery_uses_registry_and_supported_chains():
    logic = DiscoveryLogic()
    pools = [
        Pool(
            id="1",
            protocol="aave-v3",
            chain="Ethereum",
            tvl=10_000_000,
            apy=5.0,
            symbol="USDC",
            project="aave-v3",
        ),
        Pool(
            id="2",
            protocol="aave-v3",
            chain="Fantom",
            tvl=10_000_000,
            apy=5.0,
            symbol="USDC",
            project="aave-v3",
        ),
        Pool(
            id="3",
            protocol="unknown-protocol",
            chain="Ethereum",
            tvl=10_000_000,
            apy=9.0,
            symbol="USDC",
            project="unknown-protocol",
        ),
    ]
    criteria = {
        "allowed_protocols": ["aave"],
        "allowed_chains": ["ethereum", "fantom"],
        "min_pool_tvl_usd": 1_000_000,
        "min_apy": 2.0,
    }

    filtered = logic.filter_pools_by_criteria(pools, criteria)
    assert [p.id for p in filtered] == ["1"]
