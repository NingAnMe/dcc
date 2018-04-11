# coding:utf-8
"""
Created on 2018年4月10日

@author: anning
"""
import re
import os
import sys
import h5py
from datetime import datetime

import numpy as np
from configobj import ConfigObj
from dateutil.relativedelta import relativedelta

from PB import pb_time


def dcc_find_file(ipath, ifile, c_date, rolldays):
    """
    ipath:文件输入路径 其中携带的%YYYY%MM%DD 会根据真实日期替换
    ifile:文件名称   其中携带的%YYYY%MM%DD 会根据真实日期替换
    c_date:当前日期
    rolldays:滚动天数
    return:找到符合条件的所有全路径的文件清单
    """

    FileLst = []
    # c_date 当前时间
    # F_date 向前滚动后的首个日期
    if not isinstance(rolldays, int):
        rolldays = int(rolldays)
    F_date = c_date - relativedelta(days=(rolldays - 1))
    while F_date <= c_date:
        ymd = F_date.strftime('%Y%m%d')
        # 替换字符中的%YYYY%MM%DD为当前输入时间
        ex_ipath = ipath.replace('%YYYY', ymd[0:4])
        ex_ipath = ex_ipath.replace('%MM', ymd[4:6])
        ex_ipath = ex_ipath.replace('%DD', ymd[6:8])
        ex_ifile = ifile.replace('%YYYY', ymd[0:4])
        ex_ifile = ex_ifile.replace('%MM', ymd[4:6])
        ex_ifile = ex_ifile.replace('%DD', ymd[6:8])
        FullFile = os.path.join(ex_ipath, ex_ifile)
        if os.path.isfile(FullFile):
            FileLst.append(FullFile)
        F_date = F_date + relativedelta(days=1)

    return FileLst


class DccDataRead(object):
    """
    percent:数据集中的dcc_percent
    dn:数据集中的DN_ADMS
    ref:数据集中的REF_ADMS
    """

    def __init__(self):
        self.empty = True
        self.percent = None
        self.dn = None
        self.ref = None
        self.FileLst = []

    def load(self):
        for iFile in self.FileLst:
            try:
                h5File_R = h5py.File(iFile, 'r')
                # 针对 FY3D 做的调整， DCC_Percent 在 3D 是 3维， 3C 是 2维
                percent = h5File_R.get('DCC_Percent')[2]
                dn = h5File_R.get('DN_ADMs')[:]
                ref = h5File_R.get('REF_ADMs')[:]
                h5File_R.close()
            except Exception as e:
                self.FileLst.pop(iFile)
                print str(e)

            # 第一个数据
            if self.empty:
                self.percent = percent
                self.dn = dn
                self.ref = ref
            # 其他数据追加
            else:
                self.percent = np.concatenate((self.percent, percent), axis=0)
                self.dn = np.concatenate((self.dn, dn), axis=1)
                self.ref = np.concatenate((self.ref, ref), axis=1)
                self.empty = False


def dcc_data_process(data, share):
    """
    计算所有通道指定的，3x3 或是 5x5或是其他区域的均值，中值，和概率密度
    """
    # 均值
    # 过滤无效值

    #     print mean.shape
    dataMean = []
    dataMedian = []
    dataMode = []
    # 根据通道数循环
    for i in range(data.shape[0]):
        idx = np.where(data[i] < 65535)
        if len(idx[0]) != 0:
            # 如果不是天充值需要计算 均值 中值 概率密度
            mean = np.mean(data[i, idx])
            median = np.median(data[i, idx])
            hist, bin_edges = np.histogram(data[i, idx], share)
            idx = np.argmax(hist)
            mode = bin_edges[idx]

        else:  # 否则添加无效值
            mean = np.nan
            median = np.nan
            mode = np.nan
        dataMean.append(mean)
        dataMedian.append(median)
        dataMode.append(mode)
    # list转成array
    dataMean = np.array(dataMean)
    dataMedian = np.array(dataMedian)
    dataMode = np.array(dataMode)

    return dataMean, dataMedian, dataMode


