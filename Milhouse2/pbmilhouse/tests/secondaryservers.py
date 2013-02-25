'''
Created on Feb 6, 2013

@author: dvillagra
'''


from pbmilhouse import PBUtils as PBU
from pycore.SecondaryJobHandler import SecondaryJobServiceFactory
from pycore.TestUtils import printOut as PO

def pingSecondaryServer(server):
    req = handler.testConnection()
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
    
def getSingleReferenceEntry(server, handler, refName):
    req = handler.getSingleReferenceEntry(refName)
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

def getSingleProtocolEntry(server, handler, protocolName):
    req = handler.getSingleProtocolEntryBy(protocolName)
    PO('Single Protocol', req)
    
def testProtocolFunction(server, handler, protocolName=None):
    req = handler.protocolIsSplittable(protocolName)
    PO('Protocol Function', req)
    
    
    
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
    
def getModelJobInfo(server, handler, jobID):
    req = handler.getModelJobInfo(jobID)
    PO('Basic Job Info', req)

if __name__ == '__main__':
    
    print "Beginning Tests..."
    
    server = PBU.MARTIN_DVLOCAL_SMRT_SERVER
    jobID = '185018'
    protocol = 'Standard_Standard'

#    server = PBU.MP17_DVLOCAL_SMRT_SERVER
#    protocol = 'RS_Resequencing.1'
#    jobID = '055861'
    
    handler = SecondaryJobServiceFactory.create(server, disk=True)
    #pingSecondaryServer(server)
    getModelJobInfo(server, handler, jobID)
    
    
#    getReferenceSequences(server, handler)
#    getReferenceEntries(server, handler)
#    getReferenceNames(server, handler)
#    getSingleReferenceEntry(server, handler, 'Cholera_2010EL_1786')
#    
#    getProtocols(server, handler)
#    getProtocolEntries(server, handler)
#    getProtocolNames(server, handler)
#    getSingleProtocolEntry(server, handler, 'NoRL_ForwardOnly')
    testProtocolFunction(server, handler, protocol)
#    
#    getJobs(server, handler)
#    getJobEntries(server, handler)
#    getJobIDs(server, handler)
#    getSingleJobEntry(server, handler, '55842')

    print "Tests completed..."
    
    