# coding:utf-8
"""
Created on 2017年9月21日

@author: wangpeng
"""
import os
import sys

import numpy as np
from configobj import ConfigObj

from PB import pb_time


def DccDataRead(iFile):
    """
    加载 EXT 文件 或者 STANDARD 文件
    """
    names1 = ['ymd', 'Avg', 'Med', 'Mod', 'dccFiles', 'dccPoint', 'dccPrecent',
              'dccDim']
    formats1 = ['object', 'f4', 'f4', 'f4', 'i4', 'i4', 'i4', 'i4']

    names2 = ['chan', 'Avg', 'Med', 'Mod']
    formats2 = ['object', 'f4', 'f4', 'f4']

    # 加载txt文
    try:
        ary = np.loadtxt(iFile,
                         dtype={'names': tuple(names1),
                                'formats': tuple(formats1)},
                         skiprows=1, ndmin=1)
    except Exception:
        ary = np.loadtxt(iFile,
                         dtype={'names': tuple(names2),
                                'formats': tuple(formats2)},
                         skiprows=1, ndmin=1)

    return ary


def DccDataWrite(title, data, outFile):
    """
    title: 标题
    data： 数据体
    outFile:输出文件
    """

    alllines = []
    DICT_D = {}
    FilePath = os.path.dirname(outFile)
    if not os.path.exists(FilePath):
        os.makedirs(FilePath)

    if os.path.isfile(outFile) and os.path.getsize(outFile) != 0:
        fp = open(outFile, 'r')
        fp.readline()
        data_lines = fp.readlines()
        fp.close()
        # 使用字典特性，保证时间唯一，读取数据
        for line in data_lines:
            DICT_D[line[:8]] = line[8:]
        # 添加或更改数据
        for line in data:
            # line = data
            DICT_D[line[:8]] = line[8:]
        # 按照时间排序

        newlines = sorted(DICT_D.iteritems(), key=lambda d: d[0], reverse=False)
        for i in xrange(len(newlines)):
            alllines.append(str(newlines[i][0]) + str(newlines[i][1]))
        fp = open(outFile, 'w')
        fp.write(Title)
        fp.writelines(alllines)
        fp.close()
    else:
        fp = open(outFile, 'w')
        fp.write(Title)
        fp.writelines(data)
        fp.close()


########################### 主程序入口 ############################
if __name__ == '__main__':
    # 获取程序参数接口
    args = sys.argv[1:]
    help_info = \
        u'''
            【参数1】：SAT+SENSOR or SAT1_SAT2 or SAT+SENSOR_STANDARD
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

        ipath1 = inCfg['bias'][satFlag]['ipath1']
        ipath2 = inCfg['bias'][satFlag]['ipath2']
        opath = inCfg['bias'][satFlag]['opath']
        chan1 = inCfg['bias'][satFlag]['chan1']
        chan2 = inCfg['bias'][satFlag]['chan2']
        var = inCfg['bias'][satFlag]['var']
        rollday = inCfg['bias'][satFlag]['rollday']
        if 'slope' in inCfg['bias'][satFlag]:
            slope = inCfg['bias'][satFlag]['slope']
            slope = map(float, slope)
        if 'intercept' in inCfg['bias'][satFlag]:
            intercept = inCfg['bias'][satFlag]['intercept']
            intercept = map(float, intercept)

        sat1, sat2 = satFlag.split('_')

        idx = 0
        for ch1, ch2 in zip(chan1, chan2):
            if not isinstance(var, list):
                var = [var]
            for each in var:
                FileName1 = 'DCC_%s_%s_%s_Rolldays_%s_ALL.txt' % (
                    sat1, each, ch1, rollday)
                if sat2 == 'STANDARD':
                    FileName2 = 'DCC_%s_%s_STANDARD.txt' % (
                        sat1, each)
                else:
                    FileName2 = 'DCC_%s_%s_%s_Rolldays_%s_ALL.txt' % (
                        sat2, each, ch2, rollday)
                print(FileName1)
                DccFile1 = os.path.join(ipath1, FileName1)
                DccFile2 = os.path.join(ipath2, FileName2)
                ary1 = DccDataRead(DccFile1)
                ary2 = DccDataRead(DccFile2)
                #                 a = list(ary1['ymd'])
                #                 b = list(ary2['ymd'])

                ##### 3、拼接文件头和数据体信息
                Title = ('%-15s' * 8 + '\n') % (
                    'date', 'biasAvg', 'biasMed', 'biasMod', 'dccFiles',
                    'dccPoint', 'dccPrecent', 'dccDim')
                lines = []

                if sat2 == 'STANDARD':
                    dates = ary1['ymd']
                    for ymd in dates:
                        idx1 = np.where(ymd == ary1['ymd'])
                        idx1 = idx1[0][0]
                        avg1 = ary1['Avg'][idx1]
                        med1 = ary1['Med'][idx1]
                        mod1 = ary1['Mod'][idx1]

                        idx2 = np.where(ch2 == ary2['chan'])
                        avg2 = ary2['Avg'][idx2]
                        med2 = ary2['Med'][idx2]
                        mod2 = ary2['Mod'][idx2]

                        bias_avg = ((avg1 - avg2) / avg2) * 100.
                        bias_med = ((med1 - med2) / avg2) * 100.
                        bias_mod = ((mod1 - mod2) / avg2) * 100.
                        Data = ('%-15s' + '%-15.6f' * 3 + '%-15d' * 4 + '\n') % \
                               (
                                   ymd, bias_avg, bias_med, bias_mod,
                                   int(ary1['dccFiles'][idx1]),
                                   int(ary1['dccPoint'][idx1]),
                                   int(ary1['dccPrecent'][idx1]),
                                   int(ary1['dccDim'][idx1]))
                        lines.append(Data)

                else:
                    # 获取时间交集
                    a = ary1['ymd']
                    b = ary2['ymd']
                    intersection = list(set(a) & set(b))
                    for ymd in sorted(intersection):
                        idx1 = np.where(ymd == ary1['ymd'])
                        idx2 = np.where(ymd == ary2['ymd'])

                        avg1 = ary1['Avg'][idx1]
                        med1 = ary1['Med'][idx1]
                        mod1 = ary1['Mod'][idx1]

                        avg2 = ary2['Avg'][idx2] * slope[idx] + intercept[idx]
                        med2 = ary2['Med'][idx2] * slope[idx] + intercept[idx]
                        mod2 = ary2['Mod'][idx2] * slope[idx] + intercept[idx]

                        bias_avg = ((avg1 - avg2) / avg2) * 100.
                        bias_med = ((med1 - med2) / avg2) * 100.
                        bias_mod = ((mod1 - mod2) / avg2) * 100.

                        Data = ('%-15s' + '%-15.6f' * 3 + '%-15d' * 4 + '\n') % \
                               (
                                   ymd, bias_avg, bias_med, bias_mod,
                                   ary1['dccFiles'][idx1],
                                   ary1['dccPoint'][idx1],
                                   ary1['dccPrecent'][idx1],
                                   ary1['dccDim'][idx1])
                        lines.append(Data)

                FileName = 'DCC_%s_%s_%s_Rolldays_%s_ALL.txt' % (
                    satFlag, each, ch1, rollday)
                OutFile = os.path.join(opath, FileName)
                ##### 4、写入文件
                DccDataWrite(Title, lines, OutFile)

            idx = idx + 1

    else:  # 没有参数 输出帮助信息
        print help_info
