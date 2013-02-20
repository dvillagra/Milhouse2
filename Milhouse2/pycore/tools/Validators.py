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
from pycore.SecondaryJobHandler import SecondaryJobServiceFactory, SecondaryJobServiceError
from pycore.tools.LIMSHandler import LIMSMapper


class ValidationError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


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
    def csvToRecArray(csv):
        if isinstance(csv, n.recarray):
            return csv
        elif isinstance(csv, str):
            if os.path.isfile(csv):
                try:
                    return MU.getRecArrayFromCSV(csv, caseSensitive=True)
                except ValueError as err:
                    MU.logMsg('CsvToRecArray', 'Incorrectly formatted CSV file:\n %s' % err, 'error')
            else:
                MU.logMsg('CsvToRecArray', 'CSV file provided does not exist! %s' % csv, 'error')
        else:
            raise ValidationError('Unable to convert CSV definition input [%s] into RecArray' % csv)

    
    @staticmethod
    def getValidHeaderValues(minimal = False, reverse=False, tolower=False):
        allOpts = {'newJob'       : ('Name', 'SecondaryServerName', 'SMRTCellPath', 'PrimaryFolder', 'SecondaryProtocol', 'SecondaryReference', 'ExtractBy', 'MergeBy'),
                   'exisitingJob' : ('Name', 'SecondaryServerName', 'SecondaryJobID', 'ExtractBy', 'MergeBy')
                   }
        
        minOpts = {'newJob'       : ('Name', 'SecondaryServerName', 'SMRTCellPath', 'PrimaryFolder', 'SecondaryProtocol', 'SecondaryReference'),
                   'exisitingJob' : ('Name', 'SecondaryServerName', 'SecondaryJobID')
                   }
        opts = minOpts if minimal else allOpts
        if tolower:
            opts = dict([(x, tuple([z.lower() for z in y])) for x,y in opts.iteritems()])
        if reverse:
            return dict([(y,x) for x,y in opts.iteritems()])
        return opts
    
    @staticmethod
    def getValidExtractByValues():
        return ['Readlength', 'TemplateSpan', 'NErrors', 'ReadFrames', 
                'FrameRates', 'IPD', 'PulseWidth', 'Accuracy', 'PolRate', 
                'Reference', 'Barcode', 'Movie']
        
        
    def __init__(self, csv):
        self.csv = self.csvToRecArray(csv)
        
    def getExperimentDefinition(self):
        return self.csv
        
        
    def getDefinitionType(self):
        # Check to see that valid headers were supplied
        csvHeaders = filter(lambda x: not x.startswith('p_'), self.csv.dtype.names)
        jobType = None        
        for m in self.getValidHeaderValues(True).values():
            if all([x in csvHeaders for x in m]):
                jobType = self.getValidHeaderValues(minimal=True, reverse=True).get(m)
        return jobType
    
    def validateDefinition(self):
        csv = self.csv
        allHeaders = self.getValidHeaderValues()
        minHeaders = self.getValidHeaderValues(True)
        csvHeaders = filter(lambda x: not x.startswith('p_'), csv.dtype.names)
        
        if csv is None:
            msg = '[%s] is not a valid file name or stream' % str(self.csv)
            return (False, msg)
        
        # Check to see that valid headers were supplied
        jobType = self.getDefinitionType()    
        if not jobType:
            msg = 'Invalid headers supplied in input csv: %s' % str(csvHeaders)
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
        if filter(lambda x: x not in csvHeaders, minColnames):
            msg = 'Incorrectly formatted CSV file:\n Missing default column names from %s' % str(minColnames)
            return (False, msg)

        # Check to ensure SecondaryServerName maps to valid server
        try:
            secondaryServers = [SecondaryAnalysisServer.objects.get(serverName=x) for x in csv['SecondaryServerName']]
            secondaryServers = dict((x.serverName, x) for x in secondaryServers)
            serverNames = n.unique(secondaryServers.keys())
            dataHandlerDict = dict([(s, SecondaryJobServiceFactory.create(secondaryServers.get(s), disk=False)) for s in serverNames])
        except ObjectDoesNotExist:
            msg = 'Invalid SecondaryServerName. Valid values are: %s' % (', '.join([x.serverName for x in SecondaryAnalysisServer.objects.all()]))
            return (False, msg)
               
        # Check for correct naming of conditions
        if filter(lambda x: re.findall(r'[^A-Za-z0-9_\.\-]', str(x)), csv['Name']):
            msg = 'Incorrectly formatted CSV file:\n Condition names can only contain: alphanumeric characters, dashes (-), underscores (_) and dots (.)'
            return (False, msg)
        
        # Check if the non-default columns have a p_ prefix
        allColnames = allHeaders.get(jobType)
        extras = filter(lambda x: x not in allColnames, csv.dtype.names)
        if extras and not filter(lambda x: x.startswith('p_'), extras):
            msg = 'Incorrectly formatted CSV file:\n Extra parameters need to be named using a "p_" prefix' 
            return (False, msg)
        
        # Check new job specific settings
        if jobType == 'newJob':
            
            serverPropDict = dict([(s, dataHandlerDict[s].makePropertyDict(('ReferenceNames', 'ProtocolNames'))) for s in serverNames])
            
            # Check if protocols and references provided exists in secondary server's protocol list
            for s,p,r in zip(csv['SecondaryServerName'], csv['SecondaryProtocol'], csv['SecondaryReference']):
                serverProtocols = serverPropDict[s].get('ProtocolNames', [])
                serverReferences = serverPropDict[s].get('ReferenceNames', [])
                referenceWhitelist = ['LIMSTemplates', 'LIMSTemplate']
                if len(filter(lambda x: x==p, serverProtocols)) != 1:
                    msg = 'SecondaryProtocol does not map to a single name on server: %s' % p
                    return (False, msg)
                if len(filter(lambda x: x==r, serverReferences)) != 1 and r not in referenceWhitelist:
                    msg = 'SecondaryReference does not map to a single name on server: %s' % r
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
                    try:
                        limsPath = LIMSMapper(d).getDataPath()
                    except Exception as err:
                        return (False, 'SMRTCellPath [%s] is not a valid path, nor a valid LIMS Code' % (d, err))
                        
                    if limsPath:
                        scv = SMRTCellDataPathValidator(limsPath, p)
                        valid, msg = scv.isValid()
                        if not valid:
                            return (False, msg)
                    else:
                        msg = 'SMRTCellPath could not be mapped to a unique LIMS Code: %s' % d
                        return (False, msg)
            
            # Check to make sure that protocol is split/merge-able.
            if 'ExtractBy' in csvHeaders:
                for p, e in zip(csv['SecondaryProtocol'], csv['ExtractBy']):
                    if not re.findall('([Rr]esequencing|[Mm]apping)', p):
                        msg = 'SecondaryProtocol [%s] may not be extractable by [%s].  Does the protocol generate a cmp.h5?' % (p, e)
                        return (True, msg)

                        
        
        elif jobType == 'existingJob':
            
            # Check to make sure all job IDs are integers
            try:
                secondaryJobsIDs = [int(x) for x in csv['SecondaryJobID']]
            except ValueError:
                msg = 'Invalid SecondaryJobID provided.  All IDs must be integers: %s' % csv['SecondaryJobID']
                return (False, msg)
            
            # Check to make sure that jobs actually exist on specified servers
            for s,j in zip(csv['SecondaryServerName'], csv['SecondaryJobID']):
                sdh = dataHandlerDict.get(s)
                try:
                    sdh.getSingleJobEntry(j)
                except SecondaryJobServiceError: # yes, this is bad... i know
                    msg = 'Single Job ID [%s] does not exist on server [%s]' % (j,s)
                    return (False, msg)
        
        # HERE'S THE ADVANCED STUFF
 
        # Check for uniqueness of column values within conditions
        for cond in n.unique(csv['Name']):
            condRows = csv[csv['Name'] == cond]
            notUnique = ['SecondaryJobID', 'SecondaryServerName', 'SMRTCellPath', 'PrimaryFolder', 'SecondaryProtocol']
            if filter(lambda x: len(n.unique(condRows[x])) != 1, [k for k in condRows.dtype.names if k not in notUnique and not k.startswith('p_')]):
                msg = 'For condition name=%s some of the attributes are NOT unique' % cond
                return (False, msg) 

            
        # Check to make sure that split/merge was specified correctly
        if 'ExtractBy' in csvHeaders:
            for e in csv['ExtractBy']:
                bOps = ['>', '<', '==', '!=', '!==', '>=', '<=']
                combs = ['&', '|']
                opsUsed = filter(lambda x: x in e, bOps)
                if not opsUsed:
                    msg = 'Illegal syntax for ExtractBy field, please use binary operator statement (e.g. Readlength > 1000)'
                    return (False, msg)
                combsUsed = filter(lambda x: x in e, combs)
                if combsUsed:
                    e = [x.strip() for x in re.split(r'[&\|]+', e)]
                else:
                    e = [e]
                validExtract = ExperimentDefinitionValidator.getValidExtractByValues()
                if not all([any([v in x for v in validExtract]) for x in e]):
                    msg = 'Invalid ExtractBy [%s]. Please select valid ExtractBy option: %s' % (e, ', '.join(validExtract))
                    return (False, msg)
                                    
        
        return (True, 'CSV file passed validation')