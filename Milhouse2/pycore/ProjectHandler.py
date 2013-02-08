'''
Created on Feb 6, 2013

@author: dvillagra
'''

from pycore.tools.Validators import ExperimentDefinitionValidator

class ProjectFactory(object):
    
    def __init__(self, definition):
        self.validator  = ExperimentDefinitionValidator(definition)
        self.definition = self.validator.getExperimentDefinition() 
        self.is_valid   = self.validator.validateDefinition()[0]
        self.valid_msg  = self.is_valid[1]
        print 'I AM: \n%s' % self.definition
        print 'I AM VALID: (%s, %s)' % (self.is_valid, self.valid_msg) 
        
        
    def validateProjectDefinition(self):
        pass
    
    