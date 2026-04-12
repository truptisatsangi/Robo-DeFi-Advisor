# 🎯 Robo DeFi Advisor — DAO Treasury Management Module (MVP-First)

[![ASI Alliance](https://img.shields.io/badge/ASI%20Alliance-Powered-blue)](https://asi.foundation/)
[![uAgents](https://img.shields.io/badge/uAgents-Framework-green)](https://github.com/fetchai/uagents)
[![AgentVerse](https://img.shields.io/badge/AgentVerse-Platform-orange)](https://agentverse.ai/)
[![Python](https://img.shields.io/badge/Python-3.13+-yellow)](https://python.org/)

> **Governance-aligned treasury advisor for DAOs**: convert an approved treasury mandate into deterministic DeFi recommendations and governance-ready proposal drafts.  
> **MVP is proposal-only**: no autonomous execution, no custody, no wallet fund movement.

## 📋 Table of Contents

- [Project Goal](#-project-goal)
- [Current Implementation Status](#-current-implementation-status)
- [High-level Use Case](#-high-level-use-case)
- [Architecture & Components](#-architecture--components)
- [End-to-end Flow](#-end-to-end-flow)
- [Phase 1 (Implemented)](#-phase-1-implemented-mvp)
- [Phase 2 (Planned)](#-phase-2-planned-post-mvp)
- [Quick Start](#-quick-start)
- [Frontend and API (Institutional MVP)](#-frontend-and-api-institutional-mvp)
- [Agent Configuration](#-agent-configuration)
- [Beautiful Output Format](#-beautiful-output-format)
- [Protocols & Tech Stack](#-protocols--tech-stack)
- [Interaction Examples](#-interaction-examples)
- [Decision Formula and Rationale](#-decision-formula-and-rationale)
- [Security, Risk & Trust Model](#-security-risk--trust-model)
- [Why Large Protocols/DAOs Should Use This](#-why-large-protocolsdaos-should-use-this)
- [Future Scope](#-future-scope)
- [Deployment Guide](#-deployment-guide)
- [Troubleshooting](#-troubleshooting)
- [Contributors & License](#-contributors--license)

## 🎯 Project Goal

**Help DAOs deploy idle stablecoin treasury capital safely and transparently.**

Robo DeFi Advisor (RDA) converts a DAO-approved policy into:

✅ **Policy-constrained opportunity discovery**  
✅ **Deterministic risk filtering and ranking**  
✅ **Allocation suggestions + expected portfolio APY**  
✅ **Governance proposal draft (Snapshot/Tally-compatible markdown)**  
✅ **Append-only audit records linked to mandate and policy snapshot**

**Primary KPI**: reduce governance and research overhead while preserving policy control and auditability.

## 📌 Current Implementation Status

The codebase currently includes a full **Phase 1 MVP treasury recommendation pipeline**:

- `core/treasury_policy.py`: structured `TreasuryPolicy` schema with validation (risk constraints, APY bounds, protocol whitelist validation).
- `core/protocol_registry.py`: list of known DeFi protocols (name, chain, category) with helpers to check if a protocol is approved.
- `core/mandate.py`: mandate load/save/expiry checks; blocks recommendations on expired mandate.
- `agents/discovery_agent/discovery_logic.py`: fetches all pools from DeFiLlama, then filters them using the mandate's rules, and verifies APY against a secondary source before recommending.
- `agents/risk_agent/agent.py` + treasury-level risk enforcement: policy `risk.min_score` and `risk.max_level` hard filters and MeTTa.
- `agents/decision_agent/decision_logic.py`: deterministic scoring formula and ranking.
- `core/explanation.py`: rule-based per-pool explanation for governance transparency.
- `core/allocation.py`: constrained multi-pool allocation split.
- `core/proposal_templates.py`: governance-ready markdown draft generation.
- `core/audit.py`: append-only NDJSON run logs.
- `agents/treasury_agent/run.py`: orchestration flow (mandate -> discovery -> risk -> decision -> explanation -> proposal -> audit).
- `tests/`: unit coverage for policy, mandate, risk filtering, decision ranking, and discovery policy filters.

## 🚀 High-level Use Case

- **Retail or power users** want automated, intention-driven investments in DeFi
- **Users chat** with an ASI-enabled interface (ASI:One chat) and get actionable, auditable investment recommendations
- **Agents are discoverable** and reusable (via Agentverse) using secure messaging, DIDs and tamper-evident handoff (via Fetch Network)

## 🏗️ Architecture & Components

There are two ways to interact with the system:

**Flow 1 — ASI Chat interface (`main.py`)**
```
User
   ↓ natural language message
ASI:One Chat (delivers message to Treasury Agent)
   ↓
Treasury Agent (uAgent, main.py)
   ↓ raw text forwarded as-is
Discovery Agent (uAgent) ←→ DeFiLlama (pool fetch) + Aave/Compound/Curve/Yearn APIs (APY cross-check)
   ↓ candidate pools (uAgent message)
Risk Agent (uAgent)
   ↓ risk-scored pools (uAgent message)
Decision Agent (uAgent)
   ↓ final recommendation (uAgent message back to Treasury Agent)
Treasury Agent → ASI:One → User (formatted response)
```

**Flow 2 — REST API (`api/app.py`, used by the frontend)**
```
User / Frontend
   ↓ POST /api/recommendations/run  { mandate_id }
FastAPI (api/app.py)
   ↓
Mandate check  (core/mandate.py) — blocks if expired or not found
   ↓
Protocol validation  (core/protocol_registry.py)
   ↓
Discovery  (discovery_logic.py) — fetches ~19k pools from DeFiLlama,
           filters by mandate policy, ranks top-N, cross-checks APY
   ↓ candidate pools
Risk scoring  (risk_agent/agent.py, called in-process, not via uAgent)
           — scores each pool 0-100, drops pools failing policy risk limits
   ↓ risk-scored pools
Decision ranking  (decision_logic.py, called in-process)
           — normalises APY/risk/TVL, picks optimal pool + alternatives
   ↓
Explanation  (core/explanation.py) — per-pool reasoning text
Allocation   (core/allocation.py)  — splits capital across pools
Proposal     (core/proposal_templates.py) — Snapshot-ready markdown draft
Audit log    (core/audit.py) — append-only NDJSON record of this run
   ↓
JSON response to frontend
```

### Key Components:

- **🔧 uAgents** — Small autonomous agents responsible for one domain (Discovery, Risk, Decision)
- **🌐 Agentverse listing** — Makes your advisor discoverable for others
- **🔐 Fetch Network** — DID-based identity + encrypted messaging for agent-to-agent communications
- **🧠 MeTTa** — Queried for on-chain facts (contract verification, exploit history, audit links); falls back to TVL/APY/protocol scoring when data is unavailable
- **💬 ASI:One** — Chat interface that delivers messages to the Treasury Agent; intent extraction (NLP) is done by the Discovery Agent using the `asi1-mini` LLM

## 🔄 End-to-end Flow

This describes the **REST API / frontend flow** (`POST /api/recommendations/run`), which is the primary path used by the dashboard.

### Example Request:
```json
{ "mandate_id": "test-mandate-001", "amount_usd": 100000 }
```

### System Processing:

1. **Mandate check** — loads mandate by `mandate_id`; blocks if not found or expired
2. **Policy validation** — validates `TreasuryPolicy` + protocol registry
3. **Discovery** — fetches ~19k pools from DeFiLlama, filters by mandate policy, ranks top-N, cross-checks APY against Aave/Compound/Curve/Yearn APIs
4. **Risk scoring** — scores each surviving pool 0–100 (TVL + protocol reputation + APY sustainability + exploit history); drops pools that fail `risk.min_score` or `risk.max_level`
5. **Decision ranking** — normalises APY, risk score, and TVL across candidates; picks optimal pool + alternatives using deterministic formula
6. **Explanation** — adds rule-based "why selected" text to each pool
7. **Allocation** — splits capital across recommended pools respecting policy caps
8. **Proposal** — generates Snapshot-ready governance markdown draft
9. **Audit** — appends immutable NDJSON run record

> **Chat flow difference**: when using the ASI Chat interface (`main.py`), the user sends free-text. The Discovery Agent uses the `asi1-mini` LLM to extract intent (amount, APY preference, risk preference) from the message — there is no mandate in this path. Risk and Decision steps still run the same logic.

## ⚡ Quick Start

### Prerequisites

- Python 3.13+
- Virtual environment
- ASI One API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Robo-DeFi-Advisor
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** — create a `.env` file in the project root:
   ```bash
   ASI_ONE_API_KEY=your_asi_one_api_key       # used by Discovery Agent for intent extraction (asi1-mini LLM)
   AGENTVERSE_API_KEY=your_agentverse_api_key  # used for agent registration on Agentverse
   ```

5. **Start all agents**
   ```bash
   # Terminal 1 - Main Agent (handles ASI Chat)
   python main.py

   # Terminal 2 - Discovery Agent
   python agents/discovery_agent/agent.py

   # Terminal 3 - Risk Agent  
   python agents/risk_agent/agent.py

   # Terminal 4 - Decision Agent
   python agents/decision_agent/agent.py
   ```

6. **Run treasury MVP tests**
   ```bash
   python3 -m pytest tests/
   ```

## 🖥️ Frontend and API (Institutional MVP)

This repository now includes a minimal institutional dashboard stack:

- Backend API: `api/app.py` (FastAPI)
- Frontend app: `frontend/` (React + Tailwind + React Query)

### Run API service

```bash
uvicorn api.app:app --reload --port 8000
```

Available endpoints:

- `POST /api/recommendations/run`
- `GET /api/mandates`
- `GET /api/mandates/{mandate_id}`
- `GET /api/runs/latest`
- `GET /api/runs/{run_id}`
- `GET /api/audit/latest`
- `GET /api/audit/export?format=ndjson|json`

### Run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend pages:

- `/dashboard`: run form (required + optional fields), 4 KPI cards, stage filtering timeline, recommendation table, proposal draft copy
- `/mandates`: mandate list and status view
- `/runs/:run_id`: full run payload + stage telemetry
- `/settings`: non-sensitive display controls

### Stage filtering telemetry exposed to UI

The recommendation response now includes `pipeline_stats`:

- `pipeline_stats.discovery`: total fetched, policy-filtered, top-N ranked, APY-crosschecked
- `pipeline_stats.risk`: input candidates and post-risk-filter count
- `pipeline_stats.decision`: scored candidates and recommended count
- `pipeline_stats.timestamps`: run start/end UTC

### Frontend tests

Run frontend tests:

```bash
cd frontend
npm run test
```

## ✅ Phase 1 (Implemented MVP)

Phase 1 is implemented as a **recommendation and proposal generation system**:

1. Policy schema and protocol validation (`core/treasury_policy.py`, `core/protocol_registry.py`)
2. Mandate lifecycle checks (`core/mandate.py`)
3. Policy-constrained discovery (`agents/discovery_agent/discovery_logic.py`)
4. Risk constraints enforcement (`agents/risk_agent/agent.py`, treasury orchestrator)
5. Deterministic decision ranking (`agents/decision_agent/decision_logic.py`)
6. Explanation layer (`core/explanation.py`)
7. Proposal generation (`core/proposal_templates.py`)
8. Append-only audit logs (`core/audit.py`)
9. Treasury orchestration entrypoint (`agents/treasury_agent/run.py`)
10. Unit tests in `tests/`

**Critical MVP boundary**: No autonomous execution, no wallet integration, no custody, no fund movement.

## 🚧 Phase 2 (Planned Post-MVP)

Planned but intentionally **not implemented** in MVP:

- Execution within mandate (multisig/timelock controlled)
- Circuit breaker and emergency withdrawal workflow
- Cryptographically hash-chained audit trail + optional on-chain anchor
- Continuous monitoring and rebalancing triggers
- Enterprise policy ops, approvals, and reviewer gates

This split is deliberate: institutional trust requires proving policy discipline before enabling execution.

## 🔧 Agent Configuration

### Port Assignments

| Agent | Port | Endpoint | Purpose |
|-------|------|----------|---------|
| Main Agent | 8004 | `http://localhost:8004/submit` | ASI Chat interface |
| Discovery Agent | 8007 | `http://localhost:8007/submit` | Pool discovery |
| Risk Agent | 8002 | `http://localhost:8002/submit` | Risk analysis |
| Decision Agent | 8005 | `http://localhost:8005/submit` | Final decisions |

### Agent Addresses

- **Main Agent**: `agent1q26a60535xkty6hfq6xkwp573gd9d2lradhexvps2d9w5p552qf85qnrzjk`
- **Discovery Agent**: `agent1q0yp3tt90n0v9a8dq6w4q4aknv899phpluue5cpc6dt8adsujv696ndy2cm`
- **Risk Agent**: `agent1qfvk3m82xljka6y22447dufg6hnx0zuqejplxmxfvwscsq9qwr2cy0u74hw`
- **Decision Agent**: `agent1qtrv3q6048scartdhlm26xfmrdtrs763x099pem38p3xdxy04klxq7puxyq`

## 🎨 Beautiful Output Format

The system now provides beautiful, user-friendly responses in ASI Chat:

```
🎯 **INVESTMENT RECOMMENDATION** 🎯

📊 **Recommended Pool:** `227fdc0c...`

⚠️ **Risk Assessment:** 🚨 Very High (Score: 10/100)

💡 **Recommendations:**
• ⚠️ Contract not verified - high risk
• 🔍 No audit found - consider alternative pools
• 🚨 High risk pool - consider safer alternatives

💰 **Investment Amount:** $100
🎯 **Your Preference:** Safest

🚨 **Warning:** This pool has high risk. Consider safer alternatives.

---
*Powered by DeFi Risk Advisor*
```

### Features:
- ✅ **Color-coded risk levels** with emojis
- ✅ **Shortened pool IDs** for readability
- ✅ **Structured information** with clear sections
- ✅ **Smart recommendations** showing top priorities
- ✅ **Investment context** showing user preferences
- ✅ **Risk-based advice** with appropriate warnings

## 🛠️ Protocols & Tech Stack

- **ASI:One** — Chat interface; delivers user messages to the Treasury Agent
- **asi1-mini LLM** — Used inside the Discovery Agent to parse free-text into structured intent (amount, APY, preference)
- **uAgents** — Python micro-agents using agent runtime (send/receive messages)
- **Agentverse** — Registry & discovery for agents
- **Fetch Network** — DID identities, signed/encrypted agent messaging
- **MeTTa** — Queried for on-chain risk data; falls back to formula-based scoring when unavailable
- **Data Sources**: DeFiLlama (pool fetch), Aave V3 / Compound / Curve / Yearn APIs (APY cross-check only)

## 💬 Interaction Examples

### User Input:
> "Invest $1000 in a way to get at least 8% APY. I prefer stablecoins and low risk."

### Intent extracted by Discovery Agent (asi1-mini LLM):
```json
{
  "action": "invest",
  "amount": 1000,
  "min_apy": 8,
  "max_apy": null,
  "target_apy": null,
  "preference": "low"
}
```

### Final Response (ASI Chat):
```
🎯 **INVESTMENT RECOMMENDATION** 🎯

📊 **Recommended Pool:**

💱 Symbol: USDC
🏦 Protocol: Aave
⛓️ Chain: Ethereum
📈 APY: 8.20%
💧 Total Value Locked: $1,200,000,000
⚠️ Risk Assessment: 🟢 Low (Score: 82/100)

💭 Risk Analysis:
This pool has a LOW risk profile. ✓ Excellent liquidity with $1,200,000,000 TVL...
✓ Aave is an established protocol with strong track record and audits.
✓ Moderate APY (8.2%) suggests stable, sustainable returns.
✓ No known exploit history.

🔒 Security Metrics:
• Liquidity Depth: 🟢 Excellent
• Protocol Reputation: 🟢 Established & Audited
• Risk Level: 🟢 Low Risk

🔗 Pool Link: https://defillama.com/protocol/aave

💰 Your Investment: $1000
🎯 Your Preference: Low

✅ Great Choice: This pool has low risk and is suitable for conservative investments.

---
*Powered by DeFi Risk Advisor*
```
> **Note**: Pool IDs are DeFiLlama UUIDs, not on-chain contract addresses. Contract verification and audit data shown in risk factors depend on MeTTa availability.

## 📄 Sample End Output

When you call `POST /api/recommendations/run`, the response includes two key parts: **allocation** and **proposal_draft**.

### Allocation (JSON)

This is what the API returns under `recommendation.allocation`:

```json
{
  "allocations": [
    {
      "protocol": "aave-v3",
      "chain": "Ethereum",
      "apy": 8.2,
      "risk_score": 82,
      "risk_level": "low",
      "pct": 40.0,
      "amount_usd": 40000.00,
      "tvl": 1200000000,
      "url": "https://defillama.com/yields/pool/...",
      "explanation": "APY 8.2% is within mandate bounds [3%–20%]. Protocol aave-v3 is on the approved list. Risk score 82 passes minimum 60."
    },
    {
      "protocol": "compound-v3",
      "chain": "Ethereum",
      "apy": 6.9,
      "risk_score": 78,
      "risk_level": "low",
      "pct": 35.0,
      "amount_usd": 35000.00,
      "tvl": 800000000,
      "url": "https://defillama.com/yields/pool/...",
      "explanation": "APY 6.9% is within mandate bounds. Protocol compound-v3 is on the approved list. Risk score 78 passes minimum 60."
    },
    {
      "protocol": "curve",
      "chain": "Ethereum",
      "apy": 5.4,
      "risk_score": 75,
      "risk_level": "low",
      "pct": 25.0,
      "amount_usd": 25000.00,
      "tvl": 500000000,
      "url": "https://defillama.com/yields/pool/...",
      "explanation": "APY 5.4% is within mandate bounds. Protocol curve is on the approved list. Risk score 75 passes minimum 60."
    }
  ],
  "expected_portfolio_apy": 7.14,
  "total_allocated_usd": 100000.00
}
```

> Allocation is **score-weighted** (higher-scoring pools get more capital), capped at `max_tvl_per_pool_pct` from the mandate policy (default 40%). Pools with < 2% allocation are dropped.

---

### Proposal Draft (Markdown)

This is what the API returns under `proposal_draft` — ready to paste into Snapshot or Tally:

```markdown
## Treasury Allocation Proposal

Allocate **$100,000** from treasury across **3 pools**.

### Portfolio summary
- **Total allocated:** $100,000
- **Expected portfolio APY:** 7.14%
- **Number of pools:** 3

### Allocation breakdown

| Pool / Protocol | Chain    | Allocation | Amount    | APY  | Risk    | Verify       |
| --------------- | -------- | ---------- | --------- | ---- | ------- | ------------ |
| aave-v3         | Ethereum | 40.0%      | $40,000   | 8.2% | 82/100  | [View ↗](…) |
| compound-v3     | Ethereum | 35.0%      | $35,000   | 6.9% | 78/100  | [View ↗](…) |
| curve           | Ethereum | 25.0%      | $25,000   | 5.4% | 75/100  | [View ↗](…) |

### Selection rationale

- **aave-v3 (40%):** APY 8.2% is within mandate bounds [3%–20%]. Protocol aave-v3 is on the approved list. Risk score 82 passes minimum 60.
  _Mandate: `test-mandate-001` | Generated (UTC): `12 Apr 2026, 10:30 UTC` | Local: `12 Apr 2026, 16:00 IST`_
---
- **compound-v3 (35%):** APY 6.9% is within mandate bounds. Protocol compound-v3 is on the approved list. Risk score 78 passes minimum 60.
  _Mandate: `test-mandate-001` | Generated (UTC): `12 Apr 2026, 10:30 UTC` | Local: `12 Apr 2026, 16:00 IST`_
---
- **curve (25%):** APY 5.4% is within mandate bounds. Protocol curve is on the approved list. Risk score 75 passes minimum 60.
  _Mandate: `test-mandate-001` | Generated (UTC): `12 Apr 2026, 10:30 UTC` | Local: `12 Apr 2026, 16:00 IST`_
---

### Mandate & approval
- **Mandate ID:** test-mandate-001
- **Approval Ref:** dao-vote-2026-03-15
- **Generated At (UTC):** 12 Apr 2026, 10:30 UTC
- **Generated At (Local):** 12 Apr 2026, 16:00 IST

---
*Generated by RDA Treasury Advisor. Review before publishing.*
```

## 🧮 Decision Formula and Rationale

RDA uses a deterministic composite score in `agents/decision_agent/decision_logic.py`:

```text
score = 0.5 * normalized_apy
      + 0.3 * normalized_risk_score
      + 0.2 * normalized_tvl
```

Where:

- `normalized_apy`: APY normalized to `[0,1]` across candidate pools (higher is better)
- `normalized_risk_score`: risk score normalized to `[0,1]` (higher = safer)
- `normalized_tvl`: TVL normalized to `[0,1]` (higher liquidity is better)

Why this formula:

- **Governance reproducibility**: same mandate + same input data always returns the same ranking.
- **Balanced treasury objective**: DAOs want yield, but not at the cost of unsafe or illiquid pools.
- **Risk-aware by design**: risk has meaningful weight (`0.3`) and hard policy filters are applied before ranking.
- **Liquidity protection**: TVL term (`0.2`) penalizes thin pools that can create slippage/liquidity risk.
- **Explainability for review committees**: each score decomposes into explicit factors that are easy to audit.

Why these weights specifically (`0.5 / 0.3 / 0.2`):

- **0.5 APY**: treasury mandate still targets productive yield on idle capital.
- **0.3 Risk**: safety is prioritized second, preventing "highest APY wins" behavior.
- **0.2 TVL**: liquidity is a practical execution and risk-quality proxy.

These are intentionally conservative MVP defaults. A DAO can change weights later through governance, but the model remains deterministic and transparent.

## 🔐 Security, Risk & Trust Model

AI in treasury workflows introduces real risk: bad recommendations, hidden model variance, policy drift, and unauthorized execution paths.  
RDA mitigates these in the current implementation with strict controls:

- **Mandate-gated operation**: every run requires a DAO-approved `mandate_id`; expired or missing mandates are blocked.
- **Policy as single source of truth**: APY, risk, protocol, chain, TVL, and allocation caps are hard constraints.
- **Deterministic ranking (non-LLM)**: recommendation order is reproducible from explicit formula and data inputs.
- **Proposal-only MVP**: system cannot autonomously move funds; it only returns recommendations + markdown proposal drafts.
- **Registry-controlled protocol surface**: protocol allowlist validated through `core/protocol_registry.py` to prevent arbitrary unknown integrations.
- **Audit traceability**: each run logs `run_id`, `mandate_id`, `policy_snapshot`, output, and timestamp.
- **Explainability**: each recommended pool includes explicit rule-based reasons for governance review.

## 🏛️ Why Protocols/DAOs Should Use This

Large treasury organizations (e.g., Aave-scale DAOs and similarly governed protocols) care less about "AI magic" and more about **governance safety, reproducibility, and accountability**.  
RDA aligns with those requirements:

- **Governance first**: recommendations are anchored to approved mandate policy, not ad-hoc operator judgment.
- **Operational speed with controls**: compresses research/proposal cycle from days to a single policy-driven run.
- **Institutional auditability**: explicit policy snapshot + recommendation output per run provides strong compliance artifacts.
- **Transparent risk posture**: clear filters, deterministic scoring, and per-pool rationale make proposals reviewable by risk committees.
- **Safe adoption path**: DAOs can start in proposal-only mode, then adopt Phase 2 execution controls when governance is ready.

## 🔮 Future Scope

Future work remains focused on **execution safety** and **enterprise trust layers**:

- Multisig/timelock execution modules under explicit mandate limits
- Circuit-breaker and emergency runbooks
- Tamper-evident audit chains with optional on-chain anchoring
- Monitoring and reallocation triggers with governance approval workflows

## 🚀 Deployment Guide

### Local Development
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Start all agents in separate terminals (for ASI Chat flow)
python main.py                          # Terminal 1 — Treasury Agent (ASI Chat)
python agents/discovery_agent/agent.py  # Terminal 2 — Discovery Agent (intent extraction + pool fetch)
python agents/risk_agent/agent.py       # Terminal 3 — Risk Agent
python agents/decision_agent/agent.py   # Terminal 4 — Decision Agent

# 3. Test in ASI Chat interface
```

**🎯 Ready to revolutionize DeFi investing? Start your autonomous investment journey today!**