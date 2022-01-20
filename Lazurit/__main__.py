from pathlib import Path
import os
from sys import platform
import argparse
import mkCase.init as mkCase

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


def init_case(case_name, test_path, program, program_version):
    for task_name in autotest_config["cases"][case_name]["tasks"]:
        new_task = mkCase.Task(case_name=case_name,
                               task_name=task_name,
                               test_path=test_path,
                               program=program,
                               program_version=program_version)
        new_task.make_dirs()
        new_task.make_stat()
        tasks_to_run[case_name].append(new_task)
        print("Создано:", new_task.case_name, new_task.task_name, sep="---")


def start_task():
    pass


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
    CASE_PATH = Path(autotest_config["case_path"])
    TEST_PATH = Path(autotest_config["test_path"])
    # # выяснение текущей операционной системы для определения сценария
    # cur_os = platform

    #### ИНИЦИАЛИЗАЦИЯ КЕЙСОВ

    events = [mkCase.Event(mkCase.MESH_CREATE), mkCase.Event(mkCase.CONFIG_CREATE)]
    event_giver = mkCase.EventGiver()
    for event in events:
        event_giver.add_event(event)

    tasks_to_run = {}
    for case in autotest_config["cases"]:
        if (CASE_PATH / case).exists():
            tasks_to_run[case] = []
            init_case(case_name=case,
                      test_path=Path(autotest_config["test_path"]),
                      program=autotest_config["program"],
                      program_version=autotest_config["program_version"])
        else:
            raise KeyError(f"Такого кейса нет в базе: {case}")

    for case_name in tasks_to_run:
        for task in tasks_to_run[case_name]:
            event_giver.handle_events(task)

    #### ЗАПУСК НА РАСЧЁТ
