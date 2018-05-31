# encoding: utf-8

# 偏度因子测试
# 参考海通证券《CTA因子化投资与组合构建》p34-35


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime  # For datetime objects

# Import the backtrader platform
import backtrader as bt
from backtrader import Order
from backtrader import num2date

# import the strategy indicator, position management method and data engine

from CTA_factor_backtrade.CTA_base import CTA_setting_parse
from CTA_factor_backtrade.position_manage.Tgtvol_pos import Tgtvol_Position_manag
from CTA_factor_backtrade.CTA_indicators.Skewness_ind import Skewness_ind
from getdata_project.HdfUtility import HdfUtility
# import setting
from CTA_factor_backtrade.CTA_strategies.SkewnessFctlist_setting import SETTING
from getdata_project.dataUlt import EXT_Hdf_Path
# import other package
import pandas as pd
import numpy as np 
import re


class Skn_Strategy(bt.Strategy):
    params = (('shift_pos_days', 30),('skn_window_prd',15), ('trading_assetnum', 1),
              ('trading_ptflo_ratio', 0.3), ('vol_tgt_ratio', 0.05), ('pos_clct_days',15))
    od_params = None
    '''
       --------------------------------------------------------
       shift_pos_days : the holding days of portfolio, if overpass it, we will shift the position
       skn_window_prd: the waiting window days uesd to calculate the skewness indicator
       trading_assetnum: the number of asset we choose to trade
       trading_ptflo_ratio: the ratio of portfolio value used to trade
       vol_tgt_ratio : the target volitility ratio of portfolio position values
       pos_clct_days: the winfow period of position volitily calculation 
       params is the parameters that can be used to optimizate
       ---------------------------------------------------------
       od_params is the other ordinary parameters that the strategy need, and you can set it in the json file
    '''

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):        
        # record the position holding days 
        self.holding_days = 0
        # record the order name fail to complete
        self.no_trad_vt = []
        # whether the indicator produced in the strategy running
        # or fetch from the database
        self.indicator_islive = True
        self.indicator_name = 'Skewness'
        self.skn_ind = {}
        
        # record the mapping relation between index and datas name
        self.index_mapping_vt = {}
        self.vt_mapping_index = {}
        for i, data in  enumerate(self.datas):
            data._name = re.findall('^(\D*)', data._name)[0]
            self.index_mapping_vt[i] = data._name
            self.vt_mapping_index[data._name] = i
        # initiate the position management class
        pos_manage = Tgtvol_Position_manag(days = self.params.pos_clct_days, vtsymbol = self.index_mapping_vt.values())         
        pos_manage.set_RiskExp(self.params.trading_ptflo_ratio)
        pos_manage.set_pointvalue(self.od_params)
        pos_manage.set_potfolio_tgtvol(self.params.vol_tgt_ratio)
        self.pos_manage = pos_manage
        

        # 生成信号指标
        self.Indicator_Create()   
   
    def Indicator_Create(self):
        

        if self.indicator_islive:
        # 如果数据是实时生成，那么调用相关指标进行计算

            # 将同一品种的数据保存在datafeeds_vt里面
            # add the skewness indicator
            for i, vt in self.index_mapping_vt.items():        
                self.skn_ind[vt] = Skewness_ind(params =  {'window_prd':self.params.skn_window_prd},
                                              datafeed = [self.datas[i]], clockdata = self.datas[i])                
                self.skn_ind[vt].plotinfo.plot = False
            # 加个计时器：clock,然后利用计时器来提取指标
            self.clock = 0
        else:
            # 调用指标提取器提取数据
            Indicator_utl = HdfUtility()
            for vt in self.vt_mapping_index.keys():
                excode = self.od_params['excode'][self.od_params['vt'].index(vt)]
                indicator_temp = Indicator_utl.hdfRead(EXT_Hdf_Path, excode, vt, 
                                                      kind1='Indicator', 
                                                      kind2=self.indicator_name, 
                                                      kind3=None, 
                                                      startdate=self.od_params['startdate'], 
                                                      enddate=self.od_params['enddate'])           
                self.rollover_ind[vt] = indicator_temp['Indicator']
            # 加个计时器：clock,然后利用计时器来提取指标
            self.clock = self.params.rollover_window_prd - 1    
       
    def start(self):
        print('the strategy begin')

    def prenext(self):
        print('I am not ready, need %s days'%self.params.skn_window_prd)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'vtsymbole: %s BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.data._name, 
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm))


            else:  # Sell
                self.log('vtsymbole: %s SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (   order.data._name,
                             order.executed.price,
                             order.executed.value,
                             order.executed.comm))

            # self.excuted_bar_byorder[order.data._name] = len(self)
            # self.executed_bar 记录成功交易的order在哪个bar上面交易成功的，为之后退出做准备

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            print('----------------------------------------')
            print('order.status is %s'%order.status)
            self.log('Order Canceled/Margin/Rejected/expired, ordername %s:'%order.data._name) 
            
            # 将不成交的合约记录，用于之后平仓
            self.no_trad_vt.extend([order.data._name])
            

        # the order has been completed, set the self.order to none
        # self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # 记录时间
        date = self.datas[0].datetime.date(0)
        
        # 输出仓位信息
        for i, vt in self.index_mapping_vt.items():
            pos = self.positions[self.datas[i]].size
            print('vtname: %s position :%s'%(vt, pos))
        
        
        # 将数据添加到组合仓位管理中
        # 更新仓位管理的相关数据
        for i , vt in self.index_mapping_vt.items():
            self.pos_manage.update_data(vt, self.datas[i].close[0])
        # 判断是否为组合换仓日
        if self.holding_days == self.params.shift_pos_days:
            # 对之前的持仓进行平仓
            self.last_trading_vt = [vt for vt in self.pos_manage.new_trading_vt if vt not in self.no_trad_vt]
            for vt in self.last_trading_vt:
                self.close(data=self.datas[self.vt_mapping_index[vt]])
                print('%s close created , the price is %s '%(vt ,self.datas[self.vt_mapping_index[vt]].close[0]))
            
            # 寻找买入和卖出合约
            # 对指标进行排序，卖出前num个， 买入后num个
            temp_skn = pd.Series([self.skn_ind[vt][self.clock] for vt in self.index_mapping_vt.values()], \
                                 index=self.index_mapping_vt.values()).sort_values(ascending = False)
            buy_vt = list(temp_skn.tail(self.params.trading_assetnum).index)
            sell_vt = list(temp_skn.head(self.params.trading_assetnum).index)
            # 将买卖合约添加进仓位管理中
            self.pos_manage.updata_vtsymbol(buy_vt + sell_vt)
            # 计算每个合约买卖的数目
            tradingsizer_byvt = self.pos_manage.clct_sizer(cerebro.broker.getvalue())
            
            # 分别买卖相关合约
            for vt in buy_vt:
                i = self.vt_mapping_index[vt]
                sizer = tradingsizer_byvt[vt]                
                lprice = self.datas[i].close[0]+self.od_params[vt]["pricetick"]*(-10)
                self.buy(data = self.datas[i] ,exectype = Order.Limit, price = lprice,  size= sizer, \
                         valid = self.datas[i].datetime.date(0) + datetime.timedelta(self.od_params[vt]["ordervaliday"]))
                print('time :%s buy vt: %s, enter pending price : %s ,size : %s '%(date,vt,lprice,sizer))
            for vt in sell_vt:
                i = self.vt_mapping_index[vt]
                sizer = tradingsizer_byvt[vt]                
                lprice = self.datas[i].close[0] - self.od_params[vt]["pricetick"]*(-10)
                self.sell(data = self.datas[i] ,exectype = Order.Limit, price = lprice, size= sizer ,\
                                     valid = self.datas[i].datetime.date(0) + datetime.timedelta(self.od_params[vt]["ordervaliday"]))
                print('time :%s sell vt: %s, enter pending price : %s, size: %s'%(date,vt, lprice, sizer))
            self.holding_days = 1
            self.no_trad_vt = []
        if not self.indicator_islive:
            self.clock += 1
        self.holding_days += 1 
            
