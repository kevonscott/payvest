import json
import logging
from flask import Blueprint, render_template, request
from .models.finance import (
    LoanInput,
    InvestmentInput,
    SimulationConfig,
    run_scenarios,
    _amortized_payment,
    _monthly_rate,
    ScenarioResult,
)
from .models.constants import (
    DEFAULT_ANNUAL_RETURN,
    DEFAULT_ANNUAL_FEE_PCT,
    DEFAULT_MONTE_CARLO_RUNS,
    DEFAULT_RETURN_VOLATILITY,
    DEFAULT_SPLIT_PCT_INVEST,
    DEFAULT_YEARS,
)
from werkzeug.datastructures import ImmutableMultiDict
from typing import TypeVar

Num = TypeVar("Num", int, float)

bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


@bp.route("/", methods=["GET", "POST"])
def index():
    """
    Render the main index page. Handles both GET and POST requests.
    If redirected from results, uses form_data from query args or POST.
    """
    form_data = {}
    if request.method == "POST":
        form_data = request.form.to_dict()
    elif request.method == "GET":
        str_form_data = request.args.get("form_data")
        if str_form_data:
            try:
                form_data = json.loads(str_form_data)
            except json.decoder.JSONDecodeError:
                logger.exception(
                    "Failed to decode form_data from query args: %r",
                    str_form_data,
                )
                form_data = {}
    return render_template("index.html", form_data=form_data)


