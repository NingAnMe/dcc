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
from scipy.interpolate import interpn
from datetime import datetime
from Crypto.Cipher.DES3 import DES3Cipher

admsFile = 'ADMs.h5'
class DccOrgDataRead():
    '''
    percent:数据集中的dcc_percent
    dn:数据集中的DN_ADMS
    ref:数据集中的REF_ADMS
    
    '''
    def __init__(self):
        self.Azimuth = []
        self.BT_Avg_Std = []
        self.DCC_Percent = []
        self.DN_Avg_Std = []
        self.IR_Avg_Std = []
        self.IR_CAL = []
        self.LandCover = []
        self.Latitude = []
        self.Line_Num = []
        self.Longitude = []
        self.Ref_Avg_Std = []
        self.SatelliteAzimuth = []
        self.SatelliteZenith = []
        self.SunAzimuth = []
        self.SunGlint = []
        self.SunZenith = []
        self.TIME = []
        self.VIS_CAL = []
        self.Flag = 0

    def Load(self, iFile):
        try:
            h5File_R = h5py.File(iFile, 'r')
            self.Azimuth = h5File_R.get('Azimuth')[:]
            self.BT_Avg_Std = h5File_R.get('BT_Avg_Std')[:]
            self.DCC_Percent = h5File_R.get('DCC_Percent')[:]
            self.DN_Avg_Std = h5File_R.get('DN_Avg_Std')[:]
            self.IR_Avg_Std = h5File_R.get('IR_Avg_Std')[:]
            self.IR_CAL = h5File_R.get('IR_CAL')[:]
            self.LandCover = h5File_R.get('LandCover')[:]
            self.Latitude = h5File_R.get('Latitude')[:]
            self.Line_Num = h5File_R.get('Line_Num')[:]
            self.Longitude = h5File_R.get('Longitude')[:]
            self.Ref_Avg_Std = h5File_R.get('Ref_Avg_Std')[:]
            self.SatelliteAzimuth = h5File_R.get('SatelliteAzimuth')[:]
            self.SatelliteZenith = h5File_R.get('SatelliteZenith')[:]
            self.SunAzimuth = h5File_R.get('SunAzimuth')[:]
            self.SunGlint = h5File_R.get('SunGlint')[:]
            self.SunZenith = h5File_R.get('SunZenith')[:]
            self.TIME = h5File_R.get('TIME')[:]
            self.VIS_CAL = h5File_R.get('VIS_CAL')[:]
            h5File_R.close()
        except Exception as e:
#             self.FileLst.pop(iFile)
            self.Flag = -1
            print str(e)


def DccDataProcess(data, share):
    '''
    计算所有通道指定的，3x3 或是 5x5或是其他区域的均值，中值，和概率密度
    '''
    # 均值
    mean = np.mean(data, (1,))
    # 中值
    median = np.median(data, (1,))
    # 概率密度
    mode = []
    for i in xrange(data.shape[0]):
        hist, bin_edges = np.histogram(data[i], share)
        idx = np.argmax(hist)
        mode.append(bin_edges[idx])
    mode = np.array(mode)
    return mean, median, mode


