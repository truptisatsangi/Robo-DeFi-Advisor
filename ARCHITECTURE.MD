DAO Treasury Management Module — Implementation Plan (MVP-First)

Product Goal

DAOs hold billions in idle stablecoins earning little or no yield because treasury research takes time, governance proposals take days, and DeFi expertise is limited. RDA solves this by converting a DAO treasury policy into:





DeFi opportunity discovery



Risk scoring



Allocation recommendations



Governance-ready proposals

The system uses policy-driven decision making (structured parameters) instead of natural language for treasury operations.

Important Constraint

Do NOT implement autonomous treasury execution in the MVP. The MVP is a Treasury Advisor and Governance Proposal Generator only. No autonomous fund movement; no executor agent; no circuit breaker or emergency withdrawal. Those are Phase 2 (post-MVP), documented but not built.

Architecture Principles





Policy-driven decisions (single source of truth: TreasuryPolicy schema)



Governance-aligned design (every run tied to a DAO-approved mandate)



No autonomous fund custody or movement in MVP



Modular agent architecture (discovery, risk, decision, treasury orchestrator)



Clear separation between recommendation and execution (execution is out of scope for MVP)



1. Treasury Policy Schema (MVP)

Create a structured policy schema that defines treasury investment constraints. Implement as a Pydantic model. This schema is the single source of truth used by the discovery, risk, and decision agents.

Proposed schema (extend current intent shape):







Field



Type



Description



Example





min_apy



float



Minimum acceptable APY (%)



5.0





max_apy



float



null



Maximum APY (e.g. for stable yield)





target_apy



float



null



Target APY for ranking





risk



string or object



Constraint: only pools in this risk band



"low" or {"max_level": "medium"} or {"min_score": 60}





allowed_protocols



list[str]



Whitelist (empty = use default trusted list)



["aave", "compound"]





allowed_chains



list[str]



Whitelist



["ethereum", "arbitrum"]





max_tvl_per_pool_pct



float



null



Max % of treasury in one pool





min_pool_tvl_usd



float



Minimum pool TVL



1_000_000





amount_usd



float



Allocation amount



100_000





rebalance_trigger_apy_drop_pct



float



null



Trigger rebalance if APY drops by this %





preference



string



"safest"



"highest_yield"





mandate_version



int



Version of the policy when DAO amends IPS; every recommendation/execution records which version it was made under



1

Risk semantics: In the codebase, risk is already a score 0–100 (higher = safer) and level (very_low, low, medium, high, very_high). For "risk -> x% only":





Option A (level): risk.max_level = "low" → only recommend pools with risk_level in [very_low, low].



Option B (score): risk.min_score = 60 → only recommend pools with riskScore >= 60.

Recommend supporting both: e.g. risk: { "max_level": "medium", "min_score": 50 } and enforce both in Discovery/Risk/Decision.

File: core/treasury_policy.py — Pydantic model(s) TreasuryPolicy and optional nested RiskConstraints; validation as needed. Discovery, risk, and decision agents consume this schema (or a dict derived from it) as their criteria input. Policy validation: Use core/protocol_registry.validate_protocols(policy.allowed_protocols) to reject unknown protocols; see Section 1b.



1b. Protocol Registry (MVP)

Single source of truth for supported DeFi protocol metadata. All references to protocol names across discovery, risk, decision, and policy validation must go through this registry. Do not use raw protocol name strings elsewhere in the codebase.

File: core/protocol_registry.py (NEW)

Module docstring:

Single source of truth for supported DeFi protocol metadata.

All references to protocol names across discovery, risk, decision, and policy
validation must go through this registry. Do not use raw protocol name strings
elsewhere in the codebase.

To add a new protocol: add an entry to PROTOCOL_REGISTRY and ensure the
data/protocol_clients/ adapter exists or falls back to DeFiLlama.

Model: Define a dataclass or Pydantic model ProtocolEntry with:





name: str — canonical lowercase key (e.g. "aave")



display_name: str — e.g. "Aave v3"



supported_chains: list[str] — e.g. ["ethereum", "arbitrum", "polygon"]



