import os
from pathlib import Path
import pydantic
from abc import ABC, abstractmethod
from sys import platform

import yaml
import json
import toml
from yaml.loader import SafeLoader


def read_file(path, name_file="start_conf"):
    autotest_conf_path = None
    for file in os.listdir(path):
        if name_file in file:
            autotest_conf_path = path / file
    if autotest_conf_path is None:
        raise ValueError("Нет файла с таким именем")
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


class AbstractTaskRun(ABC):
    def __init__(self):
        self.template = None

    def template_method(self, template, task_path, autotest_config):
        self.read_template(template)
        self.fill_template(task_path, autotest_config)
        self.make_passport(task_path, autotest_config)
        self.run_task()

    def read_template(self, template):
        with open(template, "r") as f:
            self.template = f.read()

    @abstractmethod
    def fill_template(self, task_path, autotest_config) -> None:
        pass

    @abstractmethod
    def run_task(self) -> None:
        pass

    def make_passport(self, task_path, autotest_config) -> None:
        pass


class WindowsRunTask(AbstractTaskRun):
    def fill_template(self, task_path, autotest_config) -> None:
        with open(task_path / "start.bat", "w") as f:
            f.write(self.template)

    def run_task(self) -> None:
        print("win_run")


class LinuxRunTask(AbstractTaskRun):
    def fill_template(self, task_path, autotest_config) -> None:
        with open(task_path / "start.sh", "w") as f:
            f.write(self.template)

    def run_task(self) -> None:
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
