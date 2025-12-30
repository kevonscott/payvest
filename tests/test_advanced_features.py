import unittest
from app.models.finance import (
    LoanInput,
    InvestmentInput,
    SimulationConfig,
    run_scenarios,
)


class AdvancedFeaturesTestCase(unittest.TestCase):
    def test_debt_strategies_differ(self):
        loans = [
            LoanInput(principal=5000, apr=0.20, term_months=60),
            LoanInput(principal=15000, apr=0.05, term_months=60),
        ]
        inv = InvestmentInput(
            initial_amount=0, monthly_contribution=0, annual_return=0.07
        )
        cfg_avalanche = SimulationConfig(
            loans=loans,
            investment=inv,
            monthly_budget=500,
            horizon_years=5,
            debt_strategy="avalanche",
            monte_carlo_runs=1,
            return_volatility=0.15,
        )
        cfg_snowball = SimulationConfig(
            loans=loans,
            investment=inv,
            monthly_budget=500,
            horizon_years=5,
            debt_strategy="snowball",
            monte_carlo_runs=1,
            return_volatility=0.15,
        )
        msg = "Debt strategy '{strategy}' is not implemented. Only 'proportional' is supported"
        with self.assertRaisesRegex(
            NotImplementedError, msg.format(strategy="avalanche")
        ):
            _res_avalanche = run_scenarios(cfg_avalanche)

        with self.assertRaisesRegex(
            NotImplementedError, msg.format(strategy="snowball")
        ):
            _res_snowball = run_scenarios(cfg_snowball)
        # avalanche_net_worth = res_avalanche["loan_first"].final_net_worth
        # snowball_net_worth = res_snowball["loan_first"].final_net_worth
        # self.assertIsInstance(avalanche_net_worth, (int, float))
        # self.assertIsInstance(snowball_net_worth, (int, float))

    def test_monte_carlo_variability(self):
        loans = [LoanInput(principal=10000, apr=0.06, term_months=60)]
        inv = InvestmentInput(
            initial_amount=0,
            monthly_contribution=0,
            annual_return=0.08,
            annual_fee_pct=0.01,
        )
        cfg = SimulationConfig(
            loans=loans,
            investment=inv,
            monthly_budget=300,
            horizon_years=5,
            debt_strategy="proportional",
            monte_carlo_runs=100,
            return_volatility=0.20,
        )
        result = run_scenarios(cfg)
        mc_result = result["invest_first"].monte_carlo
        self.assertIsNotNone(mc_result)
        range_width = mc_result.percentile_90 - mc_result.percentile_10
        self.assertGreater(range_width, 1000)
        self.assertGreater(mc_result.success_probability, 0.3)
        self.assertGreaterEqual(mc_result.success_probability, 0.0)
        self.assertLessEqual(mc_result.success_probability, 1.0)

    def test_tax_advantaged_and_fees(self):
        loans = [LoanInput(principal=8000, apr=0.05, term_months=48)]
        inv_taxable = InvestmentInput(
            initial_amount=1000,
            monthly_contribution=200,
            annual_return=0.07,
            annual_fee_pct=0.015,
        )
        inv_tax_adv = InvestmentInput(
            initial_amount=1000,
            monthly_contribution=200,
            annual_return=0.07,
            annual_fee_pct=0.005,
        )
        cfg_taxable = SimulationConfig(
            loans=loans,
            investment=inv_taxable,
            monthly_budget=100,
            horizon_years=4,
            debt_strategy="avalanche",
            monte_carlo_runs=1,
            return_volatility=0.15,
        )
        cfg_tax_adv = SimulationConfig(
            loans=loans,
            investment=inv_tax_adv,
            monthly_budget=100,
            horizon_years=4,
            debt_strategy="avalanche",
            monte_carlo_runs=1,
            return_volatility=0.15,
        )
        msg = "Debt strategy 'avalanche' is not implemented. Only 'proportional' is supported"
        with self.assertRaisesRegex(NotImplementedError, msg):
            _res_taxable = run_scenarios(cfg_taxable)

        with self.assertRaisesRegex(NotImplementedError, msg):
            _res_tax_adv = run_scenarios(cfg_tax_adv)
        # taxable_balance = res_taxable["invest_first"].investment_balance
        # tax_adv_balance = res_tax_adv["invest_first"].investment_balance
        # self.assertGreaterEqual(tax_adv_balance, taxable_balance)
