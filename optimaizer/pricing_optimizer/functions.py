from optimaizer.pricing_optimizer.types import (
    PricingOptimizerInput,
    PricingOptimizerOutput,
    Inventory,
    MarketSize,
    ConversionRateCurve,
    Prediction,
)
from optimaizer.pricing_optimizer.optimizer import PricingOptimizer
import pandas as pd
import importlib.util


def load_data_from_csv(dfs) -> PricingOptimizerInput:
    product_ids = [*dfs["conversion_rate"]["product"].unique()]

    conversion_rate_curves = [
        ConversionRateCurve(
            product_id=product_id,
            curve=[
                Prediction(price=row["price"], conversion_rate=row["conversion_rate"])
                for _, row in dfs["conversion_rate"]
                .loc[dfs["conversion_rate"]["product"] == product_id]
                .iterrows()
            ],
        )
        for product_id in product_ids
    ]

    inventories = [
        Inventory(product_id=row["product"], inventory=row["inventory"])
        for _, row in dfs["inventory"].iterrows()
    ]

    market_sizes = [
        MarketSize(product_id=row["product"], market_size=row["market_size"])
        for _, row in dfs["market_size"].iterrows()
    ]

    pricing_optimizer_input = PricingOptimizerInput(
        product_ids=product_ids,
        conversion_rate_curves=conversion_rate_curves,
        inventories=inventories,
        market_sizes=market_sizes,
    )
    return pricing_optimizer_input


def get_default_pricing_parameters() -> PricingOptimizerInput:
    """
    Load default pricing parameters from a static data storage.

    Returns:
        PricingOptimizerInput: The default pricing input parameters.
    """
    from data import DATA_PATH

    csvs = [file for file in DATA_PATH.iterdir() if file.suffix == ".csv"]
    dfs = {file.stem: pd.read_csv(file) for file in csvs}
    pricing_optimizer_input = load_data_from_csv(dfs)
    return pricing_optimizer_input


def get_pricing_optimizer_code() -> str:
    """
    Get the source code of the pricing optimizer. This is needed to know the syntax to inject a custom constraint into the OR model.
    Pay careful attention to

    Returns:
        str: The source code of the pricing optimizer.
    """
    module_name = "optimaizer.pricing_optimizer.optimizer"
    spec = importlib.util.find_spec(module_name)

    if spec is None or spec.origin is None:
        raise ImportError(f"Module '{module_name}' not found.")

    with open(spec.origin, "r") as f:
        code = f.read()

    return code


def optimize_pricing(
    product_ids: list[str],
    inventories: list[Inventory],
    market_sizes: list[MarketSize],
    adhoc_ortools_constraints: list[str],
) -> PricingOptimizerOutput:
    """
    Run the pricing optimizer to determine the optimal pricing strategy for a range of products
    based on historical data, current inventory, and market conditions.

    NOTE: adhoc_ortools_constraints is a list of strings representing Python code snippets that will be
    injected at runtime by calling `solver.Add(constraint)`. Typically this relies on `namespace` variables
    that are defined within the optimizer.

    Args:
        product_ids (list[str]): List of product ids for which to optimize pricing
        inventories (list[Inventory]): List of Inventory objects containing product inventory levels
        market_sizes (list[MarketSize]): List of MarketSize objects containing market sizes for each product
        adhoc_ortools_constraints (list[str]): List of ad-hoc OR-Tools constraints to inject into the optimizer.

    Returns:
        PricingOptimizerOutput: The output of the pricing optimizer containing the optimal pricing strategy along with KPIs.
    """
    pricing_optimizer_input = get_default_pricing_parameters()

    pricing_optimizer_input = PricingOptimizerInput(
        product_ids=product_ids,
        inventories=inventories,
        market_sizes=market_sizes,
        conversion_rate_curves=pricing_optimizer_input.conversion_rate_curves,
        adhoc_ortools_constraints=adhoc_ortools_constraints,
    )
    optimizer = PricingOptimizer()
    optimizer.build_model(pricing_optimizer_input)
    return optimizer.solve()
