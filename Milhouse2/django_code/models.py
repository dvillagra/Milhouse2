'''
Created on Feb 5, 2013

@author: dvillagra
'''

from django.db import models
from django.contrib.auth.models import User
import jsonfield

import pycore.MEnums as enums

class BaseModel(models.Model):
    created_date  = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    created_by    = models.ForeignKey(User, null=True, blank=True)
    modified_by   = models.ForeignKey(User, null=True, blank=True)
    
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
    path           = models.FilePathField()
    primary_folder = models.CharField(max_length=50)
    runcode        = models.CharField(max_length=15, null=True, blank=True)

class SecondaryJob(BaseModel):
    job_id     = models.IntegerField()
    cells      = models.ManyToManyField(SMRTCell)
    reference  = models.CharField(max_length=50)
    workflow   = models.CharField(max_length=50)
    job_type   = models.SmallIntegerField(choices = enums.SECONDARY_JOB_TYPE)
    status     = models.SmallIntegerField(choices = enums.SECONDARY_STATUS)
    
class Condition(BaseModel):
    name          = models.CharField(max_length=50)
    secondary_job = models.ManyToManyField(SecondaryJob)
    filter_expr   = models.CharField(max_length=500)
    extract_dict  = jsonfield.JSONField(null=True, blank=True)
    extras        = jsonfield.JSONField(null=True, blank=True)
    status        = models.SmallIntegerField(choices = enums.CONDITION_STATUS)
    

class AnalysisProcedure(BaseModel):
    name        = models.CharField(max_length=50)
    group       = models.CharField(max_length=25)
    description = models.TextField(max_length=500, null=True, blank=True)
    script      = models.FilePathField()
    version     = models.IntegerField()

class AnalysisItem(BaseModel):
    name        = models.CharField(max_length=50)
    description = models.TextField(max_length=500)
    item_type   = models.SmallIntegerField(choices = enums.ANALYSIS_ITEM_TYPES)
    procedure   = models.ForeignKey(AnalysisProcedure)

class AnalysisProfile(BaseModel):
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
    analysis_profile = models.ManyToManyField(AnalysisProfile)
    analysis_items   = models.ManyToManyField(AnalysisItem)
    status           = models.SmallIntegerField(choices = enums.PROJECT_STATUS)
    
class ProjectComment(BaseModel):
    comment = models.TextField(max_length=500)
    project = models.ForeignKey(Project)
    
class ProjectJSON(BaseModel):
    project = models.OneToOneField(Project)
    json = jsonfield.JSONField() 



