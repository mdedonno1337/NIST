#!/usr/bin/python
# -*- coding: UTF-8 -*-

from collections import OrderedDict
from copy import deepcopy
from itertools import izip

from MDmisc.elist import flatten
from MDmisc.eobject import eobject
from MDmisc.map_r import map_r
from MDmisc.string import join, join_r

from PIL import Image

from ..traditional.config import *
from ..traditional.exceptions import notImplemented


#    Field 9.012 to list (and reverse)
def lstTo012( lst, format = None ):
    """
        Convert the entire minutiae-table to the 9.012 field format.
        
        :param lst: List of minutiae
        :type lst: list of lists
        
        :param format: Format of the minutiae
        :type format: str
        
        :return: 9.012 field
        :rtype: str
        
        Usage:
            
            >>> from NIST.fingerprint.functions import lstTo012
            >>> lstTo012(
            ...    [[  1,  7.85,  7.05, 290, 0, 'A' ],
            ...     [  2, 13.80, 15.30, 155, 0, 'A' ],
            ...     [  3, 11.46, 22.32, 224, 0, 'A' ],
            ...     [  4, 22.61, 25.17, 194, 0, 'A' ],
            ...     [  5,  6.97,  8.48, 153, 0, 'A' ],
            ...     [  6, 12.58, 19.88, 346, 0, 'A' ],
            ...     [  7, 19.69, 19.80, 111, 0, 'A' ],
            ...     [  8, 12.31,  3.87, 147, 0, 'A' ],
            ...     [  9, 13.88, 14.29, 330, 0, 'A' ],
            ...     [ 10, 15.47, 22.49, 271, 0, 'A' ]]
            ... )
            '1\\x1f07850705290\\x1f0\\x1fA\\x1e2\\x1f13801530155\\x1f0\\x1fA\\x1e3\\x1f11462232224\\x1f0\\x1fA\\x1e4\\x1f22612517194\\x1f0\\x1fA\\x1e5\\x1f06970848153\\x1f0\\x1fA\\x1e6\\x1f12581988346\\x1f0\\x1fA\\x1e7\\x1f19691980111\\x1f0\\x1fA\\x1e8\\x1f12310387147\\x1f0\\x1fA\\x1e9\\x1f13881429330\\x1f0\\x1fA\\x1e10\\x1f15472249271\\x1f0\\x1fA'
            
        The conversion can be done with a list of ( x, y, theta ) coordinates.
        The quality will be set to '00' (expert) and the type to 'A' (Ridge
        ending) for compatibility with most of the AFIS (the type 'D' (Type
        undetermined) is not always well supported).
            
            >>> lstTo012(
            ...    [[  7.85,  7.05, 290 ], 
            ...     [ 13.80, 15.30, 155 ], 
            ...     [ 11.46, 22.32, 224 ], 
            ...     [ 22.61, 25.17, 194 ], 
            ...     [  6.97,  8.48, 153 ], 
            ...     [ 12.58, 19.88, 346 ], 
            ...     [ 19.69, 19.80, 111 ], 
            ...     [ 12.31,  3.87, 147 ], 
            ...     [ 13.88, 14.29, 330 ], 
            ...     [ 15.47, 22.49, 271 ]], 
            ...    format = "xyt"
            ... )
            '1\\x1f07850705290\\x1f00\\x1fA\\x1e2\\x1f13801530155\\x1f00\\x1fA\\x1e3\\x1f11462232224\\x1f00\\x1fA\\x1e4\\x1f22612517194\\x1f00\\x1fA\\x1e5\\x1f06970848153\\x1f00\\x1fA\\x1e6\\x1f12581988346\\x1f00\\x1fA\\x1e7\\x1f19691980111\\x1f00\\x1fA\\x1e8\\x1f12310387147\\x1f00\\x1fA\\x1e9\\x1f13881429330\\x1f00\\x1fA\\x1e10\\x1f15472249271\\x1f00\\x1fA'
            
            >>> lstTo012( [] )
            ''
    """
    if isinstance( lst, list ):
        tmp = AnnotationList()
        tmp.from_list( lst, format = format )
        lst = tmp
        
    if len( lst ) == 0:
        return ""
    
    else:
        try:
            ret = [
                [ m.i, "%04d%04d%03d" % ( round( float( m.x ) * 100 ), round( float( m.y ) * 100 ), m.t ), m.q, m.d ]
                for m in lst
            ]
        
        except:
            ret = []
            i = 1
            for m in lst:
                ret.append( [ i, "%04d%04d%03d" % ( round( float( m.x ) * 100 ), round( float( m.y ) * 100 ), m.t ), '00', 'A' ] )
                i += 1
        
        return join_r( [ US, RS ], ret )

