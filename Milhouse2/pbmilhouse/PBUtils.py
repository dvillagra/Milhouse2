'''
Created on Feb 7, 2013

@author: dvillagra

Utilities for PacBio specific instances of Milhouse
'''

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_code.settings'

from django_code.models import SecondaryAnalysisServer


MP17_SMRT_SERVER_CONFIG = {'serverName'    : 'SMRTPortalMP17',
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
                             'apiRootPath'   : '/DBService/',
                             'active'        : True}


MARTIN_PROD_SERVER = SecondaryAnalysisServer(**MARTIN_PROD_SERVER_CONFIG)


MP17_DVLOCAL_SMRT_SERVER_CONFIG = {'serverName'    : 'SMRTPortalMP17DVLocal',
                                   'serverHost'    : 'mp-f017', 
                                   'serverPort'    : 8080,
                                   'homePath'      : '/Users/dvillagra/milhouse_dev/dev/sample_data/secondary/smrtportal/',
                                   'jobDataPath'   : '/Users/dvillagra/milhouse_dev/dev/sample_data/secondary/smrtportal/jobs/',
                                   'referencePath' : '/Users/dvillagra/milhouse_dev/dev/sample_data/secondary/smrtportal/references/',
                                   'protocolPath'  : '/Users/dvillagra/milhouse_dev/dev/sample_data/secondary/smrtportal/protocols/',
                                   'apiRootPath'   : '/smrtportal/api/', 
                                   'active'        : True}



MP17_DVLOCAL_SMRT_SERVER = SecondaryAnalysisServer(**MP17_DVLOCAL_SMRT_SERVER_CONFIG)


MARTIN_DVLOCAL_SMRT_SERVER_CONFIG = {'serverName'    : 'MartinDVLocal',
                                     'serverHost'    : 'smrtpipe', 
                                     'serverPort'    : 80,
                                     'homePath'      : '/Users/dvillagra/milhouse_dev/dev/sample_data/secondary/martin/',
                                     'jobDataPath'   : '/Users/dvillagra/milhouse_dev/dev/sample_data/secondary/martin/jobs/',
                                     'referencePath' : '/Users/dvillagra/milhouse_dev/dev/sample_data/secondary/martin/references/',
                                     'protocolPath'  : '/Users/dvillagra/milhouse_dev/dev/sample_data/secondary/martin/protocols/',
                                     'apiRootPath'   : '/DBService/', 
                                     'active'        : True}



MARTIN_DVLOCAL_SMRT_SERVER = SecondaryAnalysisServer(**MARTIN_DVLOCAL_SMRT_SERVER_CONFIG)


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
        

