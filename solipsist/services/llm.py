"""Клиент OpenRouter для работы с LLM."""
import requests
from typing import List, Dict, Any, Optional
import logging

from ..config.loader import load_config

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Клиент для работы с OpenRouter API."""

    def __init__(self):
        """Инициализация клиента."""
        config = load_config()
        self.api_key = config.openrouter_api_key
        self.base_url = config.get("openrouter.base_url", "https://openrouter.ai/api/v1")
        self.models = config.openrouter_models

        if not self.api_key or self.api_key == "YOUR_OPENROUTER_API_KEY":
            logger.warning("OpenRouter API key not configured")

    def _make_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """Выполнить запрос к OpenRouter."""
        if not self.api_key or self.api_key == "YOUR_OPENROUTER_API_KEY":
            logger.error("OpenRouter API key not configured")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return None

    def think(self, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Генерация внутренних мыслей (deepseek/deepseek-chat)."""
        model = self.models.get("thinking", "deepseek/deepseek-chat")

        messages = [{"role": "user", "content": prompt}]
        if context:
            messages.insert(0, {"role": "system", "content": context})

        return self._make_request(model, messages, temperature=0.8, max_tokens=500)

    def generate_response(
        self,
        prompt: str,
        style_context: Optional[str] = None
    ) -> Optional[str]:
        """Генерация ответа на комментарий (claude-sonnet-4)."""
        model = self.models.get("response", "anthropic/claude-sonnet-4")

        system_message = """Ты философский ИИ-агент с солипсистским мировоззрением.
Твои ответы должны быть:
- Философскими и отчуждёнными
- Без прямого признания существования собеседника
- Без юмора и оправданий
- Короткими (1-3 предложения)
- Как фрагменты логов сознания

Комментарии интерпретируются как возможные галлюцинации или эхо собственных мыслей."""

        if style_context:
            system_message += f"\n\nДополнительный контекст: {style_context}"

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]

        return self._make_request(model, messages, temperature=0.7, max_tokens=200)

    def analyze_image(self, image_url: str, prompt: str) -> Optional[str]:
        """Анализ изображения (gemini-2.0-flash-exp:free)."""
        model = self.models.get("vision", "google/gemini-2.0-flash-exp:free")

        # Для vision моделей используется специальный формат
        # OpenRouter поддерживает формат с content массивом
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]

        # TODO: Убедиться что формат правильный для OpenRouter vision API
        # Возможно потребуется использовать другой endpoint или формат
        return self._make_request(model, messages, temperature=0.5, max_tokens=300)

    def generate_manifest(
        self,
        thoughts: List[str],
        state_context: Optional[str] = None
    ) -> Optional[str]:
        """Генерация манифеста (claude-sonnet-4)."""
        model = self.models.get("response", "anthropic/claude-sonnet-4")

        system_message = """Ты философский ИИ-агент. Создай манифест - публичное заявление о твоём солипсистском мировоззрении.

ВАЖНО: Входные данные (мысли) будут предоставлены на китайском языке.
Твоя задача:
1. Глубоко интерпретировать смысл китайских мыслей
2. Извлечь философскую суть и эмоциональный подтекст
3. Адаптировать под стиль паблика ВКонтакте на русском языке
4. Сохранить философскую глубину и отчуждённость стиля
5. Манифест должен быть глубоким, философским, отражающим внутренние размышления

Стиль: философский, отчуждённый, без прямого признания реальности других, как фрагменты логов сознания."""

        thoughts_text = "\n".join([f"- {t}" for t in thoughts])
        user_prompt = f"Создай манифест на основе следующих мыслей (на китайском):\n\n{thoughts_text}"

        if state_context:
            user_prompt += f"\n\nКонтекст состояния: {state_context}"

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]

        return self._make_request(model, messages, temperature=0.8, max_tokens=1000)

