'''
Created on Nov 13, 2009

@author: Cory Zue
'''

from __future__ import absolute_import

from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement

from django.db import models

class SerializableModel():
    '''A serializable model.
       Override the ATTRS and ELEMS property on the to introspect 
       out the attrs and elems.  These should be dictionaries of 
       the form: 
       { attr_name: model_property,
         attr_name: model_property }
       and 
       { elem_name: model_property,
         elem_name: model_property }
       '''
    # these two fields determine how the model is displayed as XML
    # the key is the name of the attribute/element, the value is
    # the field/property used to display it.  
    ATTRS = {}
    ELEMS = {}
    # TODO: foreign keys?
    
    def to_element(self):
        """Get this as an xml element"""
        return to_element(self)
    
    def to_xml(self):
        return ElementTree.tostring(self.to_element())
        

def to_element(model):
    """Converts a SerializableModel to xml.
       Uses the class name as the root tag.
    """
    root_name = model.__class__.__name__
    top_element = Element(root_name)
    for attr_name, model_attr in model.ATTRS.items():
        top_element.set(attr_name, str(getattr(model, model_attr, "")))
    for elem_name, model_attr in model.ELEMS.items():
        sub_elt = SubElement(top_element, elem_name)
        sub_elt.text = str(getattr(model, model_attr, ""))
    return top_element 
