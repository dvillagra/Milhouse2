'''
Created on Feb 7, 2013

@author: dvillagra
'''

from pycore.SecondaryJobHandler import SecondaryServerInstance
from pycore.SecondaryJobHandler import SecondaryDataHandler as SDH

class MartinDataHandler(SecondaryServerInstance):
    
    def getReferences(self, apiCall='', apiParams=None):
        return SDH.getReferences(apiCall, apiParams)
    
    