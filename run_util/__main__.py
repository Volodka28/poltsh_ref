import os
import shutil
from pathlib import Path
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

    def template_method(self, template, task_path, autotest_config, passport):
        self.read_template(template)
        self.fill_template(task_path, autotest_config)
        self.make_passport(task_path, autotest_config, passport)
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

    def make_passport(self, task_path, autotest_config, passport) -> None:
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
        threads_count = {
            "knl": 8,
            "broadwell": 8,
            "aviator3": 8,
            "haswell": 8,
            "skylake": 8,
            "cascadelake": 8
        }
        jcpu_node = {
            "knl": 8,
            "broadwell": 8,
            "aviator3": 8,
            "haswell": 8,
            "skylake": 8,
            "cascadelake": 8
        }
        
        task_setting = read_file(task_path, "stat.")
        init_task = autotest_config["cases"][task_setting["case_name"]]["tasks"][task_setting["task_name"]]
        match [init_task['dont'], init_task['init']]:
            case ["dont", "mesh"]:
                comand = f"{autotest_config['program_version']} --dont --import_mesh --threads {threads_count[autotest_config['node_type']]}"
            case ["dont", "data"]:
                comand = f"{autotest_config['program_version']} --dont --threads {threads_count[autotest_config['node_type']]}"
            case ["cont", "data"]:
                comand = f"{autotest_config['program_version']} --cont -1 --threads {threads_count[autotest_config['node_type']]}"
            case _:
                raise KeyError('недопустимые значения для инициализации задачи')
        fill_template = self.template.format(start_str=comand,
                                             nodes_count=autotest_config["node_count"],
                                             jcpu_node=jcpu_node[autotest_config['node_type']],
                                             type_node=autotest_config['node_type'])
        with open(task_path / "start.sh", "w") as f:
            f.write(fill_template)

    def run_task(self, task_path) -> None:
        print(f"Задача {task_path.__str__()} запущена")
        work_path = os.getcwd()
        os.chdir(task_path)
        os.system("./start.sh")
        os.chdir(work_path)

    def make_passport(self, task_path, autotest_config, passport) -> None:
        with open(passport, "r") as f:
            passport = json.load(f)
        passport["user"] = os.system("echo $USER")
        passport["work_name"] = autotest_config["work_name"]
        with open(task_path / "passport.json", "w") as f:
            json.dump(passport, f, ensure_ascii=True)


def run_task(abstract_class: AbstractTaskRun, template, task_path, autotest_config, passport_template=None):
    abstract_class.template_method(template, task_path, autotest_config, passport_template)
