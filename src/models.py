from typing import Dict, List, Any, Literal
from pydantic import BaseModel, ConfigDict
import json


class Type(BaseModel):
    """Represents a parameter type used in function definitions.

    Attributes:
        type: The data type (string, boolean, integer, or number).
    """

    model_config = ConfigDict(extra="forbid")
    type: Literal["string", "boolean", "integer", "number"]


class FunctionDefinition(BaseModel):
    """Definition of a function available for function calling.

    Attributes:
        name: Function name identifier.
        description: Human-readable description of the function.
        parameters: Mapping of parameter names to their types.
        returns: Type definition for the return value.
    """

    model_config = ConfigDict(extra="forbid")
    name: str
    description: str
    parameters: Dict[str, Type]
    returns: Type


class FunctionRegistry(BaseModel):
    """Collection of available function definitions.

    Attributes:
        functions: List of FunctionDefinition objects.
    """

    model_config = ConfigDict(extra="forbid")
    functions: List[FunctionDefinition]

    @property
    def names(self) -> List[str]:
        """Get all function names in the registry.

        Returns:
            List of function name strings.
        """
        return [f.name for f in self.functions]


class Prompt(BaseModel):
    """User prompt to be converted into a function call.

    Attributes:
        prompt: Natural language text input.
    """

    model_config = ConfigDict(extra="forbid")
    prompt: str


class FunctionCall(BaseModel):
    """Generated function call from natural language.

    Attributes:
        prompt: Original user prompt.
        name: Name of the function to call.
        parameters: Arguments for the function call.
    """

    model_config = ConfigDict(extra="forbid")
    prompt: str
    name: str
    parameters: Dict[str, Any]


class Output(BaseModel):
    """Collection of generated function calls.

    Attributes:
        output: List of FunctionCall objects.
    """

    model_config = ConfigDict(extra="forbid")
    output: List[FunctionCall]

    def add(self, function_call: FunctionCall) -> None:
        """Add a function call to the output.

        Args:
            function_call: FunctionCall object to add.
        """
        self.output.append(function_call)

    def dump(self) -> str:
        """Serialize output to JSON string.

        Returns:
            JSON-formatted string with indentation.
        """
        o = self.model_dump()
        return json.dumps(o["output"], indent=4)
