'''
Created on Feb 6, 2013

@author: dvillagra
'''

import os
import numpy as n
from django_code.models import SMRTCell, SecondaryAnalysisServer, SecondaryJob, Condition, Project
from django.forms.models import model_to_dict

from pycore.tools.Validators import ExperimentDefinitionValidator
from pycore import MUtils as MU
from pycore import MEnums as enums
from pycore.tools.LIMSHandler import LIMSMapper
from pycore.SecondaryJobHandler import SecondaryDataHandlerFactory

class ProjectFactory(object):
    
    def __init__(self, definition):
        self.validator  = ExperimentDefinitionValidator(definition)
        self.definition = self.validator.getExperimentDefinition() 

    def __str__(self):
        return self.definition
        
    def validateProjectDefinition(self):
        self.is_valid, self.valid_msg = self.validator.validateDefinition()
        
    def create(self):
        MU.logMsg(self, 'Validating project definition', 'info')
        self.validateProjectDefinition()
        MU.logMsg(self, 'Validation result: %s' % self.valid_msg, 'info')
        
        if not self.is_valid:
            print 'Invalid definition! %s' % self.valid_msg
        
        # If valid csv, start to populate database objects
        if self.is_valid:
            csv = self.definition
            csvType = self.validator.getDefinitionType()
            
            
            def createSecondaryJobs():
                
                secondaryJobs = []
                
                # If this is a new secondary job, populate the necessary database tables
                if csvType == 'newJob':
                    
                    uniqueJobs = n.unique(zip(csv['SecondaryServerName'], 
                                              csv['SecondaryProtocol'], 
                                              csv['SecondaryReference']))
                    print "UNIQUE JOBS\n%s\n" % str(uniqueJobs)
                    
                    for job in uniqueJobs:
                        msg = 'Creating SecondaryJob for job info: %s' % str(job)
                        MU.logMsg(self, msg, 'info')
                        
                        # First make the job, but don't save it
                        secondaryServer = SecondaryAnalysisServer.objects.get(serverName=job[0])
                        jobObj = SecondaryJob(protocol  = job[1],
                                              reference = job[2],
                                              server    = secondaryServer,
                                              status    = enums.getChoice(enums.SECONDARY_STATUS, 'INSTANTIATED') 
                                              )
                        jobObj.save()
                        
                        # Now add the cells
                        jobRows = csv[(csv['SecondaryServerName'] == job[0]) & \
                                      (csv['SecondaryProtocol']   == job[1]) & \
                                      (csv['SecondaryReference']  == job[2])]
                        
                        jobCells = n.unique(zip(jobRows['SMRTCellPath'], jobRows['PrimaryFolder']))
                        smrtCells = []
                        for c in jobCells:
                            path, primaryFolder = tuple(c)
                            msg = 'Creating or accessing SMRTCell for data path: %s' % os.path.join(path, primaryFolder)
                            MU.logMsg(self, msg, 'info')
                            if os.path.exists(path):
                                # This is a data path
                                cell, created = SMRTCell.objects.get_or_create(path=path, primaryFolder=primaryFolder)
                                smrtCells.append(cell)
                            else:
                                # this is a LIMS Code
                                dataPath = LIMSMapper(path).getDataPath()
                                cell, created = SMRTCell.objects.get_or_create(path=dataPath, primaryFolder=primaryFolder, limsCode=path)
                                smrtCells.append(cell)
                        
                        # Add the SMRT Cells
                        [jobObj.cells.add(x) for x in smrtCells]
                        
                        msg = 'Successfully created and saved SecondaryJob: %s' % str(model_to_dict(jobObj))                      
                        MU.logMsg(self, msg, 'info')
                        
                        secondaryJobs.append(jobObj)
                    
                    else:
                        # Job already exists
                        for job, serverName in zip(csv['SecondaryJobID'], csv['SecondaryServerName']):
                            server = SecondaryAnalysisServer.objects.get(serverName=serverName)
                            newJob, created = SecondaryJob.objects.get_or_create(jobID = job, server = server)
                            
                            # Add other job info in here if job was newly created...
                            if created:
                                sdh = SecondaryDataHandlerFactory(server, disk=True)
                                jobDict = sdh.getJobEntries(apiCall='jobs/%s' % newJob.jobID)
                                refSeq = jobDict[0].get('referenceSequenceName', 'unknown')
                                protocol = jobDict[0].get('protocolName', 'unknown')
                                
                                # Get the SMRT Cells and add them
                                
                            
                            
                            secondaryJobs.append(newJob)
                        
                    return secondaryJobs
                
                
                def createConditions():
                    conditions = []
                    
                    return conditions
                
                def createProject():
                    project = None
                    
                    return project
                
                
                jobs = createSecondaryJobs()
                conditions = createConditions()
                project = createProject()
                
                return {'SecondaryJobs' : jobs,
                        'Conditions'    : conditions,
                        'Project'       : project}
                
                