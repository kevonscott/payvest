# payvest — Pay vs Invest Analyzer

A web app to compare paying down loans vs investing, or a split strategy, over a chosen time horizon. Features include debt payoff strategies, investment fees, and Monte Carlo simulation for risk analysis.

## Features

### Core Analysis
- Enter multiple loans (balance, APR, term in months)
- Investment options: initial balance, expected annual return, annual fees
- Total monthly budget: simulator allocates required loan payments first, then splits any extra between loans and investing
- Three scenarios: loan-first, invest-first, and split (configurable percentage)
- If loans are paid off early, freed cash flow is redirected to investments
- Yearly breakdowns: loan interest/principal paid, balances, invested totals, and returns
- Recommendation based on final net worth (investments minus remaining debts)

### Advanced Features
- **Debt Payment Strategies**: Proportional (even split) is implemented. Avalanche (highest APR first) and snowball (lowest balance first) are planned but not yet available.
- **Investment Fees**: Model annual management fees (0–3%)
- **Monte Carlo Simulation**: Run probabilistic analysis with configurable return volatility (default 15%)
- **Risk Analysis**: View probability of positive net worth, confidence intervals (10th–90th percentile), and median outcomes

## Run locally with uv

Install and run using the modern Python package manager `uv`:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and run
uv pip install -e .[dev]
uv run python -m flask --app app run --debug --port 5001
```

Or with traditional venv + pip:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .[dev]
python -m flask --app app run --debug
```

Open http://127.0.0.1:5001 (or :5000 for traditional setup)

## Tests

```bash
uv run pytest -v
# or: python -m pytest -v
```

## Usage Tips

1. **Use realistic inputs**: Enter your actual loan balances, APRs, and months remaining
2. **Total monthly budget**: This is the amount you have available for all loan payments and investing each month
3. **Debt strategy**: Avalanche saves the most on interest; snowball provides psychological wins; proportional splits extra evenly. **NOTE**: ONLY **proportional** is currently supported at the moment.
4. **Monte Carlo**: Run 1000+ simulations to see outcome ranges with realistic market volatility (default 15%)
5. **Fees matter**: Even 1% annual fees can significantly impact long-term returns

## Model Assumptions

- **Compounding**: Interest and returns compound monthly
- **Volatility**: Monte Carlo uses a normal distribution for annual returns
- **Fees**: Applied as annual percentage of investment balance
- **Behavior**: Assumes disciplined execution of chosen strategy
- **Correlations**: Returns are independent; does not model correlation between market performance and employment/income
- **Inflation**: Not explicitly modeled; adjust nominal rates as needed

## Next Steps

- Export results to CSV for detailed analysis (planned)
