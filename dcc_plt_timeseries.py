# coding:utf-8
"""
Created on 2017年9月21日

@author: wangpeng anning
"""
import os
import sys
from datetime import datetime
from configobj import ConfigObj
from dateutil.relativedelta import relativedelta

import numpy as np
from matplotlib.ticker import MultipleLocator

from PB import pb_time, pb_io
from DV.dv_pub_legacy import plt, mdates, set_tick_font, FONT0

from DM.SNO.dm_sno_cross_calc_map import RED, BLUE, EDGE_GRAY, ORG_NAME, mpatches


def dcc_data_read(in_file):
    names = ('date', 'avg', 'med', 'mod',
             'dcc_files', 'dcc_point', 'dcc_precent', 'dcc_dim')
    formats = ('object', 'f4', 'f4', 'f4',
               'i4', 'i4', 'i4', 'i4')

    # 加载txt文
    arys = np.loadtxt(in_file,
                      converters={0: lambda x: datetime.strptime(x, "%Y%m%d")},
                      dtype={'names': names,
                             'formats': formats},
                      skiprows=1, ndmin=1)

    return arys


def setXLocator(ax, xlim_min, xlim_max):
    day_range = (xlim_max - xlim_min).days

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
            ax.xaxis.set_major_locator(months)
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


def plot_bias(date_D, bias_D, date_M, bias_M, picPath, title,
              date_s, date_e, each, date_type, ylim_min, ylim_max):
    """
    画偏差时序折线图
    """
    plt.style.use(os.path.join(dvPath, 'dv_pub_legacy.mplstyle'))
    fig = plt.figure(figsize=(6, 4))
