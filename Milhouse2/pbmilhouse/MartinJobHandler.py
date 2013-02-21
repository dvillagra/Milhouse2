'''
Created on Feb 7, 2013

@author: dvillagra
'''

from pycore.SecondaryJobHandler import SecondaryJobService

class MartinJobServiceFactory(object):
    
    @staticmethod
    def create(server, disk):
        if disk:
            return MartinJobServiceDisk(server)
        else:
            return MartinJobServiceAPI(server)

class MartinJobServiceAPI(SecondaryJobService):

    ## REFERENCES
    def getReferences(self):
        return self.makeAPICall('SMRTReferencesInfo')
    
    def getReferenceEntries(self):
        return self._getEntries(self.getReferences(), entryName='items')
    
    def getReferenceElem(self, elem, fallback='unknown'):
        return self._getElemFrom(self.getReferenceEntries(), elem, fallback)

    def getReferenceNames(self):
        return self.getReferenceElem('ref_id', 'none')
    
    def getReferenceEntriesBy(self, params):
        entries = self.getReferenceEntries()
        return self._filterEntriesBy(entries, params)
    
    def getSingleReferenceEntryBy(self, params):
        entries = self.getReferenceEntriesBy(params)
        return self.getSingleItem(entries)
    
    def getSingleReferenceElemBy(self, params, elem, fallback=None):
        entry = self.getSingleReferenceEntryBy(params)
        return entry.get(elem, fallback)
    
    
    
    ## PROTOCOLS
    def getProtocols(self):
        return self.makeAPICall('SMRTAnalysisList')    
    
    def getProtocolEntries(self):
        return self._getEntries(self.getProtocols(), entryName='items')
    
    def getProtocolElem(self, elem, fallback='unknown'):
        return self._getElemFrom(self.getProtocolEntries(), elem, fallback)

    def getProtocolNames(self):
        return self.getProtocolElem('analysis_name', 'none')
    
    def getProtocolEntriesBy(self, params):
        entries = self.getProtocolEntries()
        return self._filterEntriesBy(entries, params)
    
    def getSingleProtocolEntryBy(self, params):
        entries = self.getProtocolEntriesBy(params)
        return self.getSingleItem(entries)
    
    def getSingleProtocolElemBy(self, params, elem, fallback=None):
        entry = self.getSingleProtocolEntryBy(params)
        return entry.get(elem, fallback)
    
    ## JOBS
    # Don't use this it takes forever!
    def getJobs(self, params=None):
        return self.makeAPICall('SMRTAnalysisJobListAll', params)
    
    def getJobEntries(self):
        return self._getEntries(self.getJobs())
    
    def getSingleJobEntry(self, jobID):
        return self.getSingleItem(self.makeAPICall('SMRTAnalysisJobByJobId', {'job_id': jobID}))
    
    def getSingleJobXML(self, jobID):
        return self.getSingleItem(self.makeAPICall('SMRTAnalysisJobXMLByJobId', {'job_id': jobID}))

    def getJobElems(self, elem, fallback='none'):
        return self._getElemFrom(self.getJobEntries(), elem, fallback)
    
    def getSingleJobElem(self, elem, jobID):
        entry = self.getSingleJobEntry(jobID)
        return self._getSingleElemFrom(entry, elem)

    def getJobIDs(self):
        return self.getJobElems('job_id')
        
    def getSMRTCellInfo(self, jobID):
        return self.getSingleItem(self.makeAPICall('SMRTAnalysisInputXMLByJobId', {'job_id': jobID}))
    
    def getBasicJobInfo(self, jobID):
        jobEntry = self.getSingleJobEntry(jobID)
        jobXML   = self.getSingleJobXML(jobID)
        
        jobInfo = {'jobId'         : 'asdf',
                   'referenceName' : 'refname',
                   'protocolName'  : 'protocolName'                   
                   }
        
        return jobInfo


class MartinJobServiceDisk(SecondaryJobService):
    
    
    ## REFERENCES
    def getReferenceNames(self):
        pass
    
    ## PROTOCOLS
    def getProtocolNames(self):
        pass
    
    ## JOBS
    def getJobIDs(self):
        pass
    

#def parseMartinXML(tocXML, martinType):
#    dataDict = {}
#    try:
#        xmltree = parse(tocXML)
#        attrs = xmltree.firstChild.getElementsByTagName('attributes')[0]
#        attrs = xmltree.getElementsByTagName('toc')[0].getElementsByTagName('attributes')[0]
#        apParams = attrs.getElementsByTagName('apParameters')[0]
#
#        attrsDict = dict([(str(node.attributes['name'].value),str(node.firstChild.data).strip())
#                          for node in attrs.childNodes
#                          if node.nodeType != 3 and node.attributes['name'].value != 'advanced'])
#        apParamsDict = dict([(str(node.attributes['name'].value),str(node.firstChild.data))
#                             for node in apParams.childNodes
#                             if node.nodeType != 3])
#
#        dataDict['MartinStatus'] = parseMartinLog(int(attrsDict.get('Job ID', 0)), martinType).values()
#
#        if attrsDict and set(['Input', 'Primary Protocol']).issubset(attrsDict):
#            dataDict['RunCodes'] = [unicode('-'.join(k.split('/')[2:])) for k in attrsDict['Input'].split(',')]
#            dataDict['PrimaryFolder'] = attrsDict['Primary Protocol']
#
#        # Note: If LIMSTemplate was used to run this job then the original 
#        # refseq name will be erased and replaced with LIMSTemplate
#        if apParamsDict and 'global.reference' in apParamsDict:
#            dataDict['MartinRefSeq'] = apParamsDict['global.reference'].split('/')[-1]
#
#    except ExpatError:
#        msg = 'Attemtping to parse Martin\'s toc.xml failed'
#        logMsg('Mutils', msg, mode='info')
#        return dataDict
#
#    return dataDict

    
    