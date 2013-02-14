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


# Consider implementing a factory pattern here, where a disk-implementation would also work 
# if no server host or server port were supplied


class SecondaryServerConnector(object):
    
    def __init__(self, server):
        self.server = server
        
    def _getConnection(self):
        return httplib.HTTPConnection(self.server.serverHost, int(self.server.serverPort), timeout=15)
    
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
            return self._makeResponse({'Success': 'False', 'ErrorMsg': msg}, responseAsDict)
        
        resp = conn.getresponse()
        if resp.status != httplib.OK:
            msg = 'Server Error Code: %d, Server error reason: %s' % (resp.status, resp.reason)
            conn.close()
            MU.logMsg(self, msg, 'error')
            return self._makeResponse({'Success': 'False', 'ErrorMsg': msg}, responseAsDict)
        
        else:  
            MU.logMsg(self, 'Successfully completed server request', 'info')             
            respDict = json.loads(resp.read())
            conn.close()
            MU.logMsg(self, 'Request returned: %s' % respDict, 'debug')
            return self._makeResponse(respDict, responseAsDict)
        


class SecondaryDataHandlerFactory(object):
    
    @staticmethod
    def create(server, disk, isPBMartin=False):
        if isPBMartin:
            # This is specific to PacBio only, do not set this to true for non-PacBio installs!!
            from pbmilhouse.MartinJobHandler import MartinDataHandlerFactory 
            return MartinDataHandlerFactory(server, disk)
        if disk:
            return SecondaryDataHandlerDisk(server)
        else:
            return SecondaryDataHandlerAPI(server)
        
#    @staticmethod
#    def tryAllMethods(server, func):
#        try:
#            SecondaryDataHandlerFactory.create(server, True)



class SecondaryDataHandler(object):
    
    def __init__(self, server):
        self.server  = server
        
    def getReferenceElem(self):
        pass
    
    def getReferenceNames(self):
        pass
    
    def getProtocolElem(self):
        pass
    
    def getProtocolNames(self):
        pass
    
    def getJobElem(self):
        pass
    
    def getJobIDs(self):
        pass

class SecondaryDataHandlerAPI(SecondaryDataHandler):
    
    def _makeAPICall(self, apiCall, apiParams=None):
        conn = SecondaryServerConnector(self.server)
        return conn.makeRequest(urljoin(self.server.apiRootPath, apiCall))
    
    def _getElemDict(self, elems):
        return elems.get('rows', [])
        
    def _getElemFrom(self, elemDict, getBy, fallback=None):
        return [r.get(getBy, fallback) for r in elemDict]
    
    ## REFERENCES
    def getReferences(self, apiCall='reference-sequences', apiParams=None):
        return self._makeAPICall(apiCall, apiParams)
    
    def getReferenceEntries(self, apiCall='reference-sequences', apiParams=None):
        refRows = self._getElemDict(self.getReferences(apiCall, apiParams))
        return self._getElemFrom(refRows, 'referenceEntry')
            
    def getReferenceElem(self, elem, apiCall='references', apiParams=None, fallback='none'):
        return self._getElemFrom(self.getProtocolEntries(apiCall, apiParams), elem, fallback)    

    def getReferenceNames(self, apiCall='reference-sequences', apiParams=None):
        return self._getReferenceElem('name', apiCall, apiParams)
        

    ## PROTOCOLS
    def getProtocols(self, apiCall='protocols', apiParams=None):
        return self._makeAPICall(apiCall, apiParams)
        
    def getProtocolEntries(self, apiCall='protocols', apiParams=None):
        return self._getElemDict(self.getProtocols(apiCall, apiParams))
        
    def getProtocolElem(self, elem, apiCall='protocols', apiParams=None, fallback='none'):
        return self._getElemFrom(self.getProtocolEntries(apiCall, apiParams), elem, fallback)    
    
    def getProtocolNames(self, apiCall='protocols', apiParams=None):
        return self._getProtocolElem('name', apiCall, apiParams)
    
    
    ## JOBS
    def getJobs(self, apiCall='jobs', apiParams=None):
        return self._makeAPICall(apiCall, apiParams)
    
    def getJobEntries(self, apiCall='jobs', apiParams=None):
        return self._getElemDict(self.getJobs(apiCall, apiParams))
    
    def getJobElem(self, elem, apiCall='jobs', apiParams=None, fallback='none'):
        return self._getElemFrom(self.getJobEntries(apiCall, apiParams), elem, fallback)
    
    def getJobIDs(self, apiCall='jobs', apiParams=None):
        return self._getJobElem('jobId', apiCall, apiParams)
    
    
    ## MAKE DICTIONARY WITH NAMES AND VALUES
    def makePropertyDict(self, props=('References', 'Protocols', 'Jobs')):
        propDict = {}
        if 'References' in props:
            propDict['References'] = self.getReferenceNames()
        if 'Protocols' in props:
            propDict['Protocols'] = self.getProtocolNames()
        if 'Jobs' in props:
            propDict['Jobs'] = self.getJobIDs()
        return propDict
    
    
