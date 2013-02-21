'''
Created on Feb 6, 2013

@author: dvillagra
'''

import urllib
import httplib
import socket
import glob
import os

from urlparse import urljoin
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError

#import time
import django.utils.simplejson as json
import pycore.MUtils as MU
from pycore.tools.LIMSHandler import LIMSMapper

# Consider implementing a factory pattern here, where a disk-implementation would also work 
# if no server host or server port were supplied

class SecondaryServerConnectorError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class SecondaryJobServiceError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SecondaryServerConnector(object):
    
    def __init__(self, server):
        self.server = server
        
    def _getConnection(self):
        return httplib.HTTPConnection(self.server.serverHost, int(self.server.serverPort), timeout=30)
    
    def _makeResponse(self, respDict, asDict=True):
        return respDict if asDict else json.dumps(respDict)
    
    def makeRequest(self, url, method='GET', params=None, responseAsDict=True):
        # Set basic request variables
        params = urllib.urlencode(params) if params else urllib.urlencode({})
        postHeaders = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
        
        # Attempt request to specified url
        try:
            conn = self._getConnection()
            if method=='POST':
                conn.request(method, url, params, postHeaders)
            else:
                conn.request(method, url, params)
            #time.sleep(2)
        except socket.error as msg:
            MU.logMsg(self, msg, 'error')
            conn.close()
            return self._makeResponse({'success': 'False', 'errorMsg': msg}, responseAsDict)
        
        resp = conn.getresponse()
        if resp.status != httplib.OK:
            msg = 'Server Error Code: %d, Server error reason: %s' % (resp.status, resp.reason)
            conn.close()
            MU.logMsg(self, msg, 'error')
            return self._makeResponse({'success': 'False', 'errorMsg': msg}, responseAsDict)
        
        else:  
            MU.logMsg(self, 'Successfully completed server request', 'info')      
            respDict = json.loads(resp.read())
            conn.close()
            MU.logMsg(self, 'Request returned: %s' % respDict, 'debug')
            return self._makeResponse(respDict, responseAsDict)
        


class SecondaryJobServiceFactory(object):
    
    @staticmethod
    def create(server, disk):
        if 'martin' in server.serverName.lower():
            # This is specific to PacBio only, do not set this to true for non-PacBio installs!!
            from pbmilhouse.MartinJobHandler import MartinJobServiceFactory
            return MartinJobServiceFactory.create(server, disk)
        # All other Milhouse instance should go through this path
        if disk:
            return SecondaryJobServiceDisk(server)
        else:
            return SecondaryJobServiceAPI(server)
        
#    @staticmethod
#    def tryAllMethods(server, func):
#        try:
#            SecondaryDataHandlerFactory.create(server, True)



