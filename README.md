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
- `core/protocol_registry.py`: canonical protocol metadata and validation helpers.
- `core/mandate.py`: mandate load/save/expiry checks; blocks recommendations on expired mandate.
- `agents/discovery_agent/discovery_logic.py`: policy-driven pool filtering, registry-aware protocol and chain checks.
- `agents/risk_agent/agent.py` + treasury-level risk enforcement: policy `risk.min_score` and `risk.max_level` hard filters.
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

```
User (ASI Chat) 
   ↓ natural language
ASI:One (NLP router / intent extraction)
   ↓ intent (structured)
Discovery Agent (uAgent) ←→ DeFi data sources (DeFiLlama, DexScreener, subgraphs)
   ↓ candidate pools
Risk Agent (uAgent + MeTTa rules)
   ↓ risk-scored pools
Decision Agent (uAgent)
   ↓ final recommendation
ASI:One → User (explainable response)
```

### Key Components:

- **🔧 uAgents** — Small autonomous agents responsible for one domain (Discovery, Risk, Decision)
- **🌐 Agentverse listing** — Makes your advisor discoverable for others
- **🔐 Fetch Network** — DID-based identity + encrypted messaging for agent-to-agent communications
- **🧠 MeTTa** — Structured knowledge & rule engine for reasoning, provenance, and explainability
- **💬 ASI:One** — Conversational front-end and intent router

## 🔄 End-to-end Flow

### Example Treasury Request:
> "Generate recommendation under mandate `test-mandate-001` for $100,000 USDC."

### System Processing:

1. **Treasury Agent** loads mandate by `mandate_id`
2. Mandate policy is validated (`TreasuryPolicy` + protocol registry)
3. **Discovery Agent** fetches pools and applies policy constraints
4. **Risk filtering** enforces `risk.min_score` and `risk.max_level`
5. **Decision Agent** computes deterministic ranking score
6. **Explanation layer** adds "why selected" to each recommendation
7. **Allocation engine** computes split + expected portfolio APY
8. **Proposal template** generates governance draft markdown
9. **Audit logger** appends immutable run record (MVP file append)

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

4. **Set up environment variables**
   ```bash
   export ASI_ONE_API_KEY="your_api_key_here"
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

- **ASI:One** — Natural language → intent router and chat UX
- **uAgents** — Python micro-agents using agent runtime (send/receive messages)
- **Agentverse** — Registry & discovery for agents
- **Fetch Network** — DID identities, signed/encrypted agent messaging
- **MeTTa** — Rule/knowledge system for explainable reasoning and provenance
- **Data Sources**: DeFiLlama, DexScreener, subgraphs, CoinGecko (prices), Etherscan (verification)

## 💬 Interaction Examples

### User Input:
> "Invest $1000 in a way to get at least 8% APY. I prefer stablecoins and low risk."

### System Processing:
```json
{
  "intent": "invest",
  "amount": 1000,
  "currency": "USD",
  "constraints": {
    "min_apy": 0.08,
    "tokens": ["USDC", "USDT"],
    "risk": "low"
  }
}
```

### Final Response (ASI Chat):
```
🎯 **INVESTMENT RECOMMENDATION** 🎯

📊 **Recommended Pool:** `0x1234...abcd`

⚠️ **Risk Assessment:** 🟢 Low (Score: 85/100)

💡 **Recommendations:**
• ✅ Contract verified - low risk
• ✅ Audit completed - trustworthy
• ✅ High liquidity - stable investment

💰 **Investment Amount:** $1000
🎯 **Your Preference:** Low

✅ **Great Choice:** This pool has low risk and is suitable for conservative investments.

Expected APY: 8.2%
Pool address: 0x1234...abcd
Liquidity: $1.2M

---
*Powered by DeFi Risk Advisor*
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

# 2. Start all agents in separate terminals
python main.py                    # Main Agent (ASI Chat)
python agents/discovery_agent/agent.py  # Discovery Agent
python agents/risk_agent/agent.py       # Risk Agent
python agents/decision_agent/agent.py   # Decision Agent, not needed now

# 3. Test in ASI Chat interface
```

**🎯 Ready to revolutionize DeFi investing? Start your autonomous investment journey today!**