protocol_type: str — "lending" | "dex" | "yield_aggregator" | "restaking"



audit_status: str — "audited" | "unaudited" | "partial"



audit_age_months: Optional[int] — months since last audit; None if unaudited



default_risk_category: str — "very_low" | "low" | "medium" | "high" | "very_high"

PROTOCOL_REGISTRY (minimum entries):





aave: display_name "Aave v3", supported_chains ["ethereum", "arbitrum", "polygon", "optimism", "base"], protocol_type "lending", audit_status "audited", audit_age_months 18, default_risk_category "low"



compound: display_name "Compound v3", supported_chains ["ethereum", "arbitrum", "polygon"], protocol_type "lending", audit_status "audited", audit_age_months 14, default_risk_category "low"



curve: display_name "Curve Finance", supported_chains ["ethereum", "arbitrum", "polygon", "optimism"], protocol_type "dex", audit_status "audited", audit_age_months 24, default_risk_category "medium"



yearn: display_name "Yearn Finance", supported_chains ["ethereum", "arbitrum"], protocol_type "yield_aggregator", audit_status "audited", audit_age_months 20, default_risk_category "medium"

Helper functions:





get_protocol(name: str) -> ProtocolEntry — Returns the entry for the given canonical name. Raises ValueError if the protocol is not in the registry. Use this instead of raw string comparisons anywhere in the codebase.



validate_protocols(names: list[str]) -> tuple[list[str], list[str]] — Given a list of protocol name strings, returns (valid_names, invalid_names). valid_names: those found in PROTOCOL_REGISTRY; invalid_names: those not found (unknown protocols). Used by TreasuryPolicy validation.

Usage: Discovery uses the registry to resolve allowed_protocols and filter by supported_chains; risk/decision can use default_risk_category and audit metadata when needed. TreasuryPolicy validation calls validate_protocols(allowed_protocols) and rejects or warns on invalid names.



2. Mandate System (MVP)

Every treasury recommendation must be tied to a DAO-approved mandate. No recommendations without a valid mandate.

Mandate record (minimal):





mandate_id: unique ID (e.g. UUID or content-addressed).



mandate_version: integer; incremented when the DAO amends the policy (IPS). Every historical recommendation and execution records mandate_version so the audit trail stays traceable after parameter updates.



dao_id / dao_name: who approved it.



policy: the TreasuryPolicy schema above (includes mandate_version for the policy snapshot).



approval_ref: link to Snapshot proposal ID or on-chain governance transaction (e.g. "Snapshot proposal #123" or "Governance tx 0x...").



valid_from / valid_until: optional time bounds. (MVP: no execution_mode or limits; recommendation-only.)

Storage: Start with file-based or SQLite per DAO (e.g. mandates/{dao_id}/{mandate_id}.json) so you don't need a heavy backend. Later: DB or Fetch/Agentverse if you want on-chain or cross-agent visibility.

Flow:





DAO approves a "Treasury Mandate" via Snapshot (or on-chain vote). The proposal text or an attachment defines the policy (or a hash of it).



Operator or bot registers the mandate in RDA (store policy + approval_ref).



Every Treasury run (recommendation or execution) is invoked with mandate_id. RDA loads the mandate, validates it (e.g. not expired), and runs Discovery/Risk/Decision only within that policy.



Every output (recommendation list, proposal draft, execution tx) includes mandate_id and approval_ref so it’s auditable: "This recommendation is under Snapshot #123."

Multisig / timelock (optional but recommended for enterprise):





For "execute_within_mandate": the executor should be a multisig or a timelock contract. RDA builds the transaction and submits it to the multisig/timelock; signers approve. No single key can move funds.



Alternatively: RDA only produces signed payloads or meta-txs that a multisig then executes. This keeps "who can move funds" entirely with the DAO’s multisig.

Implementation:





New module: **core/mandate.py** (or dao/mandate.py): load/save/validate mandate; function get_mandate(mandate_id) used by the Treasury entry point.



Treasury entry point (see below) must require mandate_id, load mandate, and pass policy into the pipeline; reject if mandate missing or invalid.

