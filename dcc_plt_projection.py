# coding: utf-8
__author__ = 'liux'

'''
FileName:     projection_dcc.py
Description:  日月投影分布图
Author:       wangpeng
Date:         2015-08-21
version:      1.0.0.050821_beat
Input:        
Output:       (^_^)
'''

import h5py
import os
import sys
import yaml

import numpy as np

from DP.dp_prj import prj_gll
from DV import dv_map


class PROJ_COMM(object):

    def __init__(self, in_proj_cfg):
        """
        读取yaml格式配置文件
        """
        if not os.path.isfile(in_proj_cfg):
            print 'Not Found %s' % in_proj_cfg
            sys.exit(-1)

        with open(in_proj_cfg, 'r') as stream:
            cfg = yaml.load(stream)
        self.sat = cfg['INFO']['sat']
        self.sensor = cfg['INFO']['sensor']
        self.ymd = cfg['INFO']['ymd']

        self.ifile = cfg['PATH']['ipath']
        self.ofile = cfg['PATH']['opath']
        self.ofile_txt = cfg['PATH']['opath_txt']

        self.cmd = cfg['PROJ']['cmd']
        self.nlat = cfg['PROJ']['nlat']
        self.slat = cfg['PROJ']['slat']
        self.wlon = cfg['PROJ']['wlon']
        self.elon = cfg['PROJ']['elon']
        self.resLat = cfg['PROJ']['resLat']
        self.resLon = cfg['PROJ']['resLon']

    def proj_fy2_dcc(self):
        print self.ymd
        # print 'start project %s %s' % (self.sat, self.sensor)
        # 初始化投影参数   rowMax=None, colMax=None
        lookup_table = prj_gll(nlat=self.nlat, slat=self.slat, wlon=self.wlon,
                               elon=self.elon, resLat=self.resLat,
                               resLon=self.resLon)
        newLats, newLons = lookup_table.generateLatsLons()
        proj_data_num = np.full_like(newLats, 0)
        row = proj_data_num.shape[0]
        col = proj_data_num.shape[1]

        for L1File in self.ifile:
            #        #    print L1File

            h5File = h5py.File(L1File, 'r')
            lons = h5File.get('Longitude')[:]
            lats = h5File.get('Latitude')[:]
            lons = lons / 100.
            lats = lats / 100.
            h5File.close()
            ii, jj = lookup_table.lonslats2ij(lons, lats)

            for i in xrange(row):
                for j in xrange(col):
                    condition = np.logical_and(ii[:, 0] == i, jj[:, 0] == j)
                    idx = np.where(condition)
                    #          if len(idx[0]) > 0:
                    #             print len(idx[0])
                    proj_data_num[i][j] = proj_data_num[i][j] + len(idx[0])

        proj_data_num = np.ma.masked_where(proj_data_num == 0, proj_data_num)
        p = dv_map.dv_map()

        p.easyplot(newLats, newLons, proj_data_num, vmin=0, vmax=10000,
                   box=[30., -30., 60., 120.], ptype=None, markersize=20,
                   marker='s')
        title_name = '%s_dcc_projection_' % self.sat + str(self.ymd)
        p.title = u'dcc： ' + str(title_name) + u' (分辨率1度)'

        fig_name = self.ofile + '/%s' % self.ymd[:6]
        if not os.path.exists(fig_name):
            os.mkdir(fig_name)

        fig_name = fig_name + '/%s_%s_dcc.png' % (self.sat, self.ymd)
        p.savefig(fig_name)
        opath_hdf = self.ofile + '/%s' % self.ymd[:6]
        if not os.path.exists(opath_hdf):
            os.mkdir(opath_hdf)

        opath_hdf = opath_hdf + '/%s_%s_dcc.hdf' % (self.sat, self.ymd)

        h5file_W = h5py.File(opath_hdf, 'w')
        h5file_W.create_dataset('proj_data_nums', dtype='i2',
                                data=proj_data_num, compression='gzip',
                                compression_opts=5, shuffle=True)
        h5file_W.close()

        ###########################################
        # read hdf file and cont values
        opath_txt = self.ofile_txt + '/%s_dcc_daily_count.txt' % self.sat
        if len(self.ifile) == 1 and len(self.ymd) == 8:
            daily_hdf = h5py.File(opath_hdf)
            data_mat = daily_hdf.get("proj_data_nums", 'r')
            count_value = np.sum(data_mat)
            self.FileSave = '%8s\t%8s\n' % (self.ymd, count_value)
            self.Write(opath_txt)

    def Write(self, FileName):
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
            Line = self.FileSave
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
            fp.writelines(self.FileSave)
            fp.close()


def main(args):
    if len(args) == 1:  # 跟参数，则处理输入的时段数据
        in_proj_cfg = args[0]
    else:
        in_proj_cfg = None

    if in_proj_cfg is None:
        print 'input args error exit'
        sys.exit(-1)
    # 初始化投影公共类
    proj = PROJ_COMM(in_proj_cfg)
    proj.proj_fy2_dcc()


if __name__ == '__main__':
    # 获取python输入参数，进行处理
    args = sys.argv[1:]
    main(args)
