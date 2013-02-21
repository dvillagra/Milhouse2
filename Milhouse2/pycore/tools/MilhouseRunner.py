'''
Created on Feb 19, 2013

@author: dvillagra
'''

#!/mnt/secondary/Share/Milhouse/prod/server/virtualenv/bin/python
import os
import sys
import argparse
import logging
import subprocess
import glob
import re
import numpy as n
from collections import OrderedDict

#Import Milhouse Utilities
import milhouse.MUtils as MU
from milhouse.MDBController import MDBCFactory
from milhouse.containers.MProject import MProjectFactory

#Is this a development or production instance?
IS_DEV_INSTANCE = False
server = 'dev' if IS_DEV_INSTANCE else 'prod' 

# Set standard and minimal analysis groups
STANDARD = ['tSummary', 'readlength', 'accuracy', 'yield']
MINIMAL = ['tSummary', 'readlength', 'accuracy', 'yield']

#Set MILHOUSE_HOME environment variable
os.environ['MILHOUSE_HOME'] = os.path.join('/mnt/secondary/Share/Milhouse', server)

# Get configuration info and check for MILHOUSE_HOME setting
if not os.environ.get('MILHOUSE_HOME'):
    print 'Environment variable MILHOUSE_HOME is not set! Exiting...'
    sys.exit(1)
else:
    CONFDICT = os.path.join(os.environ.get('MILHOUSE_HOME'), 'config', 'milhouse.conf')
    if not os.path.isfile(CONFDICT):
        print 'milhouse.conf stored at [%s] does not exist! Exiting...' % CONFDICT
        sys.exit(1)
    else:
        CONFDICT = MU.parseMilhouseConf(CONFDICT)
        print "Submitting Milhouse analysis project to %s server" % CONFDICT['MDB_TYPE']
        
