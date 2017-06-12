#!/usr/bin/python
# -*- coding: UTF-8 -*-

from NIST.fingerprint.functions import AnnotationList

def add_pairing( lst, pairing ):
    pairing = dict( pairing )

    for m in lst:
        try:
            m.n = pairing[ m.i ]
        except:
            m.n = None
        
    format = list( lst.get_format() )
    if not "n" in format:
        format.append( "n" )
        lst.set_format( format )
    
    lst.__class__ = AnnotationList
    
    return lst
