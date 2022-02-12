import os,os.path
from copy import copy
import numpy as np
import pandas as pd
from pathlib import Path
import json
import sys


istaskdir = lambda dirname: dirname[0] == dirname[0]

# def gettasklist(path):
#     res  = []
#     print(path)
#     for entry in os.scandir(path):
#         print(entry)
        
#         print(istaskdir(entry.name),entry.is_dir())
#         if entry.is_dir() and istaskdir(entry.name):
#             force_dir = os.path.join(Path, entry.name, 'forces')
#             print(force_dir)
#             if os.path.exists(force_dir) and len(list(os.scandir(force_dir))) > 0:
#                 res.append((entry.name, force_dir))
#                 print('1')
#                 print(res)
#     return res


def filter_force(forces_table: pd.DataFrame, faces: dict) -> pd.DataFrame:
    filter_series = pd.Series([False for _ in range(forces_table.__len__())])
    for crit in faces:
        tmp = pd.Series([True for _ in range(forces_table.__len__())])
        for k in crit:
            tmp = tmp & forces_table[k].isin(crit[k])
        filter_series = filter_series | tmp
    return forces_table.loc[filter_series]


def get_sum_forces(forces_table: pd.DataFrame):
    Area = -forces_table['Area'].sum()
    A_x = -forces_table['Ax'].sum()
    A_y = -forces_table['Ay'].sum()
    A_z = -forces_table['Az'].sum()
    f_x = -forces_table['Fx'].sum()
    f_y = -forces_table['Fy'].sum()
    f_z = -forces_table['Fz'].sum()
    f_tx = -forces_table['Ftx'].sum()
    f_ty = -forces_table['Fty'].sum()
    f_tz = -forces_table['Ftz'].sum()
    m_x = -forces_table['Mx'].sum()
    m_y = -forces_table['My'].sum()
    m_z = -forces_table['Mz'].sum()
    m_x_pst = -forces_table['Mx_pst'].sum()
    m_y_pst = -forces_table['My_pst'].sum()
    m_z_pst = -forces_table['Mz_pst'].sum()
    m_tx = -forces_table['Mtx'].sum()
    m_ty = -forces_table['Mty'].sum()
    m_tz = -forces_table['Mtz'].sum()
    return Area, A_x, A_y, A_z, f_x, f_y, f_z, f_tx, f_ty, f_tz, m_x, m_y, m_z, m_x_pst, m_y_pst, m_z_pst, m_tx, m_ty, m_tz


def loadforces(force_dir):
    res = []
    
    for timedir in os.scandir(force_dir):
        if timedir.is_dir():
            time = float(timedir.name)
            
            df = None
            for entry in os.scandir(os.path.join(force_dir, timedir.name)):
                tmp = pd.read_csv(os.path.join(force_dir, timedir.name, entry.name), delim_whitespace=True)
                if df is None:
                    df = tmp
                else:
                    df = pd.concat([df,tmp], ignore_index=True)
                
            res.append([time, df])
    
    
    res.sort(key=lambda x: x[0])
    return res


def calc_forces(task_path, res_path):
    with open(Path(task_path) / "config.json", "r") as f:
        config = json.load(f)

    p_st = config["Reference value"]["Static pressure, Pa"]
    lp = config["Reference value"]["Linear scale, m"]
    Lb = config["Reference value"]["Linear scale, m"]
    vel = config["Reference value"]["Velocity, m/s"]
    T = config["Reference value"]["Temperature, K"]
    rho = p_st / (287 * T)
    q = rho * vel**2 / 2

    S = 0.9
    ba = 0.348
    Ba = 0.348
    
    x0, y0, z0 = 0.0, 0.0, 0.0

    faces = faces = [
        {'BC_Name' : ['Isotermal_wall']},
        ]



    # print("Start-------------")
    varlist = ['dirname', 'time', 'beta', 'alpha', 'Area', 'Ax','Ay','Az','Fpx', 'Fpy', 'Fpz', 'Ftx', 'Fty', 'Ftz', 'Mpx', 'Mpy', 'Mpz', 'Mx_pst', 'My_pst', 'Mz_pst', 'Mtx', 'Mty', 'Mtz']
    res     = []
    res_all = []
    taskname = task_path
    force_dir = os.path.join(taskname, "forces")
    print('proc :> ', taskname)
    raw = loadforces(force_dir)
    print(force_dir)
    tmp  = taskname.split('_')
    beta = 0
    alpha= 0
    case = [beta, alpha]
    print(case)
    data = []
    for time, df in raw:
        print('\t-',time)
        tmp = filter_force(df, faces)
        forces = get_sum_forces(filter_force(df, faces))

        data.append((time, *case , *forces))
                    
        res_all.append((taskname, time, *case, *forces))
        

    res.append((taskname, beta, alpha, *data[-1]))

    df = pd.DataFrame(res_all, columns=varlist)    
        
    df['Fpx']   = df.Fpx - df.Ax*p_st
    df['Fpy']   = df.Fpy - df.Ay*p_st
    df['Fpz']   = df.Fpz - df.Az*p_st
    
    df['Cx_p'] = df.Fpx/q/S
    df['Cy_p'] = df.Fpy/q/S
    df['Cz_p'] = df.Fpz/q/S
    
    df['Fx']= df.Fpx + df.Ftx
    df['Fy']= df.Fpy + df.Fty
    df['Fz']= df.Fpz + df.Ftz
    
    df['Cx'] = df.Fx/q/S
    df['Cy'] = df.Fy/q/S
    df['Cz'] = df.Fz/q/S
    
    df['Cxa'] = df['Cx']*np.cos(np.deg2rad(df.alpha)) + df['Cy']*np.sin(np.deg2rad(df.alpha))
    df['Cya'] =-df['Cx']*np.sin(np.deg2rad(df.alpha)) + df['Cy']*np.cos(np.deg2rad(df.alpha))
    df['Cza'] = 0.


    df['Mx_pst'] = df.Mx_pst*p_st
    df['My_pst'] = df.My_pst*p_st
    df['Mz_pst'] = df.Mz_pst*p_st

    df['Mx_'] = (df.Mpx - df.Mx_pst + df.Mtx)
    df['My_'] = (df.Mpy - df.My_pst + df.Mty)
    df['Mz_'] = (df.Mpz - df.Mz_pst + df.Mtz)
    
    # Преобразуем моменты к точке x0,y0,z0
    df['Mx'] = df.Mx_ - (y0*df.Fz - z0*df.Fy)
    df['My'] = df.My_ - (z0*df.Fx - x0*df.Fz)
    df['Mz'] = df.Mz_ - (x0*df.Fy - y0*df.Fx)
    
    df['mx'] = df.Mx/q/S/Lb
    df['my'] = df.My/q/S/Ba
    df['mz'] = df.Mz/q/S/Ba
    
    df = df.sort_values(['alpha', 'time'], ascending=[True, True] )               
    df.to_excel(os.path.join(res_path, 'forces_sum_all.xls'))
    
    print('save last data')
    df.drop_duplicates('dirname', keep='last', inplace=True)
    df.to_excel(os.path.join(res_path, 'forces_sum_lasts.xls'))
    
    print('save for xls')
    columns = ['dirname', 'time', 'beta', 'alpha', 'Fx', 'Fy', 'Fz','Mx', 'My', 'Mz']
    df = df[columns]
    df.to_excel(os.path.join(res_path, 'forces_for_copy_past.xls'))
    print('finish')





if __name__ == "__main__":
    calc_forces(sys.argv[1], sys.argv[2])