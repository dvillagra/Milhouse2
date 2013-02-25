'''
Created on Feb 6, 2013

@author: dvillagra
'''

import os
import numpy as n
from django_code.models import SMRTCell, SecondaryAnalysisServer, SecondaryJob, Condition, Project
from django.forms.models import model_to_dict
from django.utils import simplejson

from pycore.tools.Validators import ExperimentDefinitionValidator
from pycore import MUtils as MU
from pycore import MEnums as enums
from pycore.tools.LIMSHandler import LIMSMapper
from pycore.SecondaryJobHandler import SecondaryJobServiceFactory, SecondaryJobService


class ProjectError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ProjectFactory(object):        
    
    @staticmethod
    def validateProjectDefinition(definition):
        validator  = ExperimentDefinitionValidator(definition)
        definition = validator.getExperimentDefinition()
        isValid, validMsg = validator.validateDefinition()
        return (isValid, validMsg)
    
    @staticmethod
    def create(definition, projectDict=None):
        classString = 'ProjectFactoryCreate'
        MU.logMsg(classString, 'Submitting project definition for validation and object creation', 'info')
        
        validator  = ExperimentDefinitionValidator(definition)
        definition = validator.getExperimentDefinition()
        isValid, validMsg = validator.validateDefinition()
        
        MU.logMsg(classString, 'Project definition validation result: %s' % validMsg, 'info')
        
        if not isValid:
            msg = 'Invalid definition, cannot create project! %s' % validMsg
            MU.logMsg(classString, msg, 'error')
            raise ProjectError(msg)
        
        # If valid csv, start to populate database objects
        csv = definition
        csvType = validator.getDefinitionType()
                    
        def createProject(pDict):
            
            if pDict is None:
                pDict = {}
            
            projects = Project.objects.count()
            if projects:
                lastProject = Project.objects.all().order_by('-projectID')[0]           
                projectID   = lastProject.projectID + 1
            else:
                projectID = 1
            
            project = Project(projectID   = projectID,
                              name        = pDict.get('name', 'dummy'),
                              description = pDict.get('description', 'dummy'),
                              tags        = pDict.get('tags', None),
                              status      = pDict.get('status', enums.getChoice(enums.PROJECT_STATUS, 'INSTANTIATED')))
            
            project.save()
            
            return project

        def createSecondaryJobs():
            
            secondaryJobObjects = {}
            
            # Do it by condition
            conditions = n.unique(csv['Name'])
            newJobDefs = {}
            for cond in conditions:                       
                condRows = csv[csv['Name'] == cond]
                    
                # If this is a new secondary job, populate the necessary database tables
                if csvType == 'newJob':
                    
                    uniqueJobs = n.unique(zip(condRows['SecondaryServerName'], 
                                              condRows['SecondaryProtocol'], 
                                              condRows['SecondaryReference'])) 

                    for job in uniqueJobs:
                        msg = 'Creating SecondaryJob for job info: %s' % str(job)
                        MU.logMsg(classString, msg, 'info')
                        
                        # First make the job, but don't save it
                        secondaryServer    = SecondaryAnalysisServer.objects.get(serverName=job[0])
                        sjs = SecondaryJobServiceFactory.create(secondaryServer)
                        
                        protocolEntry  = sjs.getModelProtocolInfo(job[1])
                        referenceEntry = sjs.getModelReferenceInfo(job[2])
                        
                        jobDef = {'protocol'  : simplejson.dumps(protocolEntry),
                                  'reference' : simplejson.dumps(referenceEntry),
                                  'server'    : secondaryServer}
                        
                        # Now add the cells
                        jobRows = condRows[(condRows['SecondaryServerName'] == job[0]) & \
                                           (condRows['SecondaryProtocol']   == job[1]) & \
                                           (condRows['SecondaryReference']  == job[2])]
                        
                        jobCells = n.unique(zip(jobRows['SMRTCellPath'], jobRows['PrimaryFolder']))
                        smrtCells = []
                        for c in jobCells:
                            path, primaryFolder = tuple(c)
                            msg = 'Creating or accessing SMRTCell for data path: %s' % os.path.join(path, primaryFolder)
                            MU.logMsg(classString, msg, 'info')
                            if os.path.exists(path):
                                # This is a data path
                                limsCode = LIMSMapper.limsCodeFromCellPath(path)
                                cell = SMRTCell.objects.get_or_create(path=path, primaryFolder=primaryFolder, limsCode=limsCode)
                                smrtCells.append(cell[0])
                            else:
                                # this is a LIMS Code
                                dataPath = LIMSMapper.cellPathFromLimsCode(path)
                                cell = SMRTCell.objects.get_or_create(path=dataPath, primaryFolder=primaryFolder, limsCode=path)
                                smrtCells.append(cell[0])
                        
                        # Add the SMRT Cells
                        jobDef['cells'] = smrtCells
                        hasJob = False
                        for pk, jd in newJobDefs.iteritems():
                            if jobDef == jd:
                                hasJob = True
                                jobObj = SecondaryJob.objects.get(id=pk)
                        
                        if not hasJob:
                            cells = jobDef.pop('cells')
                            jobObj = SecondaryJob(**jobDef)
                            jobObj.save()
                            jobObj.cells.add(*cells)
                            jobDef['cells'] = cells
                            newJobDefs[jobObj.id] = jobDef

                        msg = 'Successfully created and saved SecondaryJob: %s' % str(model_to_dict(jobObj))                      
                        MU.logMsg(classString, msg, 'info')
                        
                        # Link secondary job to condition
                        if not secondaryJobObjects.has_key(cond):
                            secondaryJobObjects[cond] = [jobObj]
                        else:
                            secondaryJobObjects[cond].append(jobObj)

                        
                else:
                    # Job already exists
                    for job, serverName in zip(condRows['SecondaryJobID'], condRows['SecondaryServerName']):
                        server = SecondaryAnalysisServer.objects.get(serverName=serverName)
                        newJob, created = SecondaryJob.objects.get_or_create(jobID = job, server = server)
                        
                        # Add other job info in here if job was newly created...
                        if True:#created:
                            sjs = SecondaryJobServiceFactory.create(server)
                            jobID = newJob.jobID
                            jobInfo  = sjs.getModelJobInfo(jobID)
                            
                            # Add protocol and reference info     
                            protocol  = SecondaryJobService.getSingleItem(jobInfo.get('protocol', {'name' : 'unknown'}))
                            reference = SecondaryJobService.getSingleItem(jobInfo.get('reference', {'name' : 'unknown'}))
                            newJob.protocol  = simplejson.dumps(protocol)
                            newJob.reference = simplejson.dumps(reference)
                                
                            newJob.save()
                            
                            # Get the SMRT Cells
                            smrtCells = jobInfo.get('inputs', [])
                            smrtCellObjs = []
                            for c in smrtCells: 
                                cell = SMRTCell.objects.get_or_create(path          = c['SMRTCellPath'],
                                                                      primaryFolder = c['PrimaryFolder'],
                                                                      limsCode      = c['LIMSCode'])
                                smrtCellObjs.append(cell[0])
                        
                            # Now add the SMRT Cells to the new job
                            [newJob.cells.add(x) for x in smrtCellObjs]
                            
                        # Link secondary job to condition
                        if not secondaryJobObjects.has_key(cond):
                            secondaryJobObjects[cond] = [newJob]
                        else:
                            secondaryJobObjects[cond].append(newJob)

            return secondaryJobObjects
            
            
        def createConditions(secondaryJobs, project):
            
            conditionObjects = []
            for cond, jobs in secondaryJobs.iteritems():
                condRows = csv[csv['Name'] == cond]
                
                extraCols = filter(lambda x: x.startswith('p_'), condRows.dtype.names)
                extrasDict = {}
                for col in extraCols:
                    extrasDict[col] = list(n.unique(condRows[col]))                        
                extrasJSON = simplejson.dumps(extrasDict)
                
                extractBy = ['( %s )' % e for e in n.unique(condRows['ExtractBy'])]
                extractByString = ' | '.join(extractBy)
                
                condObj = Condition(name       = cond, 
                                    extractBy  = extractByString,
                                    extrasDict = extrasJSON,
                                    project    = project,
                                    status     = enums.getChoice(enums.CONDITION_STATUS, 'INSTANTIATED'))
                
                condObj.save()
                
                # Add secondary jobs to condition object
                condObj.secondaryJob.add(*jobs)
                
                conditionObjects.append(condObj)
                
            return conditionObjects
        
                            
        project = createProject(projectDict)
        jobs = createSecondaryJobs()
        conditions = createConditions(jobs, project)
        
        return {'SecondaryJobs' : jobs,
                'Conditions'    : conditions,
                'Project'       : project}

                