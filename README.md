# backtrader

This is a fork of the original [backtrader](https://github.com/mementum/backtrader) —
slimmed down. The project aims to remove unnecessary features and update the package
to ensure compatibility with newer Python versions and dependencies.

## Project Aims

- Slim down unnecessary features
- Improve performance
- Update aged implementations
- Code clean-up: remove unnecessary imports
- Syntax update: make it more modern
- Remove deprecated integrations (e.g., pyfolio, IbPy, comtypes)
- Remove interactive plotting: the backend is heavy and slow
- Improved support for parallel processing

This is an ongoing process that has just started and will hopefully bring life to an
excellent project. Feel free to contribute!

---

## Features

A Python-based platform for live trading and backtesting, featuring:

- **Live Data Feed and Trading**:
  - Interactive Brokers (requires `IbPy`, benefits from installed `pytz`)
  - Visual Chart (requires fork of `comtypes` until pull request integration, benefits from `pytz`)
  - Oanda (requires `oandapy`, REST API only — v20 streaming not supported)
- **Data Sources**:
  - CSV/files, online sources, or via *pandas* and *blaze*
- **Data Management**:
  - Filters (e.g., daily bars into intraday chunks, Renko bricks)
  - Multiple data feeds and strategies supported
  - Multiple simultaneous timeframes
  - Integrated resampling and replaying capabilities
- **Backtesting Modes**:
  - Step-by-step execution or all-at-once (strategy evaluation exception)
- **Indicators**:
  - Extensive built-in indicators ([full list](http://www.backtrader.com/docu/indautoref.html))
  - TA-Lib integration (requires Python *ta-lib*)
  - Easy creation of custom indicators
- **Analyzers and Utilities**:
  - Built-in analyzers (e.g., TimeReturn, Sharpe Ratio, SQN)
  - `pyfolio` integration (**deprecated**)
- **Broker Simulation**:
  - Supports multiple order types: Market, Close, Limit, Stop, StopLimit, StopTrail,
    StopTrailLimit, OCO, bracket orders, slippage, volume filling strategies, continuous cash
    adjustments for futures-like instruments
- **Automated Staking**:
  - Sizers for position sizing
- **Cheating Modes**:
  - Cheat-on-Close
  - Cheat-on-Open
- **Schedulers and Calendars**
- **Plotting** (requires matplotlib)

---

## Installation

Backtrader is self-contained with minimal external dependencies (plotting requires
`matplotlib`).

Install by navigating to the clone of this repository and running:

```shell
pip install -e .
```

---

## Python Compatibility

Works with:

- Python version `>= 3.10`

---

## Documentation

- **Original backtrader repository**: <https://github.com/mementum/backtrader>
- **Blog**: [Backtrader Blog](http://www.backtrader.com/blog)
- **Docs**: [Full Documentation](http://www.backtrader.com/docu)
- **Indicators Reference**: [List of Built-in Indicators (122)](http://www.backtrader.com/docu/indautoref.html)

---

## Version Numbering

Follows format `X.Y.Z.I` where:

- `X`: Major version (stable, unless significant overhauls, e.g., numpy integration)
- `Y`: Minor version (new features or incompatible API changes)
- `Z`: Revision updates (documentation tweaks, minor changes, bug fixes)
- `I`: Number of built-in indicators

---

## Navigation

- [🏠 Root Directory](./README.md)
- [⬆️ Parent Directory (workspace)](../README.md)

### Subdirectories

- [Tutorials](Tutorials/README.md) — Contains tutorial code and examples
- [arbitrage](arbitrage/README.md) — Contains arbitrage strategy implementations
- [backtest](backtest/README.md) — Contains backtesting functionality
- [backtrader](backtrader/README.md) — Directory containing backtrader related files
- [contrib](contrib/README.md) — Contains contributed code
- [datas](datas/README.md) — Contains data files
- [logs](logs/README.md) — Contains log files
- [outcome](outcome/README.md) — Directory containing outcome related files
- [prompts](prompts/README.md) — Directory containing prompts related files
- [qmtbt](qmtbt/README.md) — Directory containing qmtbt related files
- [reference](reference/README.md) — Directory containing reference related files
- [samples](samples/README.md) — Contains sample code and examples
- [sandbox](sandbox/README.md) — Contains experimental or sandbox code
- [scripts](scripts/README.md) — This directory contains files related to scripts
- [src](src/README.md) — Contains source code
- [strategies](strategies/README.md) — Contains trading strategy implementations
- [tests](tests/README.md) — Contains test files and test utilities
- [tools](tools/README.md) — Contains tools and utilities
- [turtle](turtle/README.md) — Directory containing turtle related files
- [xtquant](xtquant/README.md) — Directory containing xtquant related files

---

## Directory Summary

This directory contains 31 files and 20 subdirectories.

### File Types

- .py: 6 files
- .png: 6 files
- .ipynb: 4 files
- .txt: 4 files
- .md: 3 files
- .sh: 2 files
- .rst: 1 file
- .code-workspace: 1 file
- .toml: 1 file
- .ini: 1 file
