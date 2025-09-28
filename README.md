# 🎯 Robo DeFi Advisor — ASI-Powered Autonomous Investment Assistant

[![ASI Alliance](https://img.shields.io/badge/ASI%20Alliance-Powered-blue)](https://asi.foundation/)
[![uAgents](https://img.shields.io/badge/uAgents-Framework-green)](https://github.com/fetchai/uagents)
[![AgentVerse](https://img.shields.io/badge/AgentVerse-Platform-orange)](https://agentverse.ai/)
[![Python](https://img.shields.io/badge/Python-3.13+-yellow)](https://python.org/)

> **Make Web3 investing trivial**: Tell the system what you want in plain English and the ASI agent network finds, evaluates, and recommends the best on-chain investment for you.

## 📋 Table of Contents

- [Project Goal](#-project-goal)
- [High-level Use Case](#-high-level-use-case)
- [Architecture & Components](#-architecture--components)
- [End-to-end Flow](#-end-to-end-flow)
- [Quick Start](#-quick-start)
- [Agent Configuration](#-agent-configuration)
- [Beautiful Output Format](#-beautiful-output-format)
- [Protocols & Tech Stack](#-protocols--tech-stack)
- [Interaction Examples](#-interaction-examples)
- [Security, Privacy & Trust](#-security-privacy--trust)
- [Future Scope](#-future-scope)
- [Deployment Guide](#-deployment-guide)
- [Troubleshooting](#-troubleshooting)
- [Contributors & License](#-contributors--license)

## 🎯 Project Goal

**Make investment in Web3 with negligible effort.**

A user types something like:
> "I want to invest $1000 and get at least 8% APY."

The Robo DeFi Advisor (RDA) will:

✅ **Parse the intent** from natural language  
✅ **Discover candidate pools** across DEX/aggregator datasets  
✅ **Evaluate risk** and verify constraints  
✅ **Return explainable options** (pool addresses, yield estimate, risk metrics)  
✅ **Provide beautiful, user-friendly responses** in ASI Chat  

**Primary KPI**: Increase user adoption by reducing complexity — users don't need to learn pools, fees, or risk metrics. They only describe intent.

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

### Example User Request:
> "Invest $1,000 in a way to get at least 8% APY, prefer low risk, USDC/USDT only."

### System Processing:

1. **ASI:One** → Parse intent → Produce structured intent object
2. **Discovery Agent** → Query DeFiLlama/DexScreener → Return pools matching criteria
3. **Risk Agent** → Use MeTTa knowledge-graph + metrics → Score/filter pools
4. **Decision Agent** → Reconcile constraints + risk scores + APY → Choose optimal pool
5. **ASI Chat** → Send beautiful explanation + pool address + rationale

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

## 🔐 Security, Privacy & Trust

- **🔑 DID-based identities** (Fetch Network): Agents sign their messages for authenticity verification
- **🔒 Encrypted messaging**: Agent handoffs carry sensitive details encrypted end-to-end
- **📊 Provenance**: Every metric is attached to a source (e.g., DeFiLlama + timestamp)
- **👀 Read-only analysis**: Default system only recommends, doesn't execute without explicit approval
- **✍️ User consent**: Any transaction requires explicit wallet signature (never holds private keys)

## 🔮 Future Scope

### Phase 1 (Current - MVP)
- ✅ Natural language input processing
- ✅ Pool discovery and filtering
- ✅ Risk analysis and scoring
- ✅ Beautiful recommendation output

### Phase 2 (Next)
- 🚧 **Single-click transaction flow**: Prepare transactions and show "Sign & Execute" UX
- 🚧 **Enhanced risk models**: More sophisticated risk scoring algorithms
- 🚧 **Multi-chain support**: Expand beyond single blockchain

### Phase 3 (Advanced)
- 🔮 **Continuous portfolio management**: Periodic rebalancing agents
- 🔮 **Multi-user shared strategies**: Publish strategies on Agentverse
- 🔮 **On-chain execution**: Executor agents with guardrails & multisig
- 🔮 **Governance & social trading**: Follow curated strategies from vetted stewards

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