Mandate expiry and renewal (critical for production):

When valid_until is in the past and the DAO has active positions deployed, behaviour must be explicit. Do not leave this undefined.





Auto-pause new allocations: Reject any TreasuryRequest that would deploy new capital. No new allocations or executions under this mandate.



Continue monitoring existing positions: Monitoring agent keeps watching APY, TVL, and exploit feeds for existing positions; alerts and renewal prompts still sent.



Renewal prompt to governance: Emit a clear signal (dashboard, notification, or report) that the mandate has expired and governance must vote to renew (new Snapshot proposal) or amend. Include list of active positions and current state.



Never auto-withdraw: Withdrawing funds is a capital decision and requires a governance vote (new proposal) unless it is a Tier 1 emergency (e.g. exploit confirmed, protocol halted), in which case the emergency withdrawal path (Section 6) is used with multisig approval only.

MVP behaviour: In get_mandate() and at Treasury entry, check valid_until; if expired, block new recommendations and return a message that mandate renewal is required; do not run the pipeline.



3. Audit Log (MVP)

MVP: Implement a simple append-only log. No cryptographic hash chain or on-chain anchoring in the MVP.

Log fields: run_id, mandate_id, policy_snapshot, recommendation_output, timestamp.

File: core/audit.py — append-only write (e.g. NDJSON or SQLite). Call after the Treasury flow produces a recommendation.

Phase 2 (post-MVP): Replace with hash-chained log and optional Ethereum anchoring for enterprise/compliance.



3b. Liability and Audit Trail (Phase 2 — Not in MVP)

Enterprise requirement: File-based append-only NDJSON is not sufficient for a protocol like Aave. Files can be edited, deleted, or lost. The audit trail must be cryptographically tamper-evident. Hash-chained log (see below) plus optional on-chain anchoring transforms "we have logs" into "our logs are cryptographically tamper-evident" — the right conversation for compliance.

Hash-chained log: Each audit entry includes: (1) Payload: run_id, mandate_id, mandate_version, timestamp, and rest of log content; (2) prev_entry_hash: SHA256 of previous entry (genesis for first); (3) entry_hash: SHA256(prev_entry_hash + serialized payload). Append-only; tampering invalidates the chain and is detectable. On-chain anchoring: Periodically commit current chain head hash to Ethereum (e.g. storage or calldata); Ethereum acts as notary so history cannot be rewritten after anchor.

Recommendation log payload: run_id, mandate_id, mandate_version, timestamp, policy_snapshot, input_amount, output. Execution log payload: same plus tx_hash, chain, wallet, pool, amount, multisig/proposal ID if applicable.

Documentation:





One-pager or short doc: "RDA executes only within a DAO-approved mandate. The DAO is responsible for approving the policy (protocols, chains, caps, risk limits). RDA does not custody funds; it proposes or executes transactions that the DAO’s governance has pre-approved." Include: mandate lifecycle, audit trail, optional multisig/timelock.



In-app: short disclaimer that recommendations are under mandate X; DAO is responsible for the approved policy. One-pager should also state: hash-chained audit log, optionally Ethereum-anchored; mandate lifecycle and expiry/renewal.

Implementation: core/audit.py: append_entry(entry_type, payload) computes and stores prev_entry_hash and entry_hash; expose get_chain_head() for anchoring; optional anchor_chain_to_ethereum(head_hash). Call from Treasury flow after Decision and after execution. Do not use plain file append for Phase 3 / enterprise.



4. DeFi Pool Discovery (MVP)

Extend the existing discovery agent so it accepts the TreasuryPolicy schema (or criteria dict derived from it) as input instead of free text.

Filters: allowed_protocols, allowed_chains, min_pool_tvl_usd, min_apy / max_apy. Resolve allowed_protocols via protocol registry (Section 1b): use get_protocol(name) or validate with validate_protocols; filter by supported_chains from registry when policy specifies allowed_chains. Data sources: DeFiLlama API; protocol APIs or static pool datasets for MVP. Discovery returns candidate pools.

