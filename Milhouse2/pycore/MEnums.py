'''
Created on Feb 5, 2013

@author: dvillagra
'''

# Collection Choices
SECONDARY_JOB_TYPE = (('Martin', 'Martin'), 
                      ('SMRTPortal', 'SMRTPortal'))

SECONDARY_WORKFLOWS = () #fetch from web service?

REFERENCE_SEQUENCES = () #fetch from web service?

SECONDARY_STATUS = ((0, 'FAILED'), 
                    (1, 'INSTANTIATED'), 
                    (2, 'RUNNING'), 
                    (3, 'COMPLETED'))

CONDITION_STATUS = ((0, 'FAILED'), 
                    (1, 'INSTANTIATED'), 
                    (2, 'RUNNING_ANALYSIS'),
                    (2, 'COMPLETED_ANALYSIS'),
                    (2, 'RUNNING_SPLITMERGE'),
                    (3, 'COMPLETED_SPLITMERGE'), 
                    (4, 'COMPLETED'))

ANALYSIS_ITEM_TYPES = (('Table', 'Table'),
                       ('Figure', 'Figure'))

PROJECT_STATUS = ((0, 'FAILED'),
                  (1, 'INSTANTIATED'),
                  (2, 'RUNNING_SECONDARY'),
                  (3, 'COMPLETED_SECONDARY'),
                  (4, 'RUNNING_SPLITMERGE'),
                  (5, 'COMPLETED_SPLITMERGE'),
                  (6, 'RUNNING_ANALYSIS'),
                  (7, 'COMPLETED'))
