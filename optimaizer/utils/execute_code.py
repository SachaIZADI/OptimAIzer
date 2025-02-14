from typing import Any
import textwrap
import logging
from pydantic import BaseModel
from enum import StrEnum, unique

logger = logging.getLogger(__name__)


@unique
class CodeExecutionStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


class CodeExecutionResult(BaseModel):
    code: str
    status: CodeExecutionStatus
    message: str


def execute_code(
    code: str, namespace: dict[str, Any] | None = None
) -> CodeExecutionResult:
    logger.warning("Executing arbitrary code might be unsafe.")

    namespace = namespace or {}
    code = textwrap.dedent(code)

    try:
        exec(code, namespace)
        logger.info("Code executed successfully.")
        return CodeExecutionResult(
            code=code,
            status=CodeExecutionStatus.SUCCESS,
            message="Code executed successfully.",
        )

    except Exception as e:
        logger.error(f"Error executing code: {e}")
        return CodeExecutionResult(
            code=code, status=CodeExecutionStatus.ERROR, message=str(e)
        )
