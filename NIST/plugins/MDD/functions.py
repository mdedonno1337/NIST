#!/usr/bin/python
# -*- coding: UTF-8 -*-

from MDmisc.edict import edict

from ...fingerprint.functions import AnnotationList

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

def get_minutiae_in_pairing_order( mark, ref ):
    r_p = edict( ref.get_pairing() ).reverse()
    m_p = edict( mark.get_pairing() ).reverse()
    
    keys = [ key for key in list(r_p.keys()) if key != "None" ]
    
    src = [ ref.get_minutia_by_id( r_p[ key ], "xy" ) for key in keys ]
    dst = [ mark.get_minutia_by_id( m_p[ key ], "xy" ) for key in keys ]
    
    return src, dst