#     plt.subplots_adjust(left=0.13, right=0.95, bottom=0.11, top=0.97)

    plt.plot(date_D, bias_D, 'x', ms=6,
             markerfacecolor=None, markeredgecolor=BLUE, alpha=0.8,
             mew=0.3, label='Daily')
    plt.plot(date_M, bias_M, 'o-', ms=5, lw=0.6, c=RED,
             mew=0, label='Monthly')

    plt.grid(True)
    plt.ylabel('%s %s' % (each, date_type), fontsize=11, fontproperties=FONT0)

    xlim_min = pb_time.ymd2date('%04d%02d01' % (date_s.year, date_s.month))
    xlim_max = date_e

    plt.plot([xlim_min, xlim_max], [0, 0], 'k')  # 在 y = 0 绘制一条黑色直线

    plt.xlim(xlim_min, xlim_max)
    plt.ylim(ylim_min, ylim_max)

    ax = plt.gca()
    # format the ticks
    interval = (ylim_max - ylim_min) / 8  # 8 个间隔
    minibar = interval / 2.
    setXLocator(ax, xlim_min, xlim_max)
    set_tick_font(ax)

    # 如果范围为浮点数，需要进行一次格式化，否则图像不会显示最后一个刻度
    if isinstance(interval, float):
        interval = float('%.5f' % interval)
        minibar = float('%.5f' % minibar)

    ax.yaxis.set_major_locator(MultipleLocator(interval))
    ax.yaxis.set_minor_locator(MultipleLocator(minibar))

    # title
    plt.title(title, fontsize=12, fontproperties=FONT0)

    plt.tight_layout()
    # --------------------
    fig.subplots_adjust(bottom=0.2)

    circle1 = mpatches.Circle((74, 15), 6, color=BLUE, ec=EDGE_GRAY, lw=0)
    circle2 = mpatches.Circle((164, 15), 6, color=RED, ec=EDGE_GRAY, lw=0)
    fig.patches.extend([circle1, circle2])

    fig.text(0.15, 0.02, 'Daily', color=BLUE, fontproperties=FONT0)
    fig.text(0.3, 0.02, 'Monthly', color=RED, fontproperties=FONT0)

    ymd_s, ymd_e = date_s.strftime('%Y%m%d'), date_e.strftime('%Y%m%d')
    if ymd_s != ymd_e:
        fig.text(0.50, 0.02, '%s-%s' % (ymd_s, ymd_e), fontproperties=FONT0)
    else:
        fig.text(0.50, 0.02, '%s' % ymd_s, fontproperties=FONT0)

    fig.text(0.8, 0.02, ORG_NAME, fontproperties=FONT0)
    # ---------------
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
            # 日数据
            filename_day = 'DCC_%s_%s_%s_Rolldays_%s_ALL_Daily.txt' % (
                satFlag, each, ch, rollday)
            dcc_file_day = os.path.join(ipath, rollday, filename_day)
            # 月数据
            filename_month = 'DCC_%s_%s_%s_Rolldays_%s_ALL_Monthly.txt' % (
                satFlag, each, ch, rollday)
            dcc_file_month = os.path.join(ipath, rollday, filename_month)
            ######### 一、读取dcc提取后的标准文件 ##############
            ary_day = dcc_data_read(dcc_file_day)
            ary_month = dcc_data_read(dcc_file_month)

            ######### 二、计算衰减(日数据)  ##############
            date_day = ary_day['date']

            idx = np.where(ary_day['date'] == datetime.strptime(lanch_date,
                                                                '%Y%m%d'))
            first_avg = ary_day['avg'][idx]
            first_med = ary_day['med'][idx]
            first_mod = ary_day['mod'][idx]
            # 如果是 DN，需要计算和发星第一天的相对百分比
            if 'DN' in each:
                avg_day = ary_day['avg'] / first_avg
                med_day = ary_day['med'] / first_med
                mod_day = ary_day['mod'] / first_mod
            elif 'REF' in each:
                # 如果是绘制相对偏差，已经是计算好的相对百分比，不需要除100
                # sat2 存在，代表是绘制两颗卫星的相对偏差
                if sat2:
                    avg_day = ary_day['avg']
                    med_day = ary_day['med']
                    mod_day = ary_day['mod']
                # 如果是绘制自身 REF 变化，需要除 100，还原 REF 真实值
                else:
                    avg_day = ary_day['avg'] / 100.
                    med_day = ary_day['med'] / 100.
                    mod_day = ary_day['mod'] / 100.
            else:
                print 'error: %s is not supported.' % each
                return
            print 'max: avg med mod', \
                avg_day.max(), med_day.max(), mod_day.max()
            print 'min: avg med mod', \
                avg_day.min(), med_day.min(), mod_day.min()
            datas_day = {
                'avg_day': avg_day,
                'med_day': med_day,
                'mod_day': mod_day,
            }

            ######### 三、格式化数据(月数据)  ##############
            date_month = ary_month['date'] + relativedelta(days=14)
            # 如果是 DN，需要计算和发星第一天的相对百分比
            if 'DN' in each:
                avg_month = ary_month['avg'] / first_avg
                med_month = ary_month['med'] / first_med
                mod_month = ary_month['mod'] / first_mod

            elif 'REF' in each:
                # 如果是绘制相对偏差，已经是计算好的相对百分比，不需要除100
                # sat2 存在，代表是绘制两颗卫星的相对偏差
                if sat2:
                    avg_month = ary_month['avg']
                    med_month = ary_month['med']
                    mod_month = ary_month['mod']
                # 如果是绘制自身 REF 变化，需要除 100，还原 REF 真实值
                else:
                    avg_month = ary_month['avg'] / 100.
                    med_month = ary_month['med'] / 100.
                    mod_month = ary_month['mod'] / 100.
            else:
                print 'error: %s is not supported.' % each
                return
            print 'max: avg med mod', avg_month.max(), \
                med_month.max(), mod_month.max()
            print 'min: avg med mod', avg_month.min(), \
                med_month.min(), mod_month.min()
            datas_month = {
                'avg_month': avg_month,
                'med_month': med_month,
                'mod_month': mod_month,
            }

            ######## 四、绘图   ###################
            # 绘图 y 轴的数据范围
            if each == 'REF':
                y_range = ref_range
            else:
                y_range = dn_range

            min_yaxis = float(y_range[k].split('_')[0])
            max_yaxis = float(y_range[k].split('_')[1])

            data_types = ['avg', 'med', 'mod']
            for data_type in data_types:
                ymd_e = date_e.strftime('%Y%m%d')
                outPng = os.path.join(
                    opath, rollday, ymd_e,
                    'DCC_%s_%s_%s_Rolldays_%s_Timeseries_%s.png' % (
                        satFlag, each, ch, rollday, data_type))

                date_D = date_day
                date_M = date_month

                if sat2:
                    title = '%s Minus %s %s TimeSeries' % (sat1, sat2, ch)
                else:
                    title = '%s %s TimeSeries' % (sat1, ch)

                data_D_name = '%s_day' % data_type
                data_D = datas_day.get(data_D_name)
                data_M_name = '%s_month' % data_type
                data_M = datas_month.get(data_M_name)

                name = ''
                if each == 'DN':
                    name = 'Degradation'  # DN 的图像上面 ylabel 名字
                elif each == 'REF':
                    if sat2:
                        name = 'Bias'  # Bias 的图像上面 ylabel 名字
                    else:
                        name = 'REF'  # REF 的图像上面 ylabel 名字

                plot_bias(date_D, data_D, date_M, data_M, outPng, title,
                          date_s, date_e, name, data_type, min_yaxis, max_yaxis)
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
