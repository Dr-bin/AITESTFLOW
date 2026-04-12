"""LLM Client for AITestFlow"""

import json
import logging
import re
import time
from typing import TypeVar

from dotenv import load_dotenv
import httpx
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from pydantic import BaseModel, ValidationError

from src.models import CodeResponseModel


logger = logging.getLogger(__name__)


T = TypeVar("T", bound=BaseModel)

load_dotenv()


def _repair_json(json_str: str) -> str:
    """Attempt to repair common JSON format errors"""
    json_str = re.sub(r'```json\s*', '', json_str)
    json_str = re.sub(r'```\s*$', '', json_str)
    
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    json_str = re.sub(r'(?<!")(\w+)(?=\s*:)', r'"\1"', json_str)
    
    json_str = json_str.strip()
    
    return json_str


class LLMClient:
    """Client for interacting with LLM API with enhanced error handling"""

    def __init__(self) -> None:
        """Initialize LLM client with API configuration from environment variables"""
        import os
        
        for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY"]:
            os.environ.pop(key, None)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")

        base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        try:
            self._client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                http_client=None,
                timeout=120.0,
            )
        except TypeError as e:
            # openai<=1.14 with newer httpx may fail in internal client init
            if "proxies" not in str(e):
                raise
            logger.warning(
                "OpenAI client init hit httpx compatibility issue; fallback to explicit httpx client: %s",
                e,
            )
            self._client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                http_client=httpx.Client(timeout=120.0),
                timeout=120.0,
            )
        self._model = os.getenv("LLM_MODEL", "gpt-4")
        logger.info(f"LLM Client initialized with model: {self._model}")

    def call(
        self, 
        prompt: str, 
        response_model: type[T], 
        max_retries: int = 3,
        temperature: float = 0.2
    ) -> T:
        """
        Call LLM with prompt and parse response into Pydantic model

        Args:
            prompt: The prompt to send to LLM
            response_model: Pydantic model to parse response into, or dict for raw JSON
            max_retries: Maximum number of retry attempts
            temperature: Sampling temperature (0.0 to 2.0)

        Returns:
            Parsed response_model instance

        Raises:
            RuntimeError: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"LLM call attempt {attempt + 1}/{max_retries}")
                
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                    max_tokens=4096,
                )

                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("Empty response from LLM")

                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.debug(f"Initial JSON parse failed, attempting repair: {e}")
                    repaired = _repair_json(content)
                    try:
                        parsed = json.loads(repaired)
                        logger.debug("JSON repair successful")
                    except json.JSONDecodeError as repair_error:
                        logger.error(f"JSON repair failed: {repair_error}")
                        raise e
                
                if response_model is dict:
                    logger.debug("LLM call successful (raw dict)")
                    return parsed  # type: ignore

                validated = response_model.model_validate(parsed)
                logger.debug(f"LLM call successful, validated as {response_model.__name__}")
                return validated

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
                
            except ValidationError as e:
                last_error = e
                logger.warning(f"Validation error on attempt {attempt + 1}: {e}")
                
            except RateLimitError as e:
                last_error = e
                wait_time = 2 ** attempt
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry: {e}")
                time.sleep(wait_time)
                
            except APIConnectionError as e:
                last_error = e
                logger.warning(f"API connection error on attempt {attempt + 1}: {e}")
                time.sleep(1)
                
            except APIError as e:
                last_error = e
                logger.warning(f"API error on attempt {attempt + 1}: {e}")
                
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}", exc_info=True)

        error_msg = f"LLM call failed after {max_retries} retries: {last_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def call_with_fallback(
        self,
        prompt: str,
        response_model: type[T],
        fallback_models: list = None
    ) -> T:
        """
        Call LLM with fallback to alternative models if primary fails

        Args:
            prompt: The prompt to send to LLM
            response_model: Pydantic model to parse response into
            fallback_models: List of fallback model names

        Returns:
            Parsed response_model instance
        """
        models_to_try = [self._model] + (fallback_models or [])
        
        for model in models_to_try:
            try:
                original_model = self._model
                self._model = model
                
                result = self.call(prompt, response_model, max_retries=2)
                
                self._model = original_model
                return result
                
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                continue
        
        raise RuntimeError(f"All models failed: {models_to_try}")
