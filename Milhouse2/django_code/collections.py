'''
Created on Feb 5, 2013

@author: dvillagra
'''

from mongoengine import Document, EmbeddedDocument, StringField, EmailField, \
    URLField, IntField, ListField, EmbeddedDocumentField, ReferenceField, \
    FileField, ImageField, BooleanField, DateTimeField
    
from datetime import datetime    
import pycore.MEnums as enums

# Miscellaneous
class User(Document):
    email      = EmailField(required=True)
    first_name = StringField(max_length=50)
    last_name  = StringField(max_length=50)
    

class Quote(Document):
    quote  = StringField(required=True)
    author = StringField(max_length=50)
    link   = URLField()


### Project related ###

# For Secondary Analysis Jobs
class CellName(EmbeddedDocument):
    name           = StringField()
    data_path      = StringField()
    primary_folder = StringField()
    
class SecondaryJob(Document):
    job_id    = IntField(min_value=100000, max_value=999999)
    cellname  = ListField(EmbeddedDocumentField(CellName))
    job_type  = StringField(choices = enums.SECONDARY_JOB_TYPE)
    workflow  = StringField(choices = enums.SECONDARY_WORKFLOWS)
    reference = StringField(choices = enums.REFERENCE_SEQUENCES)
    status    = StringField(choices = enums.SECONDARY_STATUS)


# For Milhouse Conditions
class ConditionExtracter(EmbeddedDocument):
    extracter_type  = StringField()
    extracter_value = StringField()
    
class ConditionFilter(EmbeddedDocument):
    filter_expression = StringField()

class ConditionExtra(EmbeddedDocument):
    extra_name  = StringField()
    extra_value = StringField()

class Condition(Document):
    name            = StringField(max_length=50)
    secondary_job   = ListField(ReferenceField(SecondaryJob))
    extracter       = ListField(EmbeddedDocumentField(ConditionExtracter))
    filter          = EmbeddedDocumentField(ConditionFilter) 
    condition_extra = ListField(EmbeddedDocumentField(ConditionExtra))
    status          = StringField(choices = enums.SECONDARY_STATUS)
    
# For Milhouse Projects
class AnalysisItem(EmbeddedDocument):
    name        = StringField()
    description = StringField()
    item_type   = StringField(unique_with=name, choices=enums.ANALYSIS_ITEM_TYPES)
    
class AnalysisPlot(AnalysisItem):
    image_file = ImageField()

class AnalysisTable(AnalysisItem):
    csv_file  = FileField()

class AnalysisProcedure(Document):
    name        = StringField(max_length=50)
    group       = StringField()
    description = StringField()
    items       = ListField(EmbeddedDocumentField(AnalysisItem))
    script      = FileField()
    version     = IntField(min_value=1)

class AnalysisProfile(Document):
    name        = StringField(max_length=50)
    group       = StringField(max_length=50)
    description = StringField()
    procedures  = ListField(ReferenceField(AnalysisProcedure))
    owner       = ReferenceField(User)
    public      = BooleanField(default=False)

class Comment(EmbeddedDocument):
    text         = StringField(max_length=500)
    created_by   = ReferenceField(User)
    created_time = DateTimeField(default = datetime.now)

class Project(Document):
    id               = IntField()
    name             = StringField(max_length=75)
    description      = StringField()
    tags             = ListField(StringField(max_length=50))
    comments         = ListField(EmbeddedDocumentField(Comment))
    status           = StringField(choices = enums.PROJECT_STATUS)
    analysis_profile = ListField(ReferenceField(AnalysisProfile))
    plots            = ListField(EmbeddedDocumentField(AnalysisPlot))
    tables           = ListField(EmbeddedDocumentField(AnalysisTable))

