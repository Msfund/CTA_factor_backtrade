# encoding: utf-8

# 基差动量因子
# 参考海通证券《CTA因子化投资与组合构建》p18
import backtrader as bt
from getdata_project.HisDayData import HisDayData

from backtrader import num2date
import numpy as np
from datetime import datetime

class BasisMmt_ind(bt.Indicator):
    lines = ('Basis_Mmt_ind',)
    def __init__(self,params, datafeed, clockdata):
        # 我们需要额外的连续近月合约和连续远月合约的数据
        # clockdata 不参与计算,仅用于时间推进
        self.datas = datafeed
        self._clock = clockdata
        self.params.window_prd = params['window_prd']
        self.addminperiod(self.params.window_prd)
        for i, data in enumerate(self.datas):
            if 'near_month' in data._name:
                self.near_index = i 
            if 'long_month' in data._name:
                self.long_index = i
                
    def Clct_ind(self):
        
        near_ret = (self.nearadjclose[1:] - self.nearadjclose[:-1])/(self.nearadjclose[:-1])
        near_cum = np.cumprod(near_ret+1)[-1] - 1
        long_ret = (self.longadjclose[1:] - self.longadjclose[:-1])/(self.longadjclose[:-1])
        long_cum = np.cumprod(long_ret+1)[-1] -1
        ind_data = near_cum - long_cum
        return ind_data
    
    def next(self):
        self.nearclose = np.array(self.datas[self.near_index].close.get(size=self.params.window_prd))
        self.nearadjclose =  np.array(self.datas[self.near_index].adjfactor.get(size=self.params.window_prd)) * self.nearclose
        self.longclose = np.array(self.datas[self.near_index].adjfactor.get(size=self.params.window_prd))
        self.longadjclose = np.array(self.datas[self.near_index].adjfactor.get(size=self.params.window_prd)) * self.longclose
        self.Basis_Mmt_ind[0] = self.Clct_ind()
        print('date: %s the Basis_Mmt indictor is %s'%(self._clock.datetime.date(0), self.Basis_Mmt_ind[0]))

        
    
    @ classmethod
    def add_exdata(cls, platform, parse_tool, setting):
        NEAR_MONTH = 'near_month'
        LONG_MONTH = 'long_month'
        data_ult = HisDayData()
        data_setting = setting['data_setting']
        for i, vt in enumerate(data_setting['vt']):
            near_data = data_ult.get_nearlong_data(vt, data_setting['excode'][i], data_setting['startdate'], 
                                                   data_setting['enddate'], type=NEAR_MONTH)
            parse_tool.add_extrdata(platform, extra_data=near_data, vt=vt, extra_name='01'+NEAR_MONTH)
            long_data =  data_ult.get_nearlong_data(vt, data_setting['excode'][i], data_setting['startdate'], 
                                                    data_setting['enddate'], type=LONG_MONTH)
            parse_tool.add_extrdata(platform, extra_data=long_data, vt=vt, extra_name='12'+LONG_MONTH)           