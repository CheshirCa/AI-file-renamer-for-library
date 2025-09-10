import os
import json
from typing import Dict, Any
from file_tools import identify_main_document

def build_initial_prompt(archive_name: str, archive_content: Dict[str, Any]) -> str:
    """
    Строит первоначальный промпт для LLM
    """
    # Автоматически определяем основной документ
    main_doc = identify_main_document(archive_content['files'])

    # Приоритет для FILE_ID.DIZ, readme* и nfo
    metadata_files = archive_content.get('metadata_content', {})
    priority_meta = list(metadata_files.keys())
    if priority_meta:
        main_doc_desc = f"{main_doc if main_doc else 'Не определен'} (метафайл для анализа: {', '.join(priority_meta)})"
    else:
        main_doc_desc = main_doc if main_doc else 'Не определен'

    prompt = f"""
Анализируй структуру архива и доступные метаданные. 

Исходное имя архива: "{archive_name}"
Расширение архива: "{os.path.splitext(archive_name)[1]}"
Основной документ внутри: "{main_doc_desc}"

Содержимое архива:
{json.dumps(archive_content, ensure_ascii=False, indent=2)}

Верни JSON ответ с одним из двух вариантов:

1. Если информации ДОСТАТОЧНО для определения содержания:
{{"decision": "rename", "new_name": "Предлагаемое_имя_архива.расширение"}}

2. Если информации НЕДОСТАТОЧНО:
{{"decision": "need_more_data", "action": "extract_text", "target": "{main_doc}", "parameters": {{"type": "first_chars", "amount": 1000}}}}

ВАЖНО: 
- Предлагаемое имя должно отражать СОДЕРЖИМОЕ АРХИВА
- Сохрани оригинальное расширение архива ({os.path.splitext(archive_name)[1]})
- В поле "target" всегда указывай конкретное существующее имя файла из списка выше
"""
    return prompt

def build_text_analysis_prompt(archive_path: str, archive_content: Dict[str, Any], target_file: str, extracted_text: str) -> str:
    """
    Строит промпт для анализа извлеченного текста
    """
    # Ограничиваем текст и очищаем опасные символы
    preview_text = extracted_text[:2000] if len(extracted_text) > 2000 else extracted_text
    preview_text = preview_text.replace('\n', ' ').replace('"', "'").replace('\\', '/')

    archive_ext = os.path.splitext(archive_path)[1]

    prompt = f"""
Проанализируй текст из файла внутри архива и предложи подходящее имя для АРХИВА.

Архив: {os.path.basename(archive_path)}
Расширение архива: {archive_ext}
Файл внутри архива: {target_file}
Извлечено текста: {len(extracted_text)} символов

Текст: {preview_text}

Верни JSON ответ:
{{"decision": "rename", "new_name": "Предлагаемое_имя_архива{archive_ext}"}}

ВАЖНО: 
- Предлагаемое имя должно отражать СОДЕРЖИМОЕ АРХИВА
- Сохрани оригинальное расширение архива ({archive_ext})
- Имя должно быть понятным и описывать содержание основного документа
"""
    return prompt
