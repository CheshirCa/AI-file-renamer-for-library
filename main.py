import re
import os
import sys
import json
import logging
import tempfile
import shutil
import argparse
from file_tools import identify_main_document, extract_text_data
from llm_client import send_to_llm
from prompts import build_initial_prompt, build_text_analysis_prompt
from formats import get_handler_for_file

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def rename_file(old_path, new_name):
    """Переименовывает файл с сохранением пути"""
    dir_path = os.path.dirname(old_path)
    new_path = os.path.join(dir_path, new_name)
    try:
        os.rename(old_path, new_path)
        logger.info(f"Файл переименован: {old_path} → {new_path}")
        print(f"Файл переименован: {new_path}")
    except Exception as e:
        logger.error(f"Ошибка при переименовании файла: {e}")

def handle_llm_decision(archive_path, archive_content, llm_response, auto_rename=False):
    """
    Обрабатывает ответ LLM, включая извлечение текста и предложение имени.
    llm_response может быть строкой JSON или уже словарем.
    """
    # Если пришла строка, пытаемся преобразовать в dict
    if isinstance(llm_response, str):
        import re, json
        cleaned_response_str = re.sub(r'```.*?```', '', llm_response, flags=re.DOTALL).strip()
        try:
            llm_response = json.loads(cleaned_response_str)
        except json.JSONDecodeError as e:
            logging.error(f"Ошибка разбора JSON ответа LLM: {e}\nОтвет (обрезано 500 символов): {cleaned_response_str[:500]}")
            return
    elif not isinstance(llm_response, dict):
        logging.error(f"LLM вернула неожиданный тип: {type(llm_response)}")
        return

    decision = llm_response.get('decision')
    if decision == 'rename':
        new_name = llm_response.get('new_name')
        logging.info(f"Предлагаемое имя архива: {new_name}")
        print(new_name)
        if auto_rename:
            rename_file(archive_path, new_name)
        else:
            answer = input(f"Переименовать архив в '{new_name}'? [y/N]: ").strip().lower()
            if answer == 'y':
                rename_file(archive_path, new_name)
    elif decision == 'need_more_data':
        target_file = llm_response.get('target')
        parameters = llm_response.get('parameters', {})

        file_obj = next((f for f in archive_content['files'] if f['name'] == target_file), None)
        if not file_obj:
            main_doc_name = identify_main_document(archive_content['files'])
            file_obj = next((f for f in archive_content['files'] if f['name'] == main_doc_name), None)
            if not file_obj:
                logging.error("В архиве не найдено подходящих файлов для обработки")
                return
            logging.info(f"Найден fallback файл: {file_obj['name']}")

        extracted_text = extract_text_data(file_obj['path'], parameters)
        logging.debug(f"Извлечено данных (первые 500 символов): {extracted_text[:500]}...")

        text_prompt = build_text_analysis_prompt(
            archive_path,
            archive_content,
            file_obj['name'],
            extracted_text
        )
        text_response = send_to_llm(text_prompt)
        handle_llm_decision(archive_path, archive_content, text_response, auto_rename)
    else:
        logging.warning("LLM вернула неизвестное решение")

def analyze_archive(archive_path, auto_rename=False):
    logger.info("Анализируем содержимое архива...")

    tmp_dir = tempfile.mkdtemp()
    files_list = []
    try:
        import patoolib
        patoolib.extract_archive(archive_path, outdir=tmp_dir)
    except Exception as e:
        logger.error(f"Не удалось распаковать архив: {e}")
        return

    for root, _, files in os.walk(tmp_dir):
        for f in files:
            file_path = os.path.join(root, f)
            size = os.path.getsize(file_path)
            files_list.append({
                'name': f,
                'path': file_path,
                'type': 'file',
                'size': size
            })

    archive_content = {'files': files_list, 'metadata_content': {}}
    logger.debug(f"Содержимое архива: {archive_content}")

    prompt = build_initial_prompt(os.path.basename(archive_path), archive_content)
    response_str = send_to_llm(prompt)
    try:
        response = json.loads(response_str)
        handle_llm_decision(archive_path, archive_content, response, auto_rename)
    except Exception as e:
        logger.error(f"Ошибка разбора JSON ответа LLM: {e}")

    shutil.rmtree(tmp_dir, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="Авто-переименование архивов")
    parser.add_argument("--file", required=True, help="Путь к архиву")
    parser.add_argument("--rename", action="store_true", help="Автоматически применять предложенное имя")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        logger.error(f"Файл не найден: {args.file}")
        return

    analyze_archive(args.file, auto_rename=args.rename)

if __name__ == "__main__":
    main()
