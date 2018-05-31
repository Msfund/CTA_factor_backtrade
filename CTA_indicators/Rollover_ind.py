# encoding: utf-8

# 展期因子策略
# 参考海通证券《CTA因子化投资与组合构建》p16
# 这里的合约的组合为近月合约和远月合约
import backtrader as bt
from CTA_factor_backtrade.Indicator_Base import Indicator_Fetch
from backtrader import num2date
import numpy as np
from datetime import datetime
import re
class Rollover_ind(bt.Indicator):
    lines = ('Rollover_ind',)
    def __init__(self, params,datafeed,clockdata):
        # datafeed 是一个品种的所有合约数据, window_prd是因子计算需要是窗口期
        # clock_data，不参与计算,仅用于时间推进
        self.datas = datafeed
        self._clock = clockdata
        self.indicator_params = params
        self.params.window_prd =params['window_prd']
        self.tradingday = self._clock.datetime.array
        self.count = self.params.window_prd -1
        # 记录还没有上市的合约
        self.un_active_data =[]
        # 记录已经退市的合约
        self.delist_data = []
        self.addminperiod(self.params.window_prd)
        # 如果datafeed应该只含有原始数据名字类似于IF1701.CFE
        # 记录其他数据，其他数据不参与计算
        self.unvalidata = [i for i, data in enumerate(self.datas) if not re.match(r'^\D+\d{3,4}.\D+',data._name)]

        
    def Clct_ind(self):
        ind_data = (np.log(self.nearclose) - np.log(self.longclose))/(self.longdays - self.neardays)
        return ind_data
    def lookfor_contract(self):
        # 寻找远月合约和近月合约
        # 当然展期因子也可以由其他合约构建，这里使用者可以继承
        
        # 调整未上市合约的下标_idx
        for i in self.un_active_data:
            lines = self.datas[i].lines
            for l in lines:
                l.idx += -1
        
        self.un_active_data = []
        
        # 找出目前尚未交易的合约
        trading_date = self.tradingday[self.count]
        # 可能还没有上市， 可能已经退市
        for i,data in enumerate(self.datas):
            if i in self.unvalidata:
                continue
            try:
                date = self.datas[i].datetime[0]
                if date > trading_date:
                    self.un_active_data.append(i)
            except:
                # 已经退市
                if i not in self.delist_data:
                    self.delist_data.append(i)

        self.count += 1    
        # 找出远月合约和近月合约  
        long_con = 'None'
        near_con = 'None'
        longest = float('-inf')
        nearest = float('inf')
        
        for i,data in enumerate(self.datas):
            if i in self.unvalidata:
                continue
            if i in self.un_active_data + self.delist_data:
                continue
            delistdate = data.delistdate[0]                
            longest = max(delistdate, longest)
            nearest = min(delistdate, nearest)
        for i,data in enumerate(self.datas):
            if i in self.unvalidata:
                continue
            if i in self.un_active_data + self.delist_data:
                continue
            if data.delistdate[0] == longest:
                long_con = i
            if data.delistdate[0] == nearest:
                near_con = i
        # the type of delistdate in the line is float        
        long_delistdate = datetime.fromordinal(int(self.datas[long_con].delistdate[0])) 
        near_delistdate = datetime.fromordinal(int(self.datas[near_con].delistdate[0]))
        
        long_closedata = self.datas[long_con].close[0]        
        long_days = long_delistdate.date() - self.datas[long_con].datetime.date(0)    
        near_closedata = self.datas[near_con].close[0]
        near_days = near_delistdate.date() - self.datas[near_con].datetime.date(0)
        
        return(long_closedata, long_days.days, near_closedata, near_days.days)
    
    def next(self):
        self.longclose, self.longdays,self.nearclose,self.neardays = self.lookfor_contract()
        self.Rollover_ind[0] = self.Clct_ind()    
        
        try:
            print('date: %s the rollover indictor of %s is %s'%(num2date(self.tradingday[self.count]), 
                                                                re.findall(r'^(\D*)',self._clock._name[0:2])[0],self.lines[0][0]))                                                                
        except:
            print self.count
        
