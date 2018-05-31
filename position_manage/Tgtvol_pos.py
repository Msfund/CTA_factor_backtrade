# encoding:utf-8
# 目标波动率仓位管理法
# 根据海通证券的《CTA因子化投资与组合的构建》P49中的持仓管理进行编写
from CTA_factor_backtrade.position_base import Position_Manag


import numpy as np
import pandas as pd

class Tgtvol_Position_manag(Position_Manag):
    def __init__(self, days, vtsymbol):
        # days : the min waiting period to calculate the variety of vt
        self.sizer_by_vt = {vt: None  for vt in vtsymbol}
        
        self.window_prd = days
        super(Tgtvol_Position_manag, self).__init__(vtsymbol)
    
    def set_potfolio_tgtvol(self, target_ratio):
        self.tgtvol_ratio = target_ratio
    
    def clct_sizer(self, potflio_value):
        # potflio_value is the values of current portfolio 
        # calculate the relation coefficient of portfolio
        asset_num = len(self.new_trading_vt)
        
        trade_yield_byvt = {vt:self.yield_by_vt[vt] for vt in self.new_trading_vt}
        data = pd.DataFrame(trade_yield_byvt)
        data = data.tail(self.window_prd)
        corr = data.corr()
        p_corr = (corr.sum().sum() - asset_num)/((asset_num - 1)*asset_num)
        for vt in self.new_trading_vt:
            length = len(self.yield_by_vt[vt])
            vol_vt = np.std(self.yield_by_vt[vt][length-self.window_prd : length])
            weight = self.tgtvol_ratio*(np.sqrt(asset_num/(1+(asset_num-1)*p_corr)))/vol_vt
            sizer = self.risk_exps*potflio_value*weight/(self.close_by_vt[vt][-1]*self.point_value[vt])
            self.sizer_by_vt[vt]  = np.floor(sizer)
        return self.sizer_by_vt
            
            
            
            
        
        