File: agents/discovery_agent/discovery_logic.py — use protocol registry for allowed protocols and chains (no raw string comparisons); use min_pool_tvl_usd and min_apy/max_apy from policy.



4b. Risk Filtering (MVP)

Use existing risk scoring; enforce hard constraints from policy: drop pools where risk_score < policy.risk.min_score or risk_level is worse than policy.risk.max_level. Output: risk_score, risk_level, explanation.

File: agents/risk_agent/agent.py.



4c. Decision / Allocation Engine (MVP)

Rank pools using a deterministic, explainable scoring formula. Apply treasury policy constraints. Output: recommended pools, suggested allocation split, expected portfolio APY. This ensures recommendations are reproducible and explainable to DAO governance.

Deterministic ranking formula:

Normalize each variable to the same scale (e.g. 0–1) across the candidate pool set, then compute a single score per pool:

score = 0.5 * normalized_apy + 0.3 * normalized_risk_score + 0.2 * normalized_tvl





normalized_apy: Map APY to [0, 1] using min-max over the candidate set (e.g. (apy - min_apy) / (max_apy - min_apy) with a guard for zero range). Higher APY is better.



normalized_risk_score: Risk agent already outputs a score 0–100 (higher = safer). Map to [0, 1] by dividing by 100. Higher is better.



normalized_tvl: Map TVL to [0, 1] using min-max over the candidate set (log scale optional for very large ranges). Higher TVL is better (liquidity).

Weights (0.5, 0.3, 0.2) are configurable; document the chosen weights in code and in governance docs so DAOs understand how pools are ordered. Sort pools by score descending; the top pool(s) and allocation split follow from this order.

Documentation: In agents/decision_agent/decision_logic.py, document this formula in a comment or docstring and expose the weights as named constants so changes are explicit. Reproducibility: same policy + same pool data must yield the same ranking.

File: agents/decision_agent/decision_logic.py — after Risk, filter by risk.min_score / risk.max_level; apply the deterministic score above; apply max_tvl_per_pool_pct when suggesting allocation. Output structure: { "recommended_pools": [...], "expected_portfolio_apy": 6.1 }.



4d. Recommendation Explanation Layer (MVP)

Add a lightweight explanation module that describes why each pool was recommended. Attach the explanation to each recommended pool in the final output to improve governance transparency.

New module: agents/explanation_agent/ (or core/explanation.py as a stateless helper used by the treasury flow).

Behaviour: For each recommended pool, produce a short, structured explanation derived from policy and pool data. Example output:





APY above policy threshold



Risk score within mandate limits



Protocol whitelisted in policy



Pool TVL above minimum threshold

Implementation: Inputs: one pool (with risk_score, risk_level, apy, tvl, protocol, chain) + the TreasuryPolicy (or criteria) used. Output: a list of strings or a single summary string (e.g. "Why this pool was selected: APY above policy threshold. Risk score within mandate limits. Protocol whitelisted in policy. Pool TVL above minimum threshold."). No LLM required for MVP; rules based on policy fields vs pool fields are sufficient. Attach as explanation or selection_reason on each recommended pool in the decision output and in the proposal/recommendation payload returned by the Treasury entry.

File: agents/explanation_agent/ (e.g. explain_pool_selection(pool: dict, policy: dict) -> list[str] or str). Called by the Decision step or by the Treasury orchestrator after Decision; result added to each pool in recommended_pools before generating the proposal and returning the final response.



5. Governance Proposal Generator (MVP)

Generate governance-ready proposals compatible with Snapshot, Tally, and Commonwealth. Return the proposal as markdown (no auto-submit in MVP; human pastes into their governance tool).

