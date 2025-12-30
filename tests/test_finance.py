import math
import unittest
from app.models.finance import (
    LoanInput,
    InvestmentInput,
    SimulationConfig,
    run_scenarios,
)


class FinanceTestCase(unittest.TestCase):
    def test_loan_first_scenario(self):
        loan = LoanInput(principal=60000, apr=0.04, term_months=80)
        invest = InvestmentInput(
            initial_amount=0, monthly_contribution=0, annual_return=0.06
        )
        cfg = SimulationConfig(
            loans=[loan],
            investment=invest,
            monthly_budget=1000,
            horizon_years=20,
            split_pct_invest=0.0,
            debt_strategy="proportional",
            monte_carlo_runs=1,
            return_volatility=0.0,
        )
        result = run_scenarios(cfg)["loan_first"]
        self.assertTrue(
            math.isclose(result.investment_balance, 281189, rel_tol=0.03)
        )

    def test_invest_first_scenario(self):
        loan = LoanInput(principal=60000, apr=0.04, term_months=80)
        invest = InvestmentInput(
            initial_amount=0, monthly_contribution=0, annual_return=0.06
        )
        cfg = SimulationConfig(
            loans=[loan],
            investment=invest,
            monthly_budget=1000,
            horizon_years=20,
            split_pct_invest=1.0,
            debt_strategy="proportional",
            monte_carlo_runs=1,
            return_volatility=0.0,
        )
        result = run_scenarios(cfg)["invest_first"]
        self.assertTrue(
            math.isclose(result.investment_balance, 281189, rel_tol=0.02)
        )

    def test_split_scenario(self):
        loan = LoanInput(principal=60000, apr=0.04, term_months=80)
        invest = InvestmentInput(
            initial_amount=0, monthly_contribution=0, annual_return=0.06
        )
        cfg = SimulationConfig(
            loans=[loan],
            investment=invest,
            monthly_budget=1000,
            horizon_years=20,
            split_pct_invest=0.5,
            debt_strategy="proportional",
            monte_carlo_runs=1,
            return_volatility=0.0,
        )
        result = run_scenarios(cfg)["split"]
        self.assertGreater(result.investment_balance, 281189 * 0.98)

    def test_simple_loan_first_vs_invest_first(self):
        loans = [LoanInput(principal=10000, apr=0.05, term_months=60)]
        inv = InvestmentInput(
            initial_amount=0, monthly_contribution=0, annual_return=0.06
        )
        cfg = SimulationConfig(
            loans=loans,
            investment=inv,
            monthly_budget=200,
            horizon_years=5,
            split_pct_invest=0.5,
            debt_strategy="proportional",
            monte_carlo_runs=1,
            return_volatility=0.15,
        )
        res = run_scenarios(cfg)
        self.assertEqual(
            set(res.keys()), {"loan_first", "invest_first", "split"}
        )
        self.assertGreaterEqual(res["loan_first"].loans_remaining_balance, 0)
        self.assertGreaterEqual(res["invest_first"].investment_balance, 0)

    def test_redirect_payments_when_loan_finishes(self):
        loans = [LoanInput(principal=1200, apr=0.05, term_months=12)]
        inv = InvestmentInput(
            initial_amount=0, monthly_contribution=0, annual_return=0.12
        )
        cfg = SimulationConfig(
            loans=loans,
            investment=inv,
            monthly_budget=200,
            horizon_years=3,
            split_pct_invest=0.0,
            debt_strategy="proportional",
            monte_carlo_runs=1,
            return_volatility=0.15,
        )
        res = run_scenarios(cfg)
        loan_first = res["loan_first"]
        final_loan_balance = loan_first.yearly[-1].loan_balance_end
        self.assertLess(final_loan_balance, 100)
        total_invested = sum(y.invested_total for y in loan_first.yearly)
        self.assertGreater(total_invested, 0)
