from __future__ import with_statement
import os, os.path
import tecplot as tp
from tecplot.exception import *
from tecplot.constant import *
import re
import json
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import numpy as np
from pathlib import Path


def last_zone_active():
    """Функция для скрытия всех зон, кроме последней"""
    frame = tp.active_frame()
    num_zones = frame.dataset.num_zones
    tp.macro.execute_command(fr'''
#!MC 1410
$!ActiveFieldMaps -= [1-{num_zones}]
$!ActiveFieldMaps += [{num_zones}]
''')
    return (num_zones)


def all_zone_active():
    """Функция для отображения всех зон"""
    frame = tp.active_frame()
    num_zones = frame.dataset.num_zones
    tp.macro.execute_command(fr'''
#!MC 1410
$!ActiveFieldMaps += [1-{num_zones}]
''')


def all_zone_hide():
    """Функция для отображения всех зон"""
    frame = tp.active_frame()
    num_zones = frame.dataset.num_zones
    tp.macro.execute_command(fr'''
#!MC 1410
$!ActiveFieldMaps -= [1-{num_zones}]
''')


def find_final_plt_files(work_dir):
    """
    Функция ищет последнее сохранение и возвращает список plt файлов и директорию хранения результирующих данных
    :param work_dir: путь до расчетной директории
    :return: список plt файлов для открытия, путь до директории сохранения
    """
    for root, dirs, files in os.walk(Path(work_dir) / "tecplot", topdown=False):
        if os.path.split(root)[-1] == "tecplot":
            Times = []
            for direct in dirs:
                if (("T-" in direct) and not ('res' in direct)):
                    T = int(re.search(r'(T-\d*)', direct).group()[2:])
                    Times.append(T)
            if len(Times) == 0:
                print("Did not find data with 'T-*' to process")
                print("Maybe your calculation is incomplete?")
                print("Exiting")
                exit()
            else:
                Times.sort()
                Final_T = Times[-1]
                Final_Save = os.path.join(root, 'T-' + str(Final_T))

    for root, dirs, files in os.walk(Final_Save, topdown=False):
        plt_files_list = files  # Список всех файлов plt в директории сохранения
    Flow_files = []
    Wall_files = []
    Ave_files = []
    for plt_file in plt_files_list:
        if ((re.search(r'(FLOW)', plt_file)) is not None) and (plt_file[-4:] == '.plt'):
            Flow_files.append(os.path.join(root, plt_file))
        if (re.search(r'(WALL)', plt_file)) is not None and (plt_file[-4:] == '.plt'):
            Wall_files.append(os.path.join(root, plt_file))
        if (re.search(r'(AVE)', plt_file)) is not None and (plt_file[-4:] == '.plt'):
            Ave_files.append(os.path.join(root, plt_file))
    if len(Ave_files) == 0:
        plt_files_list = Flow_files
    else:
        plt_files_list = Ave_files

    return plt_files_list


def make_slices(files_data, res_dir, slices, equations=None):
    """экстрактим слайсы и сохраняем лэйауты"""
    dataset = tp.data.load_tecplot(files_data)  # грузим дату в текполт(переменная, чтобы делать слайсы)
    frame = tp.active_frame()  # рамочка
    frame.plot_type = PlotType.Cartesian3D  # 2d/3d
    if equations:
        for eq in equations:
            tp.data.operate.execute_equation(equation=eq)
    slices_list = []
    for i in slices:
        all_zone_hide()
        active_zones = slices[i]["zones"]
        if not (active_zones):
            all_zone_active()
        else:
            if re.search((r'[A-Za-z]'), active_zones) is not None:
                visible_zones_index = []
                for Z in dataset.zones():
                    for visible in active_zones.split(","):
                        visible = re.search((r'\b\w*\b'), visible).group()
                        if visible in Z.name:
                            visible_zones_index.append(Z.index)
                for item_index in visible_zones_index:
                    tp.active_frame().plot().fieldmap(item_index).show = True
            else:
                tp.macro.execute_command(
                    '''$!ActiveFieldMaps += [%(active)s]''' % {"active": active_zones}
                )  # скрываем зоны

        extracted_slice = tp.data.extract.extract_slice(
            origin=slices[i]["origin"],
            normal=slices[i]["normal"],
            source=SliceSource.VolumeZones,
            dataset=dataset)  # по каким данным делаем слайс

        tp.data.save_tecplot_plt(Path(res_dir) / f'{i}.plt',
                                 zones=[last_zone_active() - 1],
                                 include_data_share_linkage=True)
        # tp.save_layout(Path(res_dir) / f'{i}.lay', include_data=True)

        slices_list.append(Path(res_dir) / f'{i}.plt')
        print('ok')
        all_zone_active()
    abs_path_list = []
    for i in range(len(slices_list)):
        abs_path_list.append(str(slices_list[i].absolute()))
    # добавляем путь к сайсу для открытия
    j = 0
    for i in slices:
        slices[i]['path'] = abs_path_list[j]
        j = j + 1
    print('All slices are extracted')
    return slices


