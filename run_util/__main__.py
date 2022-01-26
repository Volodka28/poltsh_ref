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
        self.fill_temp = None

    def template_method(self, template):
        self.read_template(template)
        self.fill_template()
        self.make_passport()
        self.run_task()

    def read_template(self, template):
        with open(template, "r") as f:
            self.fill_temp = f.read()

    @abstractmethod
    def fill_template(self) -> None:
        pass

    @abstractmethod
    def run_task(self) -> None:
        pass

    def make_passport(self) -> None:
        pass


class WindowsRunTask(AbstractTaskRun):
    def fill_template(self) -> None:
        print("win_fill")

    def run_task(self) -> None:
        print("win_run")


class LinuxRunTask(AbstractTaskRun):
    def fill_template(self) -> None:
        print("fill_linux")

    def run_task(self) -> None:
        print("run_linux")

    def make_passport(self) -> None:
        print("passport_linux")


def run_task(abstract_class: AbstractTaskRun, template):
    abstract_class.template_method(template)


if __name__ == "__main__":
    template = Path(r'D:\project\GIT\poltsh_ref\Lazurit\runTask\templates\run.bat')
    match platform:
        case "win32":
            run_task(WindowsRunTask(), template)
        case "linux":
            run_task(LinuxRunTask(), template)
        case _:
            raise ValueError("Данная система не поддерживает запуск приложения")
