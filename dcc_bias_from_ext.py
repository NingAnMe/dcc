# coding:utf-8
"""
Created on 2017年9月21日

@author: wangpeng
"""
import re
import os
import sys
from datetime import datetime

import numpy as np
from configobj import ConfigObj
from dateutil.relativedelta import relativedelta


def dcc_data_read(iFile):
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
    except IndexError:
        ary = np.loadtxt(iFile,
                         dtype={'names': tuple(names2),
                                'formats': tuple(formats2)},
                         skiprows=1, ndmin=1)

    return ary


def get_file_list(dir_path, pattern=r'.*'):
    """
    查找目录下的所有符合匹配模式的文件的绝对路径，包括文件夹中的文件
    :param dir_path: (str)目录路径
    :param pattern: (str)匹配模式 'hdf'
    :return: (list) 绝对路径列表
    """
    file_list = []
    # 递归查找目录下所有文件
    for root, dir_list, file_names in os.walk(dir_path):
        for i in file_names:
            m = re.match(pattern, i)
            if m:
                file_list.append(os.path.join(root, i))
    return file_list


def dcc_data_write(title, data, outFile):
    """
    title: 标题
    data： 数据体
    outFile: 输出文件
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
        fp.write(title)
        fp.writelines(alllines)
        fp.close()
    else:
        fp = open(outFile, 'w')
        fp.write(title)
        fp.writelines(data)
        fp.close()


def load_day_ext(ext_file):
    """
    读取日的 EXT 文件，返回 np.array
    :param ext_file:
    :return:
    """
    names = ('date', 'avg', 'med', 'mod',
             'dcc_files', 'dcc_point', 'dcc_precent', 'dcc_dim')
    formats = ('object', 'f4', 'f4', 'f4',
               'i4', 'i4', 'i4', 'i4')

    data = np.loadtxt(ext_file,
                      converters={0: lambda x: datetime.strptime(x, "%Y%m%d")},
                      dtype={'names': names,
                             'formats': formats},
                      skiprows=1, ndmin=1)
    return data


def month_average(day_data):
    """
    由 EXT 日数据生成 EXT 月平均数据
    :param day_data: EXT 日数据
    :return:
    """
    month_datas = []
    ymd_s = day_data['date'][0]  # 第一天日期
    ymd_e = day_data['date'][-1]  # 最后一天日期
    date_s = ymd_s - relativedelta(days=(ymd_s.day - 1))  # 第一个月第一天日期

    while date_s <= ymd_e:
        # 当月最后一天日期
        date_e = date_s + relativedelta(months=1) - relativedelta(days=1)

        # 查找当月所有数据
        day_date = day_data['date']
        month_idx = np.where(np.logical_and(day_date >= date_s,
                                            day_date <= date_e))

        avg_month = day_data['avg'][month_idx]
        med_month = day_data['med'][month_idx]
        mod_month = day_data['mod'][month_idx]
        dcc_files_month = day_data['dcc_files'][month_idx]
        dcc_point_month = day_data['dcc_point'][month_idx]
        dcc_precent_month = day_data['dcc_precent'][month_idx]
        dcc_dim_month = day_data['dcc_dim'][month_idx]

        ymd_data = date_s.strftime('%Y%m%d')
        avg_data = avg_month.mean()
        med_data = med_month.mean()
        mod_data = mod_month.mean()
        dcc_files_data = dcc_files_month.sum()
        dcc_point_data = dcc_point_month.sum()
        dcc_precent_data = dcc_precent_month[0]
        dcc_dim_data = dcc_dim_month[0]

        data = ('%-15s' + '%-15.6f' * 3 + '%-15d' * 4 + '\n') % (
            ymd_data, avg_data, med_data, mod_data,
            dcc_files_data, dcc_point_data, dcc_precent_data, dcc_dim_data)

        month_datas.append(data)

        date_s = date_s + relativedelta(months=1)

    return month_datas


def run(rollday):

    rollday = rollday

    ipath1 = inCfg['bias'][satFlag]['ipath1']
    ipath2 = inCfg['bias'][satFlag]['ipath2']
    opath = inCfg['bias'][satFlag]['opath']
    chan1 = inCfg['bias'][satFlag]['chan1']
    chan2 = inCfg['bias'][satFlag]['chan2']
    var = inCfg['bias'][satFlag]['var']
    if 'slope' in inCfg['bias'][satFlag]:
        slope = inCfg['bias'][satFlag]['slope']
        slope = map(float, slope)
    if 'intercept' in inCfg['bias'][satFlag]:
        intercept = inCfg['bias'][satFlag]['intercept']
        intercept = map(float, intercept)

    sat1, sat2 = satFlag.split('_')

    # 处理日 Bias 数据
    idx = 0
    for ch1, ch2 in zip(chan1, chan2):
        if not isinstance(var, list):
            var = [var]
        for each in var:
            FileName1 = 'DCC_%s_%s_%s_Rolldays_%s_ALL_Daily.txt' % (
                sat1, each, ch1, rollday)
            if sat2 == 'STANDARD':
                FileName2 = 'DCC_%s_%s_STANDARD.txt' % (
                    sat1, each)
            else:
                FileName2 = 'DCC_%s_%s_%s_Rolldays_%s_ALL_Daily.txt' % (
                    sat2, each, ch2, rollday)

            DccFile1 = os.path.join(ipath1, rollday, FileName1)
            DccFile2 = os.path.join(ipath2, FileName2)
            ary1 = dcc_data_read(DccFile1)
            ary2 = dcc_data_read(DccFile2)
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
                    avg1 = ary1['Avg'][idx1]
                    med1 = ary1['Med'][idx1]
                    mod1 = ary1['Mod'][idx1]

                    idx2 = np.where(ch2 == ary2['chan'])
                    avg2 = ary2['Avg'][idx2] * 100
                    med2 = ary2['Med'][idx2] * 100
                    mod2 = ary2['Mod'][idx2] * 100

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

                    # 计算相对偏差 Bias = (SAT1的反射率 - 基准反射率) / 基准反射率 * 100%
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

            FileName = 'DCC_%s_%s_%s_Rolldays_%s_ALL_Daily.txt' % (
                satFlag, each, ch1, rollday)
            OutFile = os.path.join(opath, rollday, FileName)
            ##### 4、写入文件
            dcc_data_write(Title, lines, OutFile)
            print OutFile
        idx = idx + 1
    print 'success daily: %s' % rollday

    # 处理月 Bias 数据
    in_file = os.path.join(opath, rollday)
    file_list = get_file_list(in_file, r'.*Daily')
    for day_file in file_list:
        out_file = day_file.replace('Daily', 'Monthly')
        title = ('%-15s' * 8 + '\n') % (
            'date', 'Avg', 'Med', 'Mod', 'dccFiles',
            'dccPoint', 'dccPrecent', 'dccDim')

        day_datas = load_day_ext(day_file)

        month_data = month_average(day_datas)

        with open(out_file, 'w') as f:
            f.write(title)
            f.writelines(month_data)
            print out_file

    print 'success monthly: %s' % rollday


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

        roll_days = inCfg['bias'][satFlag]['rollday']
        if isinstance(roll_days, str):
            roll_days = [roll_days]
        for num in roll_days:
            run(num)

    else:  # 没有参数 输出帮助信息
        print help_info
