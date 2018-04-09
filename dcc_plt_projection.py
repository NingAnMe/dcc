# coding: utf-8
__author__ = 'anning'
__date__ = '2018-04-09'

import os
import sys
import h5py
import calendar
from datetime import datetime
from multiprocessing import Pool, Lock
from dateutil.relativedelta import relativedelta

import numpy as np
from configobj import ConfigObj

from DP.dp_prj import prj_gll
from DV import dv_map
from PB import pb_time

lock = Lock()


class ProjComm(object):

    def __init__(self, in_proj_cfg, ymd_str, is_monthly_boole):
        """
        读取yaml格式配置文件
        """
        if not os.path.isfile(in_proj_cfg):
            print 'Not Found %s' % in_proj_cfg
            sys.exit(-1)
        cfg = ConfigObj(in_proj_cfg)

        self.sat = cfg['proj']['FY3D+MERSI']['sat']
        self.sensor = cfg['proj']['FY3D+MERSI']['sensor']

        if self.sat and self.sensor:
            self.sat_sensor = "%s+%s" % (self.sat, self.sensor)
        else:
            self.sat_sensor = self.sat

        self.ymd = ymd_str
        self.is_monthly = is_monthly_boole

        self.data_count = ''

        self.ifile = cfg['proj']['FY3D+MERSI']['ipath']  # SLT 数据文件
        self.ofile = cfg['proj']['FY3D+MERSI']['opath']
        self.ofile_txt = cfg['proj']['FY3D+MERSI']['opath_txt']

        self.nlat = None
        self.slat = None
        self.wlon = None
        self.elon = None
        self.resLat = None
        self.resLon = None
        if cfg['proj']['FY3D+MERSI']['nlat']:
            self.nlat = float(cfg['proj']['FY3D+MERSI']['nlat'])
        if cfg['proj']['FY3D+MERSI']['slat']:
            self.slat = float(cfg['proj']['FY3D+MERSI']['slat'])
        if cfg['proj']['FY3D+MERSI']['wlon']:
            self.wlon = float(cfg['proj']['FY3D+MERSI']['wlon'])
        if cfg['proj']['FY3D+MERSI']['elon']:
            self.elon = float(cfg['proj']['FY3D+MERSI']['elon'])
        if cfg['proj']['FY3D+MERSI']['resLat']:
            self.resLat = float(cfg['proj']['FY3D+MERSI']['resLat'])
        if cfg['proj']['FY3D+MERSI']['resLon']:
            self.resLon = float(cfg['proj']['FY3D+MERSI']['resLon'])

    def proj_dcc(self):

        # 初始化投影参数   rowMax=None, colMax=None
        lookup_table = prj_gll(resLat=self.resLat,
                               resLon=self.resLon)
        newLats, newLons = lookup_table.generateLatsLons()
        proj_data_num = np.full_like(newLats, 0)
        row = proj_data_num.shape[0]
        col = proj_data_num.shape[1]

        if self.is_monthly:  # 如果是月的，需要查找当前自然月所有数据
            PERIOD = calendar.monthrange(int(self.ymd[:4]),
                                         int(self.ymd[4:6]))[1]  # 当前月份天数
            _ymd = self.ymd[:6] + '%02d' % PERIOD  # 当月最后一天
        else:
            PERIOD = 1
            _ymd = self.ymd

        file_list = []
        for daydelta in xrange(PERIOD):
            cur_ymd = pb_time.ymd_plus(_ymd, -daydelta)
            # 判断文件是否存在
            file_name = '%s_DCC_SLT_%s.H5' % (self.sat_sensor, cur_ymd)
            ym = self.ymd[:6]
            HDF_file = os.path.join(self.ifile, ym, file_name)
            if not os.path.isfile(HDF_file):
                print("file no exist : %s" % HDF_file)
            else:
                file_list.append(HDF_file)

        if len(file_list) == 0:
            return

        # 开始进行投影
        for HDF_file in file_list:
            h5File = h5py.File(HDF_file, 'r')
            lons = h5File.get('Longitude')[:]
            lats = h5File.get('Latitude')[:]
            h5File.close()
            lons = lons / 100.
            lats = lats / 100.

            ii, jj = lookup_table.lonslats2ij(lons, lats)

            for i in xrange(row):
                for j in xrange(col):
                    condition = np.logical_and(ii[:] == i, jj[:] == j)
                    idx = np.where(condition)
                    proj_data_num[i][j] = proj_data_num[i][j] + len(idx[0])
        proj_data_num = np.ma.masked_where(proj_data_num == 0, proj_data_num)

        if self.is_monthly:
            print("plot: %s" % self.ymd[0:6])
            p = dv_map.dv_map()
            p.easyplot(newLats, newLons, proj_data_num, vmin=0, vmax=10000,
                       ptype=None, markersize=20,
                       marker='s')
            title_name = '%s_dcc_projection_' % self.sat_sensor + str(
                self.ymd[0:6])
            p.title = u'dcc： ' + str(title_name) + u' (分辨率1度)'

            opath_fig = os.path.join(self.ofile, 'Monthly', '%s' % self.ymd[:6])
            if not os.path.exists(opath_fig):
                os.makedirs(opath_fig)

            fig_name = os.path.join(opath_fig,
                                    '%s_%s_dcc_monthly.png' % (self.sat_sensor,
                                                               self.ymd[:6]))
            p.savefig(fig_name)

            opath_hdf = os.path.join(self.ofile, 'Monthly', '%s' % self.ymd[:6])
            if not os.path.exists(opath_hdf):
                os.mkdir(opath_hdf)

            opath_hdf = os.path.join(opath_hdf,
                                     '%s_%s_dcc_monthly.hdf' % (self.sat_sensor,
                                                                self.ymd[0:6]))

            h5file_W = h5py.File(opath_hdf, 'w')
            h5file_W.create_dataset('proj_data_nums', dtype='i2',
                                    data=proj_data_num, compression='gzip',
                                    compression_opts=5, shuffle=True)
            h5file_W.close()

            ###########################################
            # read hdf file and cont values
            print("write txt: %s" % self.ymd[0:6])
            if not os.path.exists(self.ofile_txt):
                os.mkdir(self.ofile_txt)
            opath_txt = os.path.join(
                self.ofile_txt, '%s_dcc_monthly_count.txt' % self.sat_sensor)

            if self.ifile and len(self.ymd) == 8:
                hdf = h5py.File(opath_hdf, 'r')
                data_mat = hdf.get("proj_data_nums")[:]
                hdf.close()
                count_value = np.sum(data_mat)
                self.data_count = '%8s\t%8s\n' % (self.ymd[0:6], count_value)

                lock.acquire()
                self.write_txt(opath_txt)
                lock.release()
        else:
            print("plot: %s" % self.ymd)
            p = dv_map.dv_map()
            p.easyplot(newLats, newLons, proj_data_num, vmin=0, vmax=10000,
                       ptype=None, markersize=20,
                       marker='s')
            title_name = '%s_dcc_projection_' % self.sat_sensor + str(self.ymd)
            p.title = u'dcc： ' + str(title_name) + u' (分辨率1度)'

            opath_fig = os.path.join(self.ofile, 'Daily', '%s' % self.ymd)
            if not os.path.exists(opath_fig):
                os.makedirs(opath_fig)

            fig_name = os.path.join(opath_fig,
                                    '%s_%s_dcc_daily.png' % (self.sat_sensor,
                                                             self.ymd))
            p.savefig(fig_name)

            opath_hdf = os.path.join(self.ofile, 'Daily', '%s' % self.ymd)
            if not os.path.exists(opath_hdf):
                os.mkdir(opath_hdf)

            opath_hdf = os.path.join(opath_hdf,
                                     '%s_%s_dcc_daily.hdf' % (self.sat_sensor,
                                                              self.ymd))

            h5file_W = h5py.File(opath_hdf, 'w')
            h5file_W.create_dataset('proj_data_nums', dtype='i2',
                                    data=proj_data_num, compression='gzip',
                                    compression_opts=5, shuffle=True)
            h5file_W.close()

            ###########################################
            # read hdf file and cont values
            print("write txt: %s" % self.ymd)
            if not os.path.exists(self.ofile_txt):
                os.mkdir(self.ofile_txt)
            opath_txt = os.path.join(
                self.ofile_txt, '%s_dcc_daily_count.txt' % self.sat_sensor)

            if self.ifile and len(self.ymd) == 8:
                hdf = h5py.File(opath_hdf, 'r')
                data_mat = hdf.get("proj_data_nums")[:]
                count_value = np.sum(data_mat)
                self.data_count = '%8s\t%8s\n' % (self.ymd, count_value)

                lock.acquire()
                self.write_txt(opath_txt)
                lock.release()

    def write_txt(self, FileName):
        allLines = []
        DICT_D = {}
        FilePath = os.path.dirname(FileName)
        if not os.path.exists(FilePath):
            os.makedirs(FilePath)

        Title = '%8s\t%8s\n' % ('[time]', '[values]')
        if os.path.isfile(FileName) and os.path.getsize(FileName) != 0:
            fp = open(FileName, 'r')
            fp.readline()
            Lines = fp.readlines()
            fp.close()
            # 使用字典特性，保证时间唯一，读取数据
            for Line in Lines:
                DICT_D[Line[:8]] = Line[8:]
            # 添加或更改数据
            Line = self.data_count
            DICT_D[Line[:8]] = Line[8:]
            # 按照时间排序

            newLines = sorted(DICT_D.iteritems(), key=lambda d: d[0],
                              reverse=False)
            for i in xrange(len(newLines)):
                allLines.append(str(newLines[i][0]) + str(newLines[i][1]))
            fp = open(FileName, 'w')
            fp.write(Title)
            fp.writelines(allLines)
            fp.close()
        else:
            fp = open(FileName, 'w')
            fp.write(Title)
            fp.writelines(self.data_count)
            fp.close()


