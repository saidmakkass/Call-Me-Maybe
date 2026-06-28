from typing import Dict, List, Union, Literal
from pydantic import BaseModel
import json


class Type(BaseModel):
    type: Literal["string", "boolean", "integer", "number"]


class FunctionDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Type]
    returns: Type


class FunctionRegistry(BaseModel):
    functions: List[FunctionDefinition]

    @property
    def names(self) -> List[str]:
        return [f.name for f in self.functions]

class Prompt(BaseModel):
    prompt: str

class FunctionCall(BaseModel):
    prompt: str
    name: str
    parameters: Dict[str, Union[str, int, float, bool]]

class Output(BaseModel):
    output: List[FunctionCall]

    def add(self, function_call: FunctionCall) -> None:
        self.output.append(function_call)

    def dump(self) -> str:
        o = self.model_dump()
        return json.dumps(o["output"], indent=4)

