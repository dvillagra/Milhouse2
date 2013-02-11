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
        
    def __unicode__(self): 
        return '%s: %s' % (self.id, self.name)
    
class UserProfile(BaseModel):
    # This field is required
    user = models.OneToOneField(User)
    
    # User info
    title = models.CharField(max_length=50, null=True, blank=True)
    group = models.CharField(max_length=50, null=True, blank=True)
    

class SMRTCell(BaseModel):
    context        = models.CharField(max_length=100)
    path           = models.FilePathField(null=True, blank=True)
    primary_folder = models.CharField(max_length=50)
    limscode       = models.CharField(max_length=50, null=True, blank=True)

#class SecondaryProtocol(BaseModel):
#    name         = models.CharField(max_length=50)
#    post_process = models.BooleanField(default=False)
#    active       = models.BooleanField(default=False)    

class SecondaryAnalysisServer(BaseModel):
    serverName    = models.CharField(max_length=40)
    serverHost    = models.CharField(max_length=75)
    serverPort    = models.IntegerField()
    homePath      = models.CharField(max_length=100)
    jobDataPath   = models.CharField(max_length=100)
    referencePath = models.CharField(max_length=100)
    protocolPath  = models.CharField(max_length=100)
    apiRootPath   = models.CharField(max_length=50, default='/smrtportal/api/')
    active        = models.BooleanField(default=False)

class SecondaryJob(BaseModel):
    job_id     = models.IntegerField()
    cells      = models.ManyToManyField(SMRTCell)
    reference  = models.CharField(max_length=50)
    protocol   = models.CharField(max_length=50)
    server     = models.ForeignKey(SecondaryAnalysisServer)    
    #server     = models.SmallIntegerField(choices = enums.SECONDARY_JOB_TYPE)
    status     = models.SmallIntegerField(choices = enums.SECONDARY_STATUS)


class AnalysisProcedure(BaseModel):
    name         = models.CharField(max_length=50)
    group        = models.CharField(max_length=25)
    description  = models.TextField(max_length=500, null=True, blank=True)
    script       = models.FilePathField()
    version      = models.IntegerField()
    post_process = models.BooleanField(default=False)

class AnalysisProcedureGroup(BaseModel):
    name        = models.CharField(max_length=50)
    group       = models.CharField(max_length=35)
    description = models.TextField(max_length=500)
    procedures  = models.ManyToManyField(AnalysisProcedure)
    owner       = models.ForeignKey(User)
    public      = models.BooleanField(default=False)
    
class Project(BaseModel):
    proj_id          = models.IntegerField()
    name             = models.CharField(max_length=75)
    description      = models.TextField(max_length=500)
    tags             = models.CharField(max_length=100)
    analysis_group   = models.ManyToManyField(AnalysisProcedureGroup)
    status           = models.SmallIntegerField(choices = enums.PROJECT_STATUS)
    
class ProjectComment(BaseModel):
    comment = models.TextField(max_length=500)
    project = models.ForeignKey(Project)
    
class ProjectJSON(BaseModel):
    project = models.OneToOneField(Project)
    json    = jsonfield.JSONField() 
    
class AnalysisItem(BaseModel):
    name        = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    item_type   = models.SmallIntegerField(choices = enums.ANALYSIS_ITEM_TYPES)
    item_file   = models.FilePathField()
    procedure   = models.ForeignKey(AnalysisProcedure)
    project     = models.ForeignKey(Project)

class Condition(BaseModel):
    name          = models.CharField(max_length=50)
    secondary_job = models.ManyToManyField(SecondaryJob)
    filter_expr   = models.CharField(max_length=500)
    extract_dict  = jsonfield.JSONField(null=True, blank=True)
    extras_dict   = jsonfield.JSONField(null=True, blank=True)
    status        = models.SmallIntegerField(choices = enums.CONDITION_STATUS)
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
