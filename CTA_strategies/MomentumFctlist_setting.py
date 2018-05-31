#encoding: utf-8

SETTING =\
{
    "basic_setting":
        {
          "startcash": 1000000,
          "commission": 0.0003,
          "default_sizer": 1,
          "analyzer":{"DrawDown" : "DW", 'SharpeRatio': 'SharpeRatio'}

        },

     "data_setting":
        {
            "startdate": "20100101",
            "enddate" : "20171231",
            #"vt": ['CF', 'C', 'JM', 'FG', 'JD', 'HC', 'RU', 'PP', 'PB', 'RB', 'TA', 'A', 'ZN', 'AG', 'NI', 'I', 'J', 'M', 'L', 'AL', 'P', 
                   #'AU', 'V', 'Y', 'CU', 'IF', 'BU', 'SR', 'SN'],
            #'excode': ['CZCE', 'DCE', 'DCE', 'CZCE', 'DCE', 'SHFE', 'SHFE', 'DCE', 'SHFE', 'SHFE', 'CZCE', 'DCE', 'SHFE', 'SHFE', 'SHFE', 'DCE', 
                       #'DCE', 'DCE', 'DCE', 'SHFE', 'DCE', 'SHFE', 'DCE', 'DCE', 'SHFE', 'CFE', 'SHFE', 'CZCE', 'SHFE'],
            'vt':['IF'],
            'excode':['CFE'],
            'COLUMNS':['datetime', 'AdjFactor', 'Open', 'Low', 'High', 'Close',  'Volume'],
            'loading_datatype':{'domdata':True, 'subdomdata':False, 'rawdata':False}
         },


    "vtsymbol_setting":
        {
            'CF':{'pricetick':5, 'ordervaliday':3, 'point_value':5},
            'C':{'pricetick':1, 'ordervaliday':3, 'point_value':10},
            'JM':{'pricetick':0.5, 'ordervaliday':3, 'point_value':60},
            'FG':{'pricetick':1, 'ordervaliday':3, 'point_value':20},
            'JD':{'pricetick':1, 'ordervaliday':3, 'point_value':10},
            'HC':{'pricetick':1, 'ordervaliday':3, 'point_value':10},
            'RU':{'pricetick':5, 'ordervaliday':3, 'point_value':10},
            'PP':{'pricetick':1, 'ordervaliday':3, 'point_value':5},
            'PB':{'pricetick':5, 'ordervaliday':3, 'point_value':5},
            'RB':{'pricetick':1, 'ordervaliday':3, 'point_value':10},
            'TA':{'pricetick':2, 'ordervaliday':3, 'point_value':5},
            'A':{'pricetick':1, 'ordervaliday':3, 'point_value':10},
            'ZN':{'pricetick':5, 'ordervaliday':3, 'point_value':5},
            'AG':{'pricetick':1, 'ordervaliday':3, 'point_value':15},
            'NI':{'pricetick':10, 'ordervaliday':3, 'point_value':1},
            'I':{'pricetick':0.5, 'ordervaliday':3, 'point_value':100},
            'J':{'pricetick':0.5, 'ordervaliday':3, 'point_value':100},
            'M':{'pricetick':1, 'ordervaliday':3, 'point_value':10},
            'L':{'pricetick':5, 'ordervaliday':3, 'point_value':5},
            'AL':{'pricetick':5, 'ordervaliday':3, 'point_value':5},
            'P':{'pricetick':2, 'ordervaliday':3, 'point_value':10},
            'AU':{'pricetick':0.05, 'ordervaliday':3, 'point_value':1000},
            'V':{'pricetick':5, 'ordervaliday':3, 'point_value':5},
            'Y':{'pricetick':2, 'ordervaliday':3, 'point_value':10},
            'CU':{'pricetick':10, 'ordervaliday':3, 'point_value':5},
            'IF':{'pricetick':0.2, 'ordervaliday':3, 'point_value':300},
            'BU':{'pricetick':2, 'ordervaliday':3, 'point_value':10},
            'SR':{'pricetick':1, 'ordervaliday':3, 'point_value':10},
            'SN':{'pricetick':10, 'ordervaliday':3, 'point_value':1}
  
        }

}




