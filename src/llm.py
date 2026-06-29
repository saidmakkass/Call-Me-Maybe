from typing import Any
from llm_sdk import Small_LLM_Model
from pydantic import BaseModel, PrivateAttr
from typing import List


class Model(BaseModel):
    model_name: str

    _model: Any = PrivateAttr()

    def model_post_init(self, __context):
        self._model = Small_LLM_Model(self.model_name)

    def encode(self, text: str) -> List[int]:
        return self._model.encode(text)[0].tolist()

    def decode(self, tokens: List[int]) -> str:
        return self._model.decode(tokens)

    def get_logits(self, input_tokens: List[int]) -> List[float]:
        return self._model.get_logits_from_input_ids(input_tokens)

    def next_token(self, logits: List[float]) -> int:
        return max(enumerate(logits), key=lambda x: x[1])[0]
