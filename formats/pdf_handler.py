import os
import logging
from typing import Dict, Any
from .base_handler import BaseFormatHandler

logger = logging.getLogger(__name__)

class PDFHandler(BaseFormatHandler):
    """Обработчик для PDF файлов"""
    
    @staticmethod
    def can_handle(file_path: str) -> bool:
        return BaseFormatHandler.get_file_extension(file_path) == '.pdf'
    
    @staticmethod
    def extract_text(file_path: str, parameters: Dict[str, Any]) -> str:
        action_type = parameters.get('type', 'first_chars')
        amount = parameters.get('amount', 500)
        
        try:
            import PyPDF2
            text = ""
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                if action_type == 'first_chars':
                    # Извлекаем текст пока не наберем нужное количество символов
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        if len(text) >= amount:
                            break
                    if text.strip():
                        return text[:amount]
                
                elif action_type == 'first_pages':
                    num_pages = min(amount, len(reader.pages))
                    for i in range(num_pages):
                        page_text = reader.pages[i].extract_text()
                        if page_text:
                            text += f"--- Страница {i+1} ---\n{page_text}\n\n"
                    if text.strip():
                        return text

            # Если PDF не содержит текста, пробуем OCR
            logger.warning(f"PDF {file_path} не содержит текста, выполняем OCR...")
            try:
                from pdf2image import convert_from_path
                from .ocr_utils import perform_ocr_images
                images = convert_from_path(file_path)
                ocr_text = perform_ocr_images(images, lang='rus+eng', max_chars=amount if action_type == 'first_chars' else None)
                return ocr_text
            except Exception as e:
                logger.error(f"Ошибка при OCR PDF {file_path}: {e}")
                return f"Ошибка при OCR PDF: {str(e)}"
            
        except ImportError:
            return "Ошибка: PyPDF2 не установлен. Установите: pip install PyPDF2"
        except Exception as e:
            logger.error(f"Ошибка при обработке PDF {file_path}: {e}")
            return f"Ошибка при обработке PDF: {str(e)}"
    
    @staticmethod
    def get_metadata(file_path: str) -> Dict[str, str]:
        """Извлекает метаданные из PDF"""
        try:
            import PyPDF2
            metadata = {}
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                pdf_metadata = reader.metadata
                
                if pdf_metadata:
                    metadata = {
                        'title': getattr(pdf_metadata, 'title', ''),
                        'author': getattr(pdf_metadata, 'author', ''),
                        'subject': getattr(pdf_metadata, 'subject', ''),
                        'creator': getattr(pdf_metadata, 'creator', ''),
                        'producer': getattr(pdf_metadata, 'producer', ''),
                        'creation_date': getattr(pdf_metadata, 'creation_date', ''),
                        'modification_date': getattr(pdf_metadata, 'modification_date', '')
                    }
            
            return {k: v for k, v in metadata.items() if v}
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении метаданных PDF: {e}")
            return {}
