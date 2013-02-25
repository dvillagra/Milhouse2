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

from xml.dom.minidom import parse, parseString
from xml.parsers.expat import ExpatError


def parseXML(xml):
    try:
        if os.path.isfile(xml):
            xmltree = parse(xml)
        else:
            xmltree = parseString(xml)
        return xmltree

    except (ExpatError, TypeError) as err:
        msg = 'Attemtping to parse protocol xml failed [%s]' % err
        logMsg('MUtils', msg, mode='warning')


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

def serverConfToDict(confFN):
    pass

##########
# Loging #
##########

# Avoiding the 'Singleton in Python' ongoing debate and using a "static" 
# function i.e. a module function
def logMsg(obj, msg, mode='info'):
    t_obj = obj.__class__.__name__ if not isinstance(obj, str) else obj
    msg = '[%s] %s' % (t_obj, msg)
    logMsg = {'info'    : lambda x: logging.info(x), 
              'error'   : lambda x: logging.error(x),
              'debug'   : lambda x: logging.debug(x), 
              'warning' : lambda x: logging.warning(x) }
    if logMsg.has_key(mode): logMsg[mode](msg)
    else: logging.error('Failed to log message at level %s: %s' % (mode, msg))
    


def getRecArrayFromCSV(incsv, columnType=None, standardDtype=False, caseSensitive=False, sanitize=False):
    data = n.ndarray([])
    if isinstance(incsv, str) and os.path.isfile(incsv) or not isinstance(incsv, str):
        if sanitize:
            fout = tempfile.NamedTemporaryFile(suffix='_sanitized.csv', delete=True)
            subprocess.call('sed "s;#;;g" %s > %s' % (incsv, fout.name), shell=True)
            incsv = fout.name

#        if columnType:
#            dictCtype = dict(columnType)
#            ctype = [(k,dictCtype[k]) for k in getHeader(incsv)]
#            data = n.rec.fromrecords(n.genfromtxt(fname=incsv, delimiter=',', skip_header=1, dtype=ctype, autostrip=True), dtype=ctype)
#        else:
        data = n.recfromcsv(incsv, autostrip=True, case_sensitive=caseSensitive)
        if standardDtype:
            t_dtype = [(dtn,data.dtype[dtn]) for dtn in data.dtype.names]
            t_dtype = map(lambda dt: (dt[0],n.dtype('|S100')) if dt[1].kind == 'S' else dt, t_dtype)
            data = n.rec.array(data.tolist(), dtype=t_dtype)

        if not data.shape:
            data.shape = (1,)

    return data
