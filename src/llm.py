from typing import Any
from llm_sdk import Small_LLM_Model
from pydantic import BaseModel, PrivateAttr
from typing import List


class Model(BaseModel):
    """Wrapper for the Small LLM Model.

    Attributes:
        model_name: Identifier of the model on Hugging Face Hub.
    """

    model_name: str

    _model: Any = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        self._model = Small_LLM_Model(self.model_name)

    def encode(self, text: str) -> Any:
        """Encode text into token IDs.

        Args:
            text: Text string to encode.

        Returns:
            List of token IDs.
        """
        return self._model.encode(text)[0].tolist()

    def decode(self, tokens: List[int]) -> Any:
        """Decode token IDs into text.

        Args:
            tokens: List of token IDs to decode.

        Returns:
            Decoded text string.
        """
        return self._model.decode(tokens)

    def get_logits(self, input_tokens: List[int]) -> Any:
        """Get logits for the next token given input token IDs.

        Args:
            input_tokens: List of input token IDs.

        Returns:
            List of logits for each possible token.
        """
        return self._model.get_logits_from_input_ids(input_tokens)

    def next_token(self, logits: List[float]) -> int:
        """Get the token with the highest logit value.

        Args:
            logits: List of logits for possible tokens.

        Returns:
            Index of the token with the highest logit.
        """
        return max(enumerate(logits), key=lambda x: x[1])[0]
