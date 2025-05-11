# backtrader

> Copyright (c) 2025 backtrader contributors

Backtrader is a robust Python framework for backtesting, algorithmic trading, and
quantitative analysis. It enables you to create, test, and run trading strategies across
multiple markets and timeframes, supporting historical data, live feeds, indicators,
sizers, commissions, optimizers, and much more.

## Key Features

- Fast, flexible backtesting for multiple strategies and assets
- Support for historical data, live feeds, and multiple timeframes
- Extensible indicator system and TA-Lib integration
- Broker support: Interactive Brokers, Oanda, Visual Chart, and more
- Strategy optimization with multiple parameters
- Analyzers, observers, sizers, plotters, and visualization tools
- Modular, object-oriented architecture
- Compatible with Python 3.7+

## Directory Structure

```asciidoc
backtrader/           # Main framework source code
  analyzers/          # Performance and risk analyzers
  brokers/            # Brokers and simulations
  feeds/              # Data feeds (historical, live, pandas, etc)
  indicators/         # Technical indicators
  observers/          # Metric observers
  plot/               # Plotting and visualization
  sizers/             # Position sizing management
  stores/             # External broker integration
  strategies/         # Example strategies
  studies/            # Studies and contributions
  utils/              # Internal utilities
contrib/              # Community extensions and examples
samples/              # Usage examples and demo scripts
tests/                # Automated tests
```

## Installation

It is recommended to use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For development:

```bash
pip install -r requirements-dev.txt
```

## Basic Usage

```python
import backtrader as bt

class MyStrategy(bt.Strategy):
    def next(self):
        if not self.position:
            self.buy()
        elif self.data.close[0] > self.data.close[-1]:
            self.sell()

cerebro = bt.Cerebro()
cerebro.addstrategy(MyStrategy)
data = bt.feeds.YahooFinanceData(dataname='AAPL', fromdate=..., todate=...)
cerebro.adddata(data)
cerebro.run()
cerebro.plot()
```

## Development

- **Lint:** `make lint` (uses ruff)
- **Format:** `make format` (uses black)
- **Tests:** `make test` (uses pytest)
- **Build:** `make build` (sdist and wheel)
- **Clean:** `make clean`

See the `Makefile` for more commands.

## TODOs

- [ ] Review and update all packaging files (`setup.py`, `pyproject.toml`, `MANIFEST.in`)
- [ ] Fix all linter/formatter/test issues
- [ ] Modernize build system and CI
- [ ] Validate documentation and examples
- [ ] Prepare and test release artifacts
- [ ] Ensure all public code is documented and ≤ 90 columns
- [ ] Update version numbers and changelog for next release
- [ ] Tag release and perform PyPI upload (dry-run first)
- [ ] Maintain a running log of all changes, decisions, and issues
- [ ] Archive all relevant docs and context for future reference

## License

GPL-3.0. See the [LICENSE](LICENSE) file for details.

## Community and Contact

- Website: [backtrader.com](https://www.backtrader.com/)
- GitHub: [github.com/mementum/backtrader](https://github.com/mementum/backtrader)
- Questions: Use [Stack Overflow](https://stackoverflow.com/questions/tagged/backtrader)

## Contributing

Contributions are welcome! Please follow these guidelines:

- Clean, tested, and documented code (Google docstring style, ≤ 90 columns)
- Use branches for PRs and clearly describe your changes
- Update the README and examples if needed
- Respect the license and do not include secrets or sensitive data

---

For more details, see the [official documentation](https://www.backtrader.com/docu/).
