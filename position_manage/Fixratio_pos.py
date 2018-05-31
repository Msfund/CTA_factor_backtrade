# encoding utf-8

# 固定比率法进行仓位管理

from position_base import Position_Manag

import numpy as np

class Fix_Position_manag(Position_Manag):
    
    def __init__(self, days, vtsymbol):
        # days : the min waiting period to calculate the variety of vt
        self.sizer_by_vt = {vt: None  for vt in vtsymbol}
        self.risk_exps =  {vt: None  for vt in vtsymbol}
        
        self.window_prd = days
        super(Fix_Position_manag, self).__init__(vtsymbol)
    def clct_sizer(self, potflio_value):
        for vt in self.new_trading_vt:
            length = len(self.close_by_vt[vt])
            vol = np.std(self.close_by_vt[vt][length - self.window_prd : length])
            self.sizer_by_vt[vt] = (potflio_value * self.risk_exps * self.set_RiskEpx_byvt[vt])/(self.point_value[vt]*vol)
    def set_RiskEpx_byvt(self, risk_ratio):
        self.risk_exps[vt] = risk_ratio
        
        
        
        
            
        
        