Template: Title e.g. "Treasury Allocation Proposal". Body: allocate $X from treasury to [Protocol] [Pool]; Expected APY, Risk Score, TVL; Mandate ID and Approval Ref (e.g. Snapshot #123); link to pool. Structured sections: Amount, Source wallet, Target pool, Risk score/level, Mandate ID and approval ref, Link to pool.

File: core/proposal_templates.py — function format_snapshot_proposal(decision_response, mandate_id, approval_ref) returning markdown; optional format_tally_proposal(...). Treasury flow returns recommendation + proposal_draft (markdown).

Phase 2 (post-MVP): Human review gate, pending_review state, confirmation endpoint, optional Snapshot API.

Where it’s used: After Decision, the Treasury flow returns (1) rich recommendation, (2) proposal_draft (markdown), (3) proposal stored as pending_review. No automatic publish.



6. Phase 2 — Post-MVP (Documented, NOT Built in MVP)

The following must not be implemented in the MVP. Document for future work:





Autonomous execution layer: Executor agent (build deposit tx, interact with DeFi protocols, submit tx); execution only within mandate limits.



Multisig / timelock: Treasury execution via DAO multisigs or timelocks (e.g. Safe, governance execution contracts).



Circuit breaker: Pause execution if TVL drops, exploit detected, oracle anomalies; explicit human reactivation.



Emergency withdrawal: Pre-staged withdrawal tx; multisig approval for fast exit.



Cryptographically verifiable audit: Hash-chained logs, optional Ethereum anchoring.



Continuous monitoring agent: Monitor APY, liquidity, risk; trigger recommendations when thresholds crossed.



6b. Execution Layer (Phase 2 — Reference Only)

Per-DAO config (Phase 2):





dao_id, chain, treasury_wallet_address (or multisig address), mandate_id (current active mandate), execution_mode: "proposal_only" | "execute_within_mandate", optional max_single_tx_usd, max_daily_volume_usd.

Executor agent / module:





Inputs: mandate_id, dao_id, allocation decision (pool, amount, protocol, chain), optional run_id.



Load mandate and DAO config; validate that allocation is within policy (protocol in whitelist, risk within band, amount within caps).



Proposal-only: Return proposal draft only (reuse section 5); no tx building.



Execute-within-mandate: Build transaction (approve + deposit into pool). Use existing patterns: no custody — either (a) relay a user/multisig-signed tx, or (b) an "operator" key with strict limits that only submits txs matching the mandate; prefer multisig/timelock so no single key holds power.



Re-check pool at execution time (e.g. TVL/APY from DeFiLlama). When the check fails: Abort the execution immediately; do not perform partial execution. Log the failure and the reason (e.g. TVL drop, APY collapse) to the audit chain. No tx is submitted. Define thresholds in config (e.g. TVL drop > X%, APY drop > Y%) so behaviour is deterministic.

Circuit breaker (mandatory for Phase 3 / enterprise):

A named circuit breaker is a set of conditions that, when triggered, immediately pause ALL autonomous execution and require explicit human reactivation. Without it, a cascading failure (e.g. bad oracle, exploit, or runaway allocation) could drain multiple positions before any human reacts.





Conditions (examples): TVL drop > X% on a monitored pool; exploit flagged (by feed or MeTTa); oracle deviation > Y%; daily volume limit hit; mandate expired; circuit breaker manually triggered.



Effect: Executor refuses to submit any new allocation or withdrawal tx until the circuit breaker is explicitly reset by an authorised party (e.g. treasury manager or multisig). Monitoring and recommendations can continue (read-only); execution is halted.



State: Store circuit breaker status (open / closed) per DAO (or globally); expose an endpoint or UI to reset only after human review. Log every open/close to the audit chain.



Design and implement the circuit breaker before building the executor — it is not an optional extra; it is the difference between a product you can pitch to Aave and one you cannot.

Emergency withdrawal (design alongside execution, not as an afterthought):

When the monitoring agent detects a critical issue (protocol depeg, exploit, halt), the plan must define what happens next. There is no point detecting a problem without a pre-agreed exit path.





Pre-staged withdrawal: For every active position, maintain a pre-staged withdrawal transaction (or a reproducible recipe to build it). So when an emergency is declared, the DAO can execute exit with one multisig approval without needing a full Snapshot vote (which takes days).



Trigger: Tier 1 emergency (e.g. exploit confirmed, protocol paused, severe depeg) is defined in policy or circuit breaker. On trigger: circuit breaker opens; treasury manager (or multisig) is notified; they can approve the pre-staged withdrawal for the affected position(s). No autonomous execution of withdrawal — human (multisig) must sign.



Design this flow alongside the execution layer — same executor or a dedicated "emergency withdrawal" agent that only submits the pre-built withdraw tx when authorised. Store pre-staged tx payloads or build instructions per position.

Where it lives: New **agents/executor_agent/** (or executor/ module) with: config loader per DAO, mandate validation, tx builder (protocol-specific or via aggregator SDK), and call to audit log on success/failure.

Integration with current pipeline: Main or a new Treasury orchestrator agent receives TreasuryRequest (mandate_id + optional overrides). It loads mandate, runs Discovery → Risk → Decision with policy from mandate, then either returns recommendation + proposal draft (proposal_only) or also calls Executor (execute_within_mandate) and returns proposal + execution status/tx hash.



7. Treasury Entry Endpoint (MVP)

Create a treasury orchestration entry point that runs the full recommendation pipeline. No execution; recommendation and proposal only.

Suggested module: agents/treasury_agent/

Flow:





Load mandate (by mandate_id)



If mandate invalid or expired → return error / renewal message; stop



Apply policy (from mandate; optional overrides); validate allowed_protocols via protocol registry



Run discovery (with policy as criteria; use protocol registry for allowed protocols/chains)



Run risk filtering (with policy constraints)



Run decision engine (deterministic ranking formula; see Section 4c)



Attach recommendation explanation to each recommended pool (explanation agent / module; see Section 4d)



Generate proposal (markdown)



Write audit log



Return recommendation (with per-pool explanations) + proposal draft

Input: { "mandate_id": "...", "amount_usd": optional }. No autonomous execution; no Executor call.

MVP flow:

flowchart LR
  subgraph dao [DAO / Client]
    A[TreasuryRequest]
  end
  subgraph rda [RDA MVP]
    M[Mandate load]
    Reg[Protocol registry]
    D[Discovery]
    R[Risk]
    Dec[Decision]
    Expl[Explanation]
    P[Proposal template]
    Audit[Audit log]
  end
  A --> M
  M --> Reg
  Reg --> D
  D --> R
  R --> Dec
  Dec --> Expl
  Expl --> P
  P --> Audit



8. MVP Positioning

Position the product as a Treasury Advisor and Governance Proposal Generator, not an autonomous fund manager. No custody; no autonomous fund movement.





Governance-aligned: Every recommendation is tied to a DAO-approved mandate. Explicit policy parameters (APY, risk, protocols, chains, caps).



Pilot narrative: MVP is proposal-only; DAOs can try recommendations and governance drafts with zero execution risk. Phase 2 can add execution within mandate (multisig) and enterprise features (tamper-evident audit, circuit breaker, emergency withdrawal).



Protocol-specific: For Aave/Compound/Uniswap, support their protocols in whitelist and use existing DeFiLlama data and risk scoring.



9. Phased Implementation

Phase 1 — MVP (what must be built)  





Treasury Policy Schema: Pydantic model in core/treasury_policy.py (min_apy, risk.max_level, risk.min_score, allowed_protocols, allowed_chains, min_pool_tvl_usd, max_tvl_per_pool_pct, amount_usd, preference, mandate_version). Validate allowed_protocols via core/protocol_registry.validate_protocols.



Protocol registry: core/protocol_registry.py; ProtocolEntry model; PROTOCOL_REGISTRY (aave, compound, curve, yearn); get_protocol(name), validate_protocols(names). Single source of truth for protocol metadata; no raw protocol strings elsewhere.



Mandate system: core/mandate.py; mandate record (mandate_id, dao_id, mandate_version, policy, approval_ref, valid_from, valid_until); JSON or SQLite storage; if expired, block recommendations and return renewal message.



DeFi pool discovery: Extend agents/discovery_agent/discovery_logic.py to accept TreasuryPolicy; use protocol registry for allowed_protocols and supported_chains; filters min_pool_tvl_usd, min_apy/max_apy; return candidate pools.



Risk filtering: agents/risk_agent/agent.py; enforce policy.risk.min_score and policy.risk.max_level; output risk_score, risk_level, explanation.



Decision / allocation engine: agents/decision_agent/decision_logic.py; deterministic ranking: score = 0.5normalized_apy + 0.3normalized_risk_score + 0.2*normalized_tvl; normalize each to same scale; document formula and weights; apply policy; output recommended_pools, allocation split, expected_portfolio_apy.



Recommendation explanation layer: agents/explanation_agent/ (or core/explanation.py); for each recommended pool produce "why selected" (APY above threshold, risk within mandate, protocol whitelisted, TVL above min); attach to each pool in final output.



Governance proposal generator: core/proposal_templates.py; markdown template for Snapshot/Tally/Commonwealth; return proposal draft.



Simple audit log: core/audit.py; append-only; run_id, mandate_id, policy_snapshot, recommendation_output, timestamp. No hash chain or on-chain anchoring in MVP.



Treasury entry endpoint: agents/treasury_agent/; input { mandate_id, amount_usd optional }; flow: load mandate → validate policy (registry) → discovery → risk → decision → explanation (per pool) → proposal → audit → return recommendation (with explanations) + proposal.

Phase 2 — Post-MVP (documented, not built)  

Execution layer, multisig/timelock, circuit breaker, emergency withdrawal, cryptographically verifiable audit trail, continuous monitoring agent. See Section 6.



10. File and Module Summary (MVP)







Area



New/Modified



Path / files





Policy schema



New



core/treasury_policy.py; validate allowed_protocols via protocol registry





Protocol registry



New



core/protocol_registry.py (ProtocolEntry, PROTOCOL_REGISTRY, get_protocol, validate_protocols)





Mandate



New



core/mandate.py





Audit



New



core/audit.py (simple append-only)





Proposal templates



New



core/proposal_templates.py





Discovery



Modify



agents/discovery_agent/discovery_logic.py (TreasuryPolicy, protocol registry, min_pool_tvl_usd, min_apy/max_apy)





Risk



Modify



agents/risk_agent/agent.py (policy risk.min_score, risk.max_level)





Decision



Modify



agents/decision_agent/decision_logic.py (deterministic ranking formula, policy, allocation split, expected_portfolio_apy)





Explanation



New



agents/explanation_agent/ or core/explanation.py (per-pool "why selected" attached to recommended_pools)





Treasury entry



New



agents/treasury_agent/ (mandate → registry → discovery → risk → decision → explanation → proposal → audit → return)

Phase 2 (not in MVP): Executor, circuit breaker, emergency withdrawal, hash-chained audit, monitoring agent — see Section 6.



11. Expected MVP Output

Given e.g. DAO treasury $10M USDC and policy "low risk stable yield", RDA should output:





Recommended pools (with protocol, chain, APY, risk score, TVL, and per-pool explanation — why selected: APY above threshold, risk within mandate, protocol whitelisted, TVL above min)



Allocation suggestion (split across pools)



Expected portfolio APY



Governance proposal draft (markdown, Snapshot/Tally/Commonwealth compatible)



Audit record (run_id, mandate_id, policy_snapshot, recommendation_output, timestamp)

Recommendations are reproducible (deterministic ranking formula) and explainable (explicit explanation per pool and protocol metadata from registry).



12. Risk Parameter Mapping (Concrete)

To make "risk -> x% only" unambiguous in the product:





Expose in policy:  





risk.max_level: enum "very_low" | "low" | "medium" | "high" | "very_high" — recommend only pools at or safer than this.  



risk.min_score: number 0–100 — recommend only pools with riskScore >= this.



In Risk agent: Already computes riskScore and riskLevel; no change.  



In Decision (and Discovery if you filter post-fetch): After scoring, exclude any pool where riskLevel is worse than max_level (e.g. if max_level is "low", exclude medium/high/very_high) or riskScore < min_score.  



UI/API: For "x% only" you can document: "risk = low" means max_level: "low"; "risk score at least 60" means min_score: 60. Optional: a small helper that maps a single "risk" dropdown (e.g. "Low only", "Medium or better") into max_level + min_score.

This keeps risk constraints explicit and enforceable end-to-end while preserving your existing risk scoring.