from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django_code.models import *


# Define an inline admin descriptor for UserProfile model
# which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, )



# Other custom models
class SMRTCellAdmin(admin.ModelAdmin):
    pass

class SecondaryWorkflowAdmin(admin.ModelAdmin):
    pass

class SecondaryJobAdmin(admin.ModelAdmin):
    pass

class ConditionAdmin(admin.ModelAdmin):
    pass

class ConditionJSONAdmin(admin.ModelAdmin):
    pass

class AnalysisProcedureAdmin(admin.ModelAdmin):
    pass

class AnalysisProcedureGroupAdmin(admin.ModelAdmin):
    pass

class AnalysisItemAdmin(admin.ModelAdmin):
    pass

class ProjectAdmin(admin.ModelAdmin):
    pass

class ProjectCommentAdmin(admin.ModelAdmin):
    pass

class ProjectJSONAdmin(admin.ModelAdmin):
    pass

class UserProfileAdmin(admin.ModelAdmin):
    pass


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register custom models
admin.site.register(SMRTCell, SMRTCellAdmin)
admin.site.register(SecondaryWorkflow, SecondaryWorkflowAdmin)
admin.site.register(SecondaryJob, SecondaryJobAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(ConditionJSON, ConditionJSONAdmin)
admin.site.register(AnalysisProcedure, AnalysisProcedureAdmin)
admin.site.register(AnalysisProcedureGroup, AnalysisProcedureGroupAdmin)
admin.site.register(AnalysisItem, AnalysisItemAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectComment, ProjectCommentAdmin)
admin.site.register(ProjectJSON, ProjectJSONAdmin)
admin.site.register(UserProfile, UserProfileAdmin) 
