'''
Created on Feb 6, 2013

@author: dvillagra
'''

import urllib
import httplib
import socket
import glob
import os
import re

from urlparse import urljoin

#import time
import django.utils.simplejson as json
import pycore.MUtils as MU
from pycore.tools.LIMSHandler import LIMSMapper
from django_code.models import SecondaryAnalysisServer

# Consider implementing a factory pattern here, where a disk-implementation would also work 
# if no server host or server port were supplied

class SecondaryServerConnectorError(Exception):
    ''' Handle errors from SecondaryServerConnector'''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class SecondaryJobServiceError(Exception):
    ''' Handle errors from SecondaryJobService'''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SecondaryServerConnector(object):
    '''Handle remote connections, use for interacting with Secondary Web Services API'''
    def __init__(self, server):
        self.server = server
        
    def _getConnection(self):
        return httplib.HTTPConnection(self.server.serverHost, int(self.server.serverPort), timeout=30)
    
    def _makeResponse(self, resp, asDict=True):
        if asDict and isinstance(resp, dict):
            return resp
        elif isinstance(resp, list):
            return resp
        if asDict:
            try:
                return json.dumps(resp)
            except ValueError as err:
                msg = 'Unable to return response as dictionary: %s' % err
                MU.logMsg(self, msg, 'warning')
                return resp
        return resp
                
    
    def makeRequest(self, url, method='GET', params=None, responseAsDict=True):
        ''' Make requests to remote servers, used for API calls'''
        
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
            MU.logMsg(self, msg, 'warning')
            conn.close()
            return self._makeResponse({'success': False, 'errorMsg': msg}, responseAsDict)
        
        resp = conn.getresponse()
        if resp.status != httplib.OK:
            msg = 'Server Error Code: %d, Server error reason: %s' % (resp.status, resp.reason)
            conn.close()
            MU.logMsg(self, msg, 'warning')
            return self._makeResponse({'success': False, 'errorMsg': msg}, responseAsDict)
        
        else:  
            MU.logMsg(self, 'Successfully completed server request', 'info')      
            respString = resp.read()
            try:
                useResp = json.loads(respString)
            except ValueError, err:
                MU.logMsg(self, 'Unable to load response string to dictionary: %s' % err, 'warning')
                useResp = respString
            conn.close()
            MU.logMsg(self, 'Request returned: %s' % useResp, 'debug')
            return self._makeResponse(useResp, responseAsDict)
        

####################################
###      JOB SERVICE FACTORY     ###
####################################

class SecondaryJobServiceFactory(object):
    
    @staticmethod
    def create(server, disk=None):
        # Create the server db model if it doesn't exist
        if isinstance(server, str):
            if os.path.isfile(str):
                server = MU.serverConfToDict(server)
            else:
                msg = 'Unable to create server with definition: %s' % (server)
                MU.logMsg('SecondaryJobServiceFactory', msg, 'error')
                raise SecondaryJobServiceError(msg)
        
        if isinstance(server, dict):
            try:
                server, created = SecondaryAnalysisServer.objects.get_or_create(**server)
                if created:
                    MU.logMsg('SecondaryJobServiceFactory', 'Created new SecondaryAnalysisServer %s' % server, 'info')
            except Exception as err:
                msg = 'Unable to create server with definition: %s.  ErrorMsg: %s' % (server, err)
                MU.logMsg('SecondaryJobServiceFactory', msg, 'error')
                raise SecondaryJobServiceError(msg)
                
        if re.findall('^martin', server.serverName.lower()):
            # This is specific to PacBio only, do not set this to true for non-PacBio installs!!
            from pbmilhouse.MartinJobHandler import MartinJobServiceFactory
            return MartinJobServiceFactory.create(server, disk)

        if disk is None:
            if server.serverHost and server.serverPort:
                sjsApi = SecondaryJobServiceAPI(server)
                ping, msg = sjsApi.testConnection()
                if ping:
                    logmsg = 'Using Server API Instance, Web Service Ping: %s' % msg
                    MU.logMsg('SecondaryJobServiceFactry', logmsg, 'info')
                    disk = False
                else:
                    logmsg = 'Using Server Disk Instance, Web Service Ping: %s' % msg,
                    MU.logMsg('SecondaryJobServiceFactory', 'info')
                    disk = True
            else:
                disk = True
        
        # All other Milhouse instance should go through this path
        if disk:
            return SecondaryJobServiceDisk(server)
        else:
            return SecondaryJobServiceAPI(server)
        


