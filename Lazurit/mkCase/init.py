import os
from pathlib import Path
import shutil
import pandas as pd
from functools import reduce  
import operator

import json
import yaml
from json.encoder import JSONEncoder
from numpyencoder import NumpyEncoder


MESH_CREATE, CONFIG_CREATE, POST_CREATE = "MESH_CREATE", "CONFIG_CREATE", "POST_CREATE"


class Task:

    def __init__(self, case_name: str, task_name: str, test_path: Path, cases_path: Path, program: str, program_version: str):
        self.post_path = None
        self.done_path = None
        self.calc_path = None
        self.cases_path = cases_path
        self.case_name = case_name
        self.task_name = task_name
        self.test_path = test_path
        self.program = program
        self.program_version = program_version
        self.passed_events = set()
        self.taken_events = set()

    def make_stat(self):
        params = dict(self.__dict__)
        for param in params:
            params[param] = str(params[param])
        with open(self.calc_path / "stat.yml", "w") as f:
            yaml.dump(params, f)

    def make_dirs(self):
        path_name = f"{self.case_name}_{self.task_name}"
        self.calc_path = self.test_path / "calc" / self.program / self.program_version / path_name
        self.done_path = self.test_path / "done" / self.program / self.program_version / path_name
        self.post_path = self.test_path / "post" / self.program / self.program_version / path_name
        if not self.done_path.exists():
            if self.calc_path.exists():
                shutil.rmtree(self.calc_path, ignore_errors=True)
            os.makedirs(self.calc_path, exist_ok=True)
            return True
        else:
            print(f"Задача {self.case_name}_{self.task_name} уже посчитана")
            return False


class Event:

    def __init__(self, kind):
        self.kind = kind


class NullHandler:

    def __init__(self, successor=None):
        self.__successor = successor

    def handle(self, task, event):
        if self.__successor is not None:
            self.__successor.handle(task, event)


class MeshCreate(NullHandler):

    def handle(self, task, event):
        if event.kind == MESH_CREATE:
            event_name = "Создание сетки и даты"
            if event.kind not in (task.passed_events | task.taken_events):
                print(f"Задание получено: \"{event_name}\"")
                task.taken_events.add(event.kind)
                ##################################
                tasks_config_data = pd.read_excel(task.cases_path / task.case_name / "tasks.xlsx")
                template_data = tasks_config_data[["task_name", "template"]]
                if task.task_name in list(template_data.task_name):
                    index_task = tasks_config_data[tasks_config_data.task_name == task.task_name].index.values.astype(int)
                    set_for_task = pd.DataFrame(tasks_config_data.iloc[index_task])  # строка датафрейма с настройками для одной задачи
                    shutil.copytree(task.cases_path / task.case_name / set_for_task.template.values[0], task.calc_path, dirs_exist_ok=True)
                else:
                    raise ValueError("Неверное значение задачи в таблице или конфиге кейса")
                ##################################
            elif event.kind in task.taken_events:
                print(f"Задание выполнено: \"{event_name}\"")
                task.passed_events.add(event.kind)
                task.taken_events.remove(event.kind)
        else:
            # print("Передаю обработку дальше")
            super().handle(task, event)


class ConfigCreate(NullHandler):
    @staticmethod
    def getFromDict(dataDict, mapList):
        return reduce(operator.getitem, mapList, dataDict)

    def setInDict(self, dataDict, mapList, value):
        self.getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value

    def update_config(self, template, data):
        data.drop('task_name', axis = 1, inplace=True)
        sequence = data.columns.str.split('.').to_list()
        values = data.iloc[0].values
        for seq, val in zip(sequence, values):
            try:
                if "[" in val:
                    val = json.loads(val)
            except TypeError:
                pass
            self.setInDict(template, seq, val)
        return template

    def handle(self, task, event):
        if event.kind == CONFIG_CREATE:
            event_name = "Создание конфига"
            if event.kind not in (task.passed_events | task.taken_events):
                print(f"Задание получено: \"{event_name}\"")
                task.taken_events.add(event.kind)
                ##################################
                # Чтение таблицы параметров задач
                tasks_config_data = pd.read_excel(task.cases_path / task.case_name / "tasks.xlsx")
                tasks_config_data.drop('template', axis = 1, inplace=True)
                if task.task_name not in list(tasks_config_data.task_name):
                    raise ValueError("Задачи с таким названием нет, проверьте конфиг кейса и таблицу")
                index_task = tasks_config_data[tasks_config_data.task_name == task.task_name].index.values.astype(int)
                set_for_task = pd.DataFrame(tasks_config_data.iloc[index_task]) # строка датафрейма с настройками для одной задачи
                # Чтение шаблона конфига
                with open(task.cases_path / task.case_name / "templates" / "config.json", "r") as f:
                    temp_config = json.load(f)
                # Замена значение в конфиге значениями из таблицы
                new_conf = self.update_config(template=temp_config, data=set_for_task)
                # Сохранение конфига в папку
                with open(task.calc_path / "config.json", "w") as f:
                    json.dump(new_conf, f, cls=NumpyEncoder)

                ##################################
            elif event.kind in task.taken_events:
                print(f"Задание выполнено: \"{event_name}\"")
                task.passed_events.add(event.kind)
                task.taken_events.remove(event.kind)
        else:
            # print("Передаю обработку дальше")
            super().handle(task, event)


class PostFileCreator(NullHandler):
    def handle(self, task, event):
        if event.kind == POST_CREATE:
            event_name = "Копирование файлов для обработки задачи"
            if event.kind not in (task.passed_events | task.taken_events):
                print(f"Задание получено: \"{event_name}\"")
                task.taken_events.add(event.kind)
                ##################################
                if "post" in os.listdir(task.cases_path / task.case_name):
                    shutil.copytree(task.cases_path / task.case_name / "post", task.calc_path / "post")
                else:
                    print(f"Задача: {task.case_name}_{task.task_name} не имеет файлов для постобработки")
                ##################################
            elif event.kind in task.taken_events:
                print(f"Задание выполнено: \"{event_name}\"")
                task.passed_events.add(event.kind)
                task.taken_events.remove(event.kind)
        else:
            # print("Передаю обработку дальше")
            super().handle(task, event)


class EventGiver:

    def __init__(self):
        self.handlers = MeshCreate(ConfigCreate(PostFileCreator()))
        self.events = []

    def add_event(self, event):
        self.events.append(event)

    def handle_events(self, task):
        for event in self.events:
            self.handlers.handle(task, event)


if __name__ == "__main__":
    CASE_PATH = Path(r"D:\project\GIT\poltsh_ref\cases")
    TEST_PATH = Path(r"C:\Users\vvbuley\Desktop\polish_test")


    events = [Event(MESH_CREATE), Event(CONFIG_CREATE), Event(POST_CREATE)]

    event_giver = EventGiver()

    for event in events:
        event_giver.add_event(event)

    task = Task(case_name="ROG_15",
                task_name="y_1",
                test_path=Path(r"C:\Users\vvbuley\Desktop\polish_test"),
                program="Lazurit",
                program_version="Lazurit_0.1")

    task.make_dirs()
    task.make_stat()
    event_giver.handle_events(task)
