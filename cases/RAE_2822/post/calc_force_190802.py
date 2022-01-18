# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os,os.path
from copy import copy
import numpy as np
import pandas as pd

Path = ''
if Path == '' :
    Path = os.curdir

S0   = 0.1*1
S    = 0.61*0.1
p_st = 70639.61
q    = 26350.701718
lp   = 1.392
ba   = 0.348

faces = [
        {'IBlock' : range(10000)},
        ]


istaskdir = lambda dirname: 'Yp' in dirname

def gettasklist(path):
    res  = []
    for entry in os.scandir(path):
        if entry.is_dir() and istaskdir(entry.name):
            force_dir = os.path.join(Path, entry.name, 'forces')
            if os.path.exists(force_dir) and len(list(os.scandir(force_dir))) > 0:
                res.append((entry.name, force_dir))
    return res


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
            

def filter_force(forces_table: pd.DataFrame, faces: dict) -> pd.DataFrame:
    filter_series = pd.Series([False for _ in range(forces_table.__len__())])
    for crit in faces:
        tmp = pd.Series([True for _ in range(forces_table.__len__())])
        for k in crit:
            tmp = tmp & forces_table[k].isin(crit[k])
        filter_series = filter_series | tmp
    return forces_table.loc[filter_series]

def get_sum_forces(forces_table: pd.DataFrame):
    A_x = -forces_table['Ax'].sum()
    A_y = -forces_table['Ay'].sum()
    A_z = -forces_table['Az'].sum()
    f_x = -forces_table['Fx'].sum()
    f_y = -forces_table['Fy'].sum()
    f_z = -forces_table['Fz'].sum()
    f_tx = -forces_table['Ftx'].sum()
    f_ty = -forces_table['Fty'].sum()
    f_tz = -forces_table['Ftz'].sum()
    return A_x, A_y, A_z, f_x, f_y, f_z, f_tx, f_ty, f_tz


if __name__ == "__main__":
    print("Start-------------")
    varlist = ['dirname', 'time', 'beta', 'alpha', 'Ax','Ay','Az','Fx', 'Fy', 'Fz', 'Ftx', 'Fty', 'Ftz']
    res     = []
    res_all = []
    
    for taskname, force_dir in gettasklist(Path):
        print('proc :> ', taskname)
        raw = loadforces(force_dir)
        
        beta = 0.0
        alpha= 2.8
        
        data = []
        for time, df in raw:
            print('\t-',time)
            tmp = filter_force(df, faces)
            forces = get_sum_forces(filter_force(df, faces))
            data.append((time, beta, alpha, *forces))
            
            res_all.append((taskname, time, beta, alpha, *forces))
    
        res.append((taskname, *data[-1]))

    df = pd.DataFrame(res_all, columns=varlist)
    df['Cx'] = ((df['Fx'] - p_st*df['Ax']) + df['Ftx'])/q/S
    df['Cy'] = ((df['Fy'] - p_st*df['Ay']) + df['Fty'])/q/S
    df['Cz'] = ((df['Fz'] - p_st*df['Az']) + df['Ftz'])/q/S
    df['Cxa'] = df.Cx*np.cos(np.deg2rad(df.alpha))*np.cos(np.deg2rad(df.beta)) + df.Cy*np.sin(np.deg2rad(df.alpha)) - df.Cz*np.cos(np.deg2rad(df.alpha))*np.sin(np.deg2rad(df.beta))
    df['Cya'] =-df.Cx*np.sin(np.deg2rad(df.alpha))*np.cos(np.deg2rad(df.beta)) + df.Cy*np.cos(np.deg2rad(df.alpha)) + df.Cz*np.sin(np.deg2rad(df.alpha))*np.sin(np.deg2rad(df.beta))
    df['Cza'] =-df.Cx*np.sin(np.deg2rad(df.beta)) + 0. + df.Cz*np.cos(np.deg2rad(df.beta))
    df.to_excel(os.path.join(Path, 'forces_sum_all.xls'))    
    
    df = pd.DataFrame(res, columns=varlist)
    df['Cx'] = ((df['Fx'] - p_st*df['Ax']) + df['Ftx'])/q/S
    df['Cy'] = ((df['Fy'] - p_st*df['Ay']) + df['Fty'])/q/S
    df['Cz'] = ((df['Fz'] - p_st*df['Az']) + df['Ftz'])/q/S
    df['Cxa'] = df.Cx*np.cos(np.deg2rad(df.alpha))*np.cos(np.deg2rad(df.beta)) + df.Cy*np.sin(np.deg2rad(df.alpha)) - df.Cz*np.cos(np.deg2rad(df.alpha))*np.sin(np.deg2rad(df.beta))
    df['Cya'] =-df.Cx*np.sin(np.deg2rad(df.alpha))*np.cos(np.deg2rad(df.beta)) + df.Cy*np.cos(np.deg2rad(df.alpha)) + df.Cz*np.sin(np.deg2rad(df.alpha))*np.sin(np.deg2rad(df.beta))
    df['Cza'] =-df.Cx*np.sin(np.deg2rad(df.beta)) + 0. + df.Cz*np.cos(np.deg2rad(df.beta))
    df.to_excel(os.path.join(Path, 'forces_sum_lasts.xls'))
    
    print('finish')
    
    
        
    