def lstTo137( lst, res = None ):
    """
        Convert the entire minutiae-table to the 9.137 field format.
        
        :param lst: List of minutiae
        :type lst: list of lists
        
        :param format: Format of the minutiae
        :type format: str
        
        :return: 9.012 field
        :rtype: str
        
        Usage:
            
            >>> from NIST.fingerprint.functions import lstTo137
            >>> lstTo137(
            ...    [[  1,  7.85,  7.05, 290, 0, 100 ], 
            ...     [  2, 13.80, 15.30, 155, 0, 100 ], 
            ...     [  3, 11.46, 22.32, 224, 0, 100 ], 
            ...     [  4, 22.61, 25.17, 194, 0, 100 ], 
            ...     [  5,  6.97,  8.48, 153, 0, 100 ], 
            ...     [  6, 12.58, 19.88, 346, 0, 100 ], 
            ...     [  7, 19.69, 19.80, 111, 0, 100 ], 
            ...     [  8, 12.31,  3.87, 147, 0, 100 ], 
            ...     [  9, 13.88, 14.29, 330, 0, 100 ], 
            ...     [ 10, 15.47, 22.49, 271, 0, 100 ]],
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
        
        :param raw: RAW input image.
        :type raw: str
        
        :param size: Size of the image ( width, height ).
        :type size: tuple
        
        :return: Converted PIL image
        :rtype: PIL.Image
        
        Usage:
        
            >>> from NIST.fingerprint.functions import RAWToPIL
            >>> RAWToPIL( chr( 255 ) * ( 500 * 500 ), ( 500, 500 ) ) # doctest: +ELLIPSIS
            <PIL.Image.Image image mode=L size=500x500 at 0x...>
    """
    return Image.frombytes( 'L', size, raw )

def PILToRAW( pil ):
    """
        Convert a PIL object to RAW string.
        
        :param pil: PIL input image.
        :type pil: PIL.Image
        
        :return: RAW formatted image
        :rtype: str
        
        Usage:
            
            >>> from NIST.fingerprint.functions import PILToRAW
            >>> from PIL import Image
            >>> p = Image.new( 'L', ( 500, 500 ), 0 )
            >>> r = PILToRAW( p )
            >>> r == '\\x00' * ( 500 * 500 )
            True
    """
    return pil.convert( 'L' ).tobytes()