####################################
###        JOB SERVICE           ###
####################################

class SecondaryJobService(object):
    '''Superclass for interaction with SMRT Analysis servers and files'''
    
    @staticmethod
    def normalizeJobID(jobID, digits=6):
        if isinstance(jobID, str):
            return jobID.zfill(digits)
        else:
            formatStr = '%%0%dd' % digits
            return formatStr % jobID
    
    @staticmethod
    def getJobDiskPath(basePath, jobID):
        jobID = SecondaryJobService.normalizeJobID(jobID)
        return os.path.join(basePath, jobID[:3], jobID)
    
    @staticmethod
    def getCellContext(smrtcell):
        return ''
    
    @staticmethod
    def getSMRTCellInfoFromFullPath(fullPath):
        cellPath = os.path.dirname(os.path.dirname(fullPath))
        primaryFolder = os.path.basename(os.path.dirname(fullPath))
        context = SecondaryJobService.getCellContext(os.path.basename(fullPath))
        limsCode =  LIMSMapper.limsCodeFromCellPath(cellPath)
        
        return {'SMRTCellPath'  : cellPath, 
                'PrimaryFolder' : primaryFolder, 
                'Context'       : context, 
                'LIMSCode'      : limsCode}
        
    @staticmethod
    def getSingleItem(items):
        isList = isinstance(items, list) or isinstance(items, tuple)
        if isList and len(items) > 1:
            raise SecondaryJobServiceError('Multiple items returned!: %s' % str(items))
        elif not items:
            raise SecondaryJobServiceError('No items returned!')
        elif isList and len(items) == 1:
            return items[0]
        else:
            return items

    
    def __init__(self, server):
        self.server  = server
        
    def getInstanceComplement(self, isAPI):
        if isAPI:
            return SecondaryJobServiceFactory.create(self.server, disk=True)
        else:
            return SecondaryJobServiceFactory.create(self.server, disk=False)    


####################################
###      JOB SERVICE API         ###
####################################

