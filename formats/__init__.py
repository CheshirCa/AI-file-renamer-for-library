from typing import Dict
import logging

HANDLERS = []

def _register_handlers():
    """Ленивая регистрация обработчиков"""
    from .txt_handler import TXTHandler
    from .pdf_handler import PDFHandler
    from .docx_handler import DOCXHandler
    from .fb2_handler import FB2Handler
    from .zip_handler import ZIPHandler
    from .epub_handler import EPUBHandler
    from .image_handler import IMAGEHandler  # Добавляем новый обработчик

    global HANDLERS
    HANDLERS = [
        TXTHandler,
        PDFHandler,
        DOCXHandler,
        FB2Handler,
        ZIPHandler,
        EPUBHandler,
        IMAGEHandler  # Добавляем в список обработчиков
    ]


def get_handler_for_file(file_path: str):
    """
    Возвращает подходящий обработчик для файла
    """
    if not HANDLERS:
        _register_handlers()

    for handler in HANDLERS:
        if handler.can_handle(file_path):
            return handler

    from .base_handler import BaseFormatHandler
    return BaseFormatHandler


def extract_text_data(file_path: str, parameters: dict) -> str:
    """
    Основная функция для извлечения текста из файла
    """
    handler = get_handler_for_file(file_path)
    return handler.extract_text(file_path, parameters)


def get_file_metadata(file_path: str) -> Dict[str, str]:
    """
    Извлекает метаданные из файла (если поддерживается)
    """
    handler = get_handler_for_file(file_path)
    if hasattr(handler, 'get_metadata'):
        return handler.get_metadata(file_path)
    return {}
