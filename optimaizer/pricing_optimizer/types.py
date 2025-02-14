from pydantic import BaseModel


class Prediction(BaseModel):
    price: float
    conversion_rate: float


class ConversionRateCurve(BaseModel):
    product_id: str
    curve: list[Prediction]


class Inventory(BaseModel):
    product_id: str
    inventory: int


class MarketSize(BaseModel):
    product_id: str
    market_size: int


class PricingOptimizerInput(BaseModel):
    product_ids: list[str]
    conversion_rate_curves: list[ConversionRateCurve]
    inventories: list[Inventory]
    market_sizes: list[MarketSize]
    adhoc_ortools_constraints: list[str] = []

    @property
    def conversion_rate_curves_dict(self) -> dict[str, list[Prediction]]:
        return {curve.product_id: curve.curve for curve in self.conversion_rate_curves}

    @property
    def inventories_dict(self) -> dict[str, int]:
        return {
            inventory.product_id: inventory.inventory for inventory in self.inventories
        }

    @property
    def market_sizes_dict(self) -> dict[str, int]:
        return {
            market_size.product_id: market_size.market_size
            for market_size in self.market_sizes
        }


class ProductResult(BaseModel):
    product_id: str
    price: float
    revenue: float
    sales: int


class ProductRevenue(BaseModel):
    product_id: str
    revenue: float


class PricingOptimizerOutput(BaseModel):
    product_results: list[ProductResult]

    @property
    def total_revenue(self) -> float:
        return sum(product_result.revenue for product_result in self.product_results)
