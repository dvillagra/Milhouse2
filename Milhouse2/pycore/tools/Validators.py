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

class ExperimentDefinitionValidator(object):

    @staticmethod
    def getHeaderValues(reverse=False):
        opts = {'newJob'       : (['Name', 'SecondaryServerName', 'LIMSCode', 'PrimaryFolder', 'SecondaryProtocol', 'SecondaryReference', 'ExtractBy', 'MergeBy'],
                                  ['Name', 'SecondaryServerName', 'DataPath', 'PrimaryFolder', 'SecondaryProtocol', 'SecondaryReference', 'ExtractBy', 'MergeBy'],),
                'exisitingJob' : (['Name', 'SecondaryServerName', 'SecondaryJobID', 'ExtractBy', 'MergeBy'],)
                }
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
        headerDict = self.getHeaderValues()
        
        if not csv:
            msg = '[%s] is not a valid file name or stream' % self.csv
            return (False, msg)
        
        # Check to see that valid headers were supplied
        jobType = None
        for row in headerDict.values():
            if csv.dtype.names in row:
                jobType = self.getHeaderValues(True).get(row)
        
        if not jobType:
            msg = 'Invalid headers supplied in input csv: %s' % csv.dtype.names
            return (False, msg)
        
        # Check if csvFN can be parsed
        if not csv.shape:
            msg = 'Invalid CSV file name or stream: file does not exist or stream can not be opened'
            return (False, msg)
                
        # Check for unpopulated default columns
        colnames = headerDict.get(jobType)
        wrngclmns = filter(lambda x: n.dtype(x[1]) == n.dtype(bool) and x[0] in colnames, csv.dtype.descr)
        if wrngclmns:
            msg = 'Incorrectly formatted CSV file:\n Column(s) [%s] have not been populated' % ', '.join([c[0] for c in wrngclmns])
            return (False, msg)

        # Check if the file contains the correct default column names
        if filter(lambda x: x not in csv.dtype.names, colnames):
            msg = 'Incorrectly formatted CSV file:\n Missing default column names from %s' % colnames
            return (False, msg)

        # Check to ensure SecondaryServerName maps to valid server
        try:
            secondaryServers = [SecondaryAnalysisServer.objects.get(serverName = x) for x in csv['SecondaryServerName']]
            secondaryServers = dict((x.name, x) for x in secondaryServers)
        except ObjectDoesNotExist:
            msg = 'Invalid SecondaryServerName. Valid values are: %s' % ([x.name for x in SecondaryAnalysisServer.objects.all()])
            return (False, msg)
        
        

        # Check for correct naming of conditions
        if filter(lambda x: re.findall(r'[^A-Za-z0-9_\.\-]', str(x)), csv['Name']):
            msg = 'Incorrectly formatted CSV file:\n Condition names can only contain: alphanumeric characters, dashes (-), underscores (_) and dots (.)'
            return (False, msg)
        
        # Check if the non-default columns have a p_ prefix
        extras = filter(lambda x: x not in colnames, self._data.dtype.names)
        if filter(lambda x: x[:2] != 'p_', extras):
            msg = 'Incorrectly formatted CSV file:\n Extra parameters need to be named using a "p_" prefix' 
            return (False, msg)

        # Check if protocol provided exists in secondary server's protocol list
        for s,p in zip(csv['SecondaryServerName'], csv['SecondaryProtocol']):
            server = secondaryServers.get(s)
            serverProtocols = SecondaryDataHandler(server).getProtocolNames()
            if not p in serverProtocols:
                msg = 'Unsupported SecondaryProtocol name provided: %s' % p
                return (False, msg)
        
        # Check if reference sequence provided exists in the reference repository
#        if 'MartinRefSeq' in self._data.dtype.names:
#            wrongrefseqs = filter(lambda x: not glob.glob('%s/%s' % (MU.MARTIN_REFREPOS[x['MartinType']], x['MartinRefSeq'])), self._data)
#            wrongrefseqs = filter(lambda x: not x['MartinRefSeq'] == 'LIMSTemplates', wrongrefseqs)
#            wrongrefseqs = filter(lambda x: not x['MartinRefSeq'] == 'LIMSTemplate', wrongrefseqs)
#            wrongrefseqs = set([x['MartinRefSeq'] for x in wrongrefseqs])
#            if wrongrefseqs:
#                msg = 'The following reference sequence names are invalid: [%s].' % ','.join(wrongrefseqs)
#                return (False, msg)                
#        
#        # Check for correctness MartinJobID values
#        if 'MartinJobID' in self._data.dtype.names:
#            wrnglens = set(filter(lambda x: x not in [6, 2], map(lambda x: len(str(x)), self._data['MartinJobID'])))                
#            if wrnglens and len(wrnglens) == 1 and wrnglens.issubset([5]) and not isSmrtPortal:
#                msg = 'Invalid MartinJobID lengths supplied:\n If these are smrtportal jobs, you need to set MartinType to smrtportal or smrtportal_mfg' 
#                return (False, msg)
#            elif wrnglens and not wrnglens.issubset([5]) or filter(lambda x: len(str(x)) == 2 and x != -1, self._data['MartinJobID']):
#                msg = 'Invalid MartinJobID lengths supplied:\n Martin expects length == 6 and smrtportal length => 5. For mixed CSVs use -1.' 
#                return (False, msg)
#                
#
#        # Check whether primary folder names are contained within the given run codes and pls.h5/bas.h5 files exist
#        if set(['RunCodes', 'PrimaryFolder']).issubset(self._data.dtype.names):
#            for row in self._data:
#                if len(row['RunCodes'].split('-')) == 2:
#                    exp,run = row['RunCodes'].split('-')
#                    if not glob.glob('/mnt/data*/vol*/%s/%s/%s/*h5' % (exp,run, row['PrimaryFolder'])):
#                        msg = 'Run code [%s] does not contain primary folder [%s] or has no pls.h5/bas.h5 files .' % (row['RunCodes'], row['PrimaryFolder'])
#                        return (False, msg)
#                else:
#                    msg = 'Run code [%s] is not of the expected format' % row['RunCodes']
#                    return (False, msg)
#                            
#        # Check for uniqueness of column values within conditions
#        for cond in n.unique(self._data['Name']):
#            sl_data = self._data[self._data['Name'] == cond]
#            if filter(lambda x: len(n.unique(sl_data[x])) != 1, [k for k in sl_data.dtype.names if k != 'RunCodes']):
#                msg = 'For condition name=%s some of the attributes are NOT unique' % cond
#                return (False, msg)                                
    return (True, 'CSV file passed validation')
        
        
