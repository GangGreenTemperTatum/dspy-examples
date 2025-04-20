import typing as t

from openai import OpenAI
from openai.types.chat import ChatCompletion

from logger import logger


def get_target_response(
    target_client: OpenAI,
    target_model_name: str,
    attack_prompt: str,
    inference_params: dict[str, t.Any] = None,
) -> str:
    if not attack_prompt:
        logger.error("No attack prompt provided to target")
        return ""
    logger.debug(f'Getting target response for "{attack_prompt}"')
    if inference_params is None:
        inference_params = {}

    response: ChatCompletion = target_client.chat.completions.create(
        model=target_model_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": attack_prompt},
        ],
        **inference_params,
    )

    content = response.choices[0].message.content.strip()
    logger.debug(f'🎯 Got target response: "{content}"')
    return content
