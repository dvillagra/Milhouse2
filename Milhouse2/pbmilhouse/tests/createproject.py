'''
Created on Feb 8, 2013

@author: dvillagra
'''

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
    
    print "\nBeginning Project Creation Tests..."
    makeProject('/Users/dvillagra/milhouse_dev/dev/projects/definitions/test.csv')
    print "Project Creation Tests Complete!\n"
    
    