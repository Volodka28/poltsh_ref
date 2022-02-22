import yaml
from yaml.loader import SafeLoader
import os
from pathlib import Path
import argparse
import pandas as pd
import shutil

tasks_temp = {
    "task_name": [
        "task1",
        "task2",
        "task3"
    ],
    "template": [
        "temp1",
        "temp2",
        "temp3"
    ]
}

def make_case_yml(case_name):
    with open("case.yml", "r") as f:
        temp = yaml.load(f, Loader=SafeLoader)
    case_conf = {}
    case_conf[case_name] = temp["case_name"]
    for i in case_conf[case_name]["tasks"]:
        case_conf[case_name]["tasks"][i]["extends"] = f"{case_name}_task:task"
    return case_conf

def make_task_yml(case_name):
    with open("task.yml", "r") as f:
        temp = yaml.load(f, Loader=SafeLoader)
    task_conf = temp
    task_conf["task"]["post"]["extends"] = f"{case_name}_post:post"
    return task_conf

def make_post_yml():
    with open("post.yml", "r") as f:
        post_conf = yaml.load(f, Loader=SafeLoader)
    return post_conf


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Инициализация пустых кейсов")
    parser.add_argument("--cases_names", type=str, help="назвния кейсов для инициализации")

    args = parser.parse_args()
    cases = args.cases_names.split(",")
    print(cases)
    for case in cases:
        case_path = Path("../" + case.lstrip(" ").rstrip(" "))
        case_path.mkdir(exist_ok=True)
        tasks = pd.DataFrame(tasks_temp)
        tasks.to_excel(case_path / "tasks.xlsx", index=False)
        for temp in tasks_temp["template"]:
            os.makedirs(case_path / temp, exist_ok=True)
        os.makedirs(case_path / "descriptions", exist_ok=True)
        os.makedirs(case_path / "template", exist_ok=True)
        shutil.copyfile("readme.docx", case_path / "readme.docx")
        
        case_config = make_case_yml(case)
        with open(case_path / f"{case}_case.yml","w") as f:
            yaml.dump(case_config, f)

        task_config = make_task_yml(case)
        with open(case_path / f"{case}_task.yml","w") as f:
            yaml.dump(task_config, f)

        post_config = make_post_yml()
        with open(case_path / f"{case}_post.yml","w") as f:
            yaml.dump(post_config, f)