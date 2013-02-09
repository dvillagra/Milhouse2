'''
Created on Feb 8, 2013

@author: dvillagra
'''

import os
import re
import glob
import numpy as n
from django.core.exceptions import ObjectDoesNotExist 

import pycore.MUtils as MU
from django_code.models import SecondaryAnalysisServer
from pycore.SecondaryJobHandler import SecondaryDataHandler
from pycore.tools.LIMSHandler import LIMSMapper


class SMRTCellDataPathValidator(object):
    
    def __init__(self, dataPath, primaryFolder):
        self.dataPath      = dataPath
        self.primaryFolder = primaryFolder
        
    def isValid(self):
        if not os.path.exists(os.path.join(self.dataPath, self.primaryFolder)):
            msg = 'SMRTCellPath [%s] does not contain primary folder [%s]' % (self.dataPath, self.primaryFolder)
            return (False, msg)
        if not glob.glob(os.path.join(self.dataPath, self.primaryFolder, '*.h5')):
            msg =  'PrimaryFolder has no pls.h5/bas.h5 files [%s]' % os.path.join(self.dataPath, self.primaryFolder) 
            return (False, msg)
        return (True, 'SMRTCellPath is valid')
        

class ExperimentDefinitionValidator(object):

    @staticmethod
    def getHeaderValues(minimal = False, reverse=False):
        allOpts = {'newJob'       : ('Name', 'SecondaryServerName', 'SMRTCellPath', 'PrimaryFolder', 'SecondaryProtocol', 'SecondaryReference', 'ExtractBy', 'MergeBy'),
                   'exisitingJob' : ('Name', 'SecondaryServerName', 'SecondaryJobID', 'ExtractBy', 'MergeBy')
                   }
        
        minOpts = {'newJob'       : ('Name', 'SecondaryServerName', 'SMRTCellPath', 'PrimaryFolder', 'SecondaryProtocol', 'SecondaryReference'),
                   'exisitingJob' : ('Name', 'SecondaryServerName', 'SecondaryJobID')
                   }
        opts = minOpts if minimal else allOpts
        if reverse:
            return dict([(y,x) for x,y in opts.iteritems()])
        return opts

    def __init__(self, csv):
        self.csv = self._getDefinitionRecArray(csv)
        
    def _getDefinitionRecArray(self, csv):
        if isinstance(csv, str):
            if os.path.isfile(csv):
                try:
                    return MU.getRecArrayFromCSV(csv)
                except ValueError as err:
                    MU.logMsg(self, 'Incorrectly formatted CSV file:\n %s' % err, 'error')
            else:
                MU.logMsg(self, 'CSV file provided does not exist! %s' % csv, 'error')
        else:
            return csv
    
    def getExperimentDefinition(self):
        return self.csv
        
    
    def validateDefinition(self):
        csv = self.csv
        allHeaders = self.getHeaderValues()
        minHeaders = self.getHeaderValues(True)
        
        if not csv:
            msg = '[%s] is not a valid file name or stream' % self.csv
            return (False, msg)
        
        # Check to see that valid headers were supplied
        jobType = None
        if tuple(csv.dtype.names) in allHeaders.values():
            jobType = self.getHeaderValues(True).get(tuple(csv.dtype.names))
        
        if not jobType:
            msg = 'Invalid headers supplied in input csv: %s' % csv.dtype.names
            return (False, msg)
        
        # Check if csvFN can be parsed
        if not csv.shape:
            msg = 'Invalid CSV file name or stream: file does not exist or stream can not be opened'
            return (False, msg)
                
        # Check for unpopulated default columns
        minColnames = minHeaders.get(jobType)
        wrngclmns = filter(lambda x: n.dtype(x[1]) == n.dtype(bool) and x[0] in minColnames, csv.dtype.descr)
        if wrngclmns:
            msg = 'Incorrectly formatted CSV file:\n Column(s) [%s] have not been populated' % ', '.join([c[0] for c in wrngclmns])
            return (False, msg)

        # Check if the file contains the correct default column names
        if filter(lambda x: x not in csv.dtype.names, minColnames):
            msg = 'Incorrectly formatted CSV file:\n Missing default column names from %s' % minColnames
            return (False, msg)

        # Check to ensure SecondaryServerName maps to valid server
        try:
            secondaryServers = [SecondaryAnalysisServer.objects.get(serverName = x) for x in csv['SecondaryServerName']]
            secondaryServers = dict((x.name, x) for x in secondaryServers)
            serverNames = set(secondaryServers.keys())
            dataHandlerDict = dict([(s, SecondaryDataHandler(secondaryServers.get(s))) for s in serverNames])
        except ObjectDoesNotExist:
            msg = 'Invalid SecondaryServerName. Valid values are: %s' % ([x.name for x in SecondaryAnalysisServer.objects.all()])
            return (False, msg)
               
        # Check for correct naming of conditions
        if filter(lambda x: re.findall(r'[^A-Za-z0-9_\.\-]', str(x)), csv['Name']):
            msg = 'Incorrectly formatted CSV file:\n Condition names can only contain: alphanumeric characters, dashes (-), underscores (_) and dots (.)'
            return (False, msg)
        
        # Check if the non-default columns have a p_ prefix
        allColnames = allHeaders.get(jobType)
        extras = filter(lambda x: x not in allColnames, self._data.dtype.names)
        if filter(lambda x: x[:2] != 'p_', extras):
            msg = 'Incorrectly formatted CSV file:\n Extra parameters need to be named using a "p_" prefix' 
            return (False, msg)                
        
        # Check new job specific settings
        if jobType == 'newJob':
            
            serverPropDict = dict([(s, dataHandlerDict[s].makePropertyDict(('References', 'Protocols'))) for s in serverNames])
            
            # Check if protocols and references provided exists in secondary server's protocol list
            for s,p,r in zip(csv['SecondaryServerName'], csv['SecondaryProtocol'], csv['SecondaryReference']):
                serverProtocols = serverPropDict[s].get('Protocols', [])
                serverReferences = serverPropDict[s].get('References', [])
                referenceWhitelist = ['LIMSTemplates', 'LIMSTemplate']
                if not p in serverProtocols:
                    msg = 'Unsupported SecondaryProtocol name provided: %s' % p
                    return (False, msg)
                if not r in serverReferences and r not in referenceWhitelist:
                    msg = 'Unsupported SecondaryReference name provided: %s' % r
                    return (False, msg)
            
            # Check whether primary folder names are contained within the given run codes and pls.h5/bas.h5 files exist
            for d,p in zip(csv['SMRTCellPath'], csv['PrimaryFolder']):
                if os.path.exists(d):
                    # A data path was given, not a LIMSCode
                    scv = SMRTCellDataPathValidator(d, p)
                    valid, msg = scv.isValid()
                    if not valid:
                        return (False, msg)
                else:
                    # Path provided might be a LIMSCode - check with the LIMSHandler to see if it validates
                    limsPath = LIMSMapper(d).getDataPath()
                    if limsPath:
                        scv = SMRTCellDataPathValidator(limsPath, p)
                        valid, msg = scv.isValid()
                        if not valid:
                            return (False, msg)
                    else:
                        msg = 'SMRTCellPath could not be mapped to a unique LIMS Code: %s' % d
                        return (False, msg)
                        
        
        elif jobType == 'existingJob':
            
            # Check to make sure all job IDs are integers
            try:
                secondaryJobsIDs = [int(x) for x in csv['SecondaryJobID']]
            except ValueError:
                msg = 'Invalid SecondaryJobID provided.  All IDs must be integers: %s' % csv['SecondaryJobID']
                return (False, msg)
            
            # Check to make sure that jobs actually exist on specified servers
            serverPropDict = dict([(s, dataHandlerDict[s].makePropertyDict(('Jobs'))) for s in serverNames])
            for s,j in zip(csv['SecondaryServerName'], csv['SecondaryJobID']):
                if not j in serverPropDict[s].get('Jobs'):
                    msg = 'Job ID [%s] does not exist on server [%s]' % (j,s)
                    return (False, msg)
            
        
        # HERE'S THE ADVANCED STUFF
 
        # Check for uniqueness of column values within conditions
        for cond in n.unique(self._data['Name']):
            sl_data = self._data[self._data['Name'] == cond]
            if filter(lambda x: len(n.unique(sl_data[x])) != 1, [k for k in sl_data.dtype.names if k != 'RunCodes']):
                msg = 'For condition name=%s some of the attributes are NOT unique' % cond
                return (False, msg)                                

    return (True, 'CSV file passed validation')
        
        
