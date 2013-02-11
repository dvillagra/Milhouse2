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

def makeProject(definition):
    proj = ProjectFactory(definition)
    PO('Project', proj)


if __name__ == '__main__':
    
    print "Beginning Tests..."
    
    milHome = os.environ.get('MILHOUSE_HOME')
    
    print "\nBeginning Project Creation Tests..."
    makeProject(os.path.join(milHome, 'projects', 'definitions', 'test.csv'))
    #makeProject('/Users/dvillagra/milhouse_dev/dev/projects/definitions/test.csv')
    print "Project Creation Tests Complete!\n"
    
    