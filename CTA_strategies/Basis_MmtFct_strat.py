# encoding: utf-8

# 基差动量因子多品种测试
# 参考海通证券《CTA因子化投资与组合构建》p18


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
from backtrader import Order

# import the strategy indicator and position management method
from CTA_factor_backtrade.CTA_base import CTA_setting_parse
from CTA_factor_backtrade.position_manage.Tgtvol_pos import Tgtvol_Position_manag
from CTA_factor_backtrade.CTA_indicators.BasisMmt_ind import BasisMmt_ind
from CTA_factor_backtrade.CTA_strategies.SkewnessFctlist_setting import SETTING

# import the data engine
from getdata_project.HdfUtility import HdfUtility
from getdata_project.HisDayData import HisDayData
# import other package
import pandas as pd
import numpy as np 
import re


class Basis_MmtStrategy(bt.Strategy):
    params = (('shift_pos_days', 30),('BasisMmt_window_prd',90), ('asset_ratio', 0.2),
              ('trading_ptflo_ratio', 0.3), ('vol_tgt_ratio', 0.05))
    od_params = None
    '''shift_pos_days : the holding days of portfolio, if overpass it, we will shift the position
       BasisMmt_window_prd: the waiting window days uesd to calculate the skewness indicator
       asset_ratio: the number of asset we choose to trade
       trading_ptflo_ratio: the ratio of portfolio value used to trade
       vol_tgt_ratio : the target volitility ratio of portfolio position values
       params is the parameters that can be used to optimizate
       od_params is the other ordinary parameters that the strategy need, and you can set it in the json file
    '''

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):        
        
        # 设置因子是否实时生成或者直接从hdf5中调用
        self.indicator_islive = True
        self.BasisMmt_ind = {}
        self.indicator_name = 'BasisMmt'
        # 记录组合持仓时间
        self.holding_days = 0
        # 记录未成交的订单
        self.no_trad_vt = []
        # 设置组合波动率
        self.pos_clct_days = 15
       
        # 每一个品种具有多个合约，为了计算因子我们需要都添加到因子当中,所以需要保存映射关系
        # 但是交易仅需要主力合约，所以也需要保存主力合约名称和指标之间的关系,在数据加载过程中，将
        # 主力合约名称保存在数据中是vt+0000, 例如:IF0000
        self.index_mapping_symbol = {i: data._name for i, data in enumerate(self.datas) if data._name[-4:]!='0000'}
        self.symbol_mapping_index = {data._name: i for i, data in enumerate(self.datas) if data._name[-4:]!='0000'}
        self.tradevt_campping_index = {re.findall('^(\D*)',data._name)[0]: i for i, data in enumerate(self.datas) if data._name[-4:]=='0000'}
        self.index_campping_tradevt = {i: re.findall('^(\D*)',data._name)[0] for i, data in enumerate(self.datas) if data._name[-4:]=='0000'}
            
        # 初始化仓位管理
        pos_manage = Tgtvol_Position_manag(days = self.pos_clct_days, vtsymbol = self.tradevt_campping_index.keys())         
        pos_manage.set_RiskExp(self.params.trading_ptflo_ratio)
        pos_manage.set_pointvalue(self.od_params)
        pos_manage.set_potfolio_tgtvol(self.params.vol_tgt_ratio)
        self.pos_manage = pos_manage
        
        # 生成信号指标
        self.Indicator_Create()
       
    def Indicator_Create(self):
        # 初始化指标数据生成器
        # Indicator_utl = CTA_Ind_data
        if self.indicator_islive:
        # 如果数据是实时生成，那么调用相关指标进行计算

            # 将同一品种的数据保存在datafeeds_vt里面
            datafeeds_vt = {vt: [] for vt in self.tradevt_campping_index.keys()}
            for i, vt in self.index_mapping_symbol.items():
                vt = re.findall('^(\D*)',vt)[0]
                datafeeds_vt[vt] = datafeeds_vt[vt] + [self.datas[i]]
            
            # 将非交易数据剔除
            self.datas = [self.datas[i] for i in self.tradevt_campping_index.values()]
            # 重新记录映射关系
            self.tradevt_campping_index = {vt: i for i, vt in enumerate(self.tradevt_campping_index.keys())}
            self.index_campping_tradevt = {i : vt for i, vt in enumerate(self.tradevt_campping_index.keys())}            
            
            # 将数据添加到指标当中,由于指标需要以系统默认的数据来进行时间计数_clock，所以需要额外添加计时种子clock_data进去,
            # 但是我们不用其进行计算            
            for vt, datalist in datafeeds_vt.items():
                clock_data = self.datas[self.tradevt_campping_index[vt]]
                self.BasisMmt_ind[vt] = BasisMmt_ind(datafeed = datalist,clockdata= clock_data,
                                                     params= {'window_prd':self.params.BasisMmt_window_prd})
                        
                # 指标太多，就不画出来了
                self.BasisMmt_ind[vt].plotinfo.plot = False
            # 计时器：clock
            self.clock = 0
        else:
            # 调用指标提取器提取数据
            Indicator_utl = HdfUtility()
            for vt in self.tradevt_campping_index.keys():
                excode = self.od_params['excode'][self.od_params['vt'].index(vt)]
                indicator_temp = Indicator_utl.hdfRead(EXT_Hdf_Path, excode, vt, 
                                                      kind1='Indicator', 
                                                      kind2=self.indicator_name, 
                                                      kind3=None, 
                                                      startdate=self.od_params['startdate'], 
                                                      enddate=self.od_params['enddate'])           
                self.BasisMmt_ind[vt] = indicator_temp['Indicator']
            # 计时器：clock
            self.clock = self.params.BasisMmt_window_prd - 1
            
    
        
    def start(self):
        print('the strategy begin')

    def prenext(self):
        print('I am not ready, need %s days'%self.params.BasisMmt_window_prd)

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
        for i, vt in self.index_campping_tradevt.items():
            pos = self.positions[self.datas[i]].size
            print('vtname: %s position :%s'%(vt, pos))


        # 将数据添加到组合仓位管理中
        # 更新仓位管理的相关数据
        for i , vt in self.index_campping_tradevt.items():
            self.pos_manage.update_data(vt, self.datas[i].close[0])
        # 判断是否为组合换仓日
        if self.holding_days == self.params.shift_pos_days:
            # 对之前的持仓进行平仓
            self.last_trading_vt = [vt for vt in self.pos_manage.new_trading_vt if vt not in self.no_trad_vt]
            for vt in self.last_trading_vt:
                self.close(data=self.datas[self.tradevt_campping_index[vt]])
                print('%s close created , the price is %s '%(vt ,self.datas[self.tradevt_campping_index[vt]].close[0]))

            # 寻找买入和卖出合约
            # 对指标进行排序，买入前asset_ratio个，卖出后asset_ratio个
            temp_ind = pd.Series([self.BasisMmt_ind[vt][0] for vt in self.index_campping_tradevt.values()], \
                                 index=self.index_campping_tradevt.values()).sort_values(ascending = False)
            
            
            trading_assetnum = max(int(self.params.asset_ratio*len(self.tradevt_campping_index)),1)
            
            buy_vt = list(temp_ind.head(trading_assetnum).index)
            sell_vt = list(temp_ind.tail(trading_assetnum).index)
            # 将买卖合约添加进仓位管理中
            self.pos_manage.updata_vtsymbol(buy_vt + sell_vt)
            # 计算每个合约买卖的数目
            tradingsizer_byvt = self.pos_manage.clct_sizer(cerebro.broker.getvalue())

            # 分别买卖相关合约
            for vt in buy_vt:
                i = self.tradevt_campping_index[vt]
                sizer = tradingsizer_byvt[vt]                
                lprice = self.datas[i].close[0]+self.od_params[vt]["pricetick"]*(-10)
                self.buy(data = self.datas[i] ,exectype = Order.Limit, price = lprice,  size= sizer, \
                         valid = self.datas[i].datetime.date(0) + datetime.timedelta(self.od_params[vt]["ordervaliday"]))
                print('time :%s buy vt: %s, enter pending price : %s ,size : %s '%(date,vt,lprice,sizer))
            for vt in sell_vt:
                i = self.tradevt_campping_index[vt]
                sizer = tradingsizer_byvt[vt]                
                lprice = self.datas[i].close[0] - self.od_params[vt]["pricetick"]*(-10)
                self.sell(data = self.datas[i] ,exectype = Order.Limit, price = lprice, size= sizer ,\
                          valid = self.datas[i].datetime.date(0) + datetime.timedelta(self.od_params[vt]["ordervaliday"]))
                print('time :%s sell vt: %s, enter pending price : %s, size: %s'%(date,vt, lprice, sizer))
            self.holding_days = 1
            self.no_trad_vt = []
        self.holding_days += 1 
        

    #def add_extradata(self, vt, code, startdate, enddate):
        ## 策略需要添加额外数据
        ## 将连续远月合约和连续近月合约的数据添加到datafeeds当中
        #data_ult = HisDayData()
        #near_data, long_data = data_ult.get_nearlong_data(vt, excode, 
                                                         #startdate, 
                                                         #enddate)
        
       