if __name__ == '__main__':  
    # Create a cerebro entity  
    cerebro = bt.Cerebro()  
    # Add a strategy  
    cerebro.addstrategy(Skn_Strategy)  
    # parameter parse
    parse_tool = CTA_setting_parse(SETTING)
    parse_tool.add2platform(platform=cerebro)
    # loading data
    parse_tool.loading_data(platform=cerebro)
    # add some parmas from setting
    parse_tool.add2strat(platform=cerebro)
    # Print out the starting conditions  
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())  
    # Run over everything  
    cerebro.run()  
    # Print out the final result  
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    
    if False:
        # save the indicator
        print('save the indicator')
        Indicator_utl = HdfUtility()
        stat = cerebro.runstrats[0][0]
        indicator_byvt = stat.skn_ind
        params = cerebro.runstrats[0][0].od_params
        for indicator, vt in indicator_byvt.items():
            indicator_data = indicator.array
            tradingday = cerebro.datasbyname(vt+'0000').datetime.array
            df = pd.DataFrame({'Indicator':indicatoe_data, 'Date':tradingday})
            date_parse = lambda x:num2date(x)
            df['Date'] = df['Date'].apply(date_parse)
            excode = params['excode'][params['vt'].index(vt)]        
            Indicator_utl.hdfWrite(EXT_Hdf_Path, excode, vt, df.set_index('Date'), kind1='Indicator', kind2=stat.indicator_name, 
                                  kind3={'window_prd':stat.params.rollover_window_prd})    
    cerebro.plot()  