'''
Created on Feb 7, 2013

@author: dvillagra
'''

import os
import re

import django.utils.simplejson as json
from pycore.SecondaryJobHandler import SecondaryJobServiceAPI, SecondaryJobServiceDisk, SecondaryServerConnector
from pycore import MUtils as MU

####################################
###      JOB SERVICE FACTORY     ###
####################################

class MartinJobServiceFactory(object):
    
    @staticmethod
    def create(server, disk=None):
        if disk is None:
            if server.serverHost and server.serverPort:
                    mjsApi = MartinJobServiceAPI(server)
                    ping, msg = mjsApi.testConnection()
                    if ping:
                        logmsg = 'Using Server API Instance, Web Service Ping: %s' % msg
                        MU.logMsg('MartinJobServiceFactory', logmsg, 'info')
                        disk = False
                    else:
                        logmsg = 'Using Server Disk Instance, Web Service Ping: %s' % msg
                        MU.logMsg('MartinJobServiceFactory', logmsg, 'info')
                        disk = True
            else:
                disk = True
                
        if disk:
            return MartinJobServiceDisk(server)
        else:
            return MartinJobServiceAPI(server)


####################################
###      JOB SERVICE API         ###
####################################

class MartinJobServiceAPI(SecondaryJobServiceAPI):
        
    def __init__(self, server):
        super(MartinJobServiceAPI, self).__init__(server)
        self.isMartin = True

    def testConnection(self):
        ping = self.makeAPICall('SMRTProjectList')
        if ping.get('items'):
            return (True, '%s web service is alive!' % self.server.serverName)
        else:
            return (False, '%s web service is not responding' % self.server.serverName)
    
    ## REFERENCES
    
    # Private methods
    def _getReferences(self):
        # This call is way too slow - should really never be used.  Perhaps it can be cached?
        return self.makeAPICall('SMRTReferencesInfo')
    
    def _getReferenceEntries(self):
        # This calls getReferences, too slow!  
        return self._getEntries(self._getReferences(), entryName='items')
    
    def _getReferenceElem(self, elem, fallback='unknown'):
        # This is also too slow
        return self._getElemFrom(self._getReferenceEntries(), elem, fallback)
    
    def _getReferenceEntriesBy(self, params):
        entries = self._getReferenceEntries()
        return self._filterEntriesBy(entries, params)
    
    def _getSingleReferenceEntry(self, refName):
        entries = self._getReferenceEntriesBy({'ref_id': refName})
        return self.getSingleItem(entries)
    
    def _getSingleReferenceElem(self, refName, elem, fallback=None):
        entry = self._getSingleReferenceEntry(refName)
        return entry.get(elem, fallback)
    
    # Public interface methods
    def getReferenceNames(self):
        # THIS IS TOO SLOW!! Use the disk
        #return self.getReferenceElem('ref_id', 'none')
        # Is it bad to use the instance complement??
        complement = self.getInstanceComplement(self.isAPI)
        return complement.getReferenceNames()

    def getModelReferenceInfo(self, refName):
        complement = self.getInstanceComplement(self.isAPI)
        return complement.getModelReferenceInfo(refName)
#        return {'name'         : refName,
#                'lastModified' : 'unknown',
#                'md5'          : 'unknown'
#                }

    def getAvailableReferenceInfo(self, refName):
        return self.getModelReferenceInfo(self, refName)
    
    
    ## PROTOCOLS
    
    # Private protocol access methods
    def _getProtocols(self):
        return self.makeAPICall('SMRTAnalysisList')    
    
    def _getProtocolEntries(self):
        return self._getEntries(self._getProtocols(), entryName='items')
    
    def _getProtocolElem(self, elem, fallback='unknown'):
        return self._getElemFrom(self._getProtocolEntries(), elem, fallback)
    
    def _getProtocolEntriesBy(self, params):
        entries = self._getProtocolEntries()
        return self._filterEntriesBy(entries, params)
    
    def _getSingleProtocolEntry(self, protocolName):
        entries = self._getProtocolEntriesBy({'analysis_name': protocolName})
        return self.getSingleItem(entries)
    
    def _getSingleProtocolElem(self, protocolName, elem, fallback=None):
        entry = self._getSingleProtocolEntry(protocolName)
        return entry.get(elem, fallback)
    
    # Public interface methods
    def getProtocolNames(self):
        return self._getProtocolElem('analysis_name', 'none')

    def getModelProtocolInfo(self, protocolName):
        complement = self.getInstanceComplement(self.isAPI)
        return complement.getModelProtocolInfo(protocolName)
