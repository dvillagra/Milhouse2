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
    def create(server, disk):
        if 'martin' in server.serverName.lower():
            # This is specific to PacBio only, do not set this to true for non-PacBio installs!!
            from pbmilhouse.MartinJobHandler import MartinDataHandlerFactory 
            return MartinDataHandlerFactory.create(server, disk)
        # All other Milhouse instance should go through this path
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

    def makePropertyDict(self):
        pass

class SecondaryDataHandlerAPI(SecondaryDataHandler):
    
    def _makeAPICall(self, apiCall, apiParams=None):
        conn = SecondaryServerConnector(self.server)
        return conn.makeRequest(urljoin(self.server.apiRootPath, apiCall))
    
    def _getElemDict(self, elems):
        return elems.get('rows', [])
        
    def _getElemFrom(self, elemDictList, getBy, fallback=None):
        return [r.get(getBy, fallback) for r in elemDictList]
    
    def _getSingleElemFrom(self, elemDict, getBy=None, fallback=None):
        if isinstance(elemDict, list) and len(elemDict) > 1:
            raise Exception('Expecting dictionary, got list: %s' % elemDict)
        elif not elemDict:
            raise Exception('Need dictionary to extract element, got nothing!')
        elif isinstance(elemDict, list) and len(elemDict) == 1:
            elemDict = elemDict[0]
        else:
            if getBy:
                return elemDict.get(getBy, fallback)
            else:
                return elemDict
        
    ## REFERENCES
    def getReferences(self, apiCall='reference-sequences', apiParams=None):
        return self._makeAPICall(apiCall, apiParams)
    
    def getReferenceEntries(self, apiCall='reference-sequences', apiParams=None):
        references = self.getReferences(apiCall, apiParams)
        elemDict = self._getElemDict(references)
        return self._getElemFrom(elemDict, 'referenceEntry')
            
    def getReferenceElem(self, elem, apiCall='references-sequences', apiParams=None, fallback='none'):
        return self._getElemFrom(self.getReferenceEntries(apiCall, apiParams), elem, fallback)    

    def getReferenceNames(self, apiCall='reference-sequences', apiParams=None):
        return self.getReferenceElem('name', apiCall, apiParams)
        

    ## PROTOCOLS
    def getProtocols(self, apiCall='protocols', apiParams=None):
        return self._makeAPICall(apiCall, apiParams)
        
    def getProtocolEntries(self, apiCall='protocols', apiParams=None):
        protocols = self.getProtocols(apiCall, apiParams)
        elemDict = self._getElemDict(protocols)
        return elemDict if elemDict else protocols
        
    def getProtocolElem(self, elem, apiCall='protocols', apiParams=None, fallback='none'):
        return self._getElemFrom(self.getProtocolEntries(apiCall, apiParams), elem, fallback)    
    
    def getProtocolNames(self, apiCall='protocols', apiParams=None):
        return self.getProtocolElem('name', apiCall, apiParams)
    
    
    ## JOBS
    
    # XXX I'm not sure how I feel about all of these different methods, it's starting to get messy
    # especially when you think about the separate Martin implementation and how that will return 
    # data in a different format
    
    def getJobs(self, apiCall='jobs', apiParams=None):
        return self._makeAPICall(apiCall, apiParams)
    
    def getJobEntries(self, apiCall='jobs', apiParams=None):
        jobs = self.getJobs(apiCall, apiParams)
        elemDict = self._getElemDict(jobs)
        return elemDict if elemDict else [jobs]
    
    def getSingleJobEntry(self, jobID, apiParams=None):
        return self._getSingleElemFrom(self.getJobs('jobs/%s' % jobID))
    
    def getJobElems(self, elem, apiCall='jobs', apiParams=None, fallback='none'):
        jobEntries = self.getJobEntries(apiCall, apiParams)
        return self._getElemFrom(jobEntries, elem, fallback)
    
    def getSingleJobElem(self, elem, jobID, apiParams=None):
        entries = self.getJobEntries('jobs/%s' % jobID, apiParams)
        return self._getSingleElemFrom(entries, elem)

    def getJobIDs(self, apiCall='jobs', apiParams=None):
        return self.getJobElems('jobId', apiCall, apiParams)
        
    def getSMRTCellInfo(self, jobID, apiParams=None):
        return self._getElemDict(self._makeAPICall('jobs/%s/inputs' % jobID))    
    
    # Generic methods for accessing job, reference, or protocol entries
    def getEntriesBy(self, entryType, params):
        typeMap = {'reference' : self.getReferenceEntries(),
                   'protocol'  : self.getProtocolEntries()}
        if entryType.lower().endswith('s'):
            entryType=entryType[:-1]
        entries = typeMap[entryType.lower()]
        return filter(lambda e: dict(filter(lambda (x,y): e[x]==y, params.iteritems())), entries)
    
    
    def getSingleEntryBy(self, entryType, params):
        entries = self.getEntriesBy(entryType, params)
        if len(entries) > 1:
            raise Exception('Multiple entries returned!: %s' % str(entries))
        elif len(entries) == 0:
            raise Exception('No entries found matching search parameters!')
        else:
            return entries[0]
    
    ## MAKE DICTIONARY WITH NAMES AND VALUES
    def makePropertyDict(self, props=('References', 'Protocols')):
        propDict = {}
        if 'References' in props:
            propDict['References'] = self.getReferenceNames()
        if 'Protocols' in props:
            propDict['Protocols'] = self.getProtocolNames()
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
                print 'toc xml', tocXML
                parsedXML = self.parseJobXML(tocXML)
                print 'PARSED XML IS: %s' % parsedXML
                return parsedXML.get(elem, 'unknown')
        except Exception as err:
            MU.logMsg(self, 'Unable to access job information from disk: %s' % err, 'info')


    def parseJobXML(self, tocXML):
        dataDict = {}
        print open(tocXML).read()
        try:
            xmltree = parse(tocXML)
            header = xmltree.firstChild.getElementsByTagName('header')
            if header:
                header = header.pop()
                jid = int(header.getAttribute('id'))
                job = header.getElementsByTagName('job')
                if jid and job:
                    job = job.pop()
                    paramsDict = {node.tagName: node.firstChild.data for node in job.childNodes if node.nodeType != 3 and node.firstChild}
                    
                    print 'PARAMS DICT: %s' % paramsDict
                    #dataDict['MartinStatus'] = parseMartinLog(mjid, 'smrtportal').values()
                    if paramsDict.get('referenceSequenceName'):
                        dataDict['SecondaryReference'] = paramsDict.get('referenceSequenceName')
                    if paramsDict.get('protocolName'):
                        dataDict['SecondaryProtocol'] = paramsDict.get('protocolName')
                            
        except ExpatError:
            msg = 'Attemtping to parse %s\'s toc.xml failed' % self.server.serverName
            MU.logMsg(self, msg, 'info')
            return dataDict
    
        return dataDict
    
    
    
        