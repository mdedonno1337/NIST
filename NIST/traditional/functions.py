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
        
        :param code: GCA code to decode
        :type code: str
        
        :return: Decoded GCA value.
        :rtype: str
        
        :raise KeyError: if the GCA code does not exists
        
        Usage:
            
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
    """
        Return an hexadecimal format of the value passed in parameter.
        
        :param x: Value to convert
        :type x: int
        
        :return: Hex representation.
        :rtype: str
        
        Usage:
        
            >>> hexformat( 255 )
            'FF'
    """
    return format( x, '02X' )

#    Binary print
def bindump( data, n = 8 ):
    """
        Return the first and last `n/2` bytes of a binary data, in hexadecimal format.
        
        :param data: Data to strip
        :rype data: str or list
        
        :return: Stripped hex representation
        :rtype: str
        
        Let `data` be a list of all hex values between `00` and `FF`:
            
            >>> data = "".join( [ chr( x ) for x in xrange( 256 ) ] )
        
        The truncated representation will be:
        
            >>> bindump( data )
            '00010203 ... FCFDFEFF (256 bytes)'
            
            >>> bindump( data, 16 )
            '0001020304050607 ... F8F9FAFBFCFDFEFF (256 bytes)'
    """
    pre = [ data[ i ] for i in xrange( n / 2 ) ]
    post = [ data[ -( i + 1 ) ] for i in xrange( n / 2 ) ]
    
    pre = multimap( [ ord, hexformat ], pre )
    post = multimap( [ ord, hexformat ], post )
    
    post = reversed( post )
    
    return "%s ... %s (%d bytes)" % ( join( "", pre ), join( "", post ), len( data ) )

#    Field split
def fieldSplitter( data ):
    """
        Split the input data in a ( tag, ntype, tagid, value ) tuple.
        
        :param data: Input tagid:value to strip
        :type data: str
        
        :return: Splitted value
        :rtype: tuple
        
        Usage:
        
            >>> fieldSplitter( "1.002:0300" )
            ('1.002', 1, 2, '0300')
    """
    tag, value = data.split( CO )
    ntype, tagid = tag.split( DO )
    ntype = int( ntype )
    tagid = int( tagid )
    
    return tag, ntype, tagid, value

#    Get label name
def get_label( ntype, tagid, fullname = False ):
    """
        Return the (full) name of a specific field.
        
        :param ntype: ntype
        :type ntype: int
        
        :param tagid: Field ID
        :type tagid: int
        
        :param fullname: Get the full name of the field
        :type fullname: boolean
        
        :return: Field (full) name
        :rtype: str
        
        Usage:
        
            >>> get_label( 1, 2 )
            'VER'
            
            >>> get_label( 1, 2, fullname = True )
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
        
        :param msg: Message to indent
        :type msg: str
        
        :param level: Level to indent (number of indentation)
        :type level: int
        
        :return: Formatted string
        :rtype: str
        
        Usage:
        
            >>> leveler( "1.002", 1 )
            '    1.002'
    """
    return "    " * level + msg

#    Tag function
def tagger( ntype, tagid ):
    """
        Return the tag value from a ntype and tag value in parameter.
        
        :param ntype: ntype value
        :type ntype: int
        
        :param tagid: Field id
        :type tagid: int
        
        :return: Formatted tag
        :rtype: str
        
        Usage:
        
            >>> tagger( 1, 2 )
            '1.002:'
    """
    return "%d.%03d:" % ( ntype, tagid )

def tagSplitter( tag ):
    """
        Split a tag in a list of [ ntype, tagid ].
        
        :param tag: Tag string
        :type tag: str
        
        :return: Splitted tag
        :rtype: tuple
        
        >>> tagSplitter( "1.002" )
        (1, 2)
        >>> tagSplitter( ( 1, 2 ) )
        (1, 2)
    """
    if isinstance( tag, str ):
        tag = tag.split( DO )
        
    if isinstance( tag, ( tuple, list ) ):
        return tuple( map( int, tag ) )
    
    else:
        raise notImplemented

def printableFieldSeparator( data ):
    """
        Replace non printable character (FS, GS, RS and US) to printables
        characters (<FS>, <GS>, <RS> and <US>).
        
        :param data: Data to format
        :type data: str
        
        :return: Formatted string
        :rtype: str
        
        Usage:
        
            >>> data = " / ".join( [ FS, GS, RS, US ] )
            >>> printableFieldSeparator( data )
            '<FS> / <GS> / <RS> / <US>'
    """
    rep = [ ( FS, '<FS>' ), ( GS, '<GS>' ), ( RS, '<RS>' ), ( US, '<US>' ) ]
    
    for old, new in rep:
        data = data.replace( old, new )
    
    return data

def split( str, num ):
    return [ str[ start : start + num ] for start in xrange( 0, len( str ), num ) ]
