#!/usr/bin/python
# -*- coding: UTF-8 -*-

from re import sub

reps = [ ( str( i ), chr( i + 65 ) ) for i in xrange( 0, 6 ) ]


def RLE_encode( data ):
    for old, new in reps:
        data = data.replace( old, new )
    
    def f( m ):
        if len( m.group( 0 ) ) == 1:
            return m.group( 1 )
        else:
            return str( len( m.group( 0 ) ) ) + m.group( 1 )
    
    return sub( r'(.)\1*', f, data )

def RLE_decode( data ):
    ret = sub( r'(\d+)(\D)', lambda m: m.group( 2 ) * int( m.group( 1 ) ), data )
    for new, old in reps:
        ret = ret.replace( old, new )
        
    return ret
