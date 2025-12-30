from dataclasses import dataclass
from typing import List, Dict, Tuple
import random
from .constants import (
    DEFAULT_ANNUAL_FEE_PCT,
    DEFAULT_SPLIT_PCT_INVEST,
    DEFAULT_MONTE_CARLO_RUNS,
    DEFAULT_RETURN_VOLATILITY,
    MONTHS_PER_YEAR,
    LOAN_BALANCE_EPSILON,
    BUDGET_EPSILON,
)


@dataclass
class LoanInput:
    """
    Represents a single loan for simulation.
    """

    principal: float
    apr: float  # annual percentage rate, e.g., 0.05 for 5%
    term_months: int


@dataclass
class InvestmentInput:
    """
    Investment parameters for simulation.
    """

    initial_amount: float
    monthly_contribution: float
    annual_return: float  # e.g., 0.06 for 6%
    annual_fee_pct: float = DEFAULT_ANNUAL_FEE_PCT


@dataclass
class SimulationConfig:
    """
    Simulation configuration.
    """

    loans: List[LoanInput]
    investment: InvestmentInput
    monthly_budget: (
        float  # total monthly budget available for loans and investing
    )
    horizon_years: int
    split_pct_invest: float = DEFAULT_SPLIT_PCT_INVEST
    # "avalanche", "snowball", "proportional"
    debt_strategy: str = "proportional"
    monte_carlo_runs: int = DEFAULT_MONTE_CARLO_RUNS
    return_volatility: float = DEFAULT_RETURN_VOLATILITY


@dataclass
class YearlyBreakdown:
    """
    Yearly summary for a scenario.
    """

    year: int
    loan_interest_paid: float
    loan_principal_paid: float
    loan_balance_end: float
    invested_total: float
    investment_returns: float
    investment_balance_end: float


@dataclass
class MonteCarloResult:
    """
    Monte Carlo simulation results for a scenario.
    """

    name: str
    mean_net_worth: float
    median_net_worth: float
    percentile_10: float
    percentile_90: float
    success_probability: float  # probability of positive net worth
    yearly_medians: List[YearlyBreakdown]


@dataclass
class ScenarioResult:
    """
    Results for a single scenario.
    """

    name: str
    yearly: List[YearlyBreakdown]
    final_net_worth: float  # investment balance minus remaining loan balances
    loans_remaining_balance: float
    investment_balance: float
    monte_carlo: MonteCarloResult | None = None


def _monthly_rate(apr: float) -> float:
    """
    Calculate the monthly interest rate from annual percentage rate (APR).

    Parameters
    ----------
    apr
        Annual percentage rate (e.g., 0.05 for 5%).
    """
    return apr / MONTHS_PER_YEAR


def _amortized_payment(
    principal: float, monthly_rate: float, term_months: int
) -> float:
    """
    Calculate the fixed monthly payment for a fully amortizing loan.

    Parameters
    ----------
    principal
        Initial loan amount.
    monthly_rate
        Monthly interest rate.
    term_months
        Number of monthly payments.

    Returns
    -------
    Monthly payment amount.
    """
    if principal <= 0:
        return 0.0
    if monthly_rate == 0:
        return principal / term_months
    numer = monthly_rate * (1 + monthly_rate) ** term_months
    denom = (1 + monthly_rate) ** term_months - 1
    return principal * numer / denom