def tetraptych( mark, pr, markidc = -1, pridc = -1 ):
    """
        Return an image with the mark and the print in the first row, and the
        corresponding images annotated in the second row.
        
        :param mark: Latent NIST object.
        :type mark: NIST
        
        :param pr: Print NIST object.
        :type pr: NIST
        
        :param markidc: IDC value for the latent NIST object.
        :type markidc: int
        
        :param pridc: IDC value for the print NIST object.
        :type pridc: int
        
        Usage:
        
            >>> from NIST.fingerprint.functions import tetraptych
            >>> tetraptych( mark, pr ) # doctest: +ELLIPSIS
            <PIL.Image.Image image mode=RGB size=1000x1000 at ...>
    """
    
    markidc = mark.checkIDC( 13, markidc )
    
    if 4 in pr.get_ntype():
        pridc = pr.checkIDC( 4, pridc )
    elif 14 in pr.get_ntype():
        pridc = pr.checkIDC( 14, pridc )
    else:
        raise notImplemented
    
    mark_img = mark.get_latent( "PIL", markidc )
    mark_annotated = mark.get_latent_annotated( markidc )
    
    pr_img = pr.get_print( "PIL", pridc )
    pr_annotated = pr.get_print_annotated( pridc )
    
    markwidth, markheight = mark.get_size( markidc )
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
    """
        Transformation the coordinates from millimeters to px.
        
        :param data: Coordinate value.
        :type data: tuple
        
        :param res: Resolution in DPI
        :type res: int
        
        :return: Transformed coordinates.
        :rtype: list of float
        
        Usage:
            
            >>> from NIST.fingerprint.functions import mm2px
            >>> mm2px( ( 12.7, 12.7 ), 500 )
            [250.0, 250.0]
    """
    if hasattr( data, '__iter__' ):
        return map( lambda x: mm2px( x, res ), data )
    else:
        return data / 25.4 * float( res )

def px2mm( data, res ):
    """
        Transformation the coordinates from pixel to millimeters
        
        :param data: Coordinate value.
        :type data: tuple
        
        :param res: Resolution in DPI
        :type res: int
        
        :return: Transformed coordinates.
        :rtype: list of float
        
        Usage:
        
            >>> from NIST.fingerprint.functions import px2mm
            >>> px2mm( ( 250, 250 ), 500 )
            [12.7, 12.7]
    """
    if hasattr( data, '__iter__' ):
        return map( lambda x: px2mm( x, res ), data )
    else:
        return data / float( res ) * 25.4

################################################################################
#
#    Minutia class
#
################################################################################

class Annotation( object ):
    """
        Annotation Class; generic class for Minutia and Core information. This
        class is not designed to be directly used, but should be overloaded with
        some custom class (see :func:`~NIST.fingerprint.functions.Minutia` and
        :func:`~NIST.fingerprint.functions.Core` for more details).
        
        Import:
        
            >>> from NIST.fingerprint.functions import Annotation
        
        Usage:
        
            >>> Annotation( [ 1.0, 2.1, 3.18 ], format = "abc" )
            Annotation( a='1.0', b='2.1', c='3.18' )
            
        By default, if the data is not provided, None is returned:
        
            >>> Annotation( [ 1.0, 2.1, 3.18 ], format = "abcd" )
            Annotation( a='1.0', b='2.1', c='3.18', d='None' )
    """
    def __init__( self, *args, **kwargs ):
        """
            Constructor of the Annotation class. Try to feed the _data variable
            with the first argument passed in the __init__() function.
        """
        self.set_format( **kwargs )
        self._data = OrderedDict( izip( list( self._format ), args[ 0 ] ) )
        
    def set_format( self, **kwargs ):
        """
            Set the format in the _format variable.
            
            :param format: Format of the Annotation object
            :type format: str or list
        """
        self._format = kwargs.get( 'format', 'i' )
    
    def as_list( self ):
        return [ self._data[ key ] for key in self._format ]
        """
            Return a list version of the Annotation object.
            
            :param format: Format to return
            :type format: str or list
            
            :return: List version of the Annotation object.
            :rtype: list
            
            Usage:
                
                >>> from NIST.fingerprint.functions import Annotation
                >>> a = Annotation( [ 1.0, 2.1, 3.18 ], format = "abc" )
                >>> a.as_list()
                [1.0, 2.1, 3.18]
                >>> a.as_list( "ab" )
                [1.0, 2.1]
        """
    
    ############################################################################
    
    def __str__( self ):
        """
            String representation of an Annotation object.
        """
        lst = [ ( f, self._data[ f ] ) for f in self._format ]
        return "%s( %s )" % ( self.__class__.__name__, ", ".join( [ "%s='%s'" % a for a in lst ] ) )
    
    def __repr__( self, *args, **kwargs ):
        return self.__str__( *args, **kwargs )    
    
    def __iter__( self ):
        for f in self._format:
            yield self._data[ f ]

    def __getitem__( self, index ):
        if type( index ) == str:
            try:
                return self._data[ index ]
            
            except KeyError:
                return None
            
        elif type( index ) == int:
            return self._data[ self._data.keys()[ index ] ]
    
    def __iadd__( self, delta ):
        """
            Overlaod of the '+=' operator, allowing to offset an Annotation with
            a tuple ( dx, dy ).
            
            :param delta: Offset to apply 
            
            Usage:
            
                >>> from NIST.fingerprint.functions import Annotation
                >>> a = Annotation( [ 1, 2 ], format = "xy" )
                >>> offset = ( 10, 12 )
                >>> a += offset
                >>> print( a )
                Annotation( x='11', y='14' )
                
            .. note:: a += delta <=> to a = Annotation.__iadd__( a, delta )
        """
        dx, dy = delta
        self.x += dx
        self.y += dy
        
        return self
    
    def __len__( self ):
        return len( self._format )
    
    def __getattr__( self, name ):
        try:
            return self._data[ name ]
        except KeyError:
            try:
                return self.default_values( name )
            except KeyError:
                msg = "'{0}' object has no attribute '{1}'"
                raise AttributeError( msg.format( self.__class__.__name__, name ) )
    
    def __setattr__( self, name, value ):
        if name.startswith( "_" ):
            super( Annotation, self ).__setattr__( name, value )
        
        else:
            self._data[ name ] = value

