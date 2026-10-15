import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

# Load .env from backend directory or project root if present
for env_path in [
    Path.cwd() / ".env",
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]:
    if env_path.exists():
        load_dotenv(env_path)
        break

def get_gemini_api_key() -> str:
    return os.environ.get("GEMINI_API_KEY", "").strip()

def get_groq_api_key() -> str:
    return os.environ.get("GROQ_API_KEY", "").strip()

def is_live_llm_available() -> bool:
    """Returns True if a valid GEMINI_API_KEY or GROQ_API_KEY is present."""
    gemini_key = get_gemini_api_key()
    if gemini_key and not gemini_key.startswith("your_") and len(gemini_key) > 10:
        return True
    groq_key = get_groq_api_key()
    if groq_key and not groq_key.startswith("your_") and len(groq_key) > 10:
        return True
    return False

def get_active_provider() -> str:
    """Returns the primary active LLM provider name."""
    gemini_key = get_gemini_api_key()
    if gemini_key and not gemini_key.startswith("your_") and len(gemini_key) > 10:
        return "Google Gemini"
    groq_key = get_groq_api_key()
    if groq_key and not groq_key.startswith("your_") and len(groq_key) > 10:
        return "Groq"
    return "none"

def get_active_model() -> str:
    """Returns the configured model name."""
    provider = get_active_provider()
    if provider == "Google Gemini":
        return os.environ.get("GEMINI_MODEL", "gemini-3.5-flash").strip()
    elif provider == "Groq":
        return os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
    return "none"

# Backward compatibility alias
def get_groq_model() -> str:
    return get_active_model()

def invoke_llm_structured(system_prompt: str, user_prompt: str, pydantic_schema: type):
    """
    Structured LLM invocation with Google Gemini (primary) and Groq (secondary).
    Returns: (result_or_none, mode_str, error_msg_or_none)
    - mode_str is 'LIVE_LLM' if a real model response was parsed successfully.
    - mode_str is 'DETERMINISTIC_FALLBACK' if key is missing, model is unreachable,
      or the response cannot be parsed — in all cases the error is returned honestly.
    """
    if not is_live_llm_available():
        return None, "DETERMINISTIC_FALLBACK", "No live LLM API key configured. Running in deterministic fallback mode."

    provider = get_active_provider()

    # ── 1. Google Gemini Provider ───────────────────────────────────────────
    if provider == "Google Gemini":
        gemini_key = get_gemini_api_key()
        primary_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash").strip()
        candidate_models = [primary_model]
        for fallback in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error = None
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=gemini_key, http_options=types.HttpOptions(timeout=10000))

            for model_name in candidate_models:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=user_prompt,
                        config={
                            "system_instruction": system_prompt,
                            "response_mime_type": "application/json",
                            "response_schema": pydantic_schema,
                            "temperature": 0.0,
                        },
                    )
                    if response and response.text:
                        parsed = pydantic_schema.model_validate_json(response.text)
                        return parsed, "LIVE_LLM", None
                except Exception as e:
                    last_error = e
                    continue

            # If all Gemini models failed, raise last_error to be formatted below
            raise last_error if last_error else RuntimeError("Gemini models returned empty response")

        except Exception as e:
            err_msg = str(e)
            # Try secondary Groq failover if available
            groq_key = get_groq_api_key()
            if groq_key and not groq_key.startswith("your_") and len(groq_key) > 10:
                try:
                    model = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
                    from langchain_groq import ChatGroq
                    llm = ChatGroq(model=model, temperature=0, api_key=groq_key)
                    structured_llm = llm.with_structured_output(pydantic_schema)
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                    result = structured_llm.invoke(messages)
                    if result:
                        return result, "LIVE_LLM", None
                except Exception:
                    pass

            if "503" in err_msg or "UNAVAILABLE" in err_msg:
                friendly = f"Gemini API experiencing temporary high demand: {err_msg}"
            elif "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                friendly = f"Gemini quota/rate limit reached: {err_msg}"
            elif "401" in err_msg or "INVALID_ARGUMENT" in err_msg:
                friendly = f"Gemini authentication failed — check GEMINI_API_KEY: {err_msg}"
            else:
                friendly = f"Gemini request failed: {err_msg}"
            return None, "DETERMINISTIC_FALLBACK", friendly

    # ── 2. Groq Provider (Secondary) ─────────────────────────────────────────
    elif provider == "Groq":
        model = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
        groq_key = get_groq_api_key()
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(model=model, temperature=0, api_key=groq_key)
            structured_llm = llm.with_structured_output(pydantic_schema)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            result = structured_llm.invoke(messages)
            return result, "LIVE_LLM", None
        except Exception as e:
            err_msg = str(e)
            if "404" in err_msg or "model_not_found" in err_msg:
                friendly = f"Groq model '{model}' not found: {err_msg}"
            elif "401" in err_msg or "authentication" in err_msg.lower():
                friendly = f"Groq authentication failed: {err_msg}"
            elif "429" in err_msg:
                friendly = f"Groq rate limit reached: {err_msg}"
            else:
                friendly = f"Groq request failed: {err_msg}"
            return None, "DETERMINISTIC_FALLBACK", friendly

    return None, "DETERMINISTIC_FALLBACK", "No active LLM provider found."
