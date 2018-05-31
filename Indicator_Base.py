# encoding: utf-8

# 本模块可用于因子的生成存储, 因子的可视化分析, 后验分析等

# Import the backtrader platform
import backtrader as bt
# import CTA_base
from CTA_factor_backtrade.CTA_base import CTA_setting_parse
# import the data engine
from getdata_project.HdfUtility import HdfUtility
from getdata_project.HisDayData import HisDayData
from CTA_factor_backtrade.ErrorType import NameError

# import other package
import pandas as pd
import numpy as np
import re
import importlib
import copy
from collections import defaultdict
from backtrader import num2date


#from matplotlib import pyplot as plt
class Indicator_Fetch(bt.Strategy):
    '''
    本类只适合需要单个品种的数据进行计算的因子
    '''
    def __init__(self, params):        
        self.indicator_params = params
        self.ind_window_prd = self.indicator_params['window_prd']
        self.ind = {}
        self.indicator_name = self.indicator_params['indicator_name']
        # 动态导入因子
        try:
            # 因子来自我们自己定义的指标
            Mould = importlib.import_module(name= 'backtrader.indicators.'+ self.indicator_name)
            self.Indicator = getattr(Mould, self.indicator_name)
        except :
            try:
                # 因子来自系统自带的指标
                Mould = importlib.import_module(name= 'CTA_factor_backtrade.CTA_indicators.'+ self.indicator_name)
                self.Indicator = getattr(Mould, self.indicator_name)
            # 抛出异常
            except :
                raise NameError(self.indicator_name)
            
            
        # 每一个品种具有多个合约，为了计算因子我们需要都添加到因子当中,所以需要保存映射关系
        # 但是交易仅需要主力合约，所以也需要保存主力合约名称和指标之间的关系,在数据加载过程中，将
        # 主力合约名称保存在数据中是vt+0000, 例如:IF0000
        self.index_mapping_symbol = {i: data._name for i, data in enumerate(self.datas)}
        self.symbol_mapping_index = {data._name: i for i, data in enumerate(self.datas)}
        
        #self.tradevt_campping_index = {re.findall('^(\D*)',data._name)[0]: i for i, data in enumerate(self.datas) if data._name[-4:]=='0000'}
        #self.index_campping_tradevt = {i: re.findall('^(\D*)',data._name)[0] for i, data in enumerate(self.datas) if data._name[-4:]=='0000'}
       
        # 生成指标
        # 这里有空可以区分系统生成的因子和自己生成的因子的不同方式，因为不同因子参数不同
        self.CTAIndicator_Create()

    def CTAIndicator_Create(self):

        
    # 如果数据是实时生成，那么调用相关指标进行计算

        # 将同一品种的数据保存在datafeeds_vt里面
        datafeeds_vt = defaultdict(list)
        for i, vt in self.index_mapping_symbol.items():
            vt = re.findall('^(\D*)',vt)[0]
            datafeeds_vt[vt] = datafeeds_vt[vt] + [self.datas[i]]         

        # 将数据添加到指标当中,由于指标需要以系统默认的数据来进行时间计数_clock，所以需要额外添加计时种子clockdata进去,
        # 但是我们不用其进行计算            
        for vt, datalist in datafeeds_vt.items():
            clock_data = self.datas[self.symbol_mapping_index[vt+'0000']]
            self.ind[vt] = self.Indicator(datafeed = datalist,clockdata = clock_data, params = self.indicator_params)
        
        
        
      
    @classmethod    
    def run_indicator(cls,indicator_name, indicator_params, SETTING):
        # Create a cerebro entity  
        cerebro = bt.Cerebro()  
        # Add a strategy
        indicator_params.update({'indicator_name':indicator_name})
        cerebro.addstrategy(Indicator_Fetch,  indicator_params)  
    
        # the parameter loading
        # parameter parse 
        # input the indicator infomation
        
        parse_tool = CTA_setting_parse(SETTING)
        # loading data
        parse_tool.loading_data(platform=cerebro)
        
        # load extra_data
        if SETTING['data_setting']['loading_datatype'].get('extradata',None):
            cls.add_exdata(indicator_name=indicator_name,platform = cerebro, parse_tool = parse_tool, setting = SETTING)

        # run 
        result = cerebro.run()
        
    
        if SETTING['indsave']:
            # save the indicator
            print('save the indicator: %s'%indicator_name)
            Indicator_Fetch.indicator_save(platform = cerebro, setting = SETTING)
    
    @classmethod
    def indicator_save(cls, platform, setting):
        Indicator_utl = HdfUtility()
        stat = platform.runstrats[0][0]
        indicator_byvt = stat.ind
        params = setting['data_setting']
        for vt, indicator in indicator_byvt.items():
            indicator_data = indicator.array
            tradingday = platform.datasbyname[vt+'0000'].datetime.array
            df = pd.DataFrame({'Indicator':indicator_data, 'Date':tradingday})
            date_parse = lambda x:num2date(x)
            df['Date'] = df['Date'].apply(date_parse)
            excode = params['excode'][params['vt'].index(vt)]        
            Indicator_utl.hdfWrite(EXT_Hdf_Path, excode, vt, df.set_index('Date'), kind1='Indicator', kind2=stat.indicator_name, 
                                   kind3={'window_prd':stat.params['window_prd']})        
  
    
    #@classmethod
    #def indicator_save(cls, indicatordata, date, indicator_name, vt, params):
        ## save the indicator
        #Indicator_utl = HdfUtility()
        #df = pd.DataFrame({'Indicator':indicatordata, 'Date':date})
        #date_parse = lambda x:num2date(x)
        #df['Date'] = df['Date'].apply(date_parse)
        #vt = re.findall('^(\D+)', vt)[0]
        #excode = find_excode(vt)
        
        #Indicator_utl.hdfWrite(EXT_Hdf_Path, excode, vt, df.set_index('Date'), kind1='Indicator', kind2=indicator_name, 
                               #kind3={'window_prd':params['window_prd']})              
    
    
    
    @classmethod
    def add_exdata(cls, indicator_name, platform, parse_tool, setting):
        '''如果因子有需要其他相关的数据，那么
           用户可以在因子里面继承
        '''
        Mould = importlib.import_module(name= 'CTA_factor_backtrade.CTA_indicators.'+ indicator_name)
        Indicator = getattr(Mould, indicator_name)
        Indicator.add_exdata(platform = platform, parse_tool = parse_tool, setting = setting)        
        

    

class Indicator_plot(object):
    '''
    展示因子
    '''
    def FctvsCumrate(self, factor, adjprice, forward ):
        '''
        展示因子的未来预测能力，横坐标为因子值，纵坐标为未来N天的累计收益
        factor: 应该是包含了所有因子的数据集
        adjprice: 品种的价格
        forward：因子向前预测N天
        '''
        adjprice = np.array(adjprice)
        ret = (adjprice[1:] - adjprice[0:-1])/(adjprice[0:-1])
        
        cumret = [np.cumprod(1+ret[i:i+forward])[-1]-1 for i in range(len(adjprice[0:-forward]))]
        
        factor = factor[0:-forward]
        factor['cumret'] = cumret
        
        figure = plt.figure(1)
        subplot = figure.subplot(len(factor.columns)-1)
        