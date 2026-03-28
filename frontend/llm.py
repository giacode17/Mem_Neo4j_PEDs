import os
import time

import anthropic
import openai
from dotenv import load_dotenv
from model_config import MODEL_TO_PROVIDER

load_dotenv()

MODEL_STRING = "gpt-4.1-mini"

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def set_model(model_id: str) -> None:
    global MODEL_STRING
    MODEL_STRING = model_id


def chat(messages, persona=None):
    provider = MODEL_TO_PROVIDER.get(MODEL_STRING, "openai")

    if provider == "openai":
        system_prompt = None
        filtered = messages
        if messages and messages[0].get("role") == "system":
            system_prompt = messages[0]["content"]
            filtered = messages[1:]

        t0 = time.time()
        out = openai_client.responses.create(
            model=MODEL_STRING,
            instructions=system_prompt,
            input=filtered,
            max_output_tokens=500,
            temperature=0.5,
            store=False,
        )
        dt = time.time() - t0
        text = out.output_text.strip()
        tok_in = out.usage.input_tokens
        tok_out = out.usage.output_tokens
        total_tok = (tok_in or 0) + (tok_out or 0) or len(text.split())
        return text, dt, total_tok, (total_tok / dt if dt else total_tok)

    if provider == "anthropic":
        system_prompt = None
        filtered = messages
        if messages and messages[0].get("role") == "system":
            system_prompt = messages[0]["content"]
            filtered = messages[1:]

        t0 = time.time()
        response = anthropic_client.messages.create(
            model=MODEL_STRING,
            max_tokens=500,
            temperature=0.5,
            system=system_prompt or "",
            messages=[{"role": m["role"], "content": m["content"]} for m in filtered],
        )
        dt = time.time() - t0
        text = response.content[0].text.strip()
        total_tok = response.usage.input_tokens + response.usage.output_tokens
        return text, dt, total_tok, (total_tok / dt if dt else total_tok)

    return None
