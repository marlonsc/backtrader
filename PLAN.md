# 🪐 Agentic Trading System

A modular, agentic framework for building, testing, and deploying trading strategies.

This project is designed to be understandable and extensible — with a focus on decision explainability, reproducibility via backtesting, and smooth integration with tools like Interactive Brokers.

> Built with ❤️ and `pydantic-ai` to enable structured, agentic tools that reason over market data like any other job processing system.

---

## 🧠 System Overview

The system is composed of modular agents that:

- Observe streaming or replayed market data  
- Make structured trade decisions (e.g. `buy_to_open`)  
- Annotate their reasoning (e.g. `"momentum breakout at 10:05 AM"`)  
- Store execution and decision logs for backtesting, review, or optimization  

---

## 📁 Project Structure (WIP)

```
agentic-trading/
├── agents/               # LongAgent, ShortAgent, BreakoutAgent, etc.
├── tools/                # Pydantic AI tools (wrap IB API, market data fetchers, etc.)
├── replay/               # Replay engine for historical market simulation
├── memory/               # pgvector-backed decision logs and embeddings
├── command_center/       # Optional UI or CLI monitoring
├── tests/
├── README.md
└── pyproject.toml
```

---

## 🚀 Getting Started

1. **Install dependencies**

```bash
pip install -e .[dev]
```

2. **Set up Postgres + pgvector**

Use Docker, Railway, or a managed Postgres service.

3. **Create your first agent**

```python
from agents.base import BaseAgent

class MyMomentumAgent(BaseAgent):
    def decide(self, market_tick) -> TradeDecision:
        # Analyze tick, return structured output
        ...
```

4. **Run in replay mode**

```bash
python replay/main.py --strategy my_momentum_agent --data data/SPY_2023.csv
```

---

## 🧪 Modes of Operation

| Mode        | Description                                  |
|-------------|----------------------------------------------|
| Replay      | Simulate historical trades for a given agent |
| Paper Trade | Live market data, no real money              |
| Live Trade  | Hooked into IB for real execution            |

---

## 🔧 Pydantic AI Tools (Planned)

Tools are typed wrappers around external capabilities. Think of them like tools in LangChain or agents in Pulsar.

- `InteractiveBrokersClientTool`: submit/cancel/monitor orders  
- `MarketDataTool`: subscribe to live or historical data  
- `ReportGeneratorTool`: summarize positions, risk, and P&L  
- `VectorLoggerTool`: annotate decisions for vector search  

All tools conform to the `ToolCall` / `ToolResponse` pattern from Pydantic AI.

---

## 📚 Roadmap

- [ ] Replay engine w/ pluggable agent strategies  
- [ ] Live data support (via Alpaca or IB)  
- [ ] Vector memory + annotation  
- [ ] Pydantic AI tool abstraction for trading verbs  
- [ ] Daily/weekly reporting CLI  
- [ ] Panel-based command center UI  

---

## 🧙‍♂️ Philosophy

Trading strategies are data-driven jobs. They should be:

- **Composable** — written like small tools, tested independently  
- **Explainable** — log *why* each decision was made  
- **Backtestable** — run on historical data in deterministic fashion  
- **Agentic** — can participate in multi-step workflows or meta-strategies  

---

## 📜 License

MIT. Trade responsibly.
