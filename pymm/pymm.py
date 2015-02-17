import xml.etree.ElementTree as ET
from . import mindmapFactories
from . import mindmapElements


class FreeplaneFile(object):
    """ Interface to Freeplane structure. Allow reading and writing of xml-like mindmap formats (.mm)

    readfile - reads file/filename and converts to structural tree with Map as first node
    writefile - writes full structural tree to file/filename
    getroot - skip the Map element and obtain its first child - the Root Node
    setroot - set the Map's only child node
    getmap - obtain the Map element. At present, this Map contains just the Root Node. Recommend just using get/setroot
    convert - generally implemented internally. Will convert an ElementTree Element into a Freeplane-compatible element
    revert - generally implemented internally. Will revert a Freeplane-compatible element to an ElementTree Element
    """
    mmFactory = mindmapFactories.MindMapConverter

    def __init__(self, mapElement=None):
        """ FreeplaneFile acts as an interface to intrepret xml-based .mm files into a tree of Nodes.

        :param mapElement: (optional) a pymm Map Element. Obtained from another FreeplaneFile's getmap() method
        :return:
        """
        self.mmFactory = self.mmFactory()  # initialize mindmap factory.
        self.mmMap = mindmapElements.Map()
        self.mmMap.append(mindmapElements.Node())  # set up map and root node
        if mapElement is not None:
            self.mmMap = mapElement  # we make the assumption that this is a mindmap Map

    def readfile(self, file_or_filename):
        """ converts the file/filename into a pymm tree

        :param file_or_filename: string path to file or file instance of mindmap (.mm)
        :return:
        """
        etMap = ET.parse(file_or_filename)
        self.mmMap = self.convert(etMap)

    def writefile(self, file_or_filename):
        """ writes internal map and linked Nodes to file/filename

        :param file_or_filename: string path to file or file instance of mindmap (.mm)
        :return:
        """
        etMap = self.revert(self.mmMap)  # the user passed in .....
        xmlTree = ET.ElementTree(etMap)
        xmlTree.write(file_or_filename)

    def getroot(self):
        """ Return Root Node """
        return self.mmMap.nodes[0]

    def setroot(self, root):
        """ Set Internal Root Node

        :param root: Root Node (Node instance) that defines the base structure of a pymm tree
        """
        self.mmMap.nodes[0] = root

    def getmap(self):
        """ Return Map Element. In pymm, Map Element is not useful as most / all important stuff is inside Root Node """
        return self.mmMap
    
    def convert(self, etElement):
        """ Convert ElementTree Element to pymm Element

        :param etElement: Element Tree Element -> generally an element from python's xml.etree.ElementTree module
        :return:
        """
        return self.mmFactory.convert_etree_element_and_tree(etElement)

    def revert(self, mmElement):
        """ Revert pymm Element to ElementTreee Element

        :param mmElement: pymm Element from pymm.mindmapElements module
        :return:
        """
        return self.mmFactory.revert_mm_element_and_tree(mmElement)