#        return {'name'         : protocolName,
#                'lastModified' : 'unknown'
#                }

    def protocolIsSplittable(self, protocolName):
        complement  = self.getInstanceComplement(self.isAPI)
        return complement.protocolIsSplittable(protocolName)
    
    def getAvailableProtocolInfo(self, protocolName):
        complement  = self.getInstanceComplement(self.isAPI)        
        return complement.getAvailableProtocolInfo(protocolName)
        

    ## JOBS
    # Private methods
    
    # Don't use this it takes forever!
    def _getJobs(self, params=None):
        return self.makeAPICall('SMRTAnalysisJobListAll', params)
    
    def _getJobEntries(self):
        return self._getEntries(self._getJobs())
    
    def _getSingleJobEntry(self, jobID):
        entry = self._getEntries(self.makeAPICall('SMRTAnalysisJobByJobId?job_id=%s' % jobID), 'items')
        return self.getSingleItem(entry)
    
    def _getSingleJobXML(self, jobID):
        return self.makeAPICall('SMRTAnalysisJobXMLByJobId?job_id=%s' % jobID)

    def _getJobElems(self, elem, fallback='none'):
        return self._getElemFrom(self._getJobEntries(), elem, fallback)
    
    def _getSingleJobElem(self, elem, jobID):
        entry = self._getSingleJobEntry(jobID)
        return self._getSingleElemFrom(entry, elem)

    def _getSMRTCellInfo(self, jobID):
        return self.makeAPICall('SMRTAnalysisInputXMLByJobId?job_id=%s' % jobID)

    # Public interface methods
    def getJobIDs(self):
        return self._getJobElems('job_id')
            
    def singleJobExists(self, jobID):
        return self._getSingleJobEntry(jobID)

    def getModelJobInfo(self, jobID):

        jobEntry     = self._getSingleJobEntry(jobID)
        complement   = self.getInstanceComplement(self.isAPI)
        protocolName = jobEntry.get('analysis_name')
        jobFile      = complement.getJobFile(jobID, 'job_%s.xml' % self.normalizeJobID(jobID))
        jobXML       = complement.parseJobXML(jobFile)
        inputFofn    = complement.getJobFile(jobID, 'input.fofn')
        inputs       = complement.getSMRTCellInfoFromFofn(inputFofn)
        
        jobInfo = {'jobId'     : jobID,
                   'protocol'  : self.getModelProtocolInfo(protocolName),
                   'reference' : self.getModelReferenceInfo(jobXML.get('referenceName')),
                   'inputs'    : inputs
                   }
        
        return jobInfo
    
    def getAvailableJobInfo(self, jobID):
        complement   = self.getInstanceComplement(self.isAPI)
        return complement.getAvailableJobInfo(jobID)

    
    def makePropertyDict(self, props=('ReferenceNames', 'ProtocolNames')):
        propDict = {}
        if 'ReferenceNames' in props:
            propDict['ReferenceNames'] = self.getReferenceNames()
        if 'ProtocolNames' in props:
            propDict['ProtocolNames'] = self.getProtocolNames()
        return propDict
    
    
    #### JOB SUBMISSION ####
    def _modelToSubmissionDict(self, job, projID):
        runby = job.runBy.name if job.runBy else 'unknown'
        jobDict = {'job_name'      : 'MilhouseID_JobID:%s_%s' % (projID, job.id),
                   'job_comment'   : 'User:%s' % runby,
                   'run_codes'     : [x.limsCode for x in job.cells.all()],
                   'primaryFolder' : self.getSingleItem(set([x.primaryFolder for x in job.cells.all()])),
                   'analysis_name' : job.protocol.get('name'),
                   'ref_id'        : job.reference.get('name'),
                   'option_id'     : -1,
                   'multiSubmit'   : 0 
                   }
        return jobDict
        
    def submitSingleJob(self, job, projID='None'):
        MU.logMsg(self, 'Attempting to submit milhouse secondary job %s to Martin server' % job.id, 'info')
        
        jobData = self._modelToSubmissionDict(job, projID)
        ref = job.reference.get('name')
        jobData['useLIMST'] = True if 'limstemplate' in ref.lower() else False
        params = {'job_data': json.dumps(jobData)}
        
        # Submit the job
        conn = SecondaryServerConnector(self.server)
        resp = conn.makeRequest('/JobService/submit', 'POST', params)

        if not resp.get('success') == False:
            msg = 'Martin: %s, Time: %s' % (resp.get('status'), resp.get('submit_datetime'))
            jobID = resp['job_id']
            MU.logMsg(self, msg, mode='info')
            
            MU.logMsg(self, 'Saving Martin Job ID: %s' % jobID, 'info')
            job.jobID = jobID
            job.save()
            return jobID
    
        elif filter(lambda x: re.findall('job submitted fail', x), resp.get('status')):
            msg = 'Martin Error: %s' % resp.get('status')
            MU.logMsg(self, msg, mode='error')
            
        else:
            MU.logMsg(self, 'Job Submission Failed', 'error')
        

    def resubmitSingleJob(self, job):
        MU.logMsg(self, 'Attempting to re-submit Martin job %s' % job.jobID, 'info')
        
        jobData = {'tSelectedJob', str(job.jobID)}
        params = {'job_data': json.dumps(jobData)}
        
        # Submit the job
        conn = SecondaryServerConnector(self.server)
        resp = conn.makeRequest('/resubmitJob', 'POST', params)

        if not resp.get('success') == False:
            MU.logMsg(self, 'Resubmitting Martin Job %s' % job.jobID, mode='info')
            return job.jobID
        
        else:
            MU.logMsg(self, 'Job Re-Submission Failed: %s' % resp.get('errorMsg'), 'error')