def dcc_data_write(title, data, outFile):
    """
    title: 标题
    data： 数据体
    outFile:输出文件
    """

    allLines = []
    DICT_D = {}
    FilePath = os.path.dirname(outFile)
    if not os.path.exists(FilePath):
        os.makedirs(FilePath)

    if os.path.isfile(outFile) and os.path.getsize(outFile) != 0:
        fp = open(outFile, 'r')
        fp.readline()
        Lines = fp.readlines()
        fp.close()
        # 使用字典特性，保证时间唯一，读取数据
        for Line in Lines:
            DICT_D[Line[:8]] = Line[8:]
        # 添加或更改数据
        Line = data
        DICT_D[Line[:8]] = Line[8:]
        # 按照时间排序

        newLines = sorted(DICT_D.iteritems(), key=lambda d: d[0], reverse=False)
        for i in xrange(len(newLines)):
            allLines.append(str(newLines[i][0]) + str(newLines[i][1]))
        fp = open(outFile, 'w')
        fp.write(title)
        fp.writelines(allLines)
        fp.close()
    else:
        fp = open(outFile, 'w')
        fp.write(title)
        fp.writelines(data)
        fp.close()


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

    ipath = inCfg['ext'][satFlag]['ipath']
    mpath = inCfg['ext'][satFlag]['mpath']
    ifile = inCfg['ext'][satFlag]['regular']
    percent = int(inCfg['ext'][satFlag]['percent'])
    share = int(inCfg['ext'][satFlag]['share'])
    window = int(inCfg['ext'][satFlag]['window'])
    # lanch_date = inCfg['ext'][satFlag]['lanch_date']
    # 按天处理
    date_s, date_e = pb_time.arg_str2date(str_time)
    while date_s <= date_e:
        ymd = date_s.strftime('%Y%m%d')

        ######### 一、查找当前天滚动后的所有文件 ##############
        FileLst = dcc_find_file(ipath, ifile, date_s, rollday)

        ######### 二、读取所rolldays条件内所有文件并对数据累加 #############
        dcc = DccDataRead()
        dcc.FileLst = FileLst
        dcc.load()
        if len(FileLst) != 0:
            ######### 三、计算中值，均值，概率密度 #############################

            Dn_mean, Dn_median, Dn_mode = dcc_data_process(dcc.dn[:, :, window],
                                                           share)
            Ref_mean, Ref_median, Ref_mode = dcc_data_process(
                dcc.ref[:, :, window], share)
            print 'rollday: %s, date: %s' % (rollday, ymd)
            ######### 四、写入数据，按照通道进行输出，规范dcc输出格式 ###########
            ######### 写入DN值
            for i in range(Dn_mean.shape[0]):
                band = i + 1
                if i >= 4 and 'FY3C+MERSI' in satFlag:
                    band = band + 1
                ##### 1、拼接文件名
                dnName = 'DCC_%s_DN_CH_%02d_Rolldays_%s_ALL_Daily.txt' % (
                    satFlag, band, rollday)

                ##### 2、拼接完整输出文件
                dnOutFile = os.path.join(mpath, rollday, dnName)
                dccFiles = len(FileLst)
                DnPoints = len(dcc.dn[i, :, window])

                ##### 3、拼接文件头和数据体信息
                Title = ('%-15s' * 8 + '\n') % (
                    'date', 'Avg', 'Med', 'Mod', 'dccFiles',
                    'dccPoint', 'dccPrecent', 'dccDim')
                Data = ('%-15s' + '%-15.6f' * 3 + '%-15d' * 4 + '\n') % (
                    ymd, Dn_mean[i], Dn_median[i], Dn_mode[i],
                    dccFiles, DnPoints, percent, window)
                ##### 4、写入文件
                dcc_data_write(Title, Data, dnOutFile)

            ######### 写入Ref值
            for i in range(Ref_mean.shape[0]):
                band = i + 1
                if i >= 4 and 'FY3C+MERSI' in satFlag:
                    band = band + 1
                ##### 1、拼接文件名
                refName = 'DCC_%s_REF_CH_%02d_Rolldays_%s_ALL_Daily.txt' % (
                    satFlag, band, rollday)

                ##### 2、拼接完整输出文件
                refOutFile = os.path.join(mpath, rollday, refName)
                dccFiles = len(FileLst)
                RefPoints = len(dcc.ref[i, :, window])

                ##### 3、拼接文件头信息
                Title = ('%-15s' * 8 + '\n') % (
                    'date', 'Avg', 'Med', 'Mod', 'dccFiles',
                    'dccPoint', 'dccPrecent', 'dccDim')
                Data = ('%-15s' + '%-15.6f' * 3 + '%-15d' * 4 + '\n') % (
                    ymd, Ref_mean[i], Ref_median[i], Ref_mode[i],
                    dccFiles, RefPoints, percent, window)
                ##### 4、写入文件
                dcc_data_write(Title, Data, refOutFile)

        date_s = date_s + relativedelta(days=1)
    print 'success daily: %s' % rollday

    # 计算月平均
    in_file = os.path.join(mpath, rollday)
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
    print 'success Monthly: %s' % rollday


########################### 主程序入口 ############################
if __name__ == '__main__':
    # 获取程序参数接口
    args = sys.argv[1:]
    help_info = \
        u'''
            【参数1】：SAT or SAT+SENSOR or SAT1_SAT2
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

    # # 开启进程池
    # threadNum = 3
    # pool = Pool(processes=int(threadNum))

    if len(args) == 2:  # 需要跟俩个参数执行
        satFlag = args[0]
        str_time = args[1]

        roll_days = inCfg['ext'][satFlag]['rollday']
        if isinstance(roll_days, str):
            roll_days = [roll_days]
        for num in roll_days:
            run(num)

    else:  # 没有参数 输出帮助信息
        print help_info
