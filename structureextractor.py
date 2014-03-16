"""
.. module:: StuctureExtractor
    :synopsis:
"""

import document
import json
import string
from lxml import etree

class StructureExtractor(object):
    """This class parses an XML file according to the format given in a
    JSON file. It generates document classes (Sentences, Documents, Metadatas,
    etc.) from the input file.
    """
    #TODO: some of these methods cannot accept Tags, require BeautifulSoup
    def __init__(self, tokenizer, structure_file):
        """Create a new StructureExtractor.

        :param Tokenizer tokenizer: A tokenizer object
        :param str structure_file: Path to a JSON file that specifies the
        document structure.
        :return: a StructureExtractor instance
        :rtype: StructureExtractor
        """
        self.t = tokenizer
        self.structure_file = open(structure_file, "r")
        self.document_structure = json.load(self.structure_file)

    def extract(self, file):
        """Extract a list of Documents from a file. This method uses the
        structure_file given in the constructor for rules to identify documents.

        :param file file: The file to extract
        :return: A list of Document objects
        :rtype: list
        """

        documents = []

        #text = ""
        #with open(file.name, "r", -1) as f: # TODO: this seems a bit ridiculous
        #    for line in f:
        #        text += f.readline() + "\n"
        # TODO: was there a reason the original was written like that?

        with open(file.name, "r") as f:
            doc = etree.parse(f)

        units = self.extract_unit_information(self.document_structure, doc)

        for unit in units:
            d = document.document.Document(metadata=unit.metadata,
                name="document",
                sentences=unit.sentences,
                title=unit.name,
                units=unit.units)
            documents.append(d)

        return documents


    def extract_unit_information(self, structure, parent_node):
        """Process the given node, according to the given structure, and return
        a list of Unit objects that represent the parent_node.

        :param dict structure: A JSON description of the structure
        :param Tag parent_node: A BeautifulSoup object of the parent node.
        :return: A list of Units
        :rtype: Unit
        """

        units = []

        unit_xpaths = structure["xpaths"]

        for xpath in unit_xpaths:
            nodes = get_nodes_from_xpath(xpath, parent_node)

            struc_name = structure["structureName"]

            for node in nodes.children:
                try:
                    metadata_structure = structure["metadata"]
                except NameError:
                    metadata_structure = None

                unit_metadata = get_metadata(metadata_structure, node)
                sents = [] # Sentence objects
                children = [] # Unit objects
                try:
                    #TODO: condense these try-catches
                    child_unit_structures = structure["units"]
                except NameError:
                    child_unit_structures = None

                if child_unit_structures != None:
                    for n in range(0, len(child_unit_structures)):
                        child_structure = child_unit_structures[n]
                        child_type = child_structure["structureName"]
                        if "sentence" in child_type:
                            child_units = self.extract_unit_information(
                                child_structure, node)
                            children.extend(child_units)
                        else:
                            sents = self.get_sentences(child_structure, node,
                                True)
                units.append(document.unit.Unit(metadata=unit_metadata,
                    units=children, sentences=sents, name=struc_name))
        return units

    def get_sentences(self, structure, parent_node, tokenize):
        """Return the sentences present in the parent_node and its children.

        :param dict structure: A JSON description of the structure
        :param Tag node: a BeautifulSoup object of the node to get sentences
        from
        :param boolean tokenize: if True, then the sentences will be tokenized
        :return: A list of Sentences.
        :rtype: list
        """

        sentences = [] # a list of sentences
        sentence_text = ""
        sentence_metadata = [] # List of Metadata objects
        unit_xpaths = structure["xpaths"]

        try:
            metadata_structure = structure["metadata"]
        except NameError:
            metadata_structure = None

        for xpath in unit_xpaths:
            #TODO: bit of redundancy here from another method
            sentence_nodes = get_nodes_from_xpath(xpath, parent_node)

            for sentence_node in sentence_nodes:
                sentence_text += sentence_node.text.strip() + "\n"
                sentence_metadata.append(get_metadata(
                    metadata_structure, sentence_node))

        if tokenize:
            sents = self.t.tokenize(sentence_text)

            for sentence in sents:
                sentence.metadata = sentence_metadata
                words = string.split(" ", sentence.sentence)
                total_word_length = 0

                for word in words:
                    total_word_length += len(word)

                # TODO: additionalMetadata is a private variable set to false,
                # why is it there?
                # if self.additional_metadata:

                sentences.append(sentence)

        else:
            sentences.append(document.sentence.Sentence(sentence=sentence_text,
                metadata=sentence_metadata))

        return sentences


def get_metadata(metadata_structure, node):
    """Return a list of Metadata objects of the metadata of the Tags in
    node according to the rules in metadata_structure.

    If the Tags have attributes, then the value fields of the metadata
    objects will be those attributes. Otherwise, the text in the Tags
    will be the values. property_name is set according to PropertyName in
    metadata_strcuture. specification is set as the object in the JSON
    file that describes the xpath and propertyName of that Metadata object.
    This function iterates over every child of metadata in the structure
    file.

    :param list structure: A JSON description of the structure
    :param Tag node: ?
    :return: A list of metadata
    :rtype: list
    """
    metadata = [] # A list of Metadata

    # TODO: do we need this check?
    if metadata_structure is not None:
        for spec in metadata_structure:
            try:
                xpaths = spec["xpaths"]
            except NameError:
                xpaths = None
            try:
                attribute = spec["attr"]
            except NameError:
                attribute = None

            extracted = [] # A list of strings

            if xpaths is not None:
                for xpath in xpaths:
                    if attribute is not None:
                        extracted = get_xpath_attribute(xpath,
                            attribute, node)
                    else:
                        extracted = get_xpath_text(xpath, node)
                    for val in extracted:
                        metadata.append(document.metadata.Metadata(
                            value=val,
                            property_name=spec["propertyName"],
                            specification=spec))
    return metadata

def get_xpath_attribute(xpath_pattern, attribute, node):
    """Return values of attribute from the child elements of node that
    match xpath_pattern.

    :param string xpath_pattern: A pattern to find matches for
    :param string attribute: The attribute whose values should be returned
    :param Tag node: The node to search in
    :return: A list of strings, the values of the attributes
    :rtype: list
    """

    values = [] # list of strings

    if len(xpath_pattern.strip()) == 0:
        vals = node.get(attribute).split(" ")
        # Split the attribute since xml does not allow multiple attributes
        if len(vals) > 0:
            for value in vals:
                values.append(value)
    else:
        nodes = node.xpath(xpath_pattern)
        for node in nodes:
            vals = node.get(attribute).split(" ")
            if len(vals) > 0:
                for val in vals:
                    values.append(val)
    return values

def get_xpath_text(xpath_pattern, node):
    """Get the text from children of node that match xpath_pattern.

    :param string xpath_pattern: The pattern to find matches for.
    :param Tag node: The node to find matches under
    :return: A list of strings
    :rtype: list
    """

    values = [] # a list of strings

    if len(xpath_pattern.strip()) == 0:
        values.append(etree.tostring(node, method="text"))
    else:
        nodes = node.xpath(xpath_pattern)
        for node in nodes:
            value = etree.tostring(nodes, method="text").strip()
            if len(value) > 0:
                values.append(value)

    return values

def get_nodes_from_xpath(xpath, nodes):
    """If the selector is longer than 0 chars, then return the children
    of nodes that match xpath. Otherwise, return all the nodes.

    :param str xpath: The xpath to match.
    :param etree nodes: LXML etree object of nodes to search.
    :return etree: The matched nodes."""
    if len(xpath.strip()) == 0:
        return nodes
    else:
        return nodes.xpath(xpath)
