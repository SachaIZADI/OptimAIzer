import logging
from ortools.linear_solver import pywraplp
from optimaizer.pricing_optimizer.types import (
    PricingOptimizerInput,
    PricingOptimizerOutput,
    ProductResult,
)
from optimaizer.utils.execute_code import CodeExecutionStatus, execute_code

logger = logging.getLogger(__name__)


class PricingOptimizer:
    def __init__(self, verbose: bool = True) -> None:
        self.solver = pywraplp.Solver.CreateSolver("CBC_MIXED_INTEGER_PROGRAMMING")
        if not self.solver:
            raise RuntimeError("Solver not available")

        if verbose:
            self.solver.EnableOutput()

        self.x: dict[tuple[str, float], pywraplp.Variable] = {}
        self.product_price: dict[str, pywraplp.LinearExpr] = {}
        self.product_revenue: dict[str, pywraplp.LinearExpr] = {}
        self.product_sales: dict[str, pywraplp.LinearExpr] = {}

    def build_model(self, optim_input: PricingOptimizerInput) -> None:
        product_ids = optim_input.product_ids

        # x is a boolean variable which equals 1 if price p is selected for product i
        x: dict[tuple[str, float], pywraplp.Variable] = {}
        product_price: dict[str, pywraplp.LinearExpr] = {}
        product_revenue: dict[str, pywraplp.LinearExpr] = {}
        product_sales: dict[str, pywraplp.LinearExpr] = {}

        for product_id in product_ids:
            curve = optim_input.conversion_rate_curves_dict[product_id]
            for prediction in curve:
                x[(product_id, prediction.price)] = self.solver.IntVar(
                    0.0, 1.0, f"x[{product_id}, {prediction.price}]"
                )

            # Only one price can be chosen for each product
            self.solver.Add(sum(x[product_id, p.price] for p in curve) == 1)

            # Calculate intermediate quantities (price, sales, revenue)
            product_price[product_id] = sum(
                x[product_id, p.price] * p.price for p in curve
            )

            inventory = optim_input.inventories_dict[product_id]
            market_size = optim_input.market_sizes_dict[product_id]
            # sales = min(demand, inventory) = min(conversion_rate * market_size, inventory)
            product_sales[product_id] = sum(
                x[product_id, p.price]
                * int(min(inventory, p.conversion_rate * market_size))
                for p in curve
            )
            product_revenue[product_id] = sum(
                x[product_id, p.price]
                * p.price
                * int(min(inventory, p.conversion_rate * market_size))
                for p in curve
            )

        # Inject Adhoc OR-Tools constraints
        # NOTE(for LLM): Pay careful attention to the syntax here.
        #  • x is a dictionary of boolean variables, where x[(product_id, price)] is 1 if price is selected for product_id
        #  • product_price is a dictionary of linear expressions where product_price[product_id] is the price for product_id
        #  • product_revenue is a dictionary of linear expressions where product_revenue[product_id] is the revenue for product_id
        #  • product_sales is a dictionary of linear expressions where product_sales[product_id] is the sales for product_id
        namespace = {
            "solver": self.solver,
            "x": x,
            "product_price": product_price,
            "product_revenue": product_revenue,
            "product_sales": product_sales,
        }
        for constraint in optim_input.adhoc_ortools_constraints:
            logger.info(f"Injecting custom constraint: {constraint}")
            result = execute_code(f"solver.Add({constraint})", namespace)

            if result.status == CodeExecutionStatus.ERROR:
                raise RuntimeError(
                    f"Error injecting custom constraint. "
                    f"Executed code: {result.code}) | Error message: {result.message}"
                )

        # Objective function: Max(revenue)
        self.solver.Maximize(sum(product_revenue.values()))

        # Cache variables for later access
        self.x = x
        self.product_price = product_price
        self.product_revenue = product_revenue
        self.product_sales = product_sales

    def solve(self) -> PricingOptimizerOutput:
        status = self.solver.Solve()
        self.raise_exception_if_model_did_not_solve(status)
        return self.format_solution()

    def format_solution(self) -> PricingOptimizerOutput:
        product_results = []
        for (product_id, price), variable in self.x.items():
            if variable.solution_value() == 1:
                product_results.append(
                    ProductResult(
                        product_id=product_id,
                        price=price,
                        revenue=self.product_revenue[product_id].solution_value(),
                        sales=self.product_sales[product_id].solution_value(),
                    )
                )
        return PricingOptimizerOutput(product_results=product_results)

    def raise_exception_if_model_did_not_solve(self, status: int) -> None:
        if status in {pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE}:
            return

        if status in {pywraplp.Solver.INFEASIBLE, pywraplp.Solver.UNBOUNDED}:
            raise RuntimeError("Infeasible or unbounded optimization problem")

        if status == pywraplp.Solver.MODEL_INVALID:
            raise RuntimeError(
                "Invalid model error when solving the optimization problem"
            )

        raise RuntimeError("Model failed to solve")