####################################
###      JOB SERVICE DISK        ###
####################################

class MartinJobServiceDisk(SecondaryJobServiceDisk):
    
    def __init__(self, server):
        super(MartinJobServiceDisk, self).__init__(server)
        self.isMartin = True
    
    ## NOTE: Many interface methods are inhereted from the superclass ##
       
    ## REFERENCES
    # All reference methods are inhereted from the super class
    
    ## PROTOCOLS
    def getModelProtocolInfo(self, protocolName):
        return {'name'         : protocolName,
                'lastModified' : 'unknown',
                'version'      : 'unknown'}
        
    def protocolIsSplittable(self, protocolName):
        protocolInfo = self.getAvailableProtocolInfo(protocolName)
        if protocolInfo:
            moduleInfo = protocolInfo.get('modules')
            if moduleInfo:
                mappingInfo = moduleInfo.get('mapping')
                if mappingInfo:
                    return mappingInfo.get('pbcmph5', False)
        return False

    
    ## JOBS    
    def getModelJobInfo(self, jobID):
        jobDict = {'jobId': jobID}
        inputFofn = self.getJobFile(jobID, 'input.fofn')
        
        if inputFofn:
            jobDict['inputs'] = self.getSMRTCellInfoFromFofn(inputFofn)
        
        jobXML = self.getJobFile(jobID, 'job_%s.xml' % self.normalizeJobID(jobID))
        if jobXML:
            jobData = self.parseJobXML(jobXML)
            protocolInfo = self.getSingleItem(jobData.get('protocol').values())
            refName = os.path.basename(protocolInfo.get('reference'))
            jobDict['reference'] = self.getModelReferenceInfo(refName)

        complement = self.getInstanceComplement(self.isAPI)
        if complement.testConnection()[0]:
            protocolName = complement._getSingleJobEntry(jobID).get('analysis_name')
        else:
            #tocXML = self.getJobFile(jobID, 'toc.xml')
            #parsedToc = self.parseTocXML(tocXML)
            protocolName = 'unknown'
        jobDict['protocol']  = self.getModelProtocolInfo(protocolName)
        
        #print 'RETURNING JOB INFO', jobDict
        return jobDict
    
    def getAvailableJobInfo(self, jobID):
        jobFile = self.getJobFile(jobID, 'job_%s.xml' % self.normalizeJobID(jobID))
        return self.parseJobXML(jobFile)
        
    
    def parseTocXML(self, tocXML):
        # Try not to use this - it will soon be deprecated
        pass
    
    
        