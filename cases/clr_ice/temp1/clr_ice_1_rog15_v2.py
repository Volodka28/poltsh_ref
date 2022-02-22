#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, os, traceback


sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))
rezpath = os.path.abspath(os.path.dirname(sys.argv[0]))

import gs1


# config_path=os.path.join(os.path.dirname(__file__), '..', '..', '..', 'grids', 'clr_ice', 'config.json')
config_path = r"D:\zircon_dist\2022.02.21\test\clr_ice\clr_ice.json"
os.chdir(os.path.dirname(config_path))

processor = gs1.config_processor(config_path)

harakt_razmer = 0.002  # некий характерный размер в сетке, который должен быть подробно описан
#harakt_wallstep = 0.00005  # шаг сетки возле стенки
harakt_wallstep = 0.000005 # шаг сетки возле стенки
#harakt_wallstep = 0.00001 # шаг сетки возле стенки
harakt_tochek = 20.0  # приемлемое количество точек на скруглении характерного диаметра
harakt_step = 3.1415 * harakt_razmer / harakt_tochek
harakt_shrink = harakt_step / harakt_wallstep
print ("Shrink Ratio = ", harakt_shrink)

processor.set_config_zone_conditions("shrink_ratio",harakt_shrink)
processor.set_config_boundary_conditions("nearwall_step",harakt_wallstep,"clr_ice_0_rog15.STL")

connect = False
if connect:
	processor.config["tasks"]["Task List"][0]={
		"Type": "gs1_command",
		"Command": "connect_to_socket",
		"Arguments": {
			"host": "localhost",
			"port": 6666
		}
	}
else:
	processor.config["tasks"]["Task List"][0]={
		"Type": "gs1_command",
		"Command": "run_local_solver",
		"Arguments": {
			"path": ".",
			"port": 33057,
			"version": None
		}
	}

processor.dump_config()
processor.do_tasks()

