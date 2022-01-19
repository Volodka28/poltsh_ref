import os 
import sys
from pathlib import Path
import pandas as pd
import json
import yaml
from yaml.loader import SafeLoader




def main(task_path, out_path):
    with open(Path(task_path) / "post" / "post_config.yml", "r") as f:
        post_conf = yaml.load(f, Loader=SafeLoader)
    with open(Path(task_path) / "statistic.json", 'r') as f:
        stat = json.load(f)
    data = pd.read_excel(Path(out_path) / "Nu.xlsx")
    angles = [-15, 0, 15, 30, 45, 60, 75]
    angle = list(data.angle)
    Nu_inf = list(data.Nu_inf)
    ver_data = {
        "task": stat["task"]
    }
    for i in angles:
        delta = [(i-j)**2 for j in angle]
        min_index = delta.index(min(delta))
        ver_data[f"Nu_{i}"] = [Nu_inf[min_index]]
    data_new = pd.DataFrame(ver_data)
    data_new.to_excel(Path(out_path) / "verify.xlsx", index=False)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
    # main(r"C:\Users\vvbuley\Desktop\test\done\Lazurit.WIN.AVX\ROG_15_y_1", r"C:\Users\vvbuley\Desktop\test\post\Lazurit.WIN.AVX/ROG_15_y_1")