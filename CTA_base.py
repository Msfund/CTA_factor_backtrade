# encoding:utf-8
# this file is to parse the strategy setting 
# and load data into backtrader platform
import backtrader as bt

from getdata_project.HisDayData import HisDayData
from getdata_project.HdfUtility import HdfUtility
from getdata_project.dataUlt import (EXT_Hdf_Path,EXT_Rawdata ,EXT_Stitch)

import copy
import datetime
import pandas as pd
import os


class CTA_setting_parse(object):
    def __init__(self, setting):
        self.params = setting
        # 基础设置，之后添加到平台当中
        # 例如组合交易的起始资金，手续费，佣金，默认交易手数，分析指标analyzers等
        self.baseinfo = self.params.get('basic_setting', None)
        # 关于交易的品种的相关信息，之后添加到策略当中
        # 例如最小价格变动价位, 订单生效日期，每点的价格，
        self.tradesetting = self.params.get('vtsymbol_setting',None)
        self.datainfo = self.params.get('data_setting',None)        
    # ------------------------------------------------------------------
    def add2platform(self, platform):

        # basic setting
        # input every basic setting into a dictionary named 'basic_setting'
        if self.baseinfo.get('startcash', None) :
            # set the starting cash
            platform.broker.setcash(self.baseinfo['startcash'])
        if self.baseinfo.get('commission', None) :
            # set the commission
            platform.broker.setcommission(self.baseinfo['commission'])
        if self.baseinfo.get('default_sizer', None) :
            # set the default sizer
            platform.addsizer(bt.sizers.FixedSize, stake=self.baseinfo['default_sizer'])  
        if self.baseinfo.get('analyzer',None):
            # add the analyzers
            analyzers = self.baseinfo['analyzer']
            for analyzer, newname in  analyzers.items():
                platform.addanalyzer(getattr(bt.analyzers, analyzer), _name = newname)
        # self.params.pop('basic_setting')
     
    def add2strat(self,platform):
        for strat in platform.strats:
            self.params['vtsymbol_setting'].update(self.params['data_setting'])
            strat[0][0].od_params = self.params['vtsymbol_setting']
    
    # ------------------------------------------------------------------------
    def loading_data(self, platform):
    
        # parse the datasetting
        
        #self.datainfo = self.params['data_setting']  
        self.Parse_datasetting()
        # loading bar data period: 1 day
        self.getdata_utl = HdfUtility()        
        # create the our datafeed
        CTA_datafeed_name = 'CTA_datafeed'.encode('utf-8')
        # if you have other data form, change the bt.feeds.pandafeed to your favour
        # you must cancel the lines in the dataserise or the lines will be overlap
        self.CTA_datafeed = type(CTA_datafeed_name,(bt.feeds.PandasData,),{'lines':self.lines, 'params':self.data_params})
        
        

            # 判断需要加载哪些类型的数据，dom ?, subdom?, rawdata?
            # 是否加载主力合约数据
        if self.datainfo['loading_datatype']['domdata']:
            self.load_domdata(platform)

        
        # 是否加载次主力合约数据
        if self.datainfo['loading_datatype']['subdomdata']:
            self.load_subdomdata(platform)
    
        # 是否加载原始数据
        if self.datainfo['loading_datatype']['rawdata']:
            # 如果需要加载原始合约数据，那么每个数据feed的名字就是合约名
            self.load_rawdata(platform)
                 

                    
    def Parse_datasetting(self):
        # lines and params setting
        self.lines = tuple([l.lower() for l in self.datainfo['COLUMNS']])
        self.data_params = (
                ('nocase', True),
                ('datetime', None),
                ('open', -1),
                ('high', -1),
                ('low', -1),
                ('close', -1),
                ('volume', -1),
                ('AdjFactor',-1),
                ('openinterest', -1),
            )
    
        params_name = [name for name, i in self.data_params ]
        add2params = [l for l in self.lines if l not in params_name]
        self.data_params = self.data_params + tuple([(name,-1) for name in add2params])        
    
        self.vtsymbol = self.datainfo['vt']
        self.excode = self.datainfo['excode']
        self.startdate = self.datainfo['startdate'] if self.datainfo.get('startdate', None) else None
        self.enddate   = self.datainfo['enddate'] if self.datainfo.get('enddate', None) else None

    # -----------------------------------------------------------------------------
    def load_domdata(self, platform):
  
        for i,vt in enumerate(self.vtsymbol):
            domdata = self.getdata_utl.hdfRead(EXT_Hdf_Path, self.excode[i], vt, kind1=EXT_Stitch,
                                                  kind2='00',kind3='1d',startdate=self.startdate,enddate=self.enddate)

            # 判断需要加载哪些类型的数据，dom ?, subdom?, rawdata?
            # 是否加载主力合约数据

            # 选择我们所需的列数据
            # 来自hdf5中的数据的时间列为Date，平台的lines默认的时间名为datetime               
            domdata = domdata.reset_index().rename(columns = {'Date':'datetime'})
            COLUMNS = list(set(domdata.columns) & set(self.datainfo['COLUMNS']))
            domdata = domdata[COLUMNS].set_index('datetime')
            
            # 由于平台只允许datetime为非float类型，所以如果数据中有其他类型需要转化为数值类型
            is_numtype = {c : pd.api.types.is_numeric_dtype(domdata[c]) for c in domdata.columns}
            if False in is_numtype.values():
                domdata = self.type_change(domdata, is_numtype)
        
            data = self.CTA_datafeed(dataname = domdata)
            # 将主力合约命名形如IF0000
            platform.adddata(data, name = vt+'0000')        
    #----------------------------------------------------------------------
    def load_subdomdata(self, platform):
        
        for i,vt in enumerate(self.vtsymbol):
            subdom =  self.getdata_utl.hdfRead(EXT_Hdf_Path, self.excode[i], vt, kind1=EXT_Stitch,
                                                  kind2='01',kind3=None,startdate=self.startdate,enddate=self.enddate)
            subdom = subdom.reset_index().rename(columns = {'Date':'datetime'}) 
            COLUMNS = set(subdom.columns) & set(self.datainfo['COLUMNS'])
            subdom = subdom[COLUMNS].set_index('datetime')
        
            # 由于平台只允许datetime为非float类型，所以如果数据中有其他类型需要转化为数值类型
            is_numtype = {c : pd.api.types.is_numeric_dtype(subdom[c]) for c in subdom.columns}
            if False in is_numtype.values():
                subdom = self.type_change(subdom, is_numtype)
        
            data = self.CTA_datafeed(dataname = subdom)
            # 将次主力合约命名形如IF0001
            platform.adddata(data, name = vt+'0001')
    #----------------------------------------------------------------------
    def load_rawdata(self, platform):
        # 如果需要加载原始合约数据，那么每个数据feed的名字就是合约名
        for i, vt in enumerate(self.vtsymbol):
            raw_data = self.getdata_utl.hdfRead(EXT_Hdf_Path,self.excode[i], vt, kind1 = 'Rawdata',kind2=None,kind3='1d',
                                              startdate = self.startdate, enddate = self.enddate)
            raw_data = raw_data.reset_index().rename(columns = {'Date':'datetime'})
            COLUMNS = list(set(raw_data.columns)&set(self.datainfo['COLUMNS']))
            contract = pd.unique(raw_data['Asset'])
            for c in contract:
                data_temp = raw_data.ix[raw_data['Asset'] == c,:]
                data_temp = data_temp[COLUMNS].set_index('datetime')
                # 由于平台只允许datetime为非float类型，所以如果数据中有其他类型需要转化为数值类型
                is_numtype = {c : pd.api.types.is_numeric_dtype(data_temp[c]) for c in data_temp.columns}
                if False in is_numtype.values():
                    data_temp = self.type_change(data_temp, is_numtype)                    
                
                data = self.CTA_datafeed(dataname = data_temp)
                platform.adddata(data, name = c)           
    
    # -----------------------------------------------------------------------------    
    def type_change(self, data, datatype_dict):
        
        for column, is_numtype in datatype_dict.items():
            if not is_numtype:
                # 这里使用者可以根据各种类型进行调整
                #if pd.api.types.is_bool_dtype(data[column])
                #if pd.api.types.is_string_dtype(data[column])
                if pd.api.types.is_datetime64_ns_dtype(data[column]):
                    date2num = lambda x : x.toordinal()
                    data[column] = data[column].apply(date2num)
        return data
        
        
        
    # ----------------------------------------------------------------------------
    def add_extrdata(self, platform, extra_data, vt, extra_name):
        # 使用者可以根据自己的需要添加其他数据集
        extra_data = extra_data.reset_index().rename(columns = {'Date':'datetime'})
        COLUMNS = list(set(self.datainfo['COLUMNS'])&set(extra_data.columns)) 
        extra_data = extra_data[COLUMNS].set_index('datetime')
        # 由于平台只允许datetime为非float类型，所以如果数据中有其他类型需要转化为数值类型
        is_numtype = {c : pd.api.types.is_numeric_dtype(extra_data[c]) for c in extra_data.columns}
        if False in is_numtype.values():
            extra_data = self.type_change(extra_data, is_numtype)            
        
        data = self.CTA_datafeed(dataname = extra_data)
        platform.adddata(data, name = vt + extra_name )




    
                
                
                
    
    
        
            
        
            
            
        
    