def DccDataWrite(dcc, idx, DN_ADMs, Ref_ADMs, ADMs, outFile):
    '''

    outFile:输出文件
    '''
    h5File_W = h5py.File(outFile, 'w')
    h5File_W.create_dataset('ADMs', dtype='f4', data=ADMs, compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('BT_Avg_Std', dtype='i4', data=dcc.BT_Avg_Std[idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('DCC_Percent', dtype='i4', data=dcc.DCC_Percent[idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('DN_ADMs', dtype='i4', data=DN_ADMs, compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('DN_Avg_Std', dtype='i4', data=dcc.DN_Avg_Std[:, idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('IR_Avg_Std', dtype='i4', data=dcc.IR_Avg_Std[idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('IR_CAL', dtype='f4', data=dcc.IR_CAL[idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('REF_ADMs', dtype='i4', data=Ref_ADMs, compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('Ref_Avg_Std', dtype='i4', data=dcc.Ref_Avg_Std[:, idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('Longitude', dtype='i4', data=dcc.Longitude[idx], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('Latitude', dtype='i4', data=dcc.Latitude[idx], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('LandCover', dtype='i4', data=dcc.LandCover[idx], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('Line_Num', dtype='i4', data=dcc.Line_Num[idx], compression='gzip', compression_opts=5, shuffle=True)

    h5File_W.create_dataset('SatelliteAzimuth', dtype='i4', data=dcc.SatelliteAzimuth[idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('SatelliteZenith', dtype='i4', data=dcc.SatelliteZenith[idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('SunAzimuth', dtype='i4', data=dcc.SunAzimuth[idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('SunGlint', dtype='i4', data=dcc.SunGlint[idx], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('Azimuth', dtype='i4', data=dcc.Azimuth[idx], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('SunZenith', dtype='i4', data=dcc.SunZenith[idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('TIME', dtype='i4', data=dcc.TIME[idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.create_dataset('VIS_CAL', dtype='f4', data=dcc.VIS_CAL[:, idx, :], compression='gzip', compression_opts=5, shuffle=True)
    h5File_W.close()

def dcc_cal_des(ymd):

    # des=（当前日期的日地距离/平均日地距离）的平方
#     year=2016
#     month=10day=08;
#     yd = dayofyear(year, month, day);  # 该天为一年中的第几天
    yd = int((datetime.strptime(ymd, '%Y%m%d')).strftime('%j'))
#     print yd
    date_s = datetime.strptime('%s0101' % ymd[:4], '%Y%m%d')
    date_e = datetime.strptime('%s1231' % ymd[:4], '%Y%m%d')
    days_year = (date_e - date_s).days
#     print days_year
    X = 2 * np.pi * (yd - 1) / float(days_year)  # / daysinyear(year);  # % 该年有多少天
#     print X
    des = 1.000109 + 0.033494 * np.cos(X) + 0.001472 * np.sin(X) + 0.000768 * np.cos(2 * X) + 0.000079 * np.sin(2 * X);
    return  1. / des

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
        if satFlag not in inCfg.keys():
            print 'not support satellite: %s' % satFlag
            sys.exit(-1)
        ######################### 读取配置 和 阈值 #####################
        ipath = inCfg['org2slt'][satFlag]['ipath']
        mpath = inCfg['org2slt'][satFlag]['opath']
        ifile = inCfg['org2slt'][satFlag]['regular']
        opath = inCfg['org2slt'][satFlag]['opath']

        TbbRange = inCfg['org2slt'][satFlag]['TbbRange']
        RefRange = inCfg['org2slt'][satFlag]['RefRange']
        tbbStdMax = inCfg['org2slt'][satFlag]['tbbStdMax']
        refStdMax = inCfg['org2slt'][satFlag]['refStdMax']
        Persent = inCfg['org2slt'][satFlag]['Persent']
        RARange = inCfg['org2slt'][satFlag]['RARange']
        VZARange = inCfg['org2slt'][satFlag]['VZARange']
        SZARange = inCfg['org2slt'][satFlag]['SZARange']
        SGA_MIN = inCfg['org2slt'][satFlag]['SGA_MIN']
        LatRange = inCfg['org2slt'][satFlag]['LatRange']
        LonRange = inCfg['org2slt'][satFlag]['LonRange']

        # 按天处理
        while date_s <= date_e:
            ymd = date_s.strftime('%Y%m%d')
              # 替换字符中的%YYYY%MM%DD为当前输入时间
            ex_ipath = ipath.replace('%YYYY', ymd[0:4])
            ex_ipath = ex_ipath.replace('%MM', ymd[4:6])
            ex_ipath = ex_ipath.replace('%DD', ymd[6:8])

            o_path = opath.replace('%YYYY', ymd[0:4])
            o_path = o_path.replace('%MM', ymd[4:6])
            o_path = o_path.replace('%DD', ymd[6:8])

            ex_ifile = ifile.replace('%YYYY', ymd[0:4])
            ex_ifile = ex_ifile.replace('%MM', ymd[4:6])
            ex_ifile = ex_ifile.replace('%DD', ymd[6:8])
            FullFile = os.path.join(ex_ipath, ex_ifile)
#             print FullFile
            ################ 读取dcc org 文件  ###############
            print '1. read dcc org file: %s' % FullFile
            dcc = DccOrgDataRead()
            dcc.Load(FullFile)

            if dcc.Flag != 0:
                date_s = date_s + relativedelta(days=1)
                continue


            ################ 开始过滤 ########################
            # 1、经纬度过滤
#             print LatRange[0], LatRange[1]
            print 'all points nums: %d' % len(dcc.Longitude)
            condition = np.logical_and(dcc.Longitude / 100. > float(LonRange[0]), dcc.Longitude / 100. < float(LonRange[1]))
            condition = np.logical_and(condition, dcc.Latitude / 100. > float(LatRange[0]))
            condition = np.logical_and(condition, dcc.Latitude / 100. < float(LatRange[1]))
            idx = np.where(condition)
            print '2. filter use Lat Lon = %d' % len(idx[0])
            # 2、tbb过滤
            condition = np.logical_and(condition, dcc.BT_Avg_Std[:, 5] > float(TbbRange[0]))
            condition = np.logical_and(condition, dcc.BT_Avg_Std[:, 5] < float(TbbRange[1]))
            condition = np.logical_and(condition, dcc.BT_Avg_Std[:, 6] < float(tbbStdMax))
            idx = np.where(condition)
            print '3. filter use Tbb = %d' % len(idx[0])

            # 3、ref过滤  用13通道
            condition = np.logical_and(condition, dcc.Ref_Avg_Std[11, :, 5] > float(RefRange[0]))
            condition = np.logical_and(condition, dcc.Ref_Avg_Std[11, :, 5] < float(RefRange[1]))
            condition = np.logical_and(condition, dcc.Ref_Avg_Std[11, :, 6] < float(refStdMax))
            idx = np.where(condition)
            print '4. filter use Ref = %d' % len(idx[0])

            # 4、prcent 过滤
            condition = np.logical_and(condition, dcc.DCC_Percent[:, 3] == int(Persent))

            idx = np.where(condition)
            print '5. filter use Prcent = %d' % len(idx[0])

            # 5、角度过滤
            condition = np.logical_and(condition, dcc.Azimuth[:, 5] / 100. > float(RARange[0]))
            condition = np.logical_and(condition, dcc.Azimuth[:, 5] / 100. < float(RARange[1]))
            condition = np.logical_and(condition, dcc.SunZenith[:, 5] / 100. > float(SZARange[0]))
            condition = np.logical_and(condition, dcc.SunZenith[:, 5] / 100. < float(SZARange[1]))
            condition = np.logical_and(condition, dcc.SatelliteZenith[:, 5] / 100. > float(VZARange[0]))
            condition = np.logical_and(condition, dcc.SatelliteZenith[:, 5] / 100. < float(VZARange[1]))
            condition = np.logical_and(condition, dcc.SunGlint > float(SGA_MIN))
            idx = np.where(condition)
            print '6. filter use Angle = %d' % len(idx[0])

            if len(idx[0]) == 0:
                date_s = date_s + relativedelta(days=1)
                continue

            # 6、计算Adms
            print '7. Cal ADMs'
            X = np.arange(5, 176)
            Y = np.arange(5, 86)
            Z = np.arange(5, 46)
            x, y, z = np.meshgrid(X, Y, Z)

            h5File_R = h5py.File(admsFile, 'r')
            adms = h5File_R.get('ADMs')[:]
            h5File_R.close()
            n_adms = np.swapaxes(adms, 0, -1)

            RA = (dcc.Azimuth[idx, 5].reshape(len(idx[0]))) / 100.
            SZA = (dcc.SunZenith[idx, 5].reshape(len(idx[0]))) / 100.
            VZA = (dcc.SatelliteZenith[idx, 5].reshape(len(idx[0]))) / 100.
            listASV = []

            for i in range(len(RA)):
                listASV.append(VZA[i])
                listASV.append(RA[i])
                listASV.append(SZA[i])
            ADMs_pixle1 = interpn((Y, X, Z), n_adms, listASV)
            # 6.2 计算des
            des = dcc_cal_des(ymd)

            DN_ADMs = dcc.DN_Avg_Std[:, idx[0], 5] / np.cos(np.deg2rad(SZA)) * des / ADMs_pixle1
            DN5_ADMs = dcc.IR_Avg_Std[idx[0], 5] / np.cos(np.deg2rad(SZA)) * des / ADMs_pixle1
            DN_ADMs_all = np.insert(DN_ADMs, 4, DN5_ADMs, 0)
            DN_ADMs_all = np.swapaxes(DN_ADMs_all, 0, 1)

            Ref_ADMs = dcc.Ref_Avg_Std[:, idx[0], 5] / np.cos(np.deg2rad(SZA)) * des / ADMs_pixle1
            Ref_ADMs = np.swapaxes(Ref_ADMs, 0, 1)

            # 7 输出slt精提取文件
            if not os.path.isdir(o_path):
                os.makedirs(o_path)
            outFile = os.path.join(o_path, '%s_DCC_SLT_%s.H5' % (satFlag, ymd))
            print '8. output %s' % outFile
            DccDataWrite(dcc, idx[0], DN_ADMs_all, Ref_ADMs, ADMs_pixle1, outFile)
            date_s = date_s + relativedelta(days=1)

    else:  # 没有参数 输出帮助信息
        print help_info