@bp.post("/simulate")
def simulate():
    """
    Handle simulation POST.

    Parses form data, validates, runs scenarios, and renders results.
    """
    form: ImmutableMultiDict = request.form

    def validate_float(
        val: Num,
        default: float = 0.0,
        min_value: float | None = None,
        max_value: float | None = None,
        scale: float = 1.0,
    ) -> float:
        """
        Parse and validate a float from input, with optional bounds and scaling.
        """
        try:
            f = float(val)
            if min_value is not None and f < min_value:
                return default
            if max_value is not None and f > max_value:
                return default
            return f * scale
        except (ValueError, TypeError):
            return default * scale

    def validate_int(
        val: Num,
        default: int = 0,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> int:
        """
        Parse and validate an integer from input, with optional bounds.
        """
        try:
            i = int(val)
            if min_value is not None and i < min_value:
                return default
            if max_value is not None and i > max_value:
                return default
            return i
        except (ValueError, TypeError):
            return default

    def parse_loans(form):
        """
        Parse loan fields from the form into a list of LoanInput.
        """
        loans = []
        i = 0
        while True:
            amount_raw = form.get(f"loan_amount_{i}")
            apr_raw = form.get(f"apr_{i}")
            term_raw = form.get(f"term_months_{i}")
            if amount_raw is None:
                break
            amount = validate_float(amount_raw, 0.0, min_value=0.0)
            apr = validate_float(apr_raw, 0.0, min_value=0.0, scale=0.01)
            term = validate_int(term_raw, 0, min_value=0)
            if amount > 0 and term > 0:
                loans.append(
                    LoanInput(
                        principal=amount,
                        apr=apr,
                        term_months=term,
                    )
                )
            i += 1
        return loans

    def parse_scalars(form) -> dict[str, int | float]:
        """
        Parse scalar fields from the form with validation and defaults.
        """
        return dict(
            initial_investment=validate_float(
                form.get("initial_investment"), 0.0, min_value=0.0
            ),
            monthly_budget=validate_float(
                form.get("monthly_budget"), 0.0, min_value=0.0
            ),
            annual_return=(
                validate_float(
                    form.get("annual_return"),
                    DEFAULT_ANNUAL_RETURN,
                    min_value=0.0,
                    scale=0.01,
                )
                or DEFAULT_ANNUAL_RETURN
            ),
            annual_fee_pct=validate_float(
                form.get("annual_fee_pct"),
                DEFAULT_ANNUAL_FEE_PCT,
                min_value=0.0,
                scale=0.01,
            ),
            monte_carlo_runs=(
                validate_int(
                    form.get("monte_carlo_runs"),
                    DEFAULT_MONTE_CARLO_RUNS,
                    min_value=1,
                )
                or DEFAULT_MONTE_CARLO_RUNS
            ),
            return_volatility=(
                validate_float(
                    form.get("return_volatility"),
                    DEFAULT_RETURN_VOLATILITY,
                    min_value=0.0,
                    scale=0.01,
                )
                or DEFAULT_RETURN_VOLATILITY
            ),
            split_pct_invest=(
                validate_float(
                    form.get("split_pct_invest"),
                    DEFAULT_SPLIT_PCT_INVEST * 100,
                    min_value=0.0,
                    max_value=100.0,
                    scale=0.01,
                )
                or DEFAULT_SPLIT_PCT_INVEST
            ),
            years=(
                validate_int(
                    form.get("years"),
                    DEFAULT_YEARS,
                    min_value=1,
                )
                or DEFAULT_YEARS
            ),
        )

    loans = parse_loans(form)
    scalars = parse_scalars(form)

    debt_strategy = form.get("debt_strategy", "proportional")
    if debt_strategy not in {"avalanche", "snowball", "proportional"}:
        logger.warning(
            "Invalid debt_strategy: %r. Defaulting to 'proportional'",
            debt_strategy,
        )
        debt_strategy = "proportional"

    error_message = None
    result: dict[str, ScenarioResult]|None = None
    best_scenario = None
    pie_chart_data = None
    input_summary = {}
    cfg = None
    try:
        inv = InvestmentInput(
            initial_amount=scalars["initial_investment"],
            monthly_contribution=0.0,
            annual_return=scalars["annual_return"],
            annual_fee_pct=scalars["annual_fee_pct"],
        )

        cfg = SimulationConfig(
            loans=loans,
            investment=inv,
            monthly_budget=scalars["monthly_budget"],
            horizon_years=int(scalars["years"]),
            split_pct_invest=scalars["split_pct_invest"],
            debt_strategy=debt_strategy,
            monte_carlo_runs=int(scalars["monte_carlo_runs"]),
            return_volatility=scalars["return_volatility"],
        )

        result: dict[str, ScenarioResult] = run_scenarios(cfg=cfg)

        total_loan_principal: int = sum(loan.principal for loan in loans)
        total_scheduled_interest: int = sum(
            _amortized_payment(
                loan.principal,
                _monthly_rate(loan.apr),
                loan.term_months,
            )
            * loan.term_months
            - loan.principal
            for loan in loans
            if loan.term_months > 0
        )
        # Compute years for each loan (term_months / 12)
        loan_years = [round(loan.term_months / 12, 2) for loan in loans]
        input_summary = {
            "years": scalars["years"],
            "total_loan_principal": total_loan_principal,
            "total_scheduled_interest": total_scheduled_interest,
            "monthly_budget": scalars["monthly_budget"],
            "num_loans": len(loans),
            "loan_years": loan_years,
            "loan_terms": [loan.term_months for loan in loans],
        }

        def get_net_worth(scenario):
            """
            Get comparable net worth for a scenario.
            """
            return (
                getattr(
                    getattr(scenario, "monte_carlo", None),
                    "median_net_worth",
                    None,
                )
                or scenario.final_net_worth
            )

        best_key = max(result, key=lambda k: get_net_worth(result[k]))
        best_scenario = result[best_key]
        pie_chart_data = {
            key: {
                "invested": sum(y.invested_total for y in scenario.yearly),
                "returns": scenario.investment_balance
                - sum(y.invested_total for y in scenario.yearly),
                "name": scenario.name,
            }
            for key, scenario in result.items()
        }
    except ValueError as e:
        error_message = str(e)
    except Exception as e:
        error_message = f"Unexpected error: {e}"

    form_dict = form.to_dict()
    logger.info(
        "Simulation complete. Best scenario: %s",
        best_scenario.name if best_scenario else "N/A",
    )
    # If error, ensure input_summary has safe defaults for template
    if error_message:
        input_summary = {
            "years": 0,
            "total_loan_principal": 0.0,
            "total_scheduled_interest": 0.0,
            "monthly_budget": 0.0,
            "num_loans": 0,
            "loan_years": [],
            "loan_terms": [],
        }
    return render_template(
        "results.html",
        result=result if not error_message else None,
        cfg=cfg,
        best_scenario=best_scenario,
        input_summary=input_summary,
        pie_chart_data=pie_chart_data,
        form_data=form_dict,
        form_data_json=json.dumps(form_dict),
        error_message=error_message,
    )
