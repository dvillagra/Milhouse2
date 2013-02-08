'''
Created on Feb 6, 2013

@author: dvillagra
'''

from pbmilhouse import PBUtils as PBU
from pycore.SecondaryJobHandler import SecondaryDataHandler, SecondaryServerConnector
from pycore.TestUtils import printOut as PO

def pingSecondaryServer(server):
    conn = SecondaryServerConnector(server)
    req = conn.makeRequest('/smrtportal/api/')
    PO('Server Response', req)


################
#  REFERENCES  #
################

def getReferenceSequences(server):
    sdata = SecondaryDataHandler(server)
    req = sdata.getReferences()
    PO('Reference Seqs', req)
    
def getReferenceEntries(server):
    sdata = SecondaryDataHandler(server)
    req = sdata.getReferenceEntries()
    PO('Reference Entries', req)   
    
def getReferenceNames(server):
    sdata = SecondaryDataHandler(server)
    req = sdata.getReferenceNames()
    PO('Reference Names', req)
    

#################
#   WORKFLOWS   #
#################
def getProtocols(server):
    sdata = SecondaryDataHandler(server)
    req = sdata.getProtocols()
    PO('Protocols', req)

def getProtocolNames(server):
    sdata = SecondaryDataHandler(server)
    req = sdata.getProtocolNames()
    PO('Protocol Names', req)

if __name__ == '__main__':
    
    print "Beginning Tests..."
    
    print "\nBeginning SMRTPortal Tests..."
    pbSmrtPortal = PBU.MP17_SMRT_SERVER
    pingSecondaryServer(pbSmrtPortal)
    getReferenceSequences(pbSmrtPortal)
    getReferenceEntries(pbSmrtPortal)
    getReferenceNames(pbSmrtPortal)
    getProtocols(pbSmrtPortal)
    getProtocolNames(pbSmrtPortal)
    print "SMRTPortal Tests Complete!\n"
    
    
#    print "\nBeginning Martin Tests..."
#    pbMartinProd = PBU.MARTIN_PROD_SERVER
#    pingSecondaryServer(pbMartinProd)
#    getReferenceSequences(pbMartinProd)
#    getReferenceEntries(pbMartinProd)
#    getReferenceNames(pbMartinProd)
#    print "\nMartin Tests Complete!\n\n"
    
    print "Tests completed..."
    
    