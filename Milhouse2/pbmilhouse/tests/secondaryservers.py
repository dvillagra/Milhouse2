'''
Created on Feb 6, 2013

@author: dvillagra
'''

from pbmilhouse import PBUtils as PBU
from pycore.SecondaryJobHandler import SecondaryJobServiceFactory, SecondaryServerConnector
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
    
def getSingleReferenceEntryBy(server, handler, params):
    req = handler.getSingleReferenceEntryBy(params)
    PO('Single Reference', req)


#################
#   PROTOCOLS   #
#################
def getProtocols(server, handler):
    req = handler.getProtocols()
    PO('Protocols', req)

def getProtocolEntries(server, handler):
    req = handler.getProtocolEntries()
    PO('Protocol Entries', req)   

def getProtocolNames(server, handler):
    req = handler.getProtocolNames()
    PO('Protocol Names', req)

def getSingleProtocolEntryBy(server, handler, params):
    req = handler.getSingleProtocolEntryBy(params)
    PO('Single Protocol', req)
    
    
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
    
    #server = PBU.MP17_SMRT_SERVER
    server = PBU.MARTIN_PROD_SERVER
    handler = SecondaryJobServiceFactory.create(server, disk=False)
    #pingSecondaryServer(server)
    
    getReferenceSequences(server, handler)
    getReferenceEntries(server, handler)
    getReferenceNames(server, handler)
    getSingleReferenceEntryBy(server, handler, {'ref_id': 'Cholera_2010EL_1786'})
    
    getProtocols(server, handler)
    getProtocolEntries(server, handler)
    getProtocolNames(server, handler)
    getSingleProtocolEntryBy(server, handler, {'analysis_name': 'NoRL_ForwardOnly'})
    
    #getJobs(server, handler)
    #getJobEntries(server, handler)
    #getJobIDs(server, handler)
    #getSingleJobEntry(server, handler, '55842')

    print "Tests completed..."
    
    