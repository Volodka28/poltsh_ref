import os
import shutil
from pathlib import Path
import pydantic
from abc import ABC, abstractmethod
from sys import platform
from subprocess import PIPE, Popen, run

import yaml
import json
import toml
from yaml.loader import SafeLoader


def read_file(path, name_file="start_conf"):
    file_path = None
    for file in os.listdir(path):
        if name_file in file:
            file_path = path / file
    if file_path is None:
        raise ValueError("Нет файла с таким именем")
    match file_path.suffix:
        case ".json":
            with open(file_path, "r") as file:
                file_path = json.load(file)
        case ".yml":
            with open(file_path, "r") as file:
                file_path = yaml.load(file, Loader=SafeLoader)
        case ".toml":
            with open(file_path, "r") as file:
                file_path = toml.load(file)
    return file_path


class AbstractTaskRun(ABC):
    def __init__(self):
        self.template = None

    def template_method(self, template, task_path, autotest_config):
        self.read_template(template)
        self.fill_template(task_path, autotest_config)
        self.make_passport(task_path, autotest_config)
        self.run_task(task_path)
        self.check_success_calc(task_path)

    def read_template(self, template):
        with open(template, "r") as f:
            self.template = f.read()

    @abstractmethod
    def fill_template(self, task_path, autotest_config) -> None:
        pass

    @abstractmethod
    def run_task(self, task_path) -> None:
        pass

    def make_passport(self, task_path, autotest_config) -> None:
        pass

    def check_success_calc(self, task_path) -> None:
        pass


class WindowsRunTask(AbstractTaskRun):
    def fill_template(self, task_path, autotest_config) -> None:
        task_setting = read_file(task_path, "stat.")
        init_task = autotest_config["cases"][task_setting["case_name"]]["tasks"][task_setting["task_name"]]
        match [init_task['dont'], init_task['init']]:
            case ["dont", "mesh"]:
                comand = f"{autotest_config['program_version']} --threads {autotest_config['proc']} --dont --import_mesh | tee log.txt"
            case ["dont", "data"]:
                comand = f"{autotest_config['program_version']} --threads {autotest_config['proc']} --dont | tee log.txt"
            case ["cont", "data"]:
                comand = f"{autotest_config['program_version']} --threads {autotest_config['proc']} --cont -1 | tee log.txt"
            case _:
                raise KeyError('недопустимые значения для инициализации задачи')

        fill_template = self.template.format(program_path=autotest_config["path_to_lazurit"],
                                             task_dir=task_path.__str__(),
                                             comand=comand)
        with open(task_path / "start.bat", "w") as f:
            f.write(fill_template)

    def run_task(self, task_path) -> None:
        print(f"Задача {task_path.__str__()} запущена")
        work_path = os.getcwd()
        os.chdir(task_path)
        process = run("start.bat", stdout=PIPE)
        os.chdir(work_path)

    def check_success_calc(self, task_path):
        stat = read_file(task_path, "stat.")
        with open(task_path / "log.txt", "r") as f:
            log = [d.replace("\x00", "").rstrip("\n") for d in f.readlines()]
        for i in log[::-1]:
            if i != "":
                last_str = i
                break
        # print(stat)
        if last_str == " ======= Program Lazurit finish! =======":
            print(f"Задача {task_path.__str__()} успешно завершена")
            done_path = Path(stat["test_path"]) / "done" / stat["program"] / stat["program_version"]
            os.makedirs(done_path, exist_ok=True)
            shutil.move(task_path, done_path, copy_function=shutil.copytree)
        else:
            print(f"Задача {task_path.__str__()} недосчиталась")


class LinuxRunTask(AbstractTaskRun):
    def fill_template(self, task_path, autotest_config) -> None:
        with open(task_path / "start.sh", "w") as f:
            f.write(self.template)

    def run_task(self, task_path) -> None:
        print("run_linux")

    def make_passport(self, task_path, autotest_config) -> None:
        print("passport_linux")


def run_task(abstract_class: AbstractTaskRun, template, task_path, autotest_config):
    abstract_class.template_method(template, task_path, autotest_config)


if __name__ == "__main__":
    template = Path(r'D:\project\GIT\poltsh_ref\Lazurit\runTask\templates\run.bat')
    task_path = Path(r"C:\Users\vvbuley\Desktop\polish_test\calc\lazurit\Lazurit.WIN.AVX.exe\ROG_15_y_0_1")
    autotest_config = read_file(path=Path(r"C:\Users\vvbuley\Desktop\polish_test"), name_file="start_conf")
    match platform:
        case "win32":
            run_task(WindowsRunTask(), template, task_path, autotest_config)
        case "linux":
            run_task(LinuxRunTask(), template, task_path, autotest_config)
        case _:
            raise ValueError("Данная система не поддерживает запуск приложения")
