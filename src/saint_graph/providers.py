from dataclasses import dataclass
from typing import Dict

@dataclass
class ProviderConfig:
    ai_role: str
    user_role: str

# プロバイダーごとの基本設定
PROVIDERS: Dict[str, ProviderConfig] = {
    "google": ProviderConfig(ai_role="model", user_role="user"),
    "openai": ProviderConfig(ai_role="assistant", user_role="user"),
}

# モデル名とプロバイダーの紐付け
MODEL_TO_PROVIDER = {
    # Google Gemini シリーズ (2026年最新)
    "gemini-3.0-flash": "google",
    "gemini-3.0-pro": "google",
    "gemini-2.5-flash-lite": "google",
    
    # OpenAI GPT シリーズ (2026年最新)
    "gpt-5.2": "openai",
}

def get_provider_config(model_name: str) -> ProviderConfig:
    """モデル名から適切なプロバイダー設定を返します。"""
    provider_name = MODEL_TO_PROVIDER.get(model_name)
    
    # マップにない場合は推論を試みる
    if not provider_name:
        if "gemini" in model_name.lower():
            provider_name = "google"
        elif "gpt" in model_name.lower():
            provider_name = "openai"
        else:
            provider_name = "google" # デフォルト
            
    return PROVIDERS[provider_name]
