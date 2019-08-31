#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import uuid
from utils import shellhelper


def is_file_exists(file_path: str) -> bool:
    path = Path(file_path)
    return path.exists()


def delete_if_exists(file_path: str):
    path = Path(file_path)
    if path.exists():
        path.unlink()


def append_line(line, output_file_path: str):
    path = Path(output_file_path)
    with path.open('a', encoding='utf-8') as f:
        print(line, file=f)


def append_lines(lines, output_file_path: str):
    path = Path(output_file_path)
    with path.open('a', encoding='utf-8') as f:
        for line in lines:
            print(line, file=f)


def generate_hex_uuid_4() -> str:
    """Generate UUID (version 4) in hexadecimal representation.
    :return: hexadecimal representation of version 4 UUID.
    """
    return str(uuid.uuid4().hex)


def generate_random_file_name_with_extension(file_extension: str) -> str:
    return "{}.{}".format(generate_hex_uuid_4(), file_extension)


def is_c_file(file_path: str):
    if file_path.endswith('.c'):
        return True
    else:
        return False


def is_test_file(file_path: str):
    result = False
    if is_java_file(file_path):
        if '/' in file_path:
            file_name = file_path.split('/')[-1].split('.')[0]
        else:
            file_name = file_path.split('.')[0]

        if file_name.startswith('Test') or file_name.endswith('Test')\
                or file_name.endswith('Tests') or file_name.endswith('TestCase')\
                or file_name.startswith('Mock') or file_name.endswith('Mock') or 'JUnit' in file_path:
            result = True

    return result


def get_all_java_files(repo_path: str) -> [Path]:
    repo_p = Path(repo_path)
    try:
        java_file_list = list(repo_p.glob('**/*.java'))
    except:
        java_file_list = shellhelper.run('find {} -name "*.java"'.format(repo_path)).split()
    return java_file_list
