'''
Created on Feb 6, 2013

@author: dvillagra
'''

from pbmilhouse import PBUtils as PBU
from pycore.SecondaryJobHandler import SecondaryDataHandlerFactory, SecondaryServerConnector
from pycore.TestUtils import printOut as PO

def pingSecondaryServer(server):
    conn = SecondaryServerConnector(server)
    req = conn.makeRequest('/smrtportal/api/')
    PO('Server Response', req)


################
#  REFERENCES  #
################

def getReferenceSequences(server, handler):
    req = handler.getReferences()
    PO('Reference Seqs', req)
    
def getReferenceEntries(server, handler):
    req = handler.getReferenceEntries()
    PO('Reference Entries', req)   
    
def getReferenceNames(server, handler):
    req = handler.getReferenceNames()
    PO('Reference Names', req)
    

#################
#   PROTOCOLS   #
#################
def getProtocols(server, handler):
    req = handler.getProtocols()
    PO('Protocols', req)

def getProtocolNames(server, handler):
    req = handler.getProtocolNames()
    PO('Protocol Names', req)


#################
#     JOBS      #
#################
def getJobs(server, handler):
    req = handler.getJobs()
    PO('Jobs', req)

def getJobEntries(server, handler):
    req = handler.getJobEntries()
    PO('Job Entries', req)

def getJobIDs(server, handler):
    req = handler.getJobIDs()
    PO('Job IDs', req)
    
def getSingleJobEntry(server, handler, jobID):
    req = handler.getSingleJobEntry(jobID)
    PO('Single Job Entry', req)

if __name__ == '__main__':
    
    print "Beginning Tests..."
    
    server = PBU.MP17_SMRT_SERVER
    handler = SecondaryDataHandlerFactory.create(server, disk=False)
    pingSecondaryServer(server)
    
    getReferenceSequences(server, handler)
    getReferenceEntries(server, handler)
    getReferenceNames(server, handler)
    
    getProtocols(server, handler)
    getProtocolNames(server, handler)
    
    getJobs(server, handler)
    getJobEntries(server, handler)
    getJobIDs(server, handler)
    getSingleJobEntry(server, handler, '55842')

    print "Tests completed..."
    
    