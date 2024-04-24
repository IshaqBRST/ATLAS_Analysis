# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 08:53:51 2024

@author: Mohammad
"""

# config.py
tuple_path = "https://atlas-opendata.web.cern.ch/atlas-opendata/samples/2020/4lep/"

samples = {
    'data': {
        'list' : ['data_A','data_B','data_C','data_D'],
    },
    r'Background $Z,t\bar{t}$' : {
        'list' : ['Zee','Zmumu','ttbar_lep'],
        'color' : "#6b59d3" # purple
    },
    r'Background $ZZ^*$' : {
        'list' : ['llll'],
        'color' : "#ff0000" # red
    },
    r'Signal ($m_H$ = 125 GeV)' : {
        'list' : ['ggH125_ZZ4lep','VBFH125_ZZ4lep','WH125_ZZ4lep','ZH125_ZZ4lep'],
        'color' : "#00cdff" # light blue
    },
}
