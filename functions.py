#!/usr/bin/env python
#  *-* coding: utf-8 *-*

from string import join

from PIL import Image

from lib.misc.multimap import multimap

try:
    from .config import *
    from .exceptions import *
    from .labels import LABEL
except:
    pass
#     from config import *
#     from exceptions import *
#     from labels import LABEL

################################################################################
#
#    Generic functions
#
################################################################################

#    Grayscale Compression Algorithm
GCA = {
    'NONE': "RAW",
    '0': "RAW",
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
    """
    return GCA[ str( code ) ]

def hexformat( x ):
    return format( x, '02x' )

#    Binary print
def bindump( data, n = 8 ):
    """
        Return the first and last n bytes of a binary data.
        
        >>> bindump( chr(255) * 250000 )
        'ffffffff ... ffffffff (250000 bytes)'
    """
    pre = [ data[ i ] for i in xrange( n / 2 ) ]
    post = [ data[ -i ] for i in xrange( n / 2 ) ]
    
    pre = multimap( [ ord, hexformat ], pre )
    post = multimap( [ ord, hexformat ], post )
    
    post = reversed( post )
    
    return "%s ... %s (%d bytes)" % ( join( pre, "" ), join( post, "" ), len( data ) )

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

#    Field 9.012 to list (and reverse)
def lstTo012( lst ):
    """
        Convert the entire minutiae-table to the 9.012 field format.
        
        >>> lstTo012(
        ...    [['000',  7.85,  7.05, 290, '00', 'A'], 
        ...     ['001', 13.80, 15.30, 155, '00', 'A'], 
        ...     ['002', 11.46, 22.32, 224, '00', 'A'], 
        ...     ['003', 22.61, 25.17, 194, '00', 'A'], 
        ...     ['004',  6.97,  8.48, 153, '00', 'A'], 
        ...     ['005', 12.58, 19.88, 346, '00', 'A'], 
        ...     ['006', 19.69, 19.80, 111, '00', 'A'], 
        ...     ['007', 12.31,  3.87, 147, '00', 'A'], 
        ...     ['008', 13.88, 14.29, 330, '00', 'A'], 
        ...     ['009', 15.47, 22.49, 271, '00', 'A']] 
        ... )
        '000\\x1f07850705290\\x1f00\\x1fA\\x1e001\\x1f13801530155\\x1f00\\x1fA\\x1e002\\x1f11462232224\\x1f00\\x1fA\\x1e003\\x1f22612517194\\x1f00\\x1fA\\x1e004\\x1f06970848153\\x1f00\\x1fA\\x1e005\\x1f12581988346\\x1f00\\x1fA\\x1e006\\x1f19691980111\\x1f00\\x1fA\\x1e007\\x1f12310387147\\x1f00\\x1fA\\x1e008\\x1f13881429330\\x1f00\\x1fA\\x1e009\\x1f15472249271\\x1f00\\x1fA'
    """
    lst = map( lstTo012field, lst )
    lst = join( lst, RS )
     
    return lst

def lstTo012field( lst ):
    """
        Function to convert a minutiae from the minutiae-table to a 9.012 sub-field.
        
        >>> lstTo012field( ['000',  7.85,  7.05, 290, '00', 'A'] )
        '000\\x1f07850705290\\x1f00\\x1fA'
    """
    id, x, y, theta, quality, t = lst
    
    return join( 
        [
            id,
            "%04d%04d%03d" % ( round( float( x ) * 100 ), round( float( y ) * 100 ), theta ),
            quality,
            t
        ],
        US
    )

################################################################################
# 
#    Image processing functions
# 
################################################################################

def RAWToPIL( raw, size = ( 500, 500 ) ):
    """
        Convert a RAW string to PIL object.
        
        >>> RAWToPIL( chr( 255 ) * 250000, ( 500, 500 ) ) #doctest: +ELLIPSIS
        <PIL.Image.Image image mode=L size=500x500 at 0x...>
    """
    return Image.frombytes( 'L', size, raw )

def PILToRAW( pil ):
    """
        Convert a PIL object to RAW string.
        
        >>> p = Image.new( '1', ( 5, 5 ) )
        >>> r = PILToRAW( p )
        >>> r
        '\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'
        >>> len( r )
        25
    """
    return pil.convert( 'L' ).tobytes()
