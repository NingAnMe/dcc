# coding:utf-8
__author__ = 'anning'
__create_date__ = '2018-04-12'

import os
import sys
from datetime import datetime
from configobj import ConfigObj
from dateutil.relativedelta import relativedelta

import h5py
import numpy as np
from matplotlib.ticker import MultipleLocator

from PB import pb_time, pb_io
from DV.dv_pub_legacy import plt, mdates, set_tick_font, FONT0, add_annotate,\
    add_title


def filter_fy3d_data(data, var):
    """
    FY3D 过滤无效值 65535, 并且除以 100
    :return:
    """
    if var == 'DN':
        idx = np.logical_and(data >= 0, data < 65535)
        data = data[idx]
    elif var == 'REF':
        idx = np.where(data < 65535)
        data = data[idx] / 100.
    else:
        data = data
    return data


class HistComm(object):
    """
    直方图公共类
    :param object:
    :return:
    """
    def __init__(self, in_proj_cfg, ymd_str=None, is_monthly_boole=None):
        """
        读取配置文件，进行初始化
        """
        if not os.path.isfile(in_proj_cfg):
            print 'Not Found %s' % in_proj_cfg
            sys.exit(-1)
        cfg = ConfigObj(in_proj_cfg)

        self.sat = cfg['hist']['FY3D+MERSI']['sat']
        self.sensor = cfg['hist']['FY3D+MERSI']['sensor']
        if self.sat and self.sensor:
            self.sat_sensor = "%s+%s" % (self.sat, self.sensor)
        else:
            self.sat_sensor = self.sat

        self.empty = True
        self.dn = None
        self.ref = None
        self.data = {}

        self.ifile = cfg['hist']['FY3D+MERSI']['ipath']  # SLT 数据文件
        self.ofile = cfg['hist']['FY3D+MERSI']['opath']
        self.ofile_txt = cfg['hist']['FY3D+MERSI']['opath_txt']
        self.window = int(cfg['hist']['FY3D+MERSI']['window'])
        self.chan = cfg['hist']['FY3D+MERSI']['band']
        self.regular = cfg['hist']['FY3D+MERSI']['regular']

        self.var = cfg['hist']['FY3D+MERSI']['var']
        if isinstance(self.var, str):
            self.var = [self.var]

    def load_data(self, slt_file):
        """
        读取 SLT 文件里面的 ADMs 数据
        :param slt_file:
        :return:
        """
        with h5py.File(slt_file, 'r') as hdf_file:
            if hdf_file.get('DN_ADMs')[:, :, self.window] is not None:
                self.data['DN'] = hdf_file.get('DN_ADMs')[:, :, self.window]
            if hdf_file.get('REF_ADMs')[:, :, self.window] is not None:
                self.data['REF'] = hdf_file.get('REF_ADMs')[:, :, self.window]

        if not self.dn:
            self.empty = False


def draw_histogram(filename, dvalues,
                   titledict=None, tl_list=None, tr_list=None,
                   bins=200, ranges=None, label='Hist'):
    """
    画直方图
    """
    plt.style.use(os.path.join(dvPath, 'dv_pub_legacy.mplstyle'))

    alpha = 1
    fig = plt.figure(figsize=(6, 4))
    fig.subplots_adjust(top=0.92, bottom=0.13, left=0.11, right=0.96)

    ax = plt.gca()
    ax.grid(True)

    ax.hist(dvalues, bins, histtype='bar', color='blue',
            label=label, alpha=alpha)

    ax.legend(prop={'size': 10})

    add_annotate(ax, tl_list, 'left')
    add_annotate(ax, tr_list, 'right')
    add_title(titledict)
    set_tick_font(ax)

    plt.savefig(filename)
    fig.clear()
    plt.close()


def run():
    # 按天处理
    date_s, date_e = pb_time.arg_str2date(str_time)
    date_c = date_s
    # 初始化 hist 类
    hist = HistComm(cfgFile)
    while date_c <= date_e:
        ymd = date_c.strftime('%Y%m%d')
        ym = ymd[0:6]

        # 加载数据
        file_name = hist.regular.replace('%YYYY%MM%DD', ymd)
        slt_file = os.path.join(hist.ifile, ym, file_name)
        # 如果文件存在，加载数据
        if os.path.isfile(slt_file):
            hist.load_data(slt_file)
        else:
            date_c = date_c + relativedelta(days=1)
            continue

        for var in hist.var:
            for k, ch in enumerate(hist.chan):
                pic_name = '%s_%s_%s_Histogram.png' % (hist.sat_sensor, var, ch)
                out_pic = os.path.join(hist.ofile, ym, ymd, pic_name)

                # 如果目录不存在，创建目录
                if not os.path.isdir(os.path.dirname(out_pic)):
                    os.makedirs(os.path.dirname(out_pic))
                print k
                print hist.data.get(var).shape
                data = hist.data.get(var)[k]
                # 过滤数据
                data = filter_fy3d_data(data, var)
                if len(data) != 0:
                    print(len(data))
                    print 'max min', data.max(), data.min()

                # 计算 Mode
                hists, bin_edges = np.histogram(data, bins=200)
                idx = np.argmax(hists)
                mode = (bin_edges[idx] + bin_edges[idx + 1]) / 2.0

                # 配置图片文字
                if var == 'DN':
                    name = 'Degradation'
                else:
                    name = var
                title = '%s %s %s Histogram' % (hist.sat_sensor, ch, name)
                xlabel = '%s' % name
                ylabel = 'Numbers'
                titledict = {'title': title, 'xlabel': xlabel,
                             'ylabel': ylabel}

                tl_list = [['{:15}: {:7.4f}'.format('Mode', mode),
                            ]]  # 左边注释

                draw_histogram(out_pic, data, titledict=titledict,
                               tl_list=tl_list)
                print out_pic

        date_c = date_c + relativedelta(days=1)


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
    omPath = os.path.dirname(ProjPath)
    dvPath = os.path.join(os.path.dirname(omPath), 'DV')
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

        run()

    else:  # 没有参数 输出帮助信息
        print help_info