class SecondaryJobService(object):
    
    def __init__(self, server):
        self.server  = server
        
    ## COMMON AND PRIVATE METHODS
    def makeAPICall(self, apiCall, apiParams=None):
        conn = SecondaryServerConnector(self.server)
        return conn.makeRequest(urljoin(self.server.apiRootPath, apiCall), params=apiParams)
    
    def getSingleItem(self, items):
        if isinstance(items, list) and len(items) > 1:
            raise SecondaryJobServiceError('Multiple entries returned!: %s' % str(items))
        elif not items:
            raise SecondaryJobServiceError('No entries found matching search parameters!')
        elif isinstance(items, list) and len(items) == 1:
            return items[0]
        else:
            return items
            
    def _getEntries(self, elems, entryName='rows'):
        return elems.get(entryName, [])
        
    def _getElemFrom(self, entries, getBy, fallback=None):
        return [r.get(getBy, fallback) for r in entries]
    
    def _getSingleElemFrom(self, entry, getBy=None, fallback=None):
        entry = self.getSingleItem(entry)
        return entry.get(getBy, fallback)
    
    def _filterEntriesBy(self, entries, params):
        return filter(lambda e: dict(filter(lambda (x,y): e[x]==y, params.iteritems())), entries)

    
    def normalizeJobID(self, jobID, digits=6):
        if isinstance(jobID, str):
            return jobID.zfill(digits)
        else:
            formatStr = '%%0%dd' % digits
            return formatStr % jobID
    
    def getJobDiskPath(self, basePath, jobID):
        jobID = self.normalizeJobID(jobID)
        return os.path.join(basePath, jobID[:3], jobID)
    
    def getJobPathFromID(self, jobID):
        jobID = self.normalizeJobID(jobID)
        jobPath = self.getJobDiskPath(self.server.jobDataPath, jobID)
        if os.path.isdir(jobPath):
            return jobPath
        else:
            msg = 'Unable to access job path for job ID [%s].  Attempted [%s]' % (jobID, jobPath)
            MU.logMsg(self, msg, 'error')
    
    def getJobFile(self, jobID, filename):
        jobPath = self.getJobPathFromID(jobID)
        if jobPath:
            jobfile = os.path.join(jobPath, filename)
            if os.path.isfile(jobfile):
                return jobfile
            else:
                msg = 'Unable to access job file [%s] for job [%s].  Attempted %s' % (filename, jobID, jobfile)
                MU.logMsg(self, msg, 'error')
    
    def getCellContext(self, smrtcell):
        return ''
    
    def getSMRTCellInfoFromFullPath(self, fullPath):
        cellPath = os.path.dirname(os.path.dirname(fullPath))
        primaryFolder = os.path.basename(os.path.dirname(fullPath))
        context = self.getCellContext(os.path.basename(fullPath))
        limsCode =  LIMSMapper.limsCodeFromCellPath(cellPath)
        
        return {'SMRTCellPath'  : cellPath, 
                'PrimaryFolder' : primaryFolder, 
                'Context'       : context, 
                'LIMSCode'      : limsCode}
    
    def getSMRTCellInfoFromFofn(self, fofn):
        fofnLines = open(fofn, 'r').readlines()
        return [self.cellInfoFromFullPath(x) for x in fofnLines]
        
    def getReferencePath(self, referenceName):
        refPath = os.path.join(self.server.referencePath, referenceName)
        if os.path.isdir(refPath):
            return refPath
        else:
            msg = 'Unable to access path for reference [%s]. Attempted %s' % (referenceName, refPath)
            MU.logMsg(self, msg, 'error')
            
    def getReferenceFile(self, referenceName):
        refPath = self.getReferencePath(referenceName)
        refFile = os.path.join(refPath, 'reference.info.xml')
        if os.path.isfile(refFile):
            return refFile
        else:
            msg = 'Unable to access file for reference [%s]. Attempted %s' % (referenceName, refFile)
            MU.logMsg(self, msg, 'error')

    def getProtocolFile(self, protocolFile):
        protocolXML = os.path.join(self.server.protocolPath, protocolFile)
        if os.path.isfile(protocolXML):
            return protocolXML
        else:
            msg = 'Unable to access file for protocol [%s]. Attempted %s' % (protocolFile, protocolXML)
            MU.logMsg(self, msg, 'error')
    

