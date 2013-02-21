'''
Created on Feb 8, 2013

@author: dvillagra

A module that takes a LIMS code in any format and defines a way to map it to a SMRT Cell data path
'''

import glob
from pycore import MUtils as MU

class LIMSMapper(object):
    
    # Override these methods to fit your own LIMS needs
    
    @staticmethod
    def limsCodeFromCellPath(cellPath):
        try:
            nums = cellPath.split('/')[-2:]
            [int(x) for x in nums]
            return '-'.join(nums)
        except ValueError:
            MU.logMsg('LIMSMapper', 'Unable to find LIMS Code from cell path %s' % cellPath, 'info')
        
    @staticmethod
    def cellPathFromLimsCode(limsCode):
        globRoot = '/mnt/data*/vol*/%s/%s'
        subVals  = tuple(limsCode.split('-'))
        globVal  = glob.glob(globRoot % subVals) 
        
        if globVal and len(globVal) == 1:
            return globVal[0]