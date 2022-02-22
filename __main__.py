from pathlib import Path
import os
from sys import platform
import argparse
import logging

import run_util.__main__ as run_util
import Lazurit.mkCase.init as LazmkCase
import zircon.mkCase.init as ZinmkCase

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


def init_case(case_name, test_path, program, program_version, cases_path):
    for task_name in autotest_config["cases"][case_name]["tasks"]:
        match program:
            case "Lazurit":
                new_task = LazmkCase.Task(case_name=case_name,
                                          task_name=task_name,
                                          test_path=test_path,
                                          cases_path=cases_path,
                                          program=program,
                                          program_version=program_version)
            case "Zircon":
                new_task = ZinmkCase.Task(case_name=case_name,
                                          task_name=task_name,
                                          test_path=test_path,
                                          cases_path=cases_path,
                                          program=program,
                                          program_version=program_version)
        if new_task.make_dirs():
            tasks_to_run[case_name].append(new_task)


def start_task():
    pass


if __name__ == "__main__":
    logging.basicConfig(filename="log.txt", level=logging.INFO, filemode="w")
    # считываем конфиг
    test_path = Path(os.getcwd())  # Путь до папки, где проходит тестирование
    logging.info(f"Тестирование начато в {test_path.__str__()}")
    autotest_config = read_autotest_config(test_path)  # Чтение конфига
    logging.info(f"Тестируемое ПО --- {autotest_config['program']}")
    logging.info(f"Версия ПО --- {autotest_config['program_version']}")
    parser = argparse.ArgumentParser(description="Описание параметров запуска")
    parser.add_argument("--test_path", type=str, help="путь, где проводится тестирование")
    parser.add_argument("--case_path", type=str, help="Путь до папки с тестовыми кейсами")
    parser.add_argument("--path_to_autotest", type=str, help="Путь до программы")
    args = parser.parse_args()
    autotest_config["test_path"] = args.test_path
    autotest_config["case_path"] = args.case_path
    autotest_config["path_to_autotest"] = args.path_to_autotest
    CASES_PATH = Path(autotest_config["case_path"])
    TEST_PATH = Path(autotest_config["test_path"])
    PATH_TO_AUTOTEST = Path(autotest_config["path_to_autotest"])

    #### ИНИЦИАЛИЗАЦИЯ КЕЙСОВ
    match autotest_config["program"]:
        case "Lazurit":
            events = [LazmkCase.Event(LazmkCase.MESH_CREATE), LazmkCase.Event(LazmkCase.CONFIG_CREATE), LazmkCase.Event(LazmkCase.POST_CREATE)]
            event_giver = LazmkCase.EventGiver()
        case "Zircon":
            events = [ZinmkCase.Event(ZinmkCase.MESH_CREATE), ZinmkCase.Event(ZinmkCase.CONFIG_CREATE), ZinmkCase.Event(ZinmkCase.POST_CREATE)]
            event_giver = LazmkCase.EventGiver()

    for event in events:
        event_giver.add_event(event)

    tasks_to_run = {}
    for case in autotest_config["cases"]:
        if (CASES_PATH / case).exists():
            tasks_to_run[case] = []
            init_case(case_name=case,
                      test_path=Path(autotest_config["test_path"]),
                      program=autotest_config["program"],
                      program_version=autotest_config["program_version"],
                      cases_path=CASES_PATH)
        else:
            logging.error(f"Такого кейса нет в базе: {case}")
            raise KeyError(f"Такого кейса нет в базе: {case}")

    for case_name in tasks_to_run:
        for task in tasks_to_run[case_name]:
            event_giver.handle_events(task)
            task.make_stat()

    #### ЗАПУСК НА РАСЧЁТ
    for case_name in tasks_to_run:
        for task in tasks_to_run[case_name]:
            match platform:
                case "win32":
                    template = PATH_TO_AUTOTEST / autotest_config["program"] / "runTask" / "templates" / "run.bat"
                    run_util.run_task(run_util.WindowsRunTask(), template, task.calc_path, autotest_config)
                case "linux":
                    passport_template = PATH_TO_AUTOTEST / autotest_config["program"] / "runTask" / "templates" / "passport.json"
                    template = PATH_TO_AUTOTEST / autotest_config["program"] / "runTask" / "templates" / "199.sh"
                    run_util.run_task(run_util.LinuxRunTask(), template, task.calc_path, autotest_config, passport_template)
                case _:
                    raise ValueError("Данная система не поддерживает запуск приложения")

    ### ПОСТОБРАБОТКА