class SecondaryJobServiceAPI(SecondaryJobService):
    
    
    #################################
    ##      HANDLE DATA  ACCESS    ##
    #################################
                
    ## REFERENCES
    def getReferences(self):
        return self.makeAPICall('reference-sequences')
    
    def getReferenceEntries(self):
        entries = self._getEntries(self.getReferences())
        return self._getElemFrom(entries, 'referenceEntry')
            
    def getReferenceElem(self, elem, fallback='unknown'):
        return self._getElemFrom(self.getReferenceEntries(), elem, fallback)

    def getReferenceNames(self):
        return self.getReferenceElem('name', 'none')
        
    def getReferenceEntriesBy(self, params):
        entries = self.getReferenceEntries()
        return self._filterEntriesBy(entries, params)
    
    def getSingleReferenceEntry(self, refName):
        entries = self.getReferenceEntriesBy({'name': refName})
        return self.getSingleItem(entries)
    
    def getSingleReferenceElem(self, refName, elem, fallback=None):
        entry = self.getSingleReferenceEntryBy(refName)
        return entry.get(elem, fallback)
    
    def getBasicReferenceInfo(self, referenceName):
        reference = self.getSingleReferencelEntryBy({'name': referenceName})
        return {'name'         : reference.get('name', 'unknown'),
                'lastModified' : reference.get('last_modified', 'unknown'),
                'md5'          : reference['digest'].get('value', 'unknown'),
                'version'      : reference.get('version', 'unknown')
                }
        
    
    ## PROTOCOLS
    def getProtocols(self):
        return self.makeAPICall('protocols')
        
    def getProtocolEntries(self):
        return self._getEntries(self.getProtocols())
        
    def getProtocolElem(self, elem, fallback='unknown'):
        return self._getElemFrom(self.getProtocolEntries(), elem, fallback)
    
    def getProtocolNames(self):
        return self.getProtocolElem('name', 'none')
    
    def getProtocolEntriesBy(self, params):
        entries = self.getProtocolEntries()
        return self._filterEntriesBy(entries, params)
    
    def getSingleProtocolEntry(self, protocolID):
        entries = self.getProtocolEntriesBy({'id': protocolID})
        return self.getSingleItem(entries)
    
    def getSingleProtocolElem(self, protocolID, elem, fallback=None):
        entry = self.getSingleProtocolEntry(protocolID)
        return entry.get(elem, fallback)
    
    def getBasicProtocolInfo(self, protocolID):
        protocol = self.getSingleProtocolEntryBy({'id': protocolID})
        return {'name'         : protocol.get('name', 'unknown'),
                'lastModified' : protocol.get('whenModified', 'unknown'),
                'protocolId'   : protocolID,
                'version'      : protocol.get('version', 'unknown')
                }
        
    
    
    ## JOBS
    
    # XXX I'm not sure how I feel about all of these different methods, it's starting to get messy
    # especially when you think about the separate Martin implementation and how that will return 
    # data in a different format
    
    def getJobs(self):
        return self.makeAPICall('jobs')
    
    def getJobEntries(self):
        return self._getEntries(self.getJobs())
    
    def getSingleJobEntry(self, jobID):
        return self.getSingleItem(self.makeAPICall('jobs/%s' % jobID))
    
    def getJobElems(self, elem, fallback='none'):
        return self._getElemFrom(self.getJobEntries(), elem, fallback)
    
    def getSingleJobElem(self, elem, jobID):
        entry = self.getSingleJobEntry(jobID)
        return self._getSingleElemFrom(entry, elem)

    def getJobIDs(self):
        return self.getJobElems('jobId')
        
    def getJobInputs(self, jobID):
        return self._getEntries(self.makeAPICall('jobs/%s/inputs' % jobID))
    
    def getSMRTCellInfo(self, jobID):
        inputs = self.getJobInputs(jobID)
        inputData = []
        for i in inputs:
            inputDict = {'SMRTCellPath'  : i.get('collectionPathUri'),
                         'PrimaryFolder' : i.get('primaryResultsFolder'),
                         'Context'       : 'none',
                         'LIMSCode'      : LIMSMapper.limsCodeFromCellPath(i.get('collectionPathUri'))
                         }
            inputData.append(inputDict)
        
        return inputData
    
    # This is the main method that should be called from the ProjectHandler,
    # must be identical for different JobService instances (e.g. SMRT Portal, Martin, Disk, API, etc).
    def getBasicJobInfo(self, jobID):
        jobEntry = self.getSingleJobEntry(jobID)
        return {'jobId'     : jobEntry.get('jobId'),
                'protocol'  : self.getBasicProtocolInfo(jobEntry.get('protocolName')),
                'reference' : self.getBasicReferenceInfo(jobEntry.get('referenceSequenceName')),
                'inputs'    : self.getSMRTCellInfo(jobID)
                }
        
    
    ## MAKE DICTIONARY WITH NAMES AND VALUES
    def makePropertyDict(self, props=('ReferenceNames', 'ProtocolNames')):
        propDict = {}
        if 'ReferenceNames' in props:
            propDict['ReferenceNames'] = self.getReferenceNames()
        if 'ProtocolNames' in props:
            propDict['ProtocolNames'] = self.getProtocolNames()
        return propDict
    
    
    #################################
    ##       HANDLE JOB SUBMIT     ##
    #################################

    def submitSecondaryJob(self, condition, job):
        # Get or create the inputs
        inputs = []
        for c in job.cells.all:
            pass
        
        # Save the inputs
        
        # Create the job
        jobData = {'name'         : 'Milhouse%s_%s' % (condition.project.name, condition.name),
                   'createdBy'    : 'MilhouseUser', 
                   'description'  : 'Milhouse%s_%s %s' % (condition.project.name, condition.name, job.protocol.name),
                   'protocolName' : job.protocol.protocolId,
                   'groupNames'   : ['all'],
                   'inputIds'     : inputs
                   }
        
        # Save the job
        
        # Submit the job
        



