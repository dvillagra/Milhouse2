'''
Created on Feb 7, 2013

@author: dvillagra
'''

from pycore.SecondaryJobHandler import SecondaryJobService

class MartinJobServiceFactory(object):
    
    @staticmethod
    def create(server, disk):
        if disk:
            return MartinJobServiceDisk(server)
        else:
            return MartinJobServiceAPI(server)

class MartinJobServiceAPI(SecondaryJobService):
    pass
#    def getReferences(self, apiCall='', apiParams=None):
#        return SDH.getReferences(apiCall, apiParams)


class MartinJobServiceDisk(SecondaryJobService):
    
    
    ## REFERENCES
    def getReferenceNames(self):
        pass
    
    ## PROTOCOLS
    def getProtocolNames(self):
        pass
    
    ## JOBS
    def getJobIDs(self):
        pass
    

#def parseMartinXML(tocXML, martinType):
#    dataDict = {}
#    try:
#        xmltree = parse(tocXML)
#        attrs = xmltree.firstChild.getElementsByTagName('attributes')[0]
#        attrs = xmltree.getElementsByTagName('toc')[0].getElementsByTagName('attributes')[0]
#        apParams = attrs.getElementsByTagName('apParameters')[0]
#
#        attrsDict = dict([(str(node.attributes['name'].value),str(node.firstChild.data).strip())
#                          for node in attrs.childNodes
#                          if node.nodeType != 3 and node.attributes['name'].value != 'advanced'])
#        apParamsDict = dict([(str(node.attributes['name'].value),str(node.firstChild.data))
#                             for node in apParams.childNodes
#                             if node.nodeType != 3])
#
#        dataDict['MartinStatus'] = parseMartinLog(int(attrsDict.get('Job ID', 0)), martinType).values()
#
#        if attrsDict and set(['Input', 'Primary Protocol']).issubset(attrsDict):
#            dataDict['RunCodes'] = [unicode('-'.join(k.split('/')[2:])) for k in attrsDict['Input'].split(',')]
#            dataDict['PrimaryFolder'] = attrsDict['Primary Protocol']
#
#        # Note: If LIMSTemplate was used to run this job then the original 
#        # refseq name will be erased and replaced with LIMSTemplate
#        if apParamsDict and 'global.reference' in apParamsDict:
#            dataDict['MartinRefSeq'] = apParamsDict['global.reference'].split('/')[-1]
#
#    except ExpatError:
#        msg = 'Attemtping to parse Martin\'s toc.xml failed'
#        logMsg('Mutils', msg, mode='info')
#        return dataDict
#
#    return dataDict

    
    