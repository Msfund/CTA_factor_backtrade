# encoding:utf-8

# 偏度因子
# 参考海通证券《CTA因子化投资与组合构建》p34-35


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

# import the packages we need
import numpy as np 


# create first strategy's indicator : skewness
class Skewness_ind(bt.Indicator):
    # create the indicator line

    lines = ('skn_ind',)
    def __init__(self, params, datafeed, clockdata):
        # 平台默认第一个数据集为计时器，由于不同的品种可能上市时间不同
        # 这里取最后一个数据集作为计时器
        self.datas = datafeed        
        self._clock = clockdata         
        self.params.window_prd = params['window_prd']
        self.addminperiod(self.params.window_prd)
    def clc_skn_ind(self, dataseries):
        mean = np.mean(dataseries)
        var = np.var(dataseries)
        self.skewness = np.mean((np.array(dataseries - mean)/var)*3)
        return self.skewness
    def next(self):
        closedata = self.datas[0].close.get(size=self.params.window_prd)
        adj_fct = self.datas[0].adjfactor.get(size = self.params.window_prd)
        adj_closedata = np.array(closedata)*np.array(adj_fct)
        self.skn_ind[0] = self.clc_skn_ind(adj_closedata)
        print ('time : %s'%self.datas[0].datetime.date(0))
        print('skewness indicator of %s is %s'%(self.datas[0]._name,self.skn_ind[0]))