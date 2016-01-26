import warnings
import copy
import re

class ChildSubsetSimplified:
    ''' Provide simplified access to specific child elements through regex 
    matching of descriptors such as tag, attributes, or a combination thereof.
    For example, if you want to simply match a tag (or tags), pass in a regular
    expression string that will fully match the desired tag(s).
    e.g. 'node|cloud'  # matches any 
    If you want to match a set of attributes, pass in a dictionary containing 
    regexes to fully match the key(s) and value(s) of the element's attributes
    e.g. {'TEXT':'.*'}  # matches any element with a 'TEXT' attribute
    e.g. {'.*': '.*flag.*'}  # matches any element with a 'flag' in its value
    e.g. {'COLOR': '.*'}  # matches anything with a 'COLOR' attribute
    You can include any number of tag and attribute regexes, each separated by
    a comma. All descriptors will have to fully match in order for an element
    to qualify as part of this subset.
    Most useful for allowing access
    to child nodes. Provide access to slicing, removal, appending

    :param element: the linked element whose children will be available through
        ElementAccessor
    :param descriptor: the list of specific descriptor of elements to group and
        provide access to.
    '''
    def __init__(self, elementInstance, **identifier):
        if not 'pre_verified' in identifier:
            self._verify_arguments(identifier)
        self._TAG = identifier.get('tag', None)
        self._TAG_REGEX = identifier.get('tag_regex', None)
        self._ATTRIB_REGEX = identifier.get('attrib_regex', {})
        self._parent = elementInstance

    @classmethod
    def _verify_arguments(cls, identifier):
        keysExpected = set(('tag', 'tag_regex', 'attrib_regex'))
        keysGot = set(identifier.keys())
        unexpectedKeys = keysGot.difference(keysExpected)
        if not keysGot:
            raise ValueError('Must pass in either/both tag_regex and ' + 
                            'attrib_regex')
        if unexpectedKeys:
            raise KeyError('Unexpected keys found in subset init: ' +
                            str(unexpectedKeys))
        tagr = identifier.get('tag_regex', None)
        if not tagr:
            tagr = None
        attribr = identifier.get('attrib_regex', {})
        tag = identifier.get('tag', None)
        if tagr and not isinstance(tagr, str):
            raise ValueError('tag_regex should be string. Got ' + str(tag))
        if attribr and not isinstance(attribr, dict):
            raise ValueError('attrib_regex should be dict.Got ' + str(attribr))
        if not tagr and not attribr and not tag:
            raise ValueError(
                'Must define either tag, tag_regex or attribregex. Got ' +
                    str(tagr) + str(attribr)
            )
        if tag and tagr:
            raise ValueError('cannot specify both tag and tag_regex matching')

    @classmethod
    def class_preconstructor(cls, **identifier):
        """return a function that, when run, will return an instance of
        ChildSubset with the identifier previously passed into
        class_preconstructor. Useful for predefining childsubset in a class
        definition. Any element inheriting from BaseElement will automatically
        call the object-instantiating function returned by this classmethod.
        However, it is recommended to use property(x) within a class
        definition, where x = ChildSubset.setup(), which does almost the same
        thing but is cleaner code-wise and easier to understand
        """
        cls._verify_arguments(identifier)
        identifier = copy.deepcopy(identifier)
        def this_function_gets_automatically_run_inside_elements__new__(elementInstance):
            return cls(elementInstance, **identifier) 
        return this_function_gets_automatically_run_inside_elements__new__ 

    @classmethod
    def setup(cls, **regexes):
        cls._verify_arguments(regexes)
        regexes['pre_verified'] = True

        def getter(parent):
            return cls(parent, **regexes)

        def setter(parent, iterable):
            self = cls(parent, **regexes)
            self[:] = iterable

        return getter, setter


    def append(self, element):
        self._parent.children.append(element)

    def remove(self, element):
        self._parent.chilren.remove(element)

    def __len__(self):
        return len(self[:])

    def __getitem__(self, index):
        if index == 0:  # speed shortcut
            for e in self:
                return e
            raise IndexError('Index out of bounds')
        elements = [e for e in self]
        return elements[index]

    def __iter__(self):
        """Iterate through _parent's children, yielding children when they
        match tag_regex and/or attrib_regex
        """
        for elem in self._parent.children:
            if self._TAG_REGEX:
                if not re.fullmatch(self._TAG_REGEX, elem.tag):
                    continue
            if self._TAG:
                if not self._TAG == elem.tag:
                    continue
            matches = lambda x, y, rx, ry: re.fullmatch(rx, x) and re.fullmatch(ry, y)
            for regK, regV in self._ATTRIB_REGEX.items():
                match = [k for k, v in elem.attrib.items() if matches(k, v, regK, regV)]
                if not match:
                    break
            else:
                yield elem


    def __setitem__(self, index, elem):
        """remove element(s), then re-appends after modification. Sloppy, but
        it works, and elements are reordered later anyways.
        what really matters is that the order of elements of the same tag are
        not altered. Note that this is very inefficient because the list is
        reconstructed each time a set-operation is applied
        """
        # check for index == 0, can use shortcut in that case
        if index == 0:
            e = self[index]
            i = self._parent.children.index(e)
            self._parent.children[i] = elem
            return
        subchildren = self[:]
        for element in subchildren:
            self._parent.children.remove(element)
        subchildren[index] = elem
        for element in subchildren:
            self._parent.children.append(element)

    def __delitem__(self, index):
        element = self[index]
        i = self._parent.children.index(element)
        del self._parent[i]


