# coding:utf-8
'''
Created on 2017年9月21日

@author: wangpeng
'''
import os, sys, h5py
from configobj import ConfigObj
from PB import pb_time
from dateutil.relativedelta import relativedelta
import numpy as np


def DccFineFile(ipath, ifile, C_date, rolldays):
    '''
    ipath:文件输入路径 其中携带的%YYYY%MM%DD 会根据真实日期替换
    ifile:文件名称   其中携带的%YYYY%MM%DD 会根据真实日期替换
    C_date:当前日期
    rolldays:滚动天数
    return:找到符合条件的所有全路径的文件清单
    '''

    FileLst = []
    # C_date 当前时间
    # F_date 向前滚动后的首个日期
    F_date = C_date - relativedelta(days=(rolldays - 1))
    while F_date <= C_date:
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


class DccDataRead():
    """
    percent:数据集中的dcc_percent
    dn:数据集中的DN_ADMS
    ref:数据集中的REF_ADMS
    """
    def __init__(self):
        self.percent = []
        self.dn = []
        self.ref = []
        self.FileLst = []

    def Load(self):
        for iFile in FileLst:
            try:
                h5File_R = h5py.File(iFile, 'r')
                # 针对 FY3D 做的调整， DCC_Percent 在 3D 是 3维， 3C 是 2维
                percent = h5File_R.get('DCC_Percent')[0]
                dn = h5File_R.get('DN_ADMs')[:]
                ref = h5File_R.get('REF_ADMs')[:]
                h5File_R.close()
            except Exception as e:
                self.FileLst.pop(iFile)
                print str(e)

            # 第一个数据
            if self.dn == []:
                self.percent = percent
                self.dn = dn
                self.ref = ref
            # 其他数据追加
            else:
                self.percent = np.concatenate((self.percent, percent), axis=0)
                self.dn = np.concatenate((self.dn, dn), axis=1)
                self.ref = np.concatenate((self.ref, ref), axis=1)


def DccDataProcess(data, share):
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
#     mean = np.mean(data, (1,))
#     mean = np.nanmean(newdata, axis=1)
    # 中值
#     median = np.median(data, (1,))
#     median = np.nanmedian(newdata, axis=1)
    # 概率密度
#     mode = []
#     for i in xrange(data.shape[0]):
#         hist, bin_edges = np.histogram(data[i], share)
#         idx = np.argmax(hist)
#         mode.append(bin_edges[idx])
#     mode = np.array(mode)
#     return mean, median, mode


def DccDataWrite(title , data, outFile):
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

        newLines = sorted(DICT_D.iteritems(), key=lambda d:d[0], reverse=False)
        for i in xrange(len(newLines)):
            allLines.append(str(newLines[i][0]) + str(newLines[i][1]))
        fp = open(outFile, 'w')
        fp.write(Title)
        fp.writelines(allLines)
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
            【参数1】：FY4A or HM08 or FY3C+MERSI
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

        # 卫星标识检查，配置中没有则不处理
        if satFlag not in inCfg['ext'].keys():
            print 'not support satellite: %s' % satFlag
            sys.exit(-1)

        ipath = inCfg['ext'][satFlag]['ipath']
        mpath = inCfg['ext'][satFlag]['mpath']
        ifile = inCfg['ext'][satFlag]['regular']
        percent = int(inCfg['ext'][satFlag]['percent'])
        rollday = int(inCfg['ext'][satFlag]['rollday'])
        share = int(inCfg['ext'][satFlag]['share'])
        window = int(inCfg['ext'][satFlag]['window'])
        # 按天处理
        while date_s <= date_e:
            ymd = date_s.strftime('%Y%m%d')

            ######### 一、查找当前天滚动后的所有文件 ##############
            FileLst = DccFineFile(ipath, ifile, date_s, rollday)

            ######### 二、读取所rolldays条件内所有文件并对数据累加 #############
            dcc = DccDataRead()
            dcc.FileLst = FileLst
            dcc.Load()
            if len(FileLst) != 0:
                ######### 三、计算中值，均值，概率密度 #############################

                Dn_mean, Dn_median, Dn_mode = DccDataProcess(dcc.dn[:, :, window], share)
                Ref_mean, Ref_median, Ref_mode = DccDataProcess(dcc.ref[:, :, window], share)
                print ymd
                ######### 四、写入数据，按照通道进行输出，规范dcc输出格式 ###########
                ######### 写入DN值
                for i in range(Dn_mean.shape[0]):
                    band = i + 1
                    if i >= 4 and 'FY3C+MERSI' in satFlag:
                        band = band + 1
                    ##### 1、拼接文件名
                    dnName = 'DCC_' + satFlag + '_DN' + '_CH_%02d' % band + '_Rolldays_%d_ALL.txt' % rollday

                    ##### 2、拼接完整输出文件
                    dnOutFile = os.path.join(mpath, dnName)
                    dccFiles = len(FileLst)
                    DnPoints = len(dcc.dn[i, :, window])

                    ##### 3、拼接文件头和数据体信息
                    Title = ('%-15s' * 8 + '\n') % ('date', 'Avg', 'Med', 'Mod', 'dccFiles',
                                                    'dccPoint', 'dccPrecent', 'dccDim')
                    Data = ('%-15s' + '%-15.6f' * 3 + '%-15d' * 4 + '\n') % (ymd, Dn_mean[i], Dn_median[i], Dn_mode[i],
                                                                             dccFiles, DnPoints, percent, window)
                    ##### 4、写入文件
                    DccDataWrite(Title, Data, dnOutFile)
                ######### 写入Ref值
                for i in range(Ref_mean.shape[0]):
                    band = i + 1
                    if i >= 4 and 'FY3C+MERSI' in satFlag:
                        band = band + 1
                    ##### 1、拼接文件名
                    refName = 'DCC_' + satFlag + '_REF' + '_CH_%02d' % band + '_Rolldays_%d_ALL.txt' % rollday

                    ##### 2、拼接完整输出文件
                    refOutFile = os.path.join(mpath, refName)
                    dccFiles = len(FileLst)
                    RefPoints = len(dcc.ref[i, :, window])

                    ##### 3、拼接文件头信息
                    Title = ('%-15s' * 8 + '\n') % ('date', 'Avg', 'Med', 'Mod', 'dccFiles',
                                                    'dccPoint', 'dccPrecent', 'dccDim')
                    Data = ('%-15s' + '%-15.6f' * 3 + '%-15d' * 4 + '\n') % (ymd, Ref_mean[i], Ref_median[i], Ref_mode[i],
                                                                             dccFiles, RefPoints, percent, window)
                    ##### 4、写入文件
                    DccDataWrite(Title, Data, refOutFile)

            date_s = date_s + relativedelta(days=1)

    else:  # 没有参数 输出帮助信息
        print help_info
