'''
Created on Feb 6, 2013

@author: dvillagra
'''

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_code.settings'

from django_code.models import SecondaryAnalysisServer
from pbmilhouse import PBUtils as PBU

def fillSecondaryServers():
    print 'Loading secondary servers'
    SecondaryAnalysisServer.objects.get_or_create(**PBU.MP17_SMRT_SERVER_CONFIG)
    SecondaryAnalysisServer.objects.get_or_create(**PBU.MARTIN_PROD_SERVER_CONFIG)
    

if __name__ == '__main__':
    
    print "START FILL DB\n"
    fillSecondaryServers()
    print "\nDONE"