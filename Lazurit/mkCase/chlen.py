import os
from pathlib import Path






MESH_CREATE, CONFIG_CREATE = "MESH_CREATE", "CONFIG_CREATE"


class Task:

    def __init__(self, case_name, task_name):
        self.case_name = case_name
        self.name = task_name
        self.passed_events = set()
        self.taken_events = set()
        self.dir_calc = "путь до расчетной директории"
        self.case_path = "Путь до папки кейса для инициализации"


    def make_dirs(self):
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


    task = Task("hui", "pizda")
    task.make_dirs(Path(os.getcwd()))

    event_giver.handle_events(task)
    print()
    task.taken_events = {MESH_CREATE}
    event_giver.handle_events(task)
    print()
    event_giver.handle_events(task)