################################################################################
# 
#    Annotation list class
# 
################################################################################

class AnnotationList( eobject ):
    def __init__( self, data = None ):
        if data != None:
            self._data = data
        else:
            self._data = []
    
    def set_format( self, format ):
        if not format == None:
            for a in self._data:
                a.set_format( format = format )

    def get_by_type( self, designation, format = None ):
        self.set_format( format )
        
        return AnnotationList( [ a for a in self._data if a.d in designation ] )
    
    def as_list( self ):
        return [ a.as_list() for a in self._data ]
    
    def get( self, format ):
        tmp = deepcopy( self )
        tmp.set_format( format )
        return tmp
    
    def append( self, value ):
        self._data.append( value )
    
    def from_list( self, data, format = None ):
        self._data = [ Minutia( d, format = format ) for d in data ]
        try:
            if not "i" in format:
                for id, _ in enumerate( self._data ):
                    self._data[ id ].i = id + 1
        except:
            pass
        
    ############################################################################
    
    def __str__( self ):
        return "[\n%s\n]" % ",\n".join( [ "\t" + str( m ) for m in self._data ] )
    
    def __repr__( self, *args, **kwargs ):
        return self.__str__( *args, **kwargs )
    
    def __iter__( self ):
        for a in self._data:
            yield a
    
    def __getitem__( self, index ):
        return self._data[ index ]
    
    def __setitem__( self, key, value ):
        self._data[ key ] = value
    
    def __len__( self ):
        return len( self._data )
    
    def __iadd__( self, delta ):
        self.apply_to_all( "__iadd__", self._data, delta )
        
        return self
    
################################################################################
# 
#    Minutia and Core objects
# 
################################################################################

class Minutia( Annotation ):
    def set_format( self, **kwargs ):
        format = kwargs.get( 'format', None )
        if format == None:
            format = "ixytqd"

        self._format = format

    def default_values( self, field ):
        return {
            'i': 0,
            'x': 0,
            'y': 0,
            't': 0,
            'q': '00',
            'd': 'A'
        }[ field ]

class Core( Annotation ):
    def set_format( self, **kwargs ):
        self._format = kwargs.get( 'format', "ixy" )
