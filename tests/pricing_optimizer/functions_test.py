from optimaizer.pricing_optimizer.functions import (
    get_default_pricing_parameters,
    optimize_pricing,
)
from data import DATA_PATH
import pandas as pd


def test_optimizer_results_with_default_parameters() -> None:
    default_pricing_parameters = get_default_pricing_parameters()

    solution = optimize_pricing(
        product_ids=default_pricing_parameters.product_ids,
        inventories=default_pricing_parameters.inventories,
        market_sizes=default_pricing_parameters.market_sizes,
        adhoc_ortools_constraints=[],
    )
    solution_df = pd.DataFrame([s.model_dump() for s in solution.product_results])

    # Expected solution computed with the default parameters in an excel file
    expected_solution_df = pd.read_csv(DATA_PATH / "solution.csv")
    pd.testing.assert_frame_equal(solution_df, expected_solution_df)


def test_optimizer_results_with_adhoc_ortools_constraints() -> None:
    default_pricing_parameters = get_default_pricing_parameters()

    # Without custom constraint, price of product-A is higher than product-B
    solution = optimize_pricing(
        product_ids=default_pricing_parameters.product_ids,
        inventories=default_pricing_parameters.inventories,
        market_sizes=default_pricing_parameters.market_sizes,
        adhoc_ortools_constraints=[],
    )
    solution_df = pd.DataFrame([s.model_dump() for s in solution.product_results])
    assert float(solution_df.query("product_id == 'product-A'")["price"]) > float(
        solution_df.query("product_id == 'product-B'")["price"]
    )

    # With custom constraint, price of product-A is lower or equal to product-B
    new_solution = optimize_pricing(
        product_ids=default_pricing_parameters.product_ids,
        inventories=default_pricing_parameters.inventories,
        market_sizes=default_pricing_parameters.market_sizes,
        adhoc_ortools_constraints=[
            "product_price['product-A'] <= product_price['product-B']"
        ],
    )
    new_solution_df = pd.DataFrame(
        [s.model_dump() for s in new_solution.product_results]
    )
    assert float(new_solution_df.query("product_id == 'product-A'")["price"]) <= float(
        new_solution_df.query("product_id == 'product-B'")["price"]
    )
