from pathlib import Path
import os
import sys
import tecplot as tp
from tecplot.exception import *
from tecplot.constant import *

def last_zone_active():
    """Фенкция для скрытия всех зон, кроме последней"""
    frame = tp.active_frame()
    num_zones = frame.dataset.num_zones
    tp.macro.execute_command(fr'''
#!MC 1410
$!ActiveFieldMaps -= [1-{num_zones}]
$!ActiveFieldMaps += [{num_zones}]
''')

def last_iter(task_path):
    tmp_dir = Path(task_path) / "tecplot"
    nums_iter = [i.lstrip("T-") for i in os.listdir(tmp_dir) if "T-" in i]
    last_iter = max(nums_iter)
    return last_iter

def files_group(task_path, num_iter, param):
    path_to_file = (Path(task_path) / "tecplot" / f"T-{num_iter}").absolute().__str__()
    if param == "ALL":
        needed_files = [f"{path_to_file}/{file}" for file in os.listdir(path_to_file)]
    elif param == "FLOW":
        needed_files = [f"{path_to_file}/{file}" for file in os.listdir(path_to_file) if param in file]
    elif param == "WALL":
        needed_files = [f"{path_to_file}/{file}" for file in os.listdir(path_to_file) if param in file]
    elif param == "AVE":
        needed_files = [f"{path_to_file}/{file}" for file in os.listdir(path_to_file) if param in file]
    elif type(param) == type([]):
        needed_files = param
    return needed_files


def picture_laz(task_path, out_path):
    num_iter = last_iter(task_path)
    needed_files = files_group(task_path, num_iter, "ALL")

    dataset = tp.data.load_tecplot(
        needed_files, read_data_option=tp.constant.ReadDataOption.ReplaceInActiveFrame)
    frame = tp.active_frame()
    extracted_slice = tp.data.extract.extract_slice(
        origin=(-1e-6, -1e-6, -1e-6),
        normal=(0, 0, 1),
        source=tp.constant.SliceSource.VolumeZones,
        dataset=dataset)
    last_zone_active()
    frame.plot_type = tp.constant.PlotType.Cartesian2D
    tp.active_frame().plot().axes.x_axis.variable_index=dataset.variable('X').index
    tp.active_frame().plot().axes.y_axis.variable_index=dataset.variable('Y').index
    var = frame.dataset.variable_names
    contour = tp.active_frame().plot().contour(0)
    contour.variable_index = var.index("U")
    tp.active_frame().plot().show_contour = True
    contour.colormap_name = 'Modern'
    contour.colormap_filter.distribution = tp.constant.ColorMapDistribution.Continuous  # Устанавливаем свойства контура --- continues
    tp.export.save_png(f"{out_path}/U_field.png", 400, supersample=3)
    tp.macro.execute_command("$!Page Name = 'Untitled'")
    tp.macro.execute_command("$!PageControl Create")
    tp.new_layout()

if __name__ == "__main__":
    picture_laz(sys.argv[1], sys.argv[2])