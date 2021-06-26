#!/usr/bin/python
# -*- coding: UTF-8 -*-

from PIL import Image

from MDmisc.multimap import multimap
from MDmisc.string import join
from MDmisc.binary import int_to_bin, bin_to_int

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
    '6': "PNG",
    'JPEG2KC': "JP2",
}

rGCA = {
    'RAW': 0,
    'WSQ': 1,
    'WSQ20': 1,
    'JPEGB': 2,
    'JPEGL': 3,
    'JP2': 4,
    'JP2L': 5,
    'PNG': 6,
    'JPEG2KC': 4,
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
            
            >>> from NIST.core.functions import decode_gca
            
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

def encode_gca( code ):
    """
        Encodes the value of the 'Grayscale Compression Algorithm' passed in
        parameter. This function does the reverse fo the `decode_gca` function.
        
            >>> from NIST.core.functions import encode_gca
            >>> encode_gca( "RAW" )
            0
            >>> encode_gca( "WSQ" )
            1
            >>> encode_gca( "WSQ20" )
            1
            >>> encode_gca( "JP2" )
            4
            >>> encode_gca( "HighCompression" )
            Traceback (most recent call last):
                ...
            KeyError
    """
    code = str( code ).upper()
    
    if code in rGCA:
        return rGCA[ code ]
    
    else:
        raise KeyError

def decode_fgp( code, only_first = False, separator = "/" ):
    """
        Decode the integer value storing the Finger Position to a readable list
        of positions codes. This function implements the standard for the
        fields 3.004, 4.004, 5.004 and 6.004.
        
        The storage of the data is done in a binary format. A total of 6 bytes
        is used to store the possible 6 potentiels fingers. Each byte encode
        one possible finger using the code described in the Table 12 of the
        standard (only using the numbes 0 to 14 for fingers). The non-used
        fields shall be set to 255.

        Example:
        
            14:
                bin:    00001110 11111111 11111111 11111111 11111111 11111111 (16492674416639)
                dec:          14      255      255      255      255      255
            
            0:
                bin:    00000000 11111111 11111111 11111111 11111111 11111111 (1099511627775)
                dec:           0      255      255      255      255      255
            
            14/7/8:
                bin:    00001110 00000111 00001000 11111111 11111111 11111111 (15423378554879)
                dec:          14        7        8      255      255      255
        
        Usage:
        
            >>> from NIST.core.functions import decode_fgp
            >>> decode_fgp( 16492674416639 )
            '14'
            >>> decode_fgp( 1099511627775 )
            '0'
            >>> decode_fgp( 15423378554879 )
            '14/7/8'
            >>> decode_fgp( 15423378554879, only_first = True )
            '14'
            >>> decode_fgp( 15423378554879, separator = "_" )
            '14_7_8'
    """
    code = int( code )
    
    # Get the binary representation, padded to 6 bytes
    code = int_to_bin( code, 6 * 8 )
    
    # Split in chunks of 8 bites
    code = [ code[ i:i + 8 ] for i in xrange( 0, len( code ), 8 ) ]
    
    # Convert each chunk to decimal
    code = [ bin_to_int( c ) for c in code ]
    
    # Remove the right padding
    code = [ str( c ) for c in code if c != 255 ]
    
    if only_first:
        return code[ 0 ]
    
    else:
        return join( separator, code )

def encode_fgp( code, separator = "/" ):
    """
        Encode the string value storing the Finger Position to the correct
        integer value. This function implements the standard for the fields
        3.004, 4.004, 5.004 and 6.004.
        
        Reverse function of the `decode_fgp` function; check the corresponding
        documentation.
        
        :param code: FGP code to encode
        :type code: str, int, list, tuple
        
        :return: Encoded FGP value.
        :rtype: int
        
        :raise Exception: if the FGP is not in the interval [ 0 , 14 ]
        
        Usage:
        
            >>> from NIST.core.functions import encode_fgp
            >>> encode_fgp( "14" )
            16492674416639
            >>> encode_fgp( "0" )
            1099511627775
            >>> encode_fgp( 0 )
            1099511627775
            >>> encode_fgp( '14/7/8' )
            15423378554879
            >>> encode_fgp( [ 14, 7, 8 ] )
            15423378554879
            >>> encode_fgp( ( 14, 7, 8 ) )
            15423378554879
            >>> encode_fgp( '14:7:8', separator = ":" )
            15423378554879
            >>> encode_fgp( '-7' )
            Traceback (most recent call last):
                ...
            Exception: Value can not be smaller than 0
            >>> encode_fgp( '15' )
            Traceback (most recent call last):
                ...
            Exception: Value can not be bigger than 14
    """
    # Convert to string as needed, if not a iterable
    if not isinstance( code, ( str, list, tuple, ) ):
        code = str( code )
    
    # Split the string to a list, as needed
    if not isinstance( code, ( list, tuple, ) ):
        code = code.split( separator )
        
    # Cast all values to integer
    code = map( int, code )
    
    # Check for the min (0) and max value (14)
    for v in code:
        if v < 0:
            raise Exception( "Value can not be smaller than 0" )
        if v > 14:
            raise Exception( "Value can not be bigger than 14" )
    
    # Expand the list with placeholders (255), and keep only the 6 first elements
    code.extend( [ 255 ] * 6 )
    code = code[ 0:6 ]
    
    # Convert the values to binary
    code = [ int_to_bin( c, 8 ) for c in code ]
    
    # Convert back the value to integer
    code = "".join( code )
    code = bin_to_int( code )
    
    return code

def hexformat( x ):
    """
        Return an hexadecimal format of the value passed in parameter.
        
        :param x: Value to convert
        :type x: int
        
        :return: Hex representation.
        :rtype: str
        
        Usage:
        
            >>> from NIST.core.functions import hexformat
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
        
        Usage:
        
            >>> from NIST.core.functions import bindump
            >>> data = "".join( [ chr( x ) for x in xrange( 256 ) ] )
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
        
            >>> from NIST.core.functions import fieldSplitter, printableFieldSeparator
            >>> fieldSplitter( "1.002:0300" )
            ('1.002', 1, 2, '0300')
            >>> s = fieldSplitter( "20.019:00:00:00.000\x1f00:00:00.001\x1e00:20:05.000\x1f01:00:00.500" )
            >>> map( printableFieldSeparator, s )
            ['20.019', 20, 19, '00:00:00.000<US>00:00:00.001<RS>00:20:05.000<US>01:00:00.500']
    """
    tag, value = data.split( CO, 1 )
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
        
            >>> from NIST.core.functions import get_label
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
        
            >>> from NIST.core.functions import leveler
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
        
            >>> from NIST.core.functions import tagger
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
        
        Usage:
        
            >>> from NIST.core.functions import tagSplitter
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
        characters (<FS>, <GS>, <RS> and <US>) for string input. If the input
        is not a string, then the value will be returned directly without any
        changes.
        
        :param data: Data to format
        :type data: any
        
        :return: Formatted string
        :rtype: same as input
        
        Usage:
        
            >>> from NIST.core.config import FS, GS, RS, US
            >>> from NIST.core.functions import printableFieldSeparator
            
            >>> data = " / ".join( [ FS, GS, RS, US ] )
            >>> printableFieldSeparator( data )
            '<FS> / <GS> / <RS> / <US>'
            >>> printableFieldSeparator( "String without any of the special characters" )
            'String without any of the special characters'
            >>> printableFieldSeparator( 1337 )
            1337
    """
    rep = [ ( FS, '<FS>' ), ( GS, '<GS>' ), ( RS, '<RS>' ), ( US, '<US>' ) ]
    
    if isinstance( data, ( str, ) ):
        for old, new in rep:
            data = data.replace( old, new )
    
    return data

def split( data, chunks_size ):
    """
        Split the input `data` parameter in chunks of length `chunks_size`.

        Usage:

            >>> from NIST.core.functions import split
            >>> split( "000102030405060708090A0B0C0D0E0F", 4 )
            ['0001', '0203', '0405', '0607', '0809', '0A0B', '0C0D', '0E0F']
            >>> split( "000102030405060708090A0B0C0D0E", 4 )
            ['0001', '0203', '0405', '0607', '0809', '0A0B', '0C0D', '0E']
    """
    return [ data[ start : start + chunks_size ] for start in xrange( 0, len( data ), chunks_size ) ]
