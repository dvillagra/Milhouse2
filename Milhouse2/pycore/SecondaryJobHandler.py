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

class SecondaryServerConnectorError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class SecondaryDataHandlerError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

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
        
    
    def getSingleItem(self, items):
        if isinstance(items, list) and len(items) > 1:
            raise SecondaryDataHandlerError('Multiple entries returned!: %s' % str(items))
        elif not items:
            raise SecondaryDataHandlerError('No entries found matching search parameters!')
        elif isinstance(items, list) and len(items) == 1:
            return items[0]
        else:
            return items
            
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
    
    ## COMMON AND PRIVATE METHODS
    def makeAPICall(self, apiCall, apiParams=None):
        conn = SecondaryServerConnector(self.server)
        return conn.makeRequest(urljoin(self.server.apiRootPath, apiCall))
    
    def _getEntries(self, elems):
        return elems.get('rows', [])
        
    def _getElemFrom(self, entries, getBy, fallback=None):
        return [r.get(getBy, fallback) for r in entries]
    
    def _getSingleElemFrom(self, entry, getBy=None, fallback=None):
        entry = self.getSingleItem(entry)
        return entry.get(getBy, fallback)
    
    def _filterEntriesBy(self, entries, params):
        return filter(lambda e: dict(filter(lambda (x,y): e[x]==y, params.iteritems())), entries)
        
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
    
    def getSingleReferenceEntryBy(self, params):
        entries = self.getReferenceEntriesBy(params)
        return self.getSingleItem(entries)
        
    
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
    
    def getSingleProtocolEntryBy(self, params):
        entries = self.getProtocolEntriesBy(params)
        return self.getSingleItem(entries)
    
    
    
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
        
    def getSMRTCellInfo(self, jobID):
        return self._getEntries(self.makeAPICall('jobs/%s/inputs' % jobID))
    
    
    
    ## MAKE DICTIONARY WITH NAMES AND VALUES
    def makePropertyDict(self, props=('ReferenceNames', 'ProtocolNames')):
        propDict = {}
        if 'ReferenceNames' in props:
            propDict['ReferenceNames'] = self.getReferenceNames()
        if 'ProtocolNames' in props:
            propDict['ProtocolNames'] = self.getProtocolNames()
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
    
    
    
        