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
from pycore.SecondaryJobHandler import SecondaryDataHandlerFactory

class ProjectFactory(object):
    
    @staticmethod
    def validateProjectDefinition(definition):
        validator  = ExperimentDefinitionValidator(definition)
        definition = validator.getExperimentDefinition()
        isValid, validMsg = validator.validateDefinition()
        return (isValid, validMsg)
    
    @staticmethod
    def create(definition):
        classString = 'ProjectFactoryCreate'
        MU.logMsg(classString, 'Submitting project definition for validation and object creation', 'info')
        
        validator  = ExperimentDefinitionValidator(definition)
        definition = validator.getExperimentDefinition()
        isValid, validMsg = validator.validateDefinition()
        
        MU.logMsg(classString, 'Project definition validation result: %s' % validMsg, 'info')
        
        if not isValid:
            print 'Invalid definition! %s' % validMsg
        

        secondaryJobObjects = {}
        conditionObjects    = []
        projectObject       = None
        
        
        # If valid csv, start to populate database objects
        if isValid:
            csv = definition
            csvType = validator.getDefinitionType()
                        
            def createSecondaryJobs():
                
                # Do it by condition
                conditions = n.unique(csv['Name'])
                newJobDefs = {}
                for cond in conditions:                       
                    condRows = csv[csv['Name'] == cond]                        
                        
                    # If this is a new secondary job, populate the necessary database tables
                    if csvType == 'newJob':
                        
                        print 'Creating secondary jobs for condition: %s' % cond
                        
                        uniqueJobs = n.unique(zip(condRows['SecondaryServerName'], 
                                                  condRows['SecondaryProtocol'], 
                                                  condRows['SecondaryReference']))

                        for job in uniqueJobs:
                            msg = 'Creating SecondaryJob for job info: %s' % str(job)
                            MU.logMsg(classString, msg, 'info')
                            
                            # First make the job, but don't save it
                            secondaryServer    = SecondaryAnalysisServer.objects.get(serverName=job[0])
                            sdh = SecondaryDataHandlerFactory.create(secondaryServer, disk=False)
                            
                            secondaryProtocol  = sdh.getSingleEntryBy('protocol', {'name' : job[1]})
                            secondaryReference = sdh.getSingleEntryBy('reference', {'name' : job[2]})
                            protocolEntry = {'name': secondaryProtocol.get('name', 'unknown'), 
                                             'lastModified': secondaryProtocol.get('whenModified')}
                            referenceEntry = {'name': secondaryReference.get('name', 'unknown'), 
                                             'lastModified': secondaryReference.get('last_modified')}
                                                        
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
                                    cell = SMRTCell.objects.get_or_create(path=path, primaryFolder=primaryFolder)
                                    smrtCells.append(cell[0])
                                else:
                                    # this is a LIMS Code
                                    dataPath = LIMSMapper(path).getDataPath()
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
                            if created:
                                sdh = SecondaryDataHandlerFactory.create(server, disk=False)
                                jobID = newJob.jobID
                                jobEntry = sdh.getSingleJobEntry(jobID)
                                
                                # Add protocol info                 
                                protocol = jobEntry.get('protocolName')                             
                                secondaryProtocol  = sdh.getSingleEntryBy('protocol', {'id' : protocol})
                                protocolEntry = {'name': secondaryProtocol.get('name', 'unknown'), 
                                                 'lastModified': secondaryProtocol.get('whenModified')}
                                
                                newJob.protocol  = simplejson.dumps(protocolEntry)
                                
                                # Add reference info
                                refSeq = jobEntry.get('referenceSequenceName')
                                secondaryReference = sdh.getSingleEntryBy('reference', {'name' : refSeq})
                                referenceEntry = {'name': secondaryReference.get('name', 'unknown'), 
                                                 'lastModified': secondaryReference.get('last_modified')}
                                newJob.reference = simplejson.dumps(referenceEntry)
                                    
                                newJob.save()
                                
                                # Get the SMRT Cells
                                smrtCells = sdh.getSMRTCellInfo(jobID)
                                smrtCellObjs = []
                                for c in smrtCells: 
                                    cell = SMRTCell.objects.get_or_create(path = c['collectionPathUri'],
                                                                          primaryFolder = c['primaryResultsFolder'],
                                                                          limsCode = MU.limsCodeFromCellPath(c['collectionPathUri']))
                                    smrtCellObjs.append(cell[0])
                            
                                # Now add the SMRT Cells to the new job
                                [newJob.cells.add(x) for x in smrtCellObjs]
                                
                            # Link secondary job to condition
                            if not secondaryJobObjects.has_key(cond):
                                secondaryJobObjects[cond] = [newJob]
                            else:
                                secondaryJobObjects[cond].append(newJob)

                        
                        #secondaryJobs.append(newJob)
                        
                print 'SECONDARY JOBS ARE: %s' % secondaryJobObjects
                return secondaryJobObjects
                
                
            def createConditions():
                
                return conditionObjects
            
            def createProject():
                
                return projectObject
                                
            jobs = createSecondaryJobs()
            conditions = createConditions()
            project = createProject()
            
            return {'SecondaryJobs' : jobs,
                    'Conditions'    : conditions,
                    'Project'       : project}

                