# users/utils/pkce_store.py
from django.core.cache import cache

KEY_FMT = "google:pkce:{state}"
TTL = 600  # 10분

def save_verifier(state: str, code_verifier: str):
    cache.set(KEY_FMT.format(state=state), code_verifier, timeout=TTL)

def pop_verifier(state: str) -> str | None:
    key = KEY_FMT.format(state=state)
    val = cache.get(key)
    if val:
        cache.delete(key)
    return val
