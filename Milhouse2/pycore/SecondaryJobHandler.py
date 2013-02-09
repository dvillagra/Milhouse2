'''
Created on Feb 6, 2013

@author: dvillagra
'''

import urllib
import httplib
import socket

from urlparse import urljoin

#import time
import django.utils.simplejson as json
import pycore.MUtils as MU



# Consider implementation a factory pattern here, where a disk-implementation would also work 
# if no server host or server port were supplied


class SecondaryServerConnector(object):
    
    def __init__(self, server):
        self.server = server
        
    def _getConnection(self):
        return httplib.HTTPConnection(self.server.serverHost, self.server.serverPort, timeout=15)
    
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
        


class SecondaryDataHandler(object):
    
    def __init__(self, server, tryDisk = True):
        self.server  = server
        self.tryDisk = tryDisk
        
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
    
    def getReferenceEntries(self):
        refRows = self._getElemDict(self.getReferences())
        return self._getElemFrom(refRows, 'referenceEntry')
            
    def getReferenceNames(self):
        return self._getElemFrom(self.getReferenceEntries(), 'name', 'none')
        

    ## PROTOCOLS
    def getProtocols(self, apiCall='protocols', apiParams=None):
        return self._makeAPICall(apiCall, apiParams)
        
    def getProtocolEntries(self):
        return self._getElemDict(self.getProtocols())
        
    def getProtocolNames(self):
        return self._getElemFrom(self.getProtocolEntries(), 'name', 'none')
    
    
    ## JOBS
    def getJobs(self, apiCall='jobs', apiParams=None):
        return self._makeAPICall(apiCall, apiParams)
    
    def getJobEntries(self):
        return self._getElemDict(self.getJobs())
    
    def getJobIDs(self):
        return self._getElemFrom(self.getProtocolEntries(), 'jobId', 'none')
    
    
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
    
    
        
    
    
    
    
        