# Slim Backtrader
This is a fork of the original [backtrader](https://github.com/mementum/backtrader) - slimmed down. 
Unnecessary features and updating the package to ensure compatibility with newer Python versions and dependencies.

Aims of this project:
- Slim down unnecessary features
- Improve performance
- Update aged implementations

For now the focus is:
- Code clean-up: remove unncessary imports
- Syntax update: make it more modern
- Remove deprecated integrations (i.e. pyfolio, IbPy, comtypes) 
- Remove interactive plotting: the backend is heavy and slow
- Improved support for parallel processing

This is an ongoing process that has just started and will hopefully bring life to an excellent project.

Feel free to contribute!

---

## Features

A Python-based platform for live trading and backtesting, featuring:

- **Live Data Feed and Trading**:
  - Interactive Brokers (requires `IbPy`, significantly benefits from installed `pytz`)
  - *Visual Chart* (requires fork of `comtypes` until pull request integration, benefits from `pytz`)
  - *Oanda* (requires `oandapy`, REST API only – v20 streaming not supported)

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
  - Extensive built-in indicators (full list available [here](http://www.backtrader.com/docu/indautoref.html))
  - *TA-Lib* integration (requires Python *ta-lib*)
  - Easy creation of custom indicators

- **Analyzers and Utilities**:
  - Built-in analyzers (e.g., TimeReturn, Sharpe Ratio, SQN)
  - `pyfolio` integration (**deprecated**)

- **Broker Simulation**:
  - Supports multiple order types: *Market*, *Close*, *Limit*, *Stop*, *StopLimit*, *StopTrail*, *StopTrailLimit*, *OCO*, bracket orders, slippage, volume filling strategies, continuous cash adjustments for futures-like instruments

- **Automated Staking**: 
  - Sizers for position sizing

- **Cheating Modes**:
  - Cheat-on-Close
  - Cheat-on-Open

- **Schedulers and Calendars**
- **Plotting** *(requires matplotlib)*

---

## Installation

Backtrader is self-contained with minimal external dependencies (plotting requires `matplotlib`).

Currently, the installation takes place by navigating to the clone of this repository and running: 

```shell script
pip install -e
```

## Python Compatibility

Works with:

- Python version `>= 3.10`

## Documentation
- **Original backtrader repository**: https://github.com/mementum/backtrader
- **Blog**: [Backtrader Blog](http://www.backtrader.com/blog)
- **Docs**: [Full Documentation](http://www.backtrader.com/docu)
- **Indicators Reference**: [List of Built-in Indicators (122)](http://www.backtrader.com/docu/indautoref.html)


## Version Numbering

Follows format `X.Y.Z.I` where:

- `X`: Major version (stable, unless significant overhauls, e.g., numpy integration).
- `Y`: Minor version (new features or incompatible API changes).
- `Z`: Revision updates (documentation tweaks, minor changes, bug fixes).
- `I`: Number of built-in indicators.

---
