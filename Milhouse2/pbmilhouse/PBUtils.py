'''
Created on Feb 7, 2013

@author: dvillagra

Utilities for PacBio specific instances of Milhouse
'''

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_code.settings'

from django_code.models import SecondaryAnalysisServer


MP17_SMRT_SERVER_CONFIG = {'serverName'    : 'SMRTPortal_MP17',
                           'serverHost'    : 'mp-f017', 
                           'serverPort'    : 8080,
                           'homePath'      : '/mnt/secondary/Smrtanalysis/opt/smrtanalysis/',
                           'jobDataPath'   : '/mnt/secondary/Smrtanalysis/userdata/jobs/',
                           'referencePath' : '/mnt/secondary/Smrtanalysis/userdata/references/',
                           'protocolPath'  : '/mnt/secondary/Smrtanalysis/opt/smrtanalysis/common/protocols/',
                           'apiRootPath'   : '/smrtportal/api/', 
                           'active'        : True}



MP17_SMRT_SERVER = SecondaryAnalysisServer(**MP17_SMRT_SERVER_CONFIG)

MARTIN_PROD_SERVER_CONFIG = {'serverName'    : 'MartinProd',
                             'serverHost'    : 'smrtpipe', 
                             'serverPort'    : 80,
                             'homePath'      : '/mnt/secondary/Smrtpipe/martin/prod/',
                             'jobDataPath'   : '/mnt/secondary/Smrtpipe/AppRoot/static/analysisJob_v2/',
                             'referencePath' : '/mnt/secondary/Smrtpipe/martin/prod/data/repository/',
                             'protocolPath'  : '/mnt/secondary/Smrtpipe/martin/prod/data/workflows/',
                             'apiRootPath'   : '',
                             'active'        : True}


MARTIN_PROD_SERVER = SecondaryAnalysisServer(**MARTIN_PROD_SERVER_CONFIG)

####################
#  CSV_VALIDATION  #
####################

OLD_CSV_HEADERS = ['Name', 'RunCodes', 'PrimaryFolder', 'MartinWorkflow', 'MartinRefSeq', 'MartinJobID', 'MartinType']

CSV_HEADER_MAPPING = {'Name'           : 'Name', 
                      'RunCodes'       : 'LIMSCode',
                      'PrimaryFolder'  : 'PrimaryFolder', 
                      'MartinWorkflow' : 'SecondaryProtocol', 
                      'MartinRefSeq'   : 'SecondaryReference',
                      'MartinType'     : 'SecondaryServerName'}
        

