from pathlib import Path
import os
from sys import platform
import argparse

import yaml
from yaml.loader import SafeLoader
import toml
import json

def read_autotest_config(path, name_config="start_conf"):
    autotest_conf_path = None
    for file in os.listdir(path):
        if name_config in file:
            autotest_conf_path = path / file
    if autotest_conf_path is None:
        raise ValueError("Нет конфига с таким именем")
    match autotest_conf_path.suffix:
        case ".json":
            with open(autotest_conf_path, "r") as file:
                autotest_conf = json.load(file)
        case ".yml":
            with open(autotest_conf_path, "r") as file:
                autotest_conf = yaml.load(file, Loader=SafeLoader)
        case ".toml":
            with open(autotest_conf_path, "r") as file:
                autotest_conf = toml.load(file)
    return autotest_conf



if __name__ == "__main__":
    # считываем конфиг
    test_path = Path(os.getcwd())  # Путь до папки, где проходит тестирование
    autotest_config = read_autotest_config(test_path)  # Чтение конфига
    parser = argparse.ArgumentParser(description="Описание параметров запуска")
    parser.add_argument("--test_path", type=str, help="путь, где проводится тестирование")
    parser.add_argument("--case_path", type=str, help="Путь до папки с тестовыми кейсами")
    args = parser.parse_args()
    autotest_config["test_path"] = args.test_path
    autotest_config["case_path"] = args.case_path
    # выяснение текущей операционной системы для определения сценария
    cur_os = platform
    #### ИНИЦИАЛИЗАЦИЯ КЕЙСОВ
    for case in autotest_config["cases"]:
        pass



    #### ЗАПУСК НА РАСЧЁТ