def make_picture(res_dir, slice, settings):
    print(slice)
    dataset = tp.data.load_tecplot(
        [res_dir / f"{slice}.plt"], read_data_option=tp.constant.ReadDataOption.ReplaceInActiveFrame)
    frame = tp.active_frame()
    variables = frame.dataset.variable_names
    tp.active_frame().plot().axes.x_axis.variable_index = dataset.variable(settings["axis_x"]).index
    tp.active_frame().plot().axes.y_axis.variable_index = dataset.variable(settings["axis_y"]).index
    # Настройки plot
    plot = frame.plot()
    if settings["lim_axes"]:
        plot.axes.x_axis.min = settings["lim_axes"]["x_min"]
        plot.axes.x_axis.max = settings["lim_axes"]["x_max"]
        plot.axes.y_axis.min = settings["lim_axes"]["y_min"]
        # plot.axes.y_axis.max = settings["lim_axes"]["y_max"]   
    ratio = abs((settings["lim_axes"]["x_max"] - settings["lim_axes"]["x_min"]) / (
                settings["lim_axes"]["y_max"] - settings["lim_axes"]["y_min"]))
    frame.width = 10 * ratio
    frame.height = 10
    for var in settings["value"]:
        contour = tp.active_frame().plot().contour(0)
        contour.variable_index = variables.index(var)
        tp.active_frame().plot().show_contour = True
        if settings["value"][var]:
            contour.levels.reset_levels(
                np.arange(settings["value"][var][0], settings["value"][var][1], settings["value"][var][2]))
            tp.active_frame().plot().contour(0).colormap_filter.continuous_min = settings["value"][var][0]
            tp.active_frame().plot().contour(0).colormap_filter.continuous_max = settings["value"][var][1]
        contour.colormap_name = 'Modern'
        contour.colormap_filter.distribution = tp.constant.ColorMapDistribution.Continuous  # Устанавливаем свойства контура --- continues\
        legend = plot.contour(0).legend
        legend.show = True
        tp.export.save_png(res_dir.absolute().__str__() + f"/{slice}_{var}.png", 400, supersample=3)
        tp.save_layout(res_dir.absolute().__str__() + f"/{slice}_{var}.lay")


def main(work_dir):
    with open(Path(work_dir) / "statistic.json", "r") as f:
        stat = json.load(f)
    with open(Path(work_dir) / "post" / "post_config.yml", "r") as f:
        post_config = yaml.load(f, Loader=SafeLoader)
    post_path = Path(stat["post_path"]) / f"{stat['case_name']}_{stat['task']}"
    # slices = post_config["picture"]
    files_data = find_final_plt_files(work_dir)
    # slices = make_slices(files_data, post_path, slices)
    # for slice in post_config["picture"]:
    #     make_picture(post_path, slice, post_config["picture"][slice])

    picture_config = post_config["picture"]
    if "equations" in picture_config.keys():
        equations = picture_config["equations"]
        slices = picture_config.copy()
        slices.pop("equations")
        slices_path = make_slices(files_data, post_path, slices, equations)
    else:
        slices_path = make_slices(files_data, post_path)
    for slice in slices:
        make_picture(post_path, slice, slices[slice])


if __name__ == "__main__":
    main(r"C:\Users\vvbuley\Desktop\test\done\Lazurit.WIN.AVX\klin_y_10")
