#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-

from __future__ import (absolute_import, division, print_function,
                       unicode_literals)

from . import Indicator
import numpy as np

class SpreadWithSignals(Indicator):
    '''
    计算两个数据之间的价差并标注买卖信号点
    
    参数:
      - data2: 第二个数据源(用于计算价差)
      - buy_signal: 买入信号数组
      - sell_signal: 卖出信号数组
    '''
    
    lines = ('spread',)  # 定义一个spread线
    alias = ('Spread',)
    plotinfo = dict(
        plot=True,
        subplot=True,  # 在单独的子图中显示
        plotname='Spread',
        plotlabels=True,
        plotlinelabels=True,
        plotymargin=0.05,
    )
    
    plotlines = dict(
        spread=dict(
            _name='Spread',
            color='blue',
            ls='-',
            _plotskip=False
        )
    )
    
    def __init__(self):
        super(SpreadWithSignals, self).__init__()
        
        # 计算价差
        self.lines.spread = self.data - self.data1
        
        # 添加买卖信号的绘制
        self.plotinfo.plotmarkers = [
            dict(
                name='buy',
                marker='^',  # 上三角
                color='g',   # 绿色
                markersize=8,
                fillstyle='full',
                text='buy %(price).2f',  # 标签格式
                textsize=8,
                textcolor='g',
                ls='',  # 无连线
                _plotskip=False
            ),
            dict(
                name='sell', 
                marker='v',  # 下三角
                color='r',   # 红色
                markersize=8,
                fillstyle='full',
                text='sell %(price).2f',  # 标签格式
                textsize=8,
                textcolor='r',
                ls='',  # 无连线
                _plotskip=False
            )
        ]

