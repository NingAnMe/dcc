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
from matplotlib.ticker import MultipleLocator

from PB import pb_time, pb_io
from DV import dv_plt
from DV.dv_pub_legacy import plt, mdates, set_tick_font, FONT0

from DM.SNO.dm_sno_cross_calc_map import RED, BLUE, EDGE_GRAY, ORG_NAME, mpatches


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


def setXLocator(ax, xlim_min, xlim_max):
    day_range = (xlim_max - xlim_min).days
#     if day_range <= 2:
#         days = mdates.HourLocator(interval=4)
#         ax.xaxis.set_major_locator(days)
#         ax.xaxis.set_major_formatter(mdates.DateFormatter('%H'))
    if day_range <= 60:
        days = mdates.DayLocator(interval=(day_range / 6))
        ax.xaxis.set_major_locator(days)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    else:
        month_range = day_range / 30
        if month_range <= 12.:
            months = mdates.MonthLocator()  # every month
            ax.xaxis.set_major_locator(months)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        elif month_range <= 24.:
            months = mdates.MonthLocator(interval=2)
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        elif month_range <= 48.:
            months = mdates.MonthLocator(interval=4)
            ax.xaxis.set_major_locator(months)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        else:
            years = mdates.YearLocator()
            ax.xaxis.set_major_locator(years)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        if month_range <= 48:
            add_year_xaxis(ax, xlim_min, xlim_max)


def add_year_xaxis(ax, xlim_min, xlim_max):
    """
    add year xaxis
    """
    if xlim_min.year == xlim_max.year:
        ax.set_xlabel(xlim_min.year, fontsize=11, fontproperties=FONT0)
        return
    newax = ax.twiny()
    newax.set_frame_on(True)
    newax.grid(False)
    newax.patch.set_visible(False)
    newax.xaxis.set_ticks_position('bottom')
    newax.xaxis.set_label_position('bottom')
    newax.set_xlim(xlim_min, xlim_max)
    newax.xaxis.set_major_locator(mdates.YearLocator())
    newax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    newax.spines['bottom'].set_position(('outward', 20))
    newax.spines['bottom'].set_linewidth(0.6)

    newax.tick_params(which='both', direction='in')
    set_tick_font(newax)
    newax.xaxis.set_tick_params(length=5)


def plot_bias(date_D, bias_D, picPath, title, date_s, date_e, each, date_type,
              ylim_min, ylim_max):
    """
    画偏差时序折线图
    """
    plt.style.use(os.path.join(dvPath, 'dv_pub_legacy.mplstyle'))
    fig = plt.figure(figsize=(6, 4))
#     plt.subplots_adjust(left=0.13, right=0.95, bottom=0.11, top=0.97)

    plt.plot(date_D, bias_D, 'x', ms=6,
             markerfacecolor=None, markeredgecolor=BLUE, alpha=0.8,
             mew=0.3, label='Daily')

    plt.grid(True)
    plt.ylabel('%s %s' % (each, date_type), fontsize=11, fontproperties=FONT0)

    xlim_min = pb_time.ymd2date('%04d%02d01' % (date_s.year, date_s.month))
    xlim_max = date_e

    plt.plot([xlim_min, xlim_max], [0, 0], 'k')  # 在 y = 0 绘制一条黑色直线

    plt.xlim(xlim_min, xlim_max)
    plt.ylim(ylim_min, ylim_max)
    ax = plt.gca()
    # format the ticks
    interval = (ylim_max - ylim_min) // 8
    minibar = interval / 2.
    setXLocator(ax, xlim_min, xlim_max)
    set_tick_font(ax)
    ax.yaxis.set_major_locator(MultipleLocator(interval))
    ax.yaxis.set_minor_locator(MultipleLocator(minibar))

    # title
    plt.title(title, fontsize=12, fontproperties=FONT0)

    plt.tight_layout()
    #--------------------
    fig.subplots_adjust(bottom=0.2)

    circle1 = mpatches.Circle((74, 15), 6, color=BLUE, ec=EDGE_GRAY, lw=0)
    # circle2 = mpatches.Circle((164, 15), 6, color=RED, ec=EDGE_GRAY, lw=0)
    fig.patches.extend([circle1])

    fig.text(0.15, 0.02, 'Daily', color=BLUE, fontproperties=FONT0)

    ymd_s, ymd_e = date_s.strftime('%Y%m%d'), date_e.strftime('%Y%m%d')
    if ymd_s != ymd_e:
        fig.text(0.50, 0.02, '%s-%s' % (ymd_s, ymd_e), fontproperties=FONT0)
    else:
        fig.text(0.50, 0.02, '%s' % ymd_s, fontproperties=FONT0)

    fig.text(0.8, 0.02, ORG_NAME, fontproperties=FONT0)
    #---------------
    pb_io.make_sure_path_exists(os.path.dirname(picPath))
    plt.savefig(picPath)
    fig.clear()
    plt.close()


