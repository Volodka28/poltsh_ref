from __future__ import with_statement
from pathlib import Path
import json
import yaml
from yaml.loader import SafeLoader
import tecplot as tp
from tecplot.exception import *
from tecplot.constant import *
import os, os.path
import sys
from pathlib import Path
import pandas as pd
import re
import json
import matplotlib.pyplot as plt


# Инструменты работы с итерациями и фалами

def last_iter(done_path):
    tmp_dir = Path(done_path) / "tecplot"
    nums_iter = [i.lstrip("T-") for i in os.listdir(tmp_dir) if "T-" in i]
    last_iter = max(nums_iter)
    return last_iter

def files_group(done_path, num_iter, param):
    path_to_file = (Path(done_path) / "tecplot" / f"T-{num_iter}").absolute().__str__()
    if param == "ALL":
        needed_files = os.listdir(path_to_file)
    elif param == "FLOW":
        needed_files = [file for file in os.listdir(path_to_file) if param in file]
    elif param == "WALL":
        needed_files = [file for file in os.listdir(path_to_file) if param in file]
    elif param == "AVE":
        needed_files = [file for file in os.listdir(path_to_file) if param in file]
    elif type(param) == type([]):
        needed_files = param
    files = ""
    for i in needed_files:
        files += f'"{path_to_file}\{i}",'
    return files.rstrip(',')


# Инструменты для заполнения шаблонов макросов

def fill_template_mcr(done_path, scripts_path, config_post, stat, mcr):
    with open(scripts_path / mcr, "r") as f:
            temp = f.read()
    with open(Path(done_path) / "config.json", "r") as f:
        config = json.load(f)
    if config_post[mcr]["key"] == []: 
        pass
    else:
        for key in config_post[mcr]["key"]:
            list_key = key.split(".") 
            tmp_value = config
            for i in list_key:
                tmp_value = tmp_value[i]
            temp = temp.replace(f"${key}$", str(tmp_value))
    if config_post[mcr]["iters"] == "LAST":
        num_iter = last_iter(done_path)
        files = files_group(done_path, num_iter, config_post[mcr]["files"])
        
    temp = temp.replace("$input_files$", files)
    temp = temp.replace("$output_path$", f"{stat['post_path']}/{stat['case_name']}_{stat['task']}")
    with open(Path(done_path) / mcr, "w") as f:
        f.write(temp)
    return temp

def start_py(done_path, stat):
    return (done_path, f"{stat['post_path']}/{stat['case_name']}_{stat['task']}")


# Операции с файлами после обработки

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
    # print(Vars)
    data = pd.read_table(file_in_path, sep='\s+', skiprows=counter - 1, names=Vars, on_bad_lines='skip')
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


def main(done_path):
    if "post" not in os.listdir(done_path):
        pass
    else:
        scripts_path = Path(done_path) / "post"
        
        with open(scripts_path / "post_config.yml", "r") as f:
            config_post = yaml.load(f, Loader=SafeLoader)
        with open(Path(done_path) / "statistic.json", "r") as f:
            stat = json.load(f)
        path_post = Path(stat['post_path']) / f"{stat['case_name']}_{stat['task']}"
        MCR_list = [i for i in os.listdir(Path(done_path) / "post") if ".mcr" in i]
        py_list = [i for i in os.listdir(Path(done_path) / "post") if ".py" in i]
        for mcr in MCR_list:
            if mcr in config_post.keys():
                macros = fill_template_mcr(done_path, scripts_path, config_post, stat, mcr)
                tp.macro.execute_command(macros)
        if "convert" in config_post.keys():
            for file in config_post["convert"]:
                table_formating(path_post / file, path_post / f"{file.split('.')[0]}.xlsx")
        for script in py_list:
            if script in config_post.keys():
                param = start_py(done_path, stat)
                cwd = os.getcwd()
                os.chdir(scripts_path)
                print(f"python {script} {param[0]} {param[1]}")
                os.system(f"python {script} {param[0]} {param[1]}")
                os.chdir(cwd)
        

             


        
    

if __name__ == "__main__":
    main(sys.argv[1])
    # main(r"C:\Users\vvbuley\Desktop\test\done\Lazurit.WIN.AVX\ROG_15_y_1")