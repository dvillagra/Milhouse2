'''
Created on Feb 5, 2013

@author: dvillagra
'''

from django.db import models
from django.contrib.auth.models import User 
from django_code.signals import create_user_profile
from django.db.models.signals import post_save
import jsonfield

import pycore.MEnums as enums

class BaseModel(models.Model):
    created_date  = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        
#    def __unicode__(self): 
#        return '%s: %s' % (self.id, self.name)
    
class UserProfile(BaseModel):
    # This field is required
    user = models.OneToOneField(User)
    
    # User info
    title = models.CharField(max_length=50, null=True, blank=True)
    group = models.CharField(max_length=50, null=True, blank=True)
    

class SMRTCell(BaseModel):
    context        = models.CharField(max_length=100, null=True, blank=True)
    path           = models.FilePathField()
    primaryFolder = models.CharField(max_length=50)
    limsCode       = models.CharField(max_length=50, null=True, blank=True)

#class SecondaryProtocol(BaseModel):
#    name         = models.CharField(max_length=50)
#    post_process = models.BooleanField(default=False)
#    active       = models.BooleanField(default=False)    

class SecondaryAnalysisServer(BaseModel):
    serverName    = models.CharField(max_length=40, unique=True)
    serverHost    = models.CharField(max_length=75)
    serverPort    = models.IntegerField()
    homePath      = models.CharField(max_length=100)
    jobDataPath   = models.CharField(max_length=100)
    referencePath = models.CharField(max_length=100)
    protocolPath  = models.CharField(max_length=100)
    apiRootPath   = models.CharField(max_length=50, default='/smrtportal/api/')
    active        = models.BooleanField(default=False)    

class SecondaryJob(BaseModel):
    jobID      = models.IntegerField(null=True, blank=True, unique=True)
    cells      = models.ManyToManyField(SMRTCell)
    reference  = jsonfield.JSONField()
    protocol   = jsonfield.JSONField()
    server     = models.ForeignKey(SecondaryAnalysisServer)
    status     = models.SmallIntegerField(choices = enums.SECONDARY_STATUS, default=1)
    
class AnalysisProcedure(BaseModel):
    name         = models.CharField(max_length=50)
    group        = models.CharField(max_length=25)
    description  = models.TextField(max_length=500, null=True, blank=True)
    script       = models.FilePathField()
    version      = models.IntegerField()
    postProcess = models.BooleanField(default=False)

class AnalysisProcedureGroup(BaseModel):
    name        = models.CharField(max_length=50)
    group       = models.CharField(max_length=35)
    description = models.TextField(max_length=500)
    procedures  = models.ManyToManyField(AnalysisProcedure)
    owner       = models.ForeignKey(User)
    public      = models.BooleanField(default=False)
    
class Project(BaseModel):
    projectID        = models.IntegerField()
    name             = models.CharField(max_length=75)
    description      = models.TextField(max_length=500)
    tags             = models.CharField(max_length=100)
    analysisGroup    = models.ManyToManyField(AnalysisProcedureGroup)
    status           = models.SmallIntegerField(choices = enums.PROJECT_STATUS, default=1)
    
class ProjectComment(BaseModel):
    comment = models.TextField(max_length=500)
    project = models.ForeignKey(Project)
    
class ProjectJSON(BaseModel):
    project = models.OneToOneField(Project)
    json    = jsonfield.JSONField() 
    
class AnalysisItem(BaseModel):
    name        = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    itemType    = models.SmallIntegerField(choices = enums.ANALYSIS_ITEM_TYPES)
    itemFile    = models.FilePathField()
    procedure   = models.ForeignKey(AnalysisProcedure)
    project     = models.ForeignKey(Project)

class Condition(BaseModel):
    name          = models.CharField(max_length=50)
    secondary_job = models.ManyToManyField(SecondaryJob)
    filter_expr   = models.CharField(max_length=500)
    extractDict   = jsonfield.JSONField(null=True, blank=True)
    extrasDict    = jsonfield.JSONField(null=True, blank=True)
    status        = models.SmallIntegerField(choices = enums.CONDITION_STATUS, default=1)
    project       = models.ForeignKey(Project)

class ConditionJSON(BaseModel):
    condition = models.OneToOneField(Condition)
    json      = jsonfield.JSONField()


##############################
##    SIGNAL DISPATCHERS    ##    
##############################

# Signal dispatcher for user creation
# automatically creates a user profile is one is requested for the user
post_save.connect(create_user_profile, sender=User)