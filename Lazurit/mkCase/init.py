import os
from pathlib import Path
import shutil
import json
import yaml

MESH_CREATE, CONFIG_CREATE = "MESH_CREATE", "CONFIG_CREATE"


class Task:

    def __init__(self, case_name: str, task_name: str, test_path: Path, program: str, program_version: str):
        self.post_path = None
        self.done_path = None
        self.calc_path = None
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
        else:
            print(f"Задача {self.case_name}_{self.task_name} уже посчитана")
        if self.post_path.exists():
            pass


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
            elif event.kind in task.taken_events:
                os.makedirs(task.calc_path / "MESH_CREATE", exist_ok=True)
                print(f"Задание выполнено: \"{event_name}\"")
                task.passed_events.add(event.kind)
                task.taken_events.remove(event.kind)
        else:
            print("Передаю обработку дальше")
            super().handle(task, event)


class ConfigCreate(NullHandler):

    def handle(self, task, event):
        if event.kind == CONFIG_CREATE:
            event_name = "Создание конфига"
            if event.kind not in (task.passed_events | task.taken_events):
                print(f"Задание получено: \"{event_name}\"")
                task.taken_events.add(event.kind)
            elif event.kind in task.taken_events:
                os.makedirs(task.calc_path / "CONFIG_CREATE", exist_ok=True)
                print(f"Задание выполнено: \"{event_name}\"")
                task.passed_events.add(event.kind)
                task.taken_events.remove(event.kind)
        else:
            print("Передаю обработку дальше")
            super().handle(task, event)


class EventGiver:

    def __init__(self):
        self.handlers = MeshCreate(ConfigCreate())
        self.events = []

    def add_event(self, event):
        self.events.append(event)

    def handle_events(self, task):
        for event in self.events:
            self.handlers.handle(task, event)


if __name__ == "__main__":
    events = [Event(MESH_CREATE), Event(CONFIG_CREATE)]

    event_giver = EventGiver()

    for event in events:
        event_giver.add_event(event)

    task = Task(case_name="ROG_15",
                task_name="task",
                test_path=Path(r"C:\Users\vvbuley\Desktop\polish_test"),
                program="Lazurit",
                program_version="Lazurit_0.1")

    task.make_dirs()
    task.make_stat()
    # event_giver.handle_events(task)
    # print(task.taken_events)
    # print(task.passed_events)
    # event_giver.handle_events(task)
    # print(task.taken_events)
    # print(task.passed_events)
