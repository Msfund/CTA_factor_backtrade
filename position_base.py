# encoding:utf-8
# this file used to manage the position of portfolio



class Position_Manag(object):
    def __init__(self, vtsymbol):
        self.vt = vtsymbol
        # record last trading vtsymbol
        self.last_trading_vt = []
        self.new_trading_vt = []
        # record everyday variety of vtsymbol
        # self.var_by_vt = {}
        # record everyday price and yield of vtsymbol
        self.close_by_vt = {vt:[] for vt in vtsymbol}
        self.yield_by_vt ={vt:[] for vt in vtsymbol}
    
    
    def update_data(self, vt, close):
        # update the close and yield data everyday
        self.close_by_vt[vt].append(close)
        if len(self.close_by_vt[vt]) >1:
            temp_yield = (self.close_by_vt[vt][-2] - self.close_by_vt[vt][-1])/self.close_by_vt[vt][-2] 
            self.yield_by_vt[vt].append(temp_yield)
    
    def updata_vtsymbol(self, trading_vt):
        # update the trading vtsymbol in the shift of position
        self.last_trading_vt = self.new_trading_vt
        self.new_trading_vt = trading_vt
    
    def set_RiskExp(self, ratio):
        # set the risk exposure
        self.risk_exps = ratio
    def set_pointvalue(self, params):
        # set every vtsymbol's value of each point
        self.point_value = {vt : params[vt]['point_value'] for vt in params['vt']}
        
        
        
    


    