class SecondaryJobServiceDisk(SecondaryJobService):
    
    
    ###########################
    ##      HANDLE DATA      ##
    ###########################
    
    
    ## REFERENCES
    def getReferenceNames(self):
        refDirs = glob.glob('%s/*' % self.server.referencePath)
        return filter(lambda x: os.path.isdir(x), refDirs)
    
    def getBasicReferenceInfo(self, referenceName):
        referenceFile = self.getReferenceFile(referenceName)
        return self.parseReferenceXML(referenceFile)

    def getSingleReferenceElem(self, referenceName, elem, fallback=None):
        return self.getBasicReferenceInfo(referenceName).get(elem, fallback)
    
    
    
    ## PROTOCOLS
    def getProtocolIDs(self):
        protocolFiles = glob.glob('%s/*' % self.server.protocolPath)
        filteredFiles = filter(lambda x: os.path.isfile(x) and x.endswith('.xml'), protocolFiles)   
        return [x[:-4] for x in filteredFiles]
    
    def getBasicProtocolInfo(self, protocolID):
        protocolFile = self.getProtocolFile('%s.xml' % protocolID)
        return self.parseProtocolXML(protocolFile)

    def getSingleProtocolElem(self, protocolID, elem, fallback=None):
        return self.getBasicProtocolInfo(protocolID).get(elem, fallback)
    
    
    ## JOBS
    def getAllJobIDs(self):
        return glob.glob('%s/*/*' % self.server.jobDataPath)

    def getBasicJobInfo(self, jobID):
        inputXML = self.getJobFile(jobID, 'input.xml')
        jobDict = {}
        jobDict['jobId'] = jobID
        if inputXML:
            inputData = self.parseInputXML(inputXML)
            jobDict['protocol']  = inputData.get('SecondaryProtocol', 'unknown'),
            jobDict['reference'] = inputData.get('SecondaryReference', 'unknown'),
            jobDict['inputs']    = self.getSMRTCellInfoFromFullPath(inputData.get('InputPaths'))
        else:
            inputFofn   = self.getJobFile(jobID, 'input.fofn')
            settingsXML = self.getJobFile(jobID, 'settings.xml')
            
            if inputFofn:
                jobDict['inputs'] = self.getSMRTCellInfoFromFofn(inputFofn)
            if settingsXML:
                jobDict['protocol']  = 'get from settings xml'
                jobDict['reference'] = 'get from settings xml'
                
        return jobDict
            


    def parseInputXML(self, inputXML):
        dataDict = {}
        try:
            xmltree = parse(inputXML)
            header = xmltree.firstChild.getElementsByTagName('header')
            dataRef = xmltree.firstChild.getElementsByTagName('dataReferences')
            
            if header and dataRef:
                header = header.pop()
                dataRef = dataRef.pop()
                jid = int(header.getAttribute('id'))
                job = header.getElementsByTagName('job')
                primFolder = dataRef.getElementsByTagName('tag')
                
                if jid and job and primFolder:
                    job = job.pop()
                    primFolder = primFolder.pop()
                    paramsDict = {node.tagName: node.firstChild.data for node in job.childNodes if node.nodeType != 3 and node.firstChild}
                    cells = map(lambda x: x.firstChild.data, dataRef.getElementsByTagName('data'))
#                    cellPaths = map(lambda x: os.path.basename(x), cells)
#                    limsCodes = map(lambda x: '-'.join(LIMSMapper.limsCodeFromCellPath(x)), cellPaths)
                    
                    if paramsDict.get('referenceSequenceName'):
                        dataDict['SecondaryReference'] = paramsDict.get('referenceSequenceName')
                        
                    if paramsDict.get('protocolName'):
                        dataDict['SecondaryProtocol'] = paramsDict.get('protocolName')
    
                    if cells:
                        dataDict['InputPaths'] = cells
    
        except ExpatError:
            msg = 'Attemtping to parse input.xml failed [%s]' % inputXML
            MU.logMsg(self, msg, mode='info')
            return dataDict
    
        return dataDict
    
    
    def parseSettingsXML(self, settingsXML):
        pass
    
    def parseReferenceXML(self, referenceXML):
        dataDict = {}
        try:
            xmltree = parse(referenceXML)
            refInfo = xmltree.firstChild.getElementsByTagName('reference_info')
            
            if refInfo:
                dataDict['name']         = refInfo.getAttribute('id')
                dataDict['lastModified'] = refInfo.getAttribute('last_modified') 
                #dataDict['md5']          = 'unknown',#refInfo.getAttribute('')
                dataDict['version']      = refInfo.getAttribute('version')
                
        except ExpatError:
            msg = 'Attemtping to parse reference.info.xml failed [%s]' % referenceXML
            MU.logMsg(self, msg, mode='info')
            return dataDict
        
        return dataDict
    
    def parseProtocolXML(self, protocolXML):
        dataDict = {}
        try:
            xmltree = parse(protocolXML)
            protocolInfo = xmltree.firstChild.getElementsByTagName('protocol')
            
            if protocolInfo:
                dataDict['name']         = protocolInfo.getAttribute('id') # Fix this to actually get the name
                #dataDict['lastModified'] = refInfo.getAttribute('last_modified') 
                dataDict['protocolId']   = protocolInfo.getAttribute('id')
                dataDict['version']      = protocolInfo.getAttribute('version')
                
        except ExpatError:
            msg = 'Attemtping to parse protocol xml failed [%s]' % protocolXML
            MU.logMsg(self, msg, mode='info')
            return dataDict
        
        return dataDict
    
    
    