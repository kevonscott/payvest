# Constants for default values
DEFAULT_ANNUAL_RETURN: float = 0.06
DEFAULT_ANNUAL_FEE_PCT: float = 0.0  # Annual percentage fee
DEFAULT_MONTE_CARLO_RUNS: int = 1000  # number of simulations for probabilistic analysis
DEFAULT_RETURN_VOLATILITY: float = 0.15  # annual standard deviation for returns (e.g., 15%)
DEFAULT_SPLIT_PCT_INVEST: float = 0.5  # for split scenario: portion of extra_budget to investing (0..1)
DEFAULT_YEARS: int = 10

# Domain constants
MONTHS_PER_YEAR: float = 12.0
LOAN_BALANCE_EPSILON: float = 1e-8  # threshold for considering a loan paid off
BUDGET_EPSILON: float = 1e-6  # tolerance for minimum payment check