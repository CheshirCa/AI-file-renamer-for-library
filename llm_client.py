import json
import google.generativeai as genai
from config import GEMINI_API_KEY
import logging

logger = logging.getLogger(__name__)

# Настраиваем Gemini
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = 'gemini-2.5-flash'

def send_to_llm(prompt: str) -> str:
    """
    Отправляет промпт в Gemini API и возвращает ответ
    """
    try:
        logger.debug(f"Отправляем запрос к Gemini API (модель: {MODEL_NAME})...")
        
        model = genai.GenerativeModel(MODEL_NAME)
        
        # Формируем промпт с четкими инструкциями по JSON
        system_prompt = """Ты должен отвечать ТОЛЬКО в формате JSON, без каких-либо дополнительных объяснений, комментариев или текста вне JSON. 
Твой ответ должен быть валидным JSON объектом с одной из двух структур:

1. Для переименования:
{"decision": "rename", "new_name": "имя_файла.расширение"}

2. Для запроса дополнительных данных:
{"decision": "need_more_data", "action": "действие", "target": "конкретное_имя_файла.расширение", "parameters": {"type": "тип", "amount": количество}}

ВАЖНО: В поле "target" всегда указывай конкретное существующее имя файла из структуры архива, а не общие имена like 'document.fb2'."""
        
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        logger.debug(f"Промпт: {full_prompt[:200]}...")
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1000,
            )
        )
        
        # Проверяем, что ответ не пустой
        if not response or not response.text:
            raise ValueError("Пустой ответ от Gemini API")
        
        logger.debug(f"Получен ответ от Gemini: {response.text}")
        
        # Очищаем ответ от возможных markdown обратных кавычек
        cleaned_response = response.text.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        
        return cleaned_response
        
    except IndexError as e:
        logger.error(f"Ошибка индекса в ответе Gemini: {e}")
        return get_fallback_response(prompt)
    except Exception as e:
        logger.error(f"Ошибка при обращении к Gemini API: {e}")
        return get_fallback_response(prompt)

def get_fallback_response(prompt: str) -> str:
    """
    Возвращает fallback response на основе анализа промпта
    """
    try:
        # Анализируем промпт чтобы понять контекст
        if "pdf" in prompt.lower() or ".pdf" in prompt:
            return json.dumps({
                "decision": "need_more_data",
                "action": "extract_text",
                "target": "*.pdf",
                "parameters": {"type": "first_chars", "amount": 1000}
            })
        elif "docx" in prompt.lower() or ".docx" in prompt:
            return json.dumps({
                "decision": "need_more_data", 
                "action": "extract_text",
                "target": "*.docx",
                "parameters": {"type": "first_chars", "amount": 1000}
            })
        elif "txt" in prompt.lower() or ".txt" in prompt:
            return json.dumps({
                "decision": "need_more_data",
                "action": "extract_text", 
                "target": "*.txt",
                "parameters": {"type": "first_chars", "amount": 1000}
            })
        else:
            # Общий fallback
            return json.dumps({
                "decision": "need_more_data",
                "action": "extract_text",
                "target": "document.*", 
                "parameters": {"type": "first_chars", "amount": 1000}
            })
    except:
        # Ultimate fallback
        return '{"decision": "need_more_data", "action": "extract_text", "target": "*.pdf", "parameters": {"type": "first_chars", "amount": 1000}}'