if __name__ == '__main__':  
    # Create a cerebro entity  
    cerebro = bt.Cerebro()  
    # Add a strategy  
    cerebro.addstrategy(Basis_MmtStrategy)  

    # the parameter loading
    # parameter parse
    parse_tool = CTA_setting_parse(SETTING)
    parse_tool.add2platform(platform=cerebro)    
    # loading data
    parse_tool.loading_data(platform=cerebro)
    # loading extra data
    NEAR_MONTH = 'near_month'
    LONG_MONTH = 'long_month'
    data_ult = HisDayData()
    data_setting = SETTING['data_setting']
    for i, vt in enumerate(data_setting['vt']):
        near_data = data_ult.get_nearlong_data(vt, data_setting['excode'][i], data_setting['startdate'], 
                                               data_setting['enddate'], type=NEAR_MONTH)
        parse_tool.add_extrdata(cerebro, extra_data=near_data, vt=vt, extra_name='01'+NEAR_MONTH)
        long_data =  data_ult.get_nearlong_data(vt, data_setting['excode'][i], data_setting['startdate'], 
                                                data_setting['enddate'], type=LONG_MONTH)
        parse_tool.add_extrdata(cerebro, extra_data=long_data, vt=vt, extra_name='12'+LONG_MONTH)
        
    # add some parmas to strategy
    parse_tool.add2strat(platform=cerebro)
    # Print out the starting conditions  
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())  
    # Run over everything  
    result = cerebro.run()  
    # Print out the final result  
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # print out tha analyzers' values
    
    for analyzer in SETTING['basic_setting']['analyzer'].values():
        data = getattr(result[0].analyzers,analyzer).get_analysis()
        print('analyzer: %s, values: %s'%(analyzer, data))
        
    
    # save the indicator
    if False:
        Indicator_utl = HdfUtility()
        stat = cerebro.runstrats[0][0]
        indicator_byvt = stat.BasisMmt_ind
        params = cerebro.runstrats[0][0].od_params
        for indicator, vt in indicator_byvt.items():
            indicator_data = indicator.array
            tradingday = cerebro.datasbyname(vt+'0000').datetime.array
            df = pd.DataFrame({'Indicator':indicatoe_data, 'Date':tradingday})
            date_parse = lambda x:num2date(x)
            df['Date'] = df['Date'].apply(date_parse)
            excode = params['excode'][params['vt'].index(vt)]        
            Indicator_utl.hdfWrite(EXT_Hdf_Path, excode, vt, df.set_index('Date'), kind1='Indicator', kind2=stat.indicator_name, 
                                  kind3={'window_prd':stat.params.BasisMmt_window_prd})
        

    
    cerebro.plot()  