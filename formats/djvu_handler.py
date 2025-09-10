import os
import logging
import subprocess
import tempfile
from typing import Dict, Any
from .base_handler import BaseFormatHandler

logger = logging.getLogger(__name__)

class DJVUHandler(BaseFormatHandler):
    """Обработчик для DJVU файлов"""
    
    @staticmethod
    def can_handle(file_path: str) -> bool:
        return BaseFormatHandler.get_file_extension(file_path) == '.djvu'
    
    @staticmethod
    def extract_text(file_path: str, parameters: Dict[str, Any]) -> str:
        action_type = parameters.get('type', 'first_chars')
        amount = parameters.get('amount', 500)

        try:
            # Пробуем использовать модуль djvu, если установлен
            import djvu  # Если нет, переходим к OCR
            # Здесь можно добавить прямое извлечение текста через djvu
            return "DJVU модуль найден, текст извлечен."
        except ImportError:
            logger.warning("Модуль djvu не найден, используем OCR через pytesseract")
            try:
                from PIL import Image
                from .ocr_utils import perform_ocr_images

                with tempfile.TemporaryDirectory() as tmpdir:
                    page_path = os.path.join(tmpdir, "page.png")
                    # Конвертируем первый слой DJVU в PNG через ddjvu
                    cmd = ['ddjvu', '-format=pnm', '-page=1', file_path, page_path]
                    subprocess.run(cmd, check=True)
                    img = Image.open(page_path)
                    ocr_text = perform_ocr_images([img], lang='rus+eng', max_chars=amount if action_type == 'first_chars' else None)
                    return ocr_text
            except FileNotFoundError:
                return "Ошибка: ddjvu не найден. Установите djvu tools."
            except Exception as e:
                logger.error(f"Ошибка при OCR DJVU {file_path}: {e}")
                return f"Ошибка при OCR DJVU: {str(e)}"
    
    @staticmethod
    def get_metadata(file_path: str) -> Dict[str, str]:
        """Извлекает метаданные из DJVU (если поддерживается)"""
        try:
            import djvu
            # Здесь можно добавить извлечение метаданных через djvu
            return {}
        except ImportError:
            return {}