def _simulate_single_run(
    cfg: SimulationConfig,
    allocate_invest: float,
    use_stochastic_returns: bool = False,
) -> Tuple[List[YearlyBreakdown], float, float]:
    """
    Simulate month-by-month over the investment horizon.

    If loans are fully paid early, redirect all freed payments to investing
    until horizon.

    Parameters
    ----------
    cfg
        Simulation configuration.
    allocate_invest
        Fraction (0..1) of extra_budget allocated to investing (remainder
        to loans).
    use_stochastic_returns
        If True, use stochastic investment returns (Monte Carlo).

    Returns
    -------
    Yearly breakdowns, remaining loan balance, final investment balance.
    """
    months = cfg.horizon_years * 12

    # Only proportional strategy is implemented
    if cfg.debt_strategy != "proportional":
        raise NotImplementedError(
            f"Debt strategy '{cfg.debt_strategy}' is not implemented. Only 'proportional' is supported."
        )

    # Prepare loan states
    loan_balances = [loan.principal for loan in cfg.loans]
    loan_rates = [_monthly_rate(loan.apr) for loan in cfg.loans]
    loan_terms = [loan.term_months for loan in cfg.loans]
    base_payments = [
        _amortized_payment(p, r, t) if t > 0 else 0.0
        for p, r, t in zip(loan_balances, loan_rates, loan_terms)
    ]

    # Check that the monthly budget is sufficient to cover minimum loan payments
    min_total_payment = sum(base_payments)
    if cfg.monthly_budget < min_total_payment - BUDGET_EPSILON:
        raise ValueError(
            f"Monthly budget (${cfg.monthly_budget:,.2f}) is less than the required minimum loan payments (${min_total_payment:,.2f}). "
            "Please increase your monthly budget to at least cover the minimum payments."
        )

    investment_balance = cfg.investment.initial_amount

    yearly: List[YearlyBreakdown] = []

    # Month-by-month simulation with dynamic investment contributions and yearly breakdown
    months = cfg.horizon_years * int(MONTHS_PER_YEAR)
    monthly_fee = cfg.investment.annual_fee_pct / MONTHS_PER_YEAR
    if use_stochastic_returns:
        annual_r = random.gauss(
            cfg.investment.annual_return, cfg.return_volatility
        )
    else:
        annual_r = cfg.investment.annual_return
    monthly_return = annual_r / 12.0
    # Track yearly stats
    year_interest_paid = 0.0
    year_principal_paid = 0.0
    year_invested_total = 0.0
    year_investment_returns = 0.0
    freed_payments = 0.0
    for m in range(1, months + 1):
        active_indices = [
            i for i, bal in enumerate(loan_balances) if bal > LOAN_BALANCE_EPSILON
        ]
        min_loan_payments = sum(base_payments[i] for i in active_indices)
        discretionary_budget = cfg.monthly_budget - min_loan_payments
        discretionary_budget = max(0.0, discretionary_budget)
        # Determine investment contribution logic by scenario
        if allocate_invest == 1.0:
            # Invest-first: invest discretionary budget (monthly budget minus min loan payments)
            invest_contrib = discretionary_budget
        elif allocate_invest == 0.0:
            # Loan-first: do not invest until all loans are paid off
            if len(active_indices) == 0:
                invest_contrib = cfg.monthly_budget
            else:
                invest_contrib = 0.0
        else:
            # Split: invest split portion plus freed payments, but after all loans are paid, invest only the full budget
            if len(active_indices) == 0:
                invest_contrib = cfg.monthly_budget
            else:
                invest_contrib = (
                    discretionary_budget * allocate_invest + freed_payments
                )
        extra_to_loans = [0.0 for _ in loan_balances]
        if allocate_invest < 1.0 and len(active_indices) > 0:
            extra_total = discretionary_budget * (1 - allocate_invest)
            for i in active_indices:
                extra_to_loans[i] = extra_total / len(active_indices)
        # Apply base payments and extra payments
        for i in active_indices:
            rate = loan_rates[i]
            interest = loan_balances[i] * rate
            principal_payment = max(0.0, base_payments[i] - interest)
            principal_applied = min(
                loan_balances[i], principal_payment + extra_to_loans[i]
            )
            loan_balances[i] -= principal_applied
            year_interest_paid += interest
            year_principal_paid += principal_applied
            # If loan paid off this month, add its base payment to freed_payments
            if loan_balances[i] < LOAN_BALANCE_EPSILON and base_payments[i] > 0:
                freed_payments += base_payments[i]
        # Update investment balance monthly
        year_invested_total += invest_contrib
        prev_balance = investment_balance
        investment_balance = (
            (investment_balance + invest_contrib)
            * (1 + monthly_return)
            * (1 - monthly_fee)
        )
        year_investment_returns += investment_balance - (
            prev_balance + invest_contrib
        )
        # Yearly breakdown
        if m % int(MONTHS_PER_YEAR) == 0:
            yearly.append(
                YearlyBreakdown(
                    year=m // int(MONTHS_PER_YEAR),
                    loan_interest_paid=year_interest_paid,
                    loan_principal_paid=year_principal_paid,
                    loan_balance_end=sum(loan_balances),
                    invested_total=year_invested_total,
                    investment_returns=year_investment_returns,
                    investment_balance_end=investment_balance,
                )
            )
            year_interest_paid = 0.0
            year_principal_paid = 0.0
            year_invested_total = 0.0
            year_investment_returns = 0.0
    loans_remaining_balance = sum(loan_balances)
    return yearly, loans_remaining_balance, investment_balance