class ChildSubset(ChildSubsetSimplified):
    ''' Provide access to specific elements within an element through matching
    of descriptor. Most useful for allowing access to child nodes. Provide
    access with indexing, slicing, removal, appending, etc.

    :param element: the linked element whose children will be available through
        ElementAccessor
    :param descriptor: the list of specific descriptor of elements to group and
        provide access to.
    '''
    
    def pop(self, index=-1):
        """ Remove and return element in children list """
        elem = self[index]
        self._parent.children.remove(elem)
        return elem

    def extend(self, elements):
        self._parent.children.extend(elements)

    def __contains__(self, element):
        return element in self[:]

    def __repr__(self):
        return str(self[:])


class SingleChild:
    """Provide access to a single child within an element's children. It does
    not directly store the child, but rather provides functions for getting,
    setting, and deleting the specified child from a parent element's children
    attribute. This is meant to be instantiated as a class property. Pass the
    setup fxn a tag_regex or attrib_regex in the same fashion as specifying a
    ChildSubset, and pass the returned values to property(). You can look at an
    example in Node.cloud.
    """

    @classmethod
    def setup(cls, **regexes):
        if not regexes:
            raise ValueError('expected either tag_regex or attrib_regex')

        def getter(parent):
            return parent.find(**regexes)

        def deleter(parent):
            deleteable = parent.find(**regexes)
            if deleteable is not None:
                parent.children.remove(deleteable)

        def setter(parent, child):
            """replace or remove child. If child passed is None, will delete
            first matching child. Otherwise will replace existing child with
            passed child or append to end of children
            """
            if child is None:
                deleter(parent)
                return
            replaceable = parent.find(**regexes)
            if replaceable is None:
                parent.children.append(child)
                return
            i = parent.children.index(replaceable)
            parent.children[i] = child

        return getter, setter, deleter


class SingleAttrib:
    """property-instantiated class to provide get/set/del access for a
    single attrib value within an element. For example, Node provides a
    .text property which accesses its .attrib['TEXT']. If del node.text
    were called, it would replace the attrib value an empty string: ''.
    In this example, attrib_name = 'TEXT', and default_value = ''
    Init this within a class as a property like:
    text = property(*SingleAttrib(attrib_name, default_value))
    """

    def __new__(cls, attrib_name, default_value):

        def getter(element):
            return element.attrib.get(attrib_name, default_value)

        def setter(element, value):
            element.attrib[attrib_name] = value

        def deleter(element):
            element.attrib[attrib_name] = default_value

        return getter, setter, deleter


class Text:
    """text for a node. Sets and gets attrib['TEXT'] for attached node """

    @classmethod
    def setup(cls, TextClass):

        def getter(parent):
            return parent.attrib.get('TEXT', '')

        def setter(parent, text):
            parent.attrib['TEXT'] = text

        def deleter(parent):
            parent.attrib['TEXT'] = ''

        return getter, setter, deleter


class Link:
    """link for a node. Sets and gets attrib['LINK'] for attached node.
    If user links a node, set attrib['LINK'] = node.attrib['ID']
    """

    @classmethod
    def setup(cls, BaseElement):

        def getter(parent):
            return parent.attrib.get('LINK')

        def setter(parent, url):
            if isinstance(url, BaseElement):
                url = url.attrib.get('ID')
            parent.attrib['LINK'] = url

        def deleter(parent):
            parent.attrib['LINK'] = None
            del parent.attrib['LINK']

        return getter, setter, deleter