#!/usr/bin/python
# -*- coding: UTF-8 -*-

from PIL import Image

from MDmisc.multimap import multimap
from MDmisc.string import join

from .config import *
from .exceptions import *
from .labels import LABEL

################################################################################
#
#    Generic functions
#
################################################################################

#    Grayscale Compression Algorithm
GCA = {
    'NONE': "RAW",
    '0': "RAW",
    'WSQ20': 'WSQ',
    '1': "WSQ",
    '2': "JPEGB",
    '3': "JPEGL",
    '4': "JP2",
    '5': "JP2L",
    '6': "PNG"
}

def decode_gca( code ):
    """
        Function to decode the 'Grayscale Compression Algorithm' value passed in
        parameter.
        
        >>> decode_gca( 'NONE' )
        'RAW'
        
        >>> decode_gca( 'JP2' )
        'JP2'
        
        >>> decode_gca( 'HighCompression' )
        Traceback (most recent call last):
            ...
        KeyError
    """
    code = str( code ).upper()
    
    if code in GCA:
        return GCA[ code ]
    
    elif code in GCA.values():
        return code
    
    else:
        raise KeyError

def hexformat( x ):
    return format( x, '02X' )

#    Binary print
def bindump( data, n = 8 ):
    """
        Return the first and last n bytes of a binary data.
        
        >>> bindump( chr(255) * 250000 )
        'FFFFFFFF ... FFFFFFFF (250000 bytes)'
        
        >>> bindump( chr(255) * 250000, 16 )
        'FFFFFFFFFFFFFFFF ... FFFFFFFFFFFFFFFF (250000 bytes)'
    """
    pre = [ data[ i ] for i in xrange( n / 2 ) ]
    post = [ data[ -i ] for i in xrange( n / 2 ) ]
    
    pre = multimap( [ ord, hexformat ], pre )
    post = multimap( [ ord, hexformat ], post )
    
    post = reversed( post )
    
    return "%s ... %s (%d bytes)" % ( join( "", pre ), join( "", post ), len( data ) )

#    Field split
def fieldSplitter( data ):
    """
        Split the input data in a ( tag, ntype, tagid, value ) tuple.
        
        >>> fieldSplitter( "1.002:0501" )
        ('1.002', 1, 2, '0501')
    """
    tag, value = data.split( CO )
    ntype, tagid = tag.split( DO )
    ntype = int( ntype )
    tagid = int( tagid )
    
    return tag, ntype, tagid, value

#    Get label name
def get_label( ntype, tagid, fullname = False ):
    """
        Return the name of a specific field.
        
        >>> get_label( 1, 2 )
        'VER'
        
        >>> get_label( 1, 2, True )
        'Version number'
    """
    index = int( fullname )
    
    try:
        return LABEL[ ntype ][ tagid ][ index ]
    except:
        if not fullname:
            return "   "
        else:
            return ""

#    Alignment function
def leveler( msg, level = 1 ):
    """
        Return an indented string.
        
        >>> leveler( "1.002", 1 )
        '    1.002'
    """
    return "    " * level + msg

#    Tag function
def tagger( ntype, tagid ):
    """
        Return the tag value from a ntype and tag value in parameter.
        
        >>> tagger( 1, 2 )
        '1.002:'
    """
    return "%d.%03d:" % ( ntype, tagid )

def tagSplitter( tag ):
    """
        Split a tag in a list of [ ntype, tagid ].
        
        >>> tagSplitter( "1.002" )
        [1, 2]
    """
    return map( int, tag.split( DO ) )

def printableFieldSeparator( ret ):
    ret = ret.replace( FS, "<FS>" )
    ret = ret.replace( GS, "<GS>" )
    ret = ret.replace( RS, "<RS>" )
    ret = ret.replace( US, "<US>" )
    
    return ret