class SecondaryJobServiceAPI(SecondaryJobService):
    
    def __init__(self, server):
        super(SecondaryJobServiceAPI, self).__init__(server)
        self.isAPI  = True
        self.isDisk = False
        self.isMartin = False

    def makeAPICall(self, apiCall, apiParams=None):
        conn = SecondaryServerConnector(self.server)
        return conn.makeRequest(urljoin(self.server.apiRootPath, apiCall), params=apiParams)
                
    def testConnection(self):
        ping = self.makeAPICall('')
        if ping.get('success'):
            return (True, '%s web service is alive!' % self.server.serverName)
        else:
            return (False, '%s web service is not responding' % self.server.serverName)
    
    def _getEntries(self, elems, entryName='rows'):
        return elems.get(entryName, [])
        
    def _getElemFrom(self, entries, getBy, fallback=None):
        return [r.get(getBy, fallback) for r in entries]
    
    def _getSingleElemFrom(self, entry, getBy=None, fallback=None):
        entry = self.getSingleItem(entry)
        return entry.get(getBy, fallback)
    
    def _filterEntriesBy(self, entries, params):
        return filter(lambda e: dict(filter(lambda (x,y): e[x]==y, params.iteritems())), entries)

    
    #################################
    ##      HANDLE DATA  ACCESS    ##
    #################################
                
    ## REFERENCES ##
    # Private methods
    def _getReferences(self):
        return self.makeAPICall('reference-sequences')
    
    def _getReferenceEntries(self):
        entries = self._getEntries(self._getReferences())
        return self._getElemFrom(entries, 'referenceEntry')
            
    def _getReferenceElem(self, elem, fallback='unknown'):
        return self._getElemFrom(self._getReferenceEntries(), elem, fallback)
        
    def _getReferenceEntriesBy(self, params):
        entries = self._getReferenceEntries()
        return self._filterEntriesBy(entries, params)
    
    def _getSingleReferenceEntry(self, refName):
        return self.getSingleItem(self.makeAPICall('reference-sequences/%s' % refName))
    
    def _getSingleReferenceElem(self, refName, elem, fallback=None):
        entry = self._getSingleReferenceEntry(refName)
        return entry.get(elem, fallback)
    
    # Public interface methods
    def getReferenceNames(self):
        return self._getReferenceElem('name', 'none')

    def getModelReferenceInfo(self, refName):
        refDict = {'name' : refName}
        reference = self._getSingleReferenceEntry(refName)
        if reference:
            digest = reference.get('digest')
            if digest:
                md5 = reference['digest'].get('value', 'unknown')
                
            refDict['lastModified'] = reference.get('last_modified', 'unknown')
            refDict['md5']          = md5
            refDict['version']      = reference.get('version', 'unknown')
        return refDict
    
    def getAvailableReferenceInfo(self, refName):
        return self.getModelReferenceInfo(refName)
    
    
    ## PROTOCOLS ##
    # Private methods
    def _getProtocols(self):
        return self.makeAPICall('protocols')
        
    def _getProtocolEntries(self):
        return self._getEntries(self._getProtocols())
        
    def _getProtocolElem(self, elem, fallback='unknown'):
        return self._getElemFrom(self._getProtocolEntries(), elem, fallback)
    
    def _getProtocolEntriesBy(self, params):
        entries = self._getProtocolEntries()
        return self._filterEntriesBy(entries, params)
    
    def _getSingleProtocolEntry(self, protocolName):
        entries = self._getProtocolEntriesBy({'id': protocolName})
        return self.getSingleItem(entries)
    
    def _getSingleProtocolElem(self, protocolName, elem, fallback=None):
        entry = self._getSingleProtocolEntry(protocolName)
        return entry.get(elem, fallback)
    
    def _getSingleProtocolXML(self, protocolName):
        return self.makeAPICall('protocols/%s' % protocolName)
    
    # Public interface methods
    def getProtocolNames(self):
        return self.makeAPICall('protocols/names')
    
    def getModelProtocolInfo(self, protocolName):
        protocolDict = {'name' : protocolName}
        protocol = self._getSingleProtocolEntry(protocolName)
        if protocol:
            protocolDict['lastModified'] = protocol.get('whenModified', 'unknown')
            protocolDict['version']      = protocol.get('version', 'unknown')
        return protocolDict
        
    def getAvailableProtocolInfo(self, protocolName):
        #protocolXML = self.getSingleProtocolXML(protocolName)
        complement = self.getInstanceComplement(self.isAPI)
        return complement.getAvailableProtocolInfo(protocolName)
    
    def protocolIsSplittable(self, protocolName):
        protocolInfo = self.getAvailableProtocolInfo(protocolName)
        if protocolInfo:
            moduleInfo = protocolInfo.get('modules')
            if moduleInfo:
                if moduleInfo.has_key('mapping'):
                    return True
        return False
        
        
        
    ## JOBS
    # Private methods    
    def _getJobs(self):
        return self.makeAPICall('jobs') # Warning: this returns a paged result, i.e. incomplete list
    
    def _getJobEntries(self):
        return self._getEntries(self._getJobs())
    
    def _getSingleJobEntry(self, jobID):
        return self.getSingleItem(self.makeAPICall('jobs/%s' % jobID))
    
    def _getJobElems(self, elem, fallback='none'):
        return self._getElemFrom(self._getJobEntries(), elem, fallback)
    
    def _getSingleJobElem(self, elem, jobID):
        entry = self._getSingleJobEntry(jobID)
        return self._getSingleElemFrom(entry, elem)

    def _getJobInputs(self, jobID):
        return self._getEntries(self.makeAPICall('jobs/%s/inputs' % jobID))

    def _getSMRTCellInfo(self, jobID):
        inputs = self._getJobInputs(jobID)
        inputData = []
        for i in inputs:
            inputDict = {'SMRTCellPath'  : i.get('collectionPathUri'),
                         'PrimaryFolder' : i.get('primaryResultsFolder'),
                         'Context'       : 'none',
                         'LIMSCode'      : LIMSMapper.limsCodeFromCellPath(i.get('collectionPathUri'))
                         }
            inputData.append(inputDict)
        
        return inputData

    # Public interface methods
    def getJobIDs(self):
        return self._getJobElems('jobId')
        
    def singleJobExists(self, jobID):
        return self._getSingleJobEntry(jobID)

    # This is the main method that should be called from the ProjectHandler,
    # must be identical for different JobService instances (e.g. SMRT Portal, Martin, Disk, API, etc).
    def getModelJobInfo(self, jobID):
        jobEntry = self._getSingleJobEntry(jobID)
        return {'jobId'     : jobEntry.get('jobId'),
                'protocol'  : self.getModelProtocolInfo(jobEntry.get('protocolName')),
                'reference' : self.getModelReferenceInfo(jobEntry.get('referenceSequenceName')),
                'inputs'    : self._getSMRTCellInfo(jobID)
                }
        
    def getAvailableJobInfo(self, jobID):
        complement = self.getInstanceComplement(self.isAPI)
        return complement.getAvailableJobInfo(jobID)
        
    
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

