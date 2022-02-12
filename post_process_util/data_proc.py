import os, os.path
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import re
import json
import matplotlib.pyplot as plt

def table_formating(file_in_path, file_out_path):
    """
    Читает сохраемый текплотом файл и сохраняет в нормальном табличном виде
    :param file_in_path: путь до неотформатированного файла
    :param file_out_path: путь до сохраняемого форматированого файла
    :return:
    """
    Vars = []
    counter = 0
    with open(file_in_path, 'r') as file:
        for line in file:
            # print(line)
            # \b\d\b число в пробелах
            if re.search(r'\b\d\b', line) is None:
                counter += 1
                # ".*" любые символы в ковычках
                if "ZONE" in line:
                    continue
                elif "|" in line:
                    continue
                elif re.search(r'".*"', line) is not None:
                    Var = re.search(r'".*"', line).group()[1:-1]
                    Vars.append(Var)
            else:
                break
    print(Vars, counter)
    data = pd.read_table(file_in_path, sep='\s+', skiprows=counter, names=Vars, on_bad_lines='skip')
    row_count = data.count()[0]
    fall_rows = []
    for i in range(row_count):
        if re.findall('^[A-Z]', data[data.columns[0]].iloc[i]):
            fall_rows.append(i)
    data_t = data.drop(index=fall_rows)
    for i in data_t:
        data_t[i] = pd.to_numeric(data_t[i])
    data_t.to_excel(file_out_path, index=False)
    return file_out_path

def create_plot(file, x_axis, y_axis, post_path):
    data = pd.read_excel(file)
    plt.plot(data[x_axis], data[y_axis])
    plt.savefig(f"{post_path.absolute().__str__()}/{x_axis}_{y_axis}.png")

def create_scatters(file, x_axis, y_axis, post_path):
    data = pd.read_excel(file)
    plt.scatter(data[x_axis], data[y_axis])
    plt.savefig(f"{post_path.absolute().__str__()}/{x_axis}_{y_axis}.png")

def main(task_path):
    with open(Path(task_path) / "post" / "report_config.json", "r") as f:
        report_conf = json.load(f)
    with open(Path(task_path) / "statistic.json", "r") as f:
        stat = json.load(f)
    path_post = Path(stat["post_path"]) / f'{stat["case_name"]}_{stat["task"]}' 
    for file in report_conf.keys():
        if report_conf[file]["convert"]:
            xlsx_file = table_formating(path_post / file, path_post / f"{file.split('.')[0]}.xlsx")
        for key in range(0,len(report_conf[file]["scatters"]),2):
            create_plot(xlsx_file, report_conf[file]["scatters"][key], report_conf[file]["scatters"][key+1], path_post)

        

    


if __name__ == "__main__":
    main(sys.argv[1])