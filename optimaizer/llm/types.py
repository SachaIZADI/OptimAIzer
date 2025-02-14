from pydantic import BaseModel
from typing import Literal, Callable, Any


class Parameter(BaseModel):
    type: Literal["object"]
    properties: dict[str, dict[str, Any]]
    required: list[str]
    additionalProperties: bool = False


class Function(BaseModel):
    name: str
    description: str
    parameters: Parameter
    strict: bool


class Tool(BaseModel):
    type: Literal["function"]
    function: Function

    @property
    def name(self):
        return self.function.name

    @classmethod
    def from_function(cls, func: Callable) -> "Tool":
        from langchain_core.utils.function_calling import convert_to_openai_function

        f = convert_to_openai_function(func)

        def _recursive_fix_properties(properties: dict[str, Any]) -> dict[str, Any]:
            if "properties" in properties:
                properties["additionalProperties"] = False

            for key, value in properties.items():
                if isinstance(value, dict) and "properties" in value:
                    properties[key]["properties"] = _recursive_fix_properties(
                        value["properties"]
                    )

                if isinstance(value, dict) and "items" in value:
                    properties[key]["items"] = _recursive_fix_properties(value["items"])

            return properties

        properties = _recursive_fix_properties(f["parameters"]["properties"])

        return cls(
            type="function",
            function=Function(
                name=f["name"],
                description=f["description"],
                parameters=Parameter(
                    type=f["parameters"]["type"],
                    properties=properties,
                    required=f["parameters"].get("required", []),
                    additionalProperties=False,
                ),
                strict=True,
            ),
        )
