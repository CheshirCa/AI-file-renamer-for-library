import os
import patoolib
import fnmatch
from typing import Dict, Any, List

def extract_archive(archive_path: str, output_dir: str) -> None:
    """Распаковывает архив в указанную директорию"""
    try:
        patoolib.extract_archive(archive_path, outdir=output_dir)
    except Exception as e:
        raise Exception(f"Ошибка распаковки архива: {e}")

def scan_archive_content(directory: str) -> Dict[str, Any]:
    """Сканирует содержимое распакованного архива"""
    content = {
        'files': [],
        'metadata_content': {}
    }
    
    for root, dirs, files in os.walk(directory):
        for name in files + dirs:
            full_path = os.path.join(root, name)
            rel_path = os.path.relpath(full_path, directory)
            
            item_info = {
                'name': rel_path,
                'type': 'directory' if os.path.isdir(full_path) else 'file',
                'size': os.path.getsize(full_path) if os.path.isfile(full_path) else None
            }
            
            content['files'].append(item_info)
            
            # Метаданные из DIZ/README
            if name.lower() in ['file_id.diz', 'readme.txt', 'readme.md', '*.nfo'] or \
               fnmatch.fnmatch(name.lower(), 'read*me*'):
                try:
                    # Пытаемся прочитать в разных кодировках
                    for encoding in ['utf-8', 'cp1251', 'cp866']:
                        try:
                            with open(full_path, 'r', encoding=encoding, errors='ignore') as f:
                                content['metadata_content'][name] = f.read(2000)
                                break
                        except:
                            continue
                except:
                    pass
    
    return content

def find_file_by_pattern(files_list: list, pattern: str) -> str:
    """
    Возвращает первый файл, подходящий под шаблон (wildcard)
    """
    for file_info in files_list:
        if file_info['type'] == 'file' and fnmatch.fnmatch(file_info['name'], pattern):
            return file_info['name']
    return None
