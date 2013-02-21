'''
Created on Feb 5, 2013

@author: dvillagra
'''

import os
import re
import logging
import numpy as n
import tempfile
import subprocess

from pycore.tools.LIMSHandler import LIMSMapper




def parseMilhouseConf(confFN):
    confDict = {}
    for line in open(confFN, 'r'):
        line = line.strip()
        if line and line[0] != '#':
            fields = map(lambda x: x.strip(), line.split('#')[0].strip().split('='))
            if len(fields) == 2:
                confDict[fields[0]] = fields[1]
    for setting in [k for k in confDict if re.findall('PORT', k)]:
        confDict[setting] = int(confDict[setting])
    return confDict


##########
# Loging #
##########

# Avoiding the 'Singleton in Python' ongoing debate and using a "static" 
# function i.e. a module function
def logMsg(obj, msg, mode='info'):
    t_obj = obj.__class__.__name__ if not isinstance(obj, str) else obj
    msg = '[%s] %s' % (t_obj, msg)
    logMsg = {'info' : lambda x: logging.info(x), 
              'error': lambda x: logging.error(x),
              'debug': lambda x: logging.debug(x) }
    if logMsg.has_key(mode): logMsg[mode](msg)
    else: logging.error('Failed to log message at level %s: %s' % (mode, msg))
    
    