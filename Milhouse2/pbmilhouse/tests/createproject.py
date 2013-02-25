'''
Created on Feb 8, 2013

@author: dvillagra
'''

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_code.settings'


from pycore.ProjectHandler import ProjectFactory
from pycore.TestUtils import printOut as PO

################
#   PROJECTS   #
################

def validateProject(definition):
    ProjectFactory.validateProjectDefinition(definition)

def makeProject(definition):
    proj = ProjectFactory.create(definition)
    PO('Secondary Jobs', proj.get('SecondaryJobs'))
    PO('Conditions', proj.get('Conditions'))
    PO('Project', proj.get('Project'))

if __name__ == '__main__':
    
    print "Beginning Tests..."
    
    milHome = os.environ.get('MILHOUSE_HOME')
    
    print "\nBeginning Project Creation Tests..."
    fileName = 'test_multi_cond_multi_job_smrtportal.csv'
    #fileName = 'test_existing_smrtportal.csv'
    
    #fileName = 'test_multi_cond_multi_job_martin_2.csv'
    #fileName = 'test_existing_martin.csv'

    #validateProject(os.path.join(milHome, 'projects', 'definitions', fileName))
    makeProject(os.path.join(milHome, 'projects', 'definitions', fileName))
    
    print "Project Creation Tests Complete!\n"