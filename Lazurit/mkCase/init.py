import os
from pathlib import Path
import shutil





MESH_CREATE, CONFIG_CREATE = "MESH_CREATE", "CONFIG_CREATE"


class Task:

    def __init__(self, case_name: str, task_name: str, test_path: Path, program: str, program_version: str):
        self.case_name = case_name
        self.task_name = task_name
        self.test_path = test_path
        self.program = program
        self.program_version = program_version
        self.passed_events = set()
        self.taken_events = set()


    def make_dirs(self):
        path_name = f"{self.case_name}_{self.task_name}"
        calc_path = self.test_path / "calc" / self.program / self.program_version / path_name
        done_path = self.test_path / "done" / self.program / self.program_version / path_name
        post_path = self.test_path / "post" / self.program / self.program_version / path_name
        if not done_path.exists():
            if calc_path.exists():
                shutil.rmtree(calc_path, ignore_errors=True)
            os.makedirs(calc_path, exist_ok=True)
        if post_path.exists():
            shutil.rmtree(post_path, ignore_errors=True)



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


    task = Task(case_name="case",
                task_name="task",
                test_path=Path(r"C:\Users\vvbuley\Desktop\polish_test"),
                program="Lazurit",
                program_version="Lazurit_0.1")
    task.make_dirs()

    event_giver.handle_events(task)
    print()
    task.taken_events = {MESH_CREATE}
    event_giver.handle_events(task)
    print()
    event_giver.handle_events(task)