def _run_monte_carlo(
    cfg: SimulationConfig, allocate_invest: float
) -> MonteCarloResult:
    """
    Run Monte Carlo simulation for a given allocation strategy.

    Parameters
    ----------
    cfg
        Simulation configuration.
    allocate_invest
        Fraction (0..1) of extra_budget allocated to investing.

    Returns
    -------
    Monte Carlo simulation results.
    """
    final_net_worths = []
    all_yearly_results = []

    for _ in range(cfg.monte_carlo_runs):
        yearly, loans_bal, inv_bal = _simulate_single_run(
            cfg, allocate_invest, use_stochastic_returns=True
        )
        final_net_worth = inv_bal - loans_bal
        final_net_worths.append(final_net_worth)
        all_yearly_results.append(yearly)

    # Calculate statistics
    final_net_worths.sort()
    mean_net_worth = sum(final_net_worths) / len(final_net_worths)
    median_net_worth = final_net_worths[len(final_net_worths) // 2]
    percentile_10 = final_net_worths[int(0.1 * len(final_net_worths))]
    percentile_90 = final_net_worths[int(0.9 * len(final_net_worths))]
    success_probability = sum(1 for nw in final_net_worths if nw > 0) / len(
        final_net_worths
    )

    # Calculate median yearly breakdown
    yearly_medians = []
    if all_yearly_results:
        for year in range(cfg.horizon_years):
            year_data = [
                result[year]
                for result in all_yearly_results
                if len(result) > year
            ]
            if year_data:
                # Take median values for each field
                median_breakdown = YearlyBreakdown(
                    year=year + 1,
                    loan_interest_paid=sorted(
                        [y.loan_interest_paid for y in year_data]
                    )[len(year_data) // 2],
                    loan_principal_paid=sorted(
                        [y.loan_principal_paid for y in year_data]
                    )[len(year_data) // 2],
                    loan_balance_end=sorted(
                        [y.loan_balance_end for y in year_data]
                    )[len(year_data) // 2],
                    invested_total=sorted(
                        [y.invested_total for y in year_data]
                    )[len(year_data) // 2],
                    investment_returns=sorted(
                        [y.investment_returns for y in year_data]
                    )[len(year_data) // 2],
                    investment_balance_end=sorted(
                        [y.investment_balance_end for y in year_data]
                    )[len(year_data) // 2],
                )
                yearly_medians.append(median_breakdown)

    return MonteCarloResult(
        name="",  # Will be set by caller
        mean_net_worth=mean_net_worth,
        median_net_worth=median_net_worth,
        percentile_10=percentile_10,
        percentile_90=percentile_90,
        success_probability=success_probability,
        yearly_medians=yearly_medians,
    )


def run_scenarios(cfg: SimulationConfig) -> Dict[str, ScenarioResult]:
    """
    Run all scenario strategies: loan-first, invest-first, and split.

    Parameters
    ----------
    cfg
        Simulation configuration.

    Returns
    -------
    Results for each scenario key.
    """
    results: Dict[str, ScenarioResult] = {}

    scenarios = [
        ("loan_first", 0.0, "Loan-first"),
        ("invest_first", 1.0, "Invest-first"),
        (
            "split",
            cfg.split_pct_invest,
            f"Split ({int(cfg.split_pct_invest * 100)}% invest)",
        ),
    ]

    for key, allocate_invest, name in scenarios:
        # Run deterministic simulation
        yearly, loans_bal, inv_bal = _simulate_single_run(
            cfg, allocate_invest, use_stochastic_returns=False
        )

        # Run Monte Carlo if requested
        monte_carlo_result = None
        if cfg.monte_carlo_runs > 1:
            monte_carlo_result = _run_monte_carlo(cfg, allocate_invest)
            monte_carlo_result.name = name

        results[key] = ScenarioResult(
            name=name,
            yearly=yearly,
            loans_remaining_balance=loans_bal,
            investment_balance=inv_bal,
            final_net_worth=inv_bal - loans_bal,
            monte_carlo=monte_carlo_result,
        )

    return results