def run(rollday):
    try:
        sat1, sat2 = satFlag.split('_')
    except ValueError:
        sat1 = satFlag
        sat2 = None

    rollday = rollday
    ipath = inCfg['plt'][satFlag]['ipath']
    opath = inCfg['plt'][satFlag]['opath']
    lanch_date = inCfg['plt'][satFlag]['lanch_date']
    var = inCfg['plt'][satFlag]['var']
    band = inCfg['plt'][satFlag]['band']
    ref_range = inCfg['plt'][satFlag]['REF_range']
    dn_range = inCfg['plt'][satFlag]['DN_range']

    date_s, date_e = pb_time.arg_str2date(str_time)

    # 拼接需要读取的文件
    if not isinstance(var, list):
        var = [var]
    print(var)
    for each in var:
        for k, ch in enumerate(band):
            print each, ch
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
                MedATT = (ary['Med'] / FirstMed) * 100
                ModATT = (ary['Mod'] / FirstMod) * 100
                print 'max: avg med mod', AvgATT.max(), MedATT.max(), ModATT.max()
                print 'min: avg med mod', AvgATT.min(), MedATT.min(), ModATT.min()
            elif 'REF' in each:
                # 如果是绘制相对偏差，已经是计算好的相对百分比，不需要除100
                # sat2 存在，代表是绘制两颗卫星的相对偏差
                if sat2:
                    AvgATT = ary['Avg']
                    MedATT = ary['Med']
                    ModATT = ary['Mod']
                    print 'max: avg med mod', AvgATT.max(), MedATT.max(), ModATT.max()
                    print 'min: avg med mod', AvgATT.min(), MedATT.min(), ModATT.min()
                # 如果是绘制自身 REF 变化，需要除 100，还原 REF 真实值
                else:
                    AvgATT = ary['Avg'] / 100.
                    MedATT = ary['Med'] / 100.
                    ModATT = ary['Mod'] / 100.
                    print 'max: avg med mod', AvgATT.max(), MedATT.max(), ModATT.max()
                    print 'min: avg med mod', AvgATT.min(), MedATT.min(), ModATT.min()
            datas = {
                'AvgATT': AvgATT,
                'MedATT': MedATT,
                'ModATT': ModATT,
            }

            ######## 三、绘图   ###################
            # 绘图 y 轴的数据范围
            if each == 'REF':
                y_range = ref_range
            else:
                y_range = dn_range

            min_yaxis = int(y_range[k].split('_')[0])
            max_yaxis = int(y_range[k].split('_')[1])

            data_types = ['Avg', 'Med', 'Mod']
            for data_type in data_types:
                ymd_e = date_e.strftime('%Y%m%d')
                outPng = os.path.join(
                    opath, rollday, ymd_e,
                    'DCC_%s_%s_%s_Rolldays_%s_Timeseries_%s.png' % (
                        satFlag, each, ch, rollday, data_type))

                date_D = []
                for i in xrange(len(ary['ymd'])):
                    dtime = datetime.strptime(ary['ymd'][i], '%Y%m%d')
                    date_D.append(dtime)
                if sat2:
                    title = '%s Minus %s %s TimeSeries' % (sat1, sat2, ch)
                else:
                    title = '%s %s TimeSeries' % (sat1, ch)
                print title
                data_name = '%sATT' % data_type
                data_D = datas.get(data_name)
                plot_bias(date_D, data_D, outPng, title, date_s, date_e,
                          each, data_type, min_yaxis, max_yaxis)
                print(outPng)


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

        roll_days = inCfg['plt'][satFlag]['rollday']
        if isinstance(roll_days, str):
            roll_days = [roll_days]
        for num in roll_days:
            run(num)

    else:  # 没有参数 输出帮助信息
        print help_info
