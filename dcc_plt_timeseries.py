# coding:utf-8
"""
Created on 2017年9月21日

@author: wangpeng
"""
import os
import sys
from datetime import datetime
from configobj import ConfigObj

import numpy as np

from PB import pb_time
from DV import dv_plt


def DccDataRead(iFile):
    names = ['ymd', 'Avg', 'Med', 'Mod', 'dccFiles',
             'dccPoint', 'dccPrecent', 'dccDim']
    formats = ['object', 'f4', 'f4', 'f4', 'i4', 'i4', 'i4', 'i4']

    # 加载txt文
    arys = np.loadtxt(iFile,
                      dtype={'names': tuple(names),
                             'formats': tuple(formats)},
                      skiprows=1, ndmin=1)

    return arys


########################### 主程序入口 ############################
if __name__ == '__main__':
    # 获取程序参数接口
    args = sys.argv[1:]
    help_info = \
        u'''
            【参数1】：SAT or SAT+SENSOR or SAT1_SAT2 or SAT+SENSOR_STANDARD
            【参数2】：yyyymmdd-yyyymmdd
        '''
    if '-h' in args:
        print help_info
        sys.exit(-1)

    # 获取程序所在位置，拼接配置文件
    MainPath, MainFile = os.path.split(os.path.realpath(__file__))
    ProjPath = os.path.dirname(MainPath)
    cfgFile = os.path.join(MainPath, 'global_dcc.cfg')
    # 配置不存在预警
    if not os.path.isfile(cfgFile):
        print (u'配置文件不存在 %s' % cfgFile)
        sys.exit(-1)
    # 载入配置文件
    inCfg = ConfigObj(cfgFile)

    if len(args) == 2:  # 需要跟俩个参数执行
        satFlag = args[0]
        str_time = args[1]
        date_s, date_e = pb_time.arg_str2date(str_time)

        #         # 卫星标识检查，配置中没有则不处理
        #         if satFlag not in inCfg.keys():
        #             print 'not support satellite: %s' % satFlag
        #             sys.exit(-1)
        try:
            sat1, sat2 = satFlag.split('_')
        except ValueError:
            sat2 = None

        ipath = inCfg['plt'][satFlag]['ipath']
        opath = inCfg['plt'][satFlag]['opath']
        rollday = inCfg['plt'][satFlag]['rollday']
        lanch_date = inCfg['plt'][satFlag]['lanch_date']
        var = inCfg['plt'][satFlag]['var']
        band = inCfg['plt'][satFlag]['band']

        # 拼接需要读取的文件
        if not isinstance(var, list):
            var = [var]
        print(var)
        for each in var:
            for ch in band:
                FileName = 'DCC_%s_%s_%s_Rolldays_%s_ALL.txt' % (
                    satFlag, each, ch, rollday)
                DccFile = os.path.join(ipath, FileName)
                ######### 一、读取dcc提取后的标准文件 ##############
                ary = DccDataRead(DccFile)

                ######### 二、计算衰减  ##############
                idx = np.where(ary['ymd'] == lanch_date)
                FirstAvg = ary['Avg'][idx]
                FirstMed = ary['Med'][idx]
                FirstMod = ary['Mod'][idx]
                # 如果是 DN，需要计算和发星第一天的相对百分比
                if 'DN' in each:
                    AvgATT = (ary['Avg'] / FirstAvg) * 100
                    MedATT = (ary['Med'] / FirstAvg) * 100
                    ModATT = (ary['Mod'] / FirstAvg) * 100
                elif 'REF' in each:
                    # 如果是绘制相对偏差，已经是计算好的相对百分比，不需要除100
                    # sat2 存在，代表是绘制两颗卫星的相对偏差
                    if sat2:
                        AvgATT = ary['Avg']
                        MedATT = ary['Med']
                        ModATT = ary['Mod']
                    # 如果是绘制自身 REF 变化，需要除 100，还原 REF 真实值
                    else:
                        AvgATT = ary['Avg'] / 100.
                        MedATT = ary['Med'] / 100.
                        ModATT = ary['Mod'] / 100.

                ######## 三、绘图   ###################
                outPng_avg = os.path.join(opath,
                                          'DCC_%s_%s_%s_Rolldays_%s_Timeseries_Avg.png' % (
                                              satFlag, each, ch, rollday))
                outPng_med = os.path.join(opath,
                                          'DCC_%s_%s_%s_Rolldays_%s_Timeseries_Med.png' % (
                                              satFlag, each, ch, rollday))
                outPng_mod = os.path.join(opath,
                                          'DCC_%s_%s_%s_Rolldays_%s_Timeseries_Mod.png' % (
                                              satFlag, each, ch, rollday))
                x = []
                for i in xrange(len(ary['ymd'])):
                    dtime = datetime.strptime(ary['ymd'][i], '%Y%m%d')
                    x.append(dtime)
                p = dv_plt.dv_time_series(figsize=(8, 4))
                p.fig.subplots_adjust(bottom=0.15)
                #                 p.y_fmt = "%0.3f"
                p.easyplot(x, AvgATT, 'r', 'avg', marker='x-', markersize=3,
                           mec="r")
                p.title = u'%s %s 时序图' % (satFlag, ch)
                p.ylabel = u'%s Avg' % each
                p.savefig(outPng_avg)
                print(outPng_avg)
                p = dv_plt.dv_time_series(figsize=(8, 4))
                p.fig.subplots_adjust(bottom=0.15)
                #                 p.y_fmt = "%0.3f"
                p.easyplot(x, MedATT, 'r', 'med', marker='x-', markersize=3,
                           mec="r")
                p.title = u'%s %s 时序图' % (satFlag, ch)
                p.ylabel = u'%s Med' % each
                p.savefig(outPng_med)
                print(outPng_med)
                p = dv_plt.dv_time_series(figsize=(8, 4))
                p.fig.subplots_adjust(bottom=0.15)
                #                 p.y_fmt = "%0.3f"
                p.easyplot(x, ModATT, 'r', 'mod', marker='x-', markersize=3,
                           mec="r")
                p.title = u'%s %s 时序图' % (satFlag, ch)
                p.ylabel = u'%s Mod' % each
                p.savefig(outPng_mod)
                print(outPng_mod)
    else:  # 没有参数 输出帮助信息
        print help_info
