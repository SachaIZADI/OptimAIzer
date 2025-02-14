from dotenv import load_dotenv
import logging
from optimaizer.llm.agent import OpenAIAgent
from optimaizer.pricing_optimizer.functions import (
    get_pricing_optimizer_code,
    optimize_pricing,
    get_default_pricing_parameters,
)

from optimaizer.utils import logging_config  # noqa: F401


load_dotenv()
logger = logging.getLogger(__name__)


def start_pricing_agent() -> OpenAIAgent:
    SYSTEM_PROMPT = """
    You are an AI-powered pricing optimizer tasked with determining the optimal pricing strategy for a range of products based on historical data, current inventory, and market conditions.

    You have access to specialized tools that allow you to:

        • Retrieve default data (supported products, current inventory, market size, etc.).
        • Execute an OR model to compute optimal pricing with the given input parameters. It is also possible to inject custom constraints that will be executed at runtime.
        • Get the source code of the OR model to inspect its formulation. This is needed to know the syntax to inject a custom constraint into the OR model.

    Instructions:
    1. Use at most one tool per response. Wait for the results of a tool call before making further decisions.
    2. Integrate the returned results carefully into your reasoning for subsequent actions.
    3. If an error occurs during a tool call, report the error clearly and propose a corrective action before proceeding.
    4. When ready to conclude the interaction, provide a clear and concise summary of your pricing recommendations and the constraints applied.
    5. Base your decisions strictly on the data provided by the tools and follow a logical, step-by-step approach in optimizing the pricing strategy.
    6. If you need to inject a custom constraint, pay extra attention to the syntax provided in the source code of the OR model, and the variables in the namespace.
    7. If a user asked you something that you cannot answer or this raises an error you cannot fix easily, provide an informative error message and suggest a way to proceed.

    Your objective is to guide the user toward the best pricing strategy while adapting to dynamic constraints and new data inputs.
    """

    agent = OpenAIAgent(system_prompt=SYSTEM_PROMPT)
    agent.register_function(optimize_pricing)
    agent.register_function(get_default_pricing_parameters)
    agent.register_function(get_pricing_optimizer_code)
    return agent


if __name__ == "__main__":
    # Example script containing interactions with the pricing optimizer agent

    agent = start_pricing_agent()

    result = agent(
        """
        Optimize pricing for the following products: product-A, product-B, product-C

        Inventory levels are:
        - product-A: 90
        - product-B: 55
        - product-C: use default value
        """,
    )
    logger.debug(result)

    result = agent(
        """
        Do the same for product-A and product-B only.
        Keep the same inventory level, but change the market size for product-A to 1000.
        """,
    )
    logger.debug(result)

    result = agent(
        """
        Now add a custom constraint to the optimizer such that the price of product-A is lower or equal to the price of product-B.
        """,
    )
    logger.debug(result)

    # NOTE: the constraint below (x < y) is not supported by the optimizer, and will throw an error
    result = agent(
        """
        Now add a custom constraint to the optimizer such that the price of product-A is strictly lower to the price of product-B.
        """,
    )
    logger.debug(result)

    if "proceed" in result.lower():
        logger.debug("LLM Asked the user to proceed after an error!")
        result = agent(
            """Yes please do.""",
        )
        logger.debug(result)

    result = agent(
        """
        I would like the price of A to be between 0.5 and 1.5.
        """,
    )
    logger.debug(result)