#    def submitSecondaryJob(self, condition, job):
#        # Get or create the inputs
#        inputs = []
#        for c in job.cells.all:
#            pass
#        
#        # Save the inputs
#        
#        # Create the job
#        jobData = {'name'         : 'Milhouse%s_%s' % (condition.project.name, condition.name),
#                   'createdBy'    : 'MilhouseUser', 
#                   'description'  : 'Milhouse%s_%s %s' % (condition.project.name, condition.name, job.protocol.name),
#                   'protocolName' : job.protocol.protocolId,
#                   'groupNames'   : ['all'],
#                   'inputIds'     : inputs
#                   }
#        
#        # Save the job
#        
#        # Submit the job
        


####################################
###      JOB SERVICE DISK        ###
####################################

class SecondaryJobServiceDisk(SecondaryJobService):
    
    
    def __init__(self, server):
        super(SecondaryJobServiceDisk, self).__init__(server)    
        self.isAPI    = False
        self.isDisk   = True
        self.isMartin = False
    
    ## HELPER METHODS FOR DISK DATA ACCESS    
    def getJobPathFromID(self, jobID):
        jobID = self.normalizeJobID(jobID)
        jobPath = self.getJobDiskPath(self.server.jobDataPath, jobID)
        if os.path.isdir(jobPath):
            return jobPath
        else:
            msg = 'Unable to access job path for job ID [%s].  Attempted [%s]' % (jobID, jobPath)
            MU.logMsg(self, msg, 'warning')
    
    def getJobFile(self, jobID, filename, dataFile=False):
        jobPath = self.getJobPathFromID(jobID)
        if jobPath:
            jobfile = os.path.join(jobPath, 'data', filename) if dataFile else os.path.join(jobPath, filename)
            if os.path.isfile(jobfile):
                return jobfile
            else:
                msg = 'Unable to access job file [%s] for job [%s].  Attempted %s' % (filename, jobID, jobfile)
                MU.logMsg(self, msg, 'warning')

    def getSMRTCellInfoFromFofn(self, fofn):
        fofnLines = open(fofn, 'r').readlines()
        return [self.getSMRTCellInfoFromFullPath(x) for x in fofnLines]
        
    def getReferencePath(self, referenceName):
        refPath = os.path.join(self.server.referencePath, referenceName)
        if os.path.isdir(refPath):
            return refPath
        else:
            msg = 'Unable to access path for reference [%s]. Attempted %s' % (referenceName, refPath)
            MU.logMsg(self, msg, 'warning')
            
    def getReferenceFile(self, referenceName):
        refPath = self.getReferencePath(referenceName)
        if refPath:
            refFile = os.path.join(refPath, 'reference.info.xml')
            if os.path.isfile(refFile):
                return refFile
            else:
                msg = 'Unable to access file for reference [%s]. Attempted %s' % (referenceName, refFile)
                MU.logMsg(self, msg, 'warning')

    def getProtocolFile(self, protocolFile):
        protocolXML = os.path.join(self.server.protocolPath, protocolFile)
        if os.path.isfile(protocolXML):
            return protocolXML
        else:
            msg = 'Unable to access file for protocol [%s]. Attempted %s' % (protocolFile, protocolXML)
            MU.logMsg(self, msg, 'warning')
     
    def _getXMLParamValue(self, node):
        value = node.getElementsByTagName('value')
        if value:
            child = value.pop().firstChild
            if child:
                return child.data
        return None
    
    ###########################
    ##      HANDLE DATA      ##
    ###########################
    
    ## REFERENCES ##
    # Public interface methods
    def getReferenceNames(self):
        refDirs = glob.glob('%s/*' % self.server.referencePath)
        return [os.path.basename(r) for r in filter(lambda x: os.path.isdir(x), refDirs)]
    
    def getModelReferenceInfo(self, refName):
        refInfo = {'name'         : refName,
                   'lastModified' : 'unknown', 
                   'md5'          : 'unknown', 
                   'version'      : 'unknown'}
        if refName:
            referenceFile = self.getReferenceFile(refName)
            if referenceFile:
                parsedInfo = self.parseReferenceXML(referenceFile)
                for k,v in parsedInfo.iteritems():
                    if refInfo.has_key(k) and k != 'name':
                        refInfo[k] = v
        return refInfo
    
    def getAvailableReferenceInfo(self, refName):
        return self.getModelReferenceInfo(self, refName)
        
    
    
    ## PROTOCOLS
    # Public interface methods
    def getProtocolNames(self):
        protocolFiles = glob.glob('%s/*' % self.server.protocolPath)
        filteredFiles = filter(lambda x: os.path.isfile(x) and x.endswith('.xml'), protocolFiles)
        return [os.path.basename(x[:-4]) for x in filteredFiles]
    
    def getModelProtocolInfo(self, protocolName):
        protocolInfo = {'name'         : protocolName, 
                        'lastModified' : 'unknown', 
                        'version'      : 'unknown'}
        if protocolName:
            protocolFile = self.getProtocolFile('%s.xml' % protocolName)
            if protocolFile:
                parsedInfo = self.parseJobXML(protocolFile)
                for k,v in parsedInfo.iteritems():
                    if protocolInfo.has_key(k) and k != 'name':
                        protocolInfo[k] = v
        return protocolInfo
    
    def getSingleProtocolElem(self, protocolName, elem, fallback=None):
        return self.getModelProtocolInfo(protocolName).get(elem, fallback)
    
    def getAvailableProtocolInfo(self, protocolName):
        protocolXML = self.getProtocolFile('%s.xml' % protocolName)
        return self.parseJobXML(protocolXML)

    def protocolIsSplittable(self, protocolName):
        protocolInfo = self.getAvailableProtocolInfo(protocolName)
        if protocolInfo:
            moduleInfo = protocolInfo.get('modules')
            if moduleInfo:
                if moduleInfo.has_key('mapping'):
                    return True
        return False
        
    
    ## JOBS    
    def getJobIDs(self):
        return glob.glob('%s/*/*' % self.server.jobDataPath)

    def singleJobExists(self, jobID):
        return self.getSingleItem(self.getJobPathFromID(jobID))

    def getModelJobInfo(self, jobID):
        inputXML = self.getJobFile(jobID, 'input.xml')
        jobDict = {'jobId': jobID}
        if inputXML:
            inputData = self.parseInputXML(inputXML)
            jobDict['protocol']  = self.getModelProtocolInfo(inputData.get('SecondaryProtocol')),
            jobDict['reference'] = self.getModelReferenceInfo(inputData.get('SecondaryReference')),
            jobDict['inputs']    = [self.getSMRTCellInfoFromFullPath(x) for x in inputData.get('InputPaths')]
        else:
            inputFofn = self.getJobFile(jobID, 'input.fofn')
            jobXML    = self.getJobFile(jobID, 'settings.xml')
            
            if inputFofn:
                jobDict['inputs'] = self.getSMRTCellInfoFromFofn(inputFofn)
            if jobXML:
                parsedSettings = self.parseJobXML(jobXML)
                protocolName = self.getSingleItem(parsedSettings.get('protocol').keys())
                jobDict['protocol']  = self.getModelProtocolInfo(protocolName)
                
                refInfo = self.getSingleItem(parsedSettings.get('protocol').values())
                refName = os.path.basename(refInfo.get('reference'))
                jobDict['reference'] = self.getModelProtocolInfo(refName)
        
        #print 'RETURNING JOB INFO', jobDict
        return jobDict
    
    def getAvailableJobInfo(self, jobID):
        jobFile = self.getJobFile(jobID, 'settings.xml')
        return self.parseJobXML(jobFile)

            
    ## MAKE DICTIONARY WITH NAMES AND VALUES
    def makePropertyDict(self, props=('ReferenceNames', 'ProtocolNames')):
        propDict = {}
        if 'ReferenceNames' in props:
            propDict['ReferenceNames'] = self.getReferenceNames()
        if 'ProtocolNames' in props:
            propDict['ProtocolNames'] = self.getProtocolNames()
        return propDict


    
    ## FILE PARSING
    def parseInputXML(self, inputXML):
        dataDict = {}
        
        xmltree = MU.parseXML(inputXML)
        if xmltree:
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
                    cells = [l.firstChild.data for l in dataRef.getElementsByTagName('location')]
    #                    cellPaths = map(lambda x: os.path.basename(x), cells)
    #                    limsCodes = map(lambda x: '-'.join(LIMSMapper.limsCodeFromCellPath(x)), cellPaths)
                    
                    if paramsDict.get('referenceSequenceName'):
                        dataDict['SecondaryReference'] = paramsDict.get('referenceSequenceName')
                        
                    if paramsDict.get('protocolName'):
                        dataDict['SecondaryProtocol'] = paramsDict.get('protocolName')
    
                    if cells:
                        dataDict['InputPaths'] = cells
    
        return dataDict
    
        
    def parseReferenceXML(self, referenceXML):
        dataDict = {}
        xmltree = MU.parseXML(referenceXML)
        if xmltree:
            refInfo = xmltree.getElementsByTagName('reference_info')
            
            if refInfo:
                refInfo = refInfo.pop()
                dataDict['name']         = refInfo.getAttribute('id')
                dataDict['lastModified'] = refInfo.getAttribute('last_modified') 
                #dataDict['md5']          = 'unknown',#refInfo.getAttribute('')
                dataDict['version']      = refInfo.getAttribute('version')
                
        return dataDict
    
    def parseJobXML(self, jobXML):
        protocolDict = {}
        xmltree = MU.parseXML(jobXML)
        if xmltree:
            protocolInfo = xmltree.getElementsByTagName('protocol')
            moduleStageInfo   = xmltree.getElementsByTagName('moduleStage')
    
            if protocolInfo:
                elemAttr = 'name' if self.isMartin else 'id'
                protocolParams = {x.getAttribute(elemAttr): x.getElementsByTagName('param') for x in protocolInfo}
                if protocolParams:
                    protocolDict['protocol'] = {x: {e.getAttribute('name'): self._getXMLParamValue(e) for e in y} for x,y in protocolParams.iteritems()}
                
            if moduleStageInfo:
                moduleParams = {x.getAttribute('name'): x.getElementsByTagName('param') for x in moduleStageInfo}
                if moduleParams:
                    protocolDict['modules'] = {x: {e.getAttribute('name'): self._getXMLParamValue(e) for e in y} for x,y in moduleParams.iteritems()}
            
        return protocolDict
    

    