#Tool for running Milhouse Jobs from command line
class ToolRunner(object):
    
    def __init__(self):
        self.mDB = MDBCFactory.getMDBController('data', 
                                                mdbServer=CONFDICT['MDB_SERVER'], 
                                                mdbPort=CONFDICT['MDB_PORT'],
                                                mlDataDir=CONFDICT['ML_DATADIR'])
        self.mDBS = self.mDB.getMDBExtra()[0]
        self._parseOptions()
        self._setupLogging()

    def _parseOptions(self):
        desc = ['Tool for running and managing Milhouse projects from the command line.',
                'Notes: For all command-line arguments, default values are listed in [].']
        self._parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                               description='\n'.join(desc))

        self.parser = argparse.ArgumentParser(add_help=False)
        self.parser.add_argument('-i', '--info', action='store_true', dest='info', default=False, 
                                 help='turn on progress monitoring to stdout [%(default)s]')
        self.parser.add_argument('-d', '--debug', action='store_true', dest='debug', default=False, 
                                 help='turn on progress monitoring to stdout and keep temp files [%(default)s]')
        self.parser.add_argument('-v', '--version', action='version', version= '0.1')

        subparsers = self._parser.add_subparsers(dest='subName')
        
        # Run
        parser_r = subparsers.add_parser('run', 
                                         help='Tool for running Milhouse projects by consuming experiment CSV files',
                                         parents=[self.parser])
        parser_r.add_argument('infile', metavar='input.csv',
                              help='input CSV filename')
        parser_r.add_argument('--analysisType', dest='atype', default='Standard',  
                              help='Analysis type: Standard or Minimal [%(default)s]')
        parser_r.add_argument('--title', dest='title', required=True,  
                              help='Milhouse project title in quotes')
        parser_r.add_argument('--description', dest='desc', default=None,  
                              help='Milhouse project description in quotes')
        parser_r.add_argument('--hypothesis', dest='hyp', default=None,  
                              help='Milhouse project hypothesis in quotes')
        
        # Status check
        parser_s = subparsers.add_parser('status', 
                                         help='Tool for checking a Milhouse project\'s status',
                                         parents=[self.parser])
        parser_s.add_argument('--id', dest='id', required=True,  
                              help='Milhouse project ID')

        self.args = self._parser.parse_args()
        self._validateArgs()

    def _setupLogging(self):
        logLevel = logging.INFO if self.args.info else logging.ERROR
        logLevel = logging.DEBUG if self.args.debug else logLevel
        logging.basicConfig(level=logLevel, format='%(asctime)s [%(levelname)s] %(message)s')

    def _validateArgs(self):
        if self.args.subName == 'run':
            if not os.path.isfile(self.args.infile):
                self.parser.error('Input file %s does not exist!' % self.args.infile)
            else:
                self._validateCSV(self.args.infile)
            if self.args.atype not in ['Standard', 'Minimal']:
                self.parser.error('Analysis type can be either Standard or Minimal!')
        if self.args.subName == 'status':
            try:
                self.args.id = int(self.args.id)
            except ValueError:
                self.parser.error('Milhouse projects IDs can only be ints!')
            
    def _validateCSV(self, csvFN):
        try:
            data = MU.getRecArrayFromCSV(self.args.infile, caseSensitive=True)
            CSVF_DEFAULT = MU.getCSVF('MartinJobID' in data.dtype.names, withExtras=True)
            
            # Check for correct usage of MartinType
            if 'MartinType' in data.dtype.names:
                if not set(n.unique(data['MartinType'])).issubset(MU.MARTIN_ROOT.keys()):
                    msg = 'Invalid MartinType value, allowed values are = [%s]' % ', '.join(MU.MARTIN_ROOT.keys())
                    logging.error(msg)
                    sys.exit(0)
                elif 'smrtportal' in data['MartinType']:
                    if 'MartinJobID' not in data.dtype.names:
                        msg = 'Smrportal conditions can not be run at this time and thus require a populated MartinJobID column' 
                        logging.error(msg)
                        sys.exit(0)
            else:
                data = MU.addColumnToRecArray(data, [MU.MARTIN_ROOT.keys()[0]] * len(data), ('MartinType', '|S11'), tail=True)
                
            # Check for unpopulated default columns
            wrngclmns = filter(lambda x: n.dtype(x[1]) == n.dtype(bool) and x[0] in MU.CSVF_ALL, data.dtype.descr)
            if wrngclmns:
                msg = 'Incorrectly formatted CSV file:\n Column(s) [%s] have not been populated' % ', '.join([c[0] for c in wrngclmns])
                logging.error(msg)
                sys.exit(0)

            # Check if the file contains the correct default column names
            if filter(lambda x: x not in data.dtype.names, CSVF_DEFAULT):
                msg = 'Incorrectly formatted CSV file:\n Missing default column names from %s' % CSVF_DEFAULT
                logging.error(msg)
                sys.exit(0)

            # Check for correct naming of conditions
            if filter(lambda x: re.findall(r'[^A-Za-z0-9_\.\-]', x), data['Name']):
                msg = 'Incorrectly formatted CSV file:\n Condition names can only contain: alphanumeric characters, dashes (-), underscores (_) and dots (.)'
                logging.error(msg)
                sys.exit(0)
            
            # Check if the non-default columns have a p_ prefix
            extras = filter(lambda x: x not in MU.CSVF_ALL, data.dtype.names)
            if filter(lambda x: x[:2] != 'p_', extras):
                msg = 'Incorrectly formatted CSV file:\n Extra parameters need to be named using a "p_" prefix' 
                logging.error(msg)
                sys.exit(0)

            # Check if workflow provided exists in martin's list of workflows
            if 'smrtportal' not in data['MartinType']:
                mWkflowNames = self.mDBS.getMartinWkflowDict().keys()
                if filter(lambda x: x not in mWkflowNames, n.unique(data['MartinWorkflow'])):
                    msg = 'Unsupported Martin Workflow name provided.'
                    logging.error(msg)
                    sys.exit(0)
            
            # Check if reference sequence provided exists in the reference repository
            if 'MartinRefSeq' in data.dtype.names:
                wrongrefseqs = set(filter(lambda x: not glob.glob('%s/%s' % (MU.MARTIN_REFREPOS[x['MartinType']], x['MartinRefSeq'])), data))
                if wrongrefseqs:
                    msg = 'The following reference sequence names are invalid: [%s].' % ','.join(wrongrefseqs)
                    logging.error(msg)
                    sys.exit(0)                
            
            # Check for correctness MartinJobID values
            if 'MartinJobID' in data.dtype.names:
                wrnglens = set(filter(lambda x: x != 6, map(lambda x: len(str(x)), data['MartinJobID'])))
                if wrnglens and len(wrnglens) == 1 and wrnglens.issubset([5]) and 'smrtportal' not in data['MartinType']:
                    msg = 'Invalid MartinJobID lengths supplied:\n If these are smrtportal jobs, you need to set MartinType to smrtportal' 
                    logging.error(msg)
                    sys.exit(0)
                elif wrnglens and not wrnglens.issubset([5]):
                    msg = 'Invalid MartinJobID lengths supplied:\n Martin expects length == 6 and smrtportal length => 5' 
                    logging.error(msg)
                    sys.exit(0)                                                          

            # Check whether primary folder names are contained within the given run codes
            if set(['RunCodes', 'PrimaryFolder']).issubset(data.dtype.names):
                for row in data:
                    if len(row['RunCodes'].split('-')) == 2:
                        exp,run = row['RunCodes'].split('-')
                        if not glob.glob('/mnt/data*/vol*/%s/%s/%s' % (exp,run, row['PrimaryFolder'])):
                            msg = 'Run code [%s] does not contain primary folder [%s].' % (row['RunCodes'], row['PrimaryFolder'])
                            logging.error(msg)
                            sys.exit(0)                
            
            # Check for uniqueness of column values within conditions
            for cond in n.unique(data['Name']):
                sl_data = data[data['Name'] == cond]
                if filter(lambda x: len(n.unique(sl_data[x])) != 1, [k for k in sl_data.dtype.names if k != 'RunCodes']):
                    msg = 'For condition name=%s some of the attributes are NOT unique' % cond
                    logging.error(msg)                   
                    sys.exit(0)                                

        except ValueError as err:
            msg = 'Incorrectly formatted CSV file:\n %s' % err
            logging.error(msg)
            sys.exit(0)
        
    def run(self):
        if self.args.subName == 'run':            
            condDict = MU.parseExperimentCSV(self.args.infile)
            dataDict = {'Analysis': STANDARD if self.args.atype == 'Standard' else MINIMAL,
                        'Conditions': OrderedDict([(k,condDict[k]) for k in sorted(condDict.keys())]),
                        'Description': self.args.desc,
                        'Hypothesis': self.args.hyp,
                        'RunBy': subprocess.Popen('whoami', stdout=subprocess.PIPE, shell=True).stdout.read().strip(),
                        'Tags': ['PrimaryRetraining'],
                        'Title': self.args.title}

            mProjectR = MProjectFactory.getMProject('Runable', self.mDB)
            mProjectR.setFromDict(dataDict)
            mProjectR.register()
            print "Registered Milhouse Project %s" % mProjectR.ID
        elif self.args.subName == 'status':
            mProject = self.mDB.getMProjectFromID(self.args.id)
            sDict = mProject.getStatusDict()
            print 'Milhouse Project %d: %s [by: %s]' % (self.args.id, mProject.title, mProject.runby)
            print 'Status: %s' % sDict['Status']
            print 'Martin: %.1f%%' % sDict['Conditions']
            print 'Analysis-Plots: %.1f%%' % sDict['Analysis']['Plots']
            print 'Analysis-Tables: %.1f%%' % sDict['Analysis']['Tables']
            
if __name__ == '__main__':    
    ToolRunner().run()