class SecondaryDataHandlerDisk(SecondaryDataHandler):
    
    def getJobIDs(self):
        return glob.glob('%s/*/*' % self.server.jobDataPath)

    def getSMRTCellInfo(self, jobID):
        jobID = MU.normalizeJobID(jobID)
        jobPath = MU.getJobDiskPath(self.server.jobDataPath, jobID)
        inFofn = os.path.join(jobPath, 'input.fofn')
        if os.path.isfile(inFofn):
            fofnLines = open(inFofn, 'r').readlines()
            return [MU.cellInfoFromFofnLine(x) for x in fofnLines]
        
    
    def getReferenceElem(self):
        pass
    
    def getReferenceNames(self):
        pass
    
    def getProtocolElem(self):
        pass
    
    def getProtocolNames(self):
        pass
    
    def getJobElem(self, jobID, elem):
        try:
            jobID = MU.normalizeJobID(jobID)
            jobPath = MU.getJobDiskPath(self.server.jobDataPath, jobID)
            cellInfoElems = ['SMRTCellPath', 'PrimaryFolder', 'Context', 'LIMSCode']
            if elem in cellInfoElems:
                return self.getSMRTCellInfo(jobID).get(elem)
            else:
                tocXML = os.path.join(jobPath, 'toc.xml')
                parsedXML = self.parseJobXML(tocXML)
                return parsedXML.get(elem, [])
        except Exception as err:
            MU.logMsg(self, 'Unable to access job information from disk: %s' % err, 'info')


    def parseJobXML(self, tocXML):
        dataDict = {}
        try:
            xmltree = parse(tocXML)
            header = xmltree.firstChild.getElementsByTagName('header')
            dataRef = xmltree.firstChild.getElementsByTagName('dataReferences')
            if header and dataRef:
                header = header.pop()
                dataRef = dataRef.pop()
                mjid = int(header.getAttribute('id'))
                job = header.getElementsByTagName('job')
                primFolder = dataRef.getElementsByTagName('tag')
                if mjid and job and primFolder:
                    job = job.pop()
                    primFolder = primFolder.pop()
                    paramsDict = {node.tagName: node.firstChild.data for node in job.childNodes if node.nodeType != 3 and node.firstChild}
    
                    #dataDict['MartinStatus'] = parseMartinLog(mjid, 'smrtportal').values()
    
                    if paramsDict.get('referenceSequenceName'):
                        dataDict['SecondaryReference'] = paramsDict.get('referenceSequenceName')
    
                    if paramsDict.get('protocolName'):
                        dataDict['SecondaryProtocol'] = paramsDict.get('protocolName')
    
                    if primFolder.firstChild:
                        dataDict['PrimaryFolder'] = primFolder.firstChild.data
                        
        except ExpatError:
            msg = 'Attemtping to parse %s\'s toc.xml failed' % self.server.serverName
            MU.logMsg(self, msg, 'info')
            return dataDict
    
        return dataDict
    
    
    
        