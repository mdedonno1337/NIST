#!/usr/bin/python
# -*- coding: UTF-8 -*-

from MDmisc.elist import flatten
from MDmisc.map_r import map_r
from MDmisc.string import join, join_r

from PIL import Image

from ..traditional.config import *


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
    ret = [
        [ id, "%04d%04d%03d" % ( round( float( x ) * 100 ), round( float( y ) * 100 ), theta ), q, d ]
        for id, x, y, theta, q, d in lst
    ]
    
    return join_r( [ US, RS ], ret )

def lstTo137( lst, res = None ):
    """
        Convert the entire minutiae-table to the 9.137 field format.
        
        >>> lstTo137(
        ...    [[ 1,  7.85,  7.05, 290, '0', '100' ], 
        ...     [ 2, 13.80, 15.30, 155, '0', '100' ], 
        ...     [ 3, 11.46, 22.32, 224, '0', '100' ], 
        ...     [ 4, 22.61, 25.17, 194, '0', '100' ], 
        ...     [ 5,  6.97,  8.48, 153, '0', '100' ], 
        ...     [ 6, 12.58, 19.88, 346, '0', '100' ], 
        ...     [ 7, 19.69, 19.80, 111, '0', '100' ], 
        ...     [ 8, 12.31,  3.87, 147, '0', '100' ], 
        ...     [ 9, 13.88, 14.29, 330, '0', '100' ], 
        ...     [10, 15.47, 22.49, 271, '0', '100' ]],
        ...    500
        ... )
        '1\\x1f154\\x1f138\\x1f290\\x1f0\\x1f100\\x1e2\\x1f271\\x1f301\\x1f155\\x1f0\\x1f100\\x1e3\\x1f225\\x1f439\\x1f224\\x1f0\\x1f100\\x1e4\\x1f445\\x1f495\\x1f194\\x1f0\\x1f100\\x1e5\\x1f137\\x1f166\\x1f153\\x1f0\\x1f100\\x1e6\\x1f247\\x1f391\\x1f346\\x1f0\\x1f100\\x1e7\\x1f387\\x1f389\\x1f111\\x1f0\\x1f100\\x1e8\\x1f242\\x1f76\\x1f147\\x1f0\\x1f100\\x1e9\\x1f273\\x1f281\\x1f330\\x1f0\\x1f100\\x1e10\\x1f304\\x1f442\\x1f271\\x1f0\\x1f100'
    """
    
    if float in map( type, flatten( lst ) ) or res:
        lst = [
            [ id, mm2px( x , res ), mm2px( y, res ), theta, q, d ]
            for id, x, y, theta, q, d in lst
        ]
    
    lst = map_r( int, lst )
    
    return join_r( [ US, RS ], lst )

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

def tetraptych( mark, pr, pridc = -1 ):
    """
        Return an image with the mark and the print in the first row, and the
        corresponding images annotated in the second row.
        
                    +++++++++++++++++++++++++++++++++++++++
                    +                  +                  +
                    +                  +                  +
                    +                  +                  +
                    +       mark       +       print      +
                    +                  +                  +
                    +                  +                  +
                    +                  +                  +
                    +++++++++++++++++++++++++++++++++++++++
                    +                  +                  +
                    +                  +                  +
                    +                  +                  +
                    +       mark       +       print      +
                    +    annotated     +     annotated    +
                    +                  +                  +
                    +                  +                  +
                    +                  +                  +
                    +++++++++++++++++++++++++++++++++++++++
        
    """
    mark_img = mark.get_latent( "PIL" )
    mark_annotated = mark.get_latent_annotated()
    
    pr_img = pr.get_print( "PIL", pridc )
    pr_annotated = pr.get_print_annotated( pridc )
    
    markwidth, markheight = mark.get_size()
    prwidth, prheight = pr.get_size( pridc )
    
    maxheight = max( markheight, prheight )
    
    new = Image.new( "RGB", ( markwidth + prwidth, 2 * maxheight ), "white" )
    
    new.paste( mark_img, ( 0, 0 ) )
    new.paste( pr_img, ( markwidth, 0 ) )
    new.paste( mark_annotated, ( 0, maxheight ) )
    new.paste( pr_annotated, ( markwidth, maxheight ) )
    
    return new

################################################################################
#    
#    Coordinates changes
#    
################################################################################

def mm2px( data, res ):
    if hasattr( data, '__iter__' ):
        return map( lambda x: mm2px( x, res ), data )
    else:
        return data / 25.4 * float( res )

def px2mm( data, res ):
    if hasattr( data, '__iter__' ):
        return map( lambda x: px2mm( x, res ), data )
    else:
        return data / float( res ) * 25.4
