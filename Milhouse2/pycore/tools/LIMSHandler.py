'''
Created on Feb 8, 2013

@author: dvillagra

A module that takes a LIMS code in any format and defines a way to map it to a SMRT Cell data path
'''

import glob

class LIMSMapper(object):
    
    def __init__(self, limsCode):
        self.limsCode = limsCode
        
    # Override this method to fit your own LIMS needs
    def getDataPath(self):
        globRoot = '/mnt/data*/vol*/%s/%s'
        subVals  = tuple(self.limsCode.split('-'))
        globVal  = glob.glob(globRoot % subVals) 
        
        if globVal and len(globVal) == 1:
            return globVal[0]
        
    