def run(config, run_ymd, monthly):
    # 配置文件
    in_proj_cfg = config

    # 初始化投影公共类
    print('start: %s' % run_ymd)
    proj = ProjComm(in_proj_cfg, run_ymd, monthly)
    proj.proj_dcc()
    print('success: %s' % run_ymd)


if __name__ == '__main__':
    # 获取程序参数接口
    args = sys.argv[1:]
    help_info = \
        u'''
            【参数1】：SAT+SENSOR
            【参数2】：yyyymmdd-yyyymmdd or yyyymm-yyyymm
        '''
    if '-h' in args:
        print(help_info)
        sys.exit(-1)

    # 获取程序所在位置，拼接配置文件
    MainPath, MainFile = os.path.split(os.path.realpath(__file__))
    ProjPath = os.path.dirname(MainPath)
    omPath = os.path.dirname(ProjPath)
    dvPath = os.path.join(os.path.dirname(omPath), 'DV')
    cfgFile = os.path.join(ProjPath, 'dcc', 'global_dcc.cfg')

    # 配置不存在预警
    if not os.path.isfile(cfgFile):
        print(u'配置文件不存在 %s' % cfgFile)
        sys.exit(-1)

    # 读取全局配置
    inCfg = ConfigObj(cfgFile)
    threadNum = inCfg['CROND']['threads']  # 线程数量

    # 开启进程池
    pool = Pool(processes=int(threadNum))

    if len(args) == 2:  # 跟参数，则处理输入的时段数据
        sat_sensor = args[0]
        str_time = args[1]
        date_s, date_e = pb_time.arg_str2date(str_time)

        if len(str_time) == 17:
            timeStep = relativedelta(days=1)
            is_monthly = False
        elif len(str_time) == 13:
            timeStep = relativedelta(months=1)
            is_monthly = True
        else:
            print(help_info)
            sys.exit(-1)

        # 开启并行
        while date_s <= date_e:
            ymd = date_s.strftime('%Y%m%d')
            pool.apply_async(run, (cfgFile, ymd, is_monthly))
            date_s = date_s + timeStep

        pool.close()
        pool.join()

    elif len(args) == 1:  # 跟参数，则处理输入的时段数据
        sat_sensor = args[0]
        lanch_date = inCfg['plt'][sat_sensor]['lanch_date']  # 第一天数据时间
        today = datetime.utcnow().strftime('%Y%m%d')  # 现在时间
        str_time = '%s-%s' % (lanch_date, today)

        date_s, date_e = pb_time.arg_str2date(str_time)

        if len(str_time) == 17:
            timeStep = relativedelta(days=1)
        else:
            print(help_info)
            sys.exit(-1)

        # 开启并行
        while date_s <= date_e:
            ymd = date_s.strftime('%Y%m%d')
            pool.apply_async(run, (sat_sensor, ymd))
            date_s = date_s + timeStep

        pool.close()
        pool.join()

    else:
        print(help_info)
        sys.exit(-1)
