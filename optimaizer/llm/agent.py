from openai import OpenAI
from openai.types.chat.chat_completion_message_tool_call import Function
from optimaizer.llm.types import Tool
import json
from pydantic import BaseModel

import os
from typing import Callable, Any
from logging import getLogger

logger = getLogger(__name__)


class OpenAIAgent:
    def __init__(self, system_prompt: str | None) -> None:
        self.__client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._model = "gpt-4o-mini"
        self.conversation_history: list[dict[str, str]] = []

        self.tools: list[Tool] = []
        self.functions: dict[str, Callable] = {}

        if system_prompt:
            self.conversation_history.append(
                {"role": "system", "content": system_prompt}
            )

    def register_function(self, func: Callable) -> None:
        tool = Tool.from_function(func)
        self.tools.append(tool)
        self.functions[tool.name] = func

    def call_function(self, tool_call: Function) -> Any:
        logger.info(
            f"Calling function {tool_call.name} with arguments {tool_call.arguments}"
        )
        result = self.functions[tool_call.name](**json.loads(tool_call.arguments))
        logger.debug(f"Result of {tool_call.name}({tool_call.arguments}): {result}")
        return result

    def __call__(self, user_prompt: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_prompt})

        while True:
            response = self.__client.chat.completions.create(
                model=self._model,
                messages=self.conversation_history,
                tools=self.tools,
            )
            message = response.choices[0].message

            if message.tool_calls:
                # NOTE: We allow only one function call at a time
                if len(message.tool_calls) > 1:
                    logger.warning("Multiple function calls are not supported")
                    message.tool_calls = message.tool_calls[:1]
                self.conversation_history.append(message)

                try:
                    result = self.call_function(
                        response.choices[0].message.tool_calls[0].function
                    )
                    serialized_result = (
                        result.model_dump_json()
                        if isinstance(result, BaseModel)
                        else str(result)
                    )

                except Exception as e:
                    serialized_result = str(e)
                    function = response.choices[0].message.tool_calls[0].function
                    logger.error(f"Error executing function ({function.name}): {e}")

                self.conversation_history.append(
                    {
                        "role": "tool",
                        "tool_call_id": message.tool_calls[0].id,
                        "content": serialized_result,
                    }
                )

            else:  # NOTE: Assumes the LLM gives back an answer to the user
                break

        self.conversation_history.append(message)
        return message.content
