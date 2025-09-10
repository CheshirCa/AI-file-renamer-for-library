import os
import logging
import fnmatch
from typing import Dict, Any

logger = logging.getLogger(__name__)

def identify_main_document(files_list: list) -> str:
    """
    Определяет основной документ в списке файлов
    """
    document_files = []
    document_extensions = ['.pdf', '.docx', '.txt', '.fb2', '.djvu', '.epub', '.zip']
    
    for file_info in files_list:
        if file_info['type'] == 'file':
            ext = os.path.splitext(file_info['name'])[1].lower()
            if ext in document_extensions:
                document_files.append(file_info)
    
    if not document_files:
        return ""
    
    # Сортируем по размеру (предполагаем, что больший файл - основной)
    document_files.sort(key=lambda x: x['size'] or 0, reverse=True)
    
    return document_files[0]['name']


def extract_text_data(file_path: str, parameters: Dict[str, Any]) -> str:
    """
    Основная функция для извлечения текста из файла
    Использует модульную систему обработчиков
    """
    try:
        from formats import extract_text_data as format_extract_text
        return format_extract_text(file_path, parameters)
    except ImportError as e:
        logger.error(f"Ошибка импорта модуля formats: {e}")
        return _fallback_extract_text(file_path, parameters)
    except Exception as e:
        logger.error(f"Ошибка в модульной системе: {e}")
        return _fallback_extract_text(file_path, parameters)


def _fallback_extract_text(file_path: str, parameters: Dict[str, Any]) -> str:
    """
    Простая реализация на случай проблем с модулями
    """
    action_type = parameters.get('type', 'first_chars')
    amount = parameters.get('amount', 500)
    
    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        if file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(amount)
        elif file_ext == '.pdf':
            try:
                import PyPDF2
                text = ""
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        if len(text) >= amount:
                            break
                return text[:amount]
            except:
                return "Не удалось прочитать PDF"
        elif file_ext == '.docx':
            try:
                import docx
                doc = docx.Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs])
                return text[:amount]
            except:
                return "Не удалось прочитать DOCX"
        elif file_ext == '.epub':
            try:
                import zipfile
                text_parts = []
                with zipfile.ZipFile(file_path, 'r') as epub_zip:
                    for file_name in epub_zip.namelist():
                        if file_name.endswith(('.xhtml', '.html', '.xml', '.txt')):
                            try:
                                with epub_zip.open(file_name) as f:
                                    content = f.read().decode('utf-8', errors='ignore')
                                    text_parts.append(content[:200])
                                    if len(' '.join(text_parts)) >= amount:
                                        break
                            except:
                                continue
                return ' '.join(text_parts)[:amount]
            except:
                return "Не удалось прочитать EPUB"
        elif file_ext == '.djvu':
            try:
                from formats.djvu_handler import DJVUHandler
                return DJVUHandler.extract_text(file_path, parameters)
            except:
                return "Ошибка: не установлен модуль djvu. Установите его для работы с djvu файлами..."
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(amount)
    except Exception as e:
        return f"Ошибка при fallback обработке: {str(e)}"

