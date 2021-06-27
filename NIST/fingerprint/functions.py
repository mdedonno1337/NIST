#!/usr/bin/python
# -*- coding: UTF-8 -*-

from collections import OrderedDict, Counter
from copy import deepcopy
from cStringIO import StringIO, InputType, OutputType
from itertools import izip
from math import sqrt
from PIL import Image

import json
import numpy as np

from MDmisc.binary import string_to_hex
from MDmisc.elist import flatten, ifall
from MDmisc.eobject import eobject
from MDmisc.imageprocessing import PILToRAW, RAWToPIL
from MDmisc.map_r import map_r
from MDmisc.string import join, join_r

from ..core.config import RS, US
from ..core.exceptions import notImplemented

try:
    from WSQ import WSQ
    wsq_enable = True

except:
    class WSQ( object ):
        def __init__( self ):
            raise Exception( "WSQ not supported" )
    
    wsq_enable = False

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
        
        This function can not be called with no parameter:
        
            >>> lstTo012( None )
            Traceback (most recent call last):
            ...
            notImplemented
    """
    if isinstance( lst, list ):
        tmp = AnnotationList()
        tmp.from_list( lst, format = format, type = 'Minutia' )
        lst = tmp
        
    if isinstance( lst, AnnotationList ):
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
    
    else:
        raise notImplemented

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

def changeFormatImage( input, outformat, **options ):
    """
        Function to change the format of the input image.
        
        Usage:
        
            >>> from NIST.fingerprint.functions import changeFormatImage
            >>> from hashlib import md5
            >>> from PIL import Image
            >>> from MDmisc.binary import string_to_hex
        
        To convert an PIL image to a RAW string, use the following commands:
        
            >>> imgPIL = Image.new( "L", ( 500, 500 ), 255 )
            >>> imgRAW = changeFormatImage( imgPIL, "RAW" )
            
            >>> md5( imgPIL.tobytes() ).hexdigest()
            '7157c3d901362236afbdd84de3f61007'
            >>> md5( imgRAW ).hexdigest()
            '7157c3d901362236afbdd84de3f61007'
        
        All format supported by PIL are supported as output format:
        
            >>> changeFormatImage( imgPIL, "TIFF" ) # doctest: +ELLIPSIS
            <PIL.TiffImagePlugin.TiffImageFile image mode=L size=500x500 at ...>
            >>> changeFormatImage( imgPIL, "PNG" ) # doctest: +ELLIPSIS
            <PIL.PngImagePlugin.PngImageFile image mode=L size=500x500 at ...>
            
        You can also convert a StringIO buffer:
        
            >>> from cStringIO import StringIO
            >>> imgBuffer = StringIO()
            >>> imgPIL.save( imgBuffer, 'JPEG' )
            >>> imgRAW2 = changeFormatImage( imgBuffer, "RAW" )
            >>> imgRAW == imgRAW2
            True
        
        A `notImplemented` is raised if the input format is not supported or if
        the output format is not implemented in this function or by PIL:
        
            >>> changeFormatImage( None, "RAW" )
            Traceback (most recent call last):
            ...
            notImplemented: Input format not supported
            
            >>> d = changeFormatImage( imgPIL, "WSQ" )
            >>> string_to_hex( d[ 0:4 ] )
            'FFA0FFA8'
            
            >>> md5( d ).hexdigest()
            '8879e56b34aa878dd31f72b5e850d808'
    """
    outformat = outformat.upper()
    
    # Convert the input data to PIL format
    if isinstance( input, Image.Image ):
        img = input
    
    elif isinstance( input, str ):
        try:
            buff = StringIO( input )
            img = Image.open( buff )
            
            if img.format in [ "TGA" ]:
                raise Exception
        
        except:
            if string_to_hex( input[ 0 : 4 ] ) in [ "FFA0FFA4", "FFA0FFA5", "FFA0FFA6", "FFA0FFA2", "FFA0FFA8" ]:
                img = RAWToPIL( WSQ().decode( input ), **options )
                
            else:
                if outformat == "RAW":
                    return input
                else:
                    img = RAWToPIL( input, **options )
    
    elif isinstance( input, ( OutputType, InputType ) ):
        img = Image.open( input )
    
    else:
        raise notImplemented( "Input format not supported" )
    
    # Convert the PIL format to the output format
    if outformat == "PIL":
        return img
    
    elif outformat == "RAW":
        return PILToRAW( img )
    
    elif outformat == "WSQ":
        return WSQ().encode( img, **options )
    
    else:
        try:
            buff = StringIO()
            img.save( buff, format = outformat )
            return Image.open( buff )
        
        except:
            raise notImplemented( "Output format not supported by PIL" )

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
            >>> img = tetraptych( sample_type_13, sample_type_4_tpcard, pridc = 1 )
            >>> img# doctest: +ELLIPSIS
            <PIL.Image.Image image mode=RGB size=1604x1536 at ...>
            
            >>> from hashlib import md5
            >>> md5( img.tobytes() ).hexdigest()
            '3779a044e5a56b56380a895a9a5297ea'
    """
    
    markidc = mark.checkIDC( 13, markidc )
    
    if 4 in pr.get_ntype():
        pridc = pr.checkIDC( 4, pridc )
    elif 14 in pr.get_ntype():
        pridc = pr.checkIDC( 14, pridc )
    elif 13 in pr.get_ntype():
        pridc = pr.checkIDC( 13, pridc )
    else:
        raise notImplemented
    
    mark_img = mark.get_latent( "PIL", markidc )
    mark_annotated = mark.get_latent_annotated( markidc )
    
    pr_img = pr.get_image( "PIL", pridc )
    pr_annotated = pr.get_image_annotated( pridc )
    
    markwidth, markheight = mark.get_size( markidc )
    prwidth, prheight = pr.get_size( pridc )
    
    maxheight = max( markheight, prheight )
    
    new = Image.new( "RGB", ( markwidth + prwidth, 2 * maxheight ), "white" )
    
    new.paste( mark_img, ( 0, 0 ) )
    new.paste( pr_img, ( markwidth, 0 ) )
    new.paste( mark_annotated, ( 0, maxheight ) )
    new.paste( pr_annotated, ( markwidth, maxheight ) )
    
    return new

def diptych( mark, pr, markidc = -1, pridc = -1 ):
    markwidth, markheight = mark.get_size( markidc )
    prwidth, prheight = pr.get_size( pridc )
    maxheight = max( markheight, prheight )
    
    mark_annotated = mark.get_latent_annotated( markidc )
    pr_annotated = pr.get_image_annotated( pridc )
    
    new = Image.new( "RGB", ( markwidth + prwidth, maxheight ), "white" )
    new.paste( mark_annotated, ( 0, 0 ) )
    new.paste( pr_annotated, ( markwidth, 0 ) )
    
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
        
        :cvar defaultformat: Default format to store the Annotation data.
        
        Import:
        
            >>> from NIST.fingerprint.functions import Annotation
        
        Usage:
        
            >>> Annotation( [ 1.0, 2.1, 3.18 ], format = "abc" )
            Annotation( a='1.0', b='2.1', c='3.18' )
            
        By default, if the data is not provided, None is returned:
        
            >>> Annotation( [ 1.0, 2.1, 3.18 ], format = "abcd" )
            Annotation( a='1.0', b='2.1', c='3.18', d='None' )
            
        The Annotation can also be initialized with keyword arguments:
        
            >>> Annotation( a = 1.0, b = 2.1, c = 3.18 )
            Annotation( a='1.0', c='3.18', b='2.1' )
            
        .. note::
            Since the keyword arguments are stored in a dictionary, the order of
            the keys are not ensured. This will be corrected in Python3.6.
            
            >>> Annotation( c = 3.18, b = 2.1, a = 1.0 )
            Annotation( a='1.0', c='3.18', b='2.1' )
    """
    defaultformat = "i"
    
    def __init__( self, *args, **kwargs ):
        """
            Constructor of the Annotation class. Try to feed the _data variable
            with the first argument passed in the __init__() function.
        """
        format = kwargs.pop( "format", None )
        
        self.set_format( format = format )
        
        if kwargs:
            self.set_format( format = kwargs.keys() )
            self._data = OrderedDict( kwargs.iteritems() )
        
        elif len( args ) != 0:
            self._data = OrderedDict( izip( list( self._format ), args[ 0 ] ) )
        
        else:
            self._data = OrderedDict( [] )
        
    def set_format( self, format = None, **kwargs ):
        """
            Set the format in the _format variable.
            
            :param format: Format of the Annotation object
            :type format: str or list
        """
        if format == None:
            format = self.defaultformat
        
        self._format = list( format )
    
    def as_list( self, format = None ):
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
        if format == None:
            format = self._format
            
        return [ self._data[ key ] for key in format ]
    
    def as_json( self ):
        """
            Return the current object as a json string.
            
            :return: Json representation of the current Annotation
            :rtype: str
            
            Usage:
                
                >>> from NIST.fingerprint.functions import Annotation
                >>> a = Annotation( [ 1.0, 2.1, 3.18 ], format = "abc" )
                >>> a.as_json()
                '{"a": 1.0, "b": 2.1, "c": 3.18}'
        """
        return json.dumps( self._data )
    
    ############################################################################
    
    def __str__( self ):
        """
            String representation of an Annotation object. Used by the print
            function.
            
            The string representation is the following::
                
                Annotation( var1='value1', var2='value2', ... )
        """
        lst = [ ( f, self.__getitem__( f ) ) for f in self._format ]
        return "%s( %s )" % ( self.__class__.__name__, ", ".join( [ "%s='%s'" % a for a in lst ] ) )
    
    def __repr__( self, *args, **kwargs ):
        """
            Object representation. This function call the
            :func:`~NIST.fingerprint.functions.Annotation.__str__` function
        """
        return self.__str__( *args, **kwargs )    
    
    def __iter__( self ):
        """
            Overloading of the :func:`__iter__` function, getting the
            information directly in the _data variable.
        """
        for f in self._format:
            yield self._data[ f ]
    
    def get( self, name, default = None ):
        """
            Function to get a particular variable inside the Annotation object.
            
            Let 'a' be defined as follow:
            
                >>> from NIST.fingerprint.functions import Annotation
                >>> a = Annotation( [ 1.0, 2.1, 3.18 ], format = "abc" )
            
            To retrieve the variable 'a', you can either call it with the variable name: 
            
                >>> a.get( 'a' )
                1.0
        """
        try:
            return self.__getattr__( name )
        except:
            return default
    
    def __getitem__( self, index ):
        """
            Function to get an item stored in the Annotation object like in a
            `list` object. If the variable is not present in the _data object,
            'None' is returned.
            
            :param index: Index to retrieve
            :type index: str or int
            
            Let 'a' be defined as follow:
            
                >>> from NIST.fingerprint.functions import Annotation
                >>> a = Annotation( [ 1.0, 2.1, 3.18 ], format = "abc" )
            
            To retrieve the variable 'a', you can either call it with the variable name: 
            
                >>> a[ 'a' ]
                1.0
            
            or use the index in the Annotation object (here, the fist element, ie the index 0): 
             
                >>> a[ 0 ]
                1.0
        """
        try:
            if isinstance( index, str ):
                return self._data[ index ]
                
            elif isinstance( index, int ):
                return self._data[ self._data.keys()[ index ] ]
            
        except KeyError:
            return None
        
    def __iadd__( self, delta ):
        """
            Overload of the '+=' operator, allowing to offset an Annotation with
            a tuple ( dx, dy ).
            
            :param delta: Offset to apply
            :type delta: tuple
            
            Let 'a' be defined as follow:
            
                >>> from NIST.fingerprint.functions import Annotation
                >>> a = Annotation( [ 1, 2, 3 ], format = "xyt" )
                >>> a
                Annotation( x='1', y='2', t='3' )
            
            To shift the Annotation by a distance `offset`, use the following commands. 
            
                >>> offset = ( 10, 12 )
                >>> a += offset
                >>> a
                Annotation( x='11', y='14', t='3' )
            
            .. note:: This function works only for ( x, y ) coordinates. The other variables stores in the `Annotation` object are not changed.
            
            .. note:: The following instructions are equivalent:
                    
                * a += delta <=> a = a.__iadd__( delta )
                * a += delta <=> a = Annotation.__iadd__( a, delta )
                
        """
        dx, dy = delta
        self.x += dx
        self.y += dy
        
        return self
    
    def __len__( self ):
        """
            Get the number of elements to except in the Annotation object (not
            the effective number of objects stored in this particular object).
            
            Let 'a' be defined as follow:
            
                >>> from NIST.fingerprint.functions import Annotation
                >>> a = Annotation( [ 1, 2, 3 ], format = "xyt" )
            
            If the format if changed as follow:
            
                >>> a.set_format( format = "xy" )
            
            then, the excepted length of the Annotation `a` is:
            
                >>> len( a )
                2
                >>> a
                Annotation( x='1', y='2' )
            
            even if the data stored is not changed:
            
                >>> a._data
                OrderedDict([('x', 1), ('y', 2), ('t', 3)])
        """
        return len( self._format )
    
    def __getattr__( self, name ):
        """
            Get a value stored in the Annotation object. If the value is not
            stored in the Annotation object, the 'None' value is returned.
            
            Let 'a' be defined as follow:
            
                >>> from NIST.fingerprint.functions import Annotation
                >>> a = Annotation( [ 1, 2, 3 ], format = "xyt" )
                
            To retrieve the variable 'x', use the following command:
            
                >>> a.x
                1
            
            .. note:: The following instructions are equivalent:
            
                * a.var <=> a.__getattr__( var )
                * a.var <=> Annotation.__getattr__( a, var )
                
            If the variable name is stored in a python variable (dynamic access),
            the value can be retrived as follow:
            
                >>> var = 'x'
                >>> a.__getattr__( var )
                1
        """
        try:
            return self._data[ name ]
        except KeyError:
            try:
                return self.default_values( name )
            except KeyError:
                msg = "'{0}' object has no attribute '{1}'"
                raise AttributeError( msg.format( self.__class__.__name__, name ) )
    
    def __setattr__( self, name, value ):
        """
            Function to set an attribute in the Annotation object.
            
            Let 'a' be defined as follow:
            
                >>> from NIST.fingerprint.functions import Annotation
                >>> a = Annotation( [ 1, 2, 3 ], format = "xyt" )
            
            To change the value of a variable, let say 'x', use the following command:
            
                >>> a.x = 18
                >>> a
                Annotation( x='18', y='2', t='3' )
                
            .. note:: All non-related object variables have to start with '_'.
            
            The privates variables 'format' is defined (by the
            :func:`~NIST.fingerprint.functions.Annotation.set_format`) as follow:
            
                >>> a._format = "xyt"
                >>> a
                Annotation( x='18', y='2', t='3' )
            
            This variable is not related to the Annotation data (ie x, y and t),
            but have to be store in the Annotation object. All privates
            variables are not shone in the string representation.
        """
        if name.startswith( "_" ):
            super( Annotation, self ).__setattr__( name, value )
        
        else:
            self._data[ name ] = value
            
    def __eq__( self, other ):
        """
            Compare the Annotation object with all variables used in the _format
            string. The hidden data is not used while comparing the objects. The
            order of the variables is not important. The comparison is made
            regardess of the type of the data stored.
            
            Usage :
            
                >>> from NIST.fingerprint.functions import Annotation
                >>> a = Annotation( [ 1, 2, 3 ], format = "xyt" )
                >>> b = Annotation( [ 1, 3, 2 ], format = "xty" )
                >>> c = Annotation( [ 1, 2, 3.0 ], format = "xyt" )
                >>> d = Annotation( [ 1, 2, 3.0 ], format = "xyt" )
                >>> d.id = 18
                
                >>> e = Annotation( [ 1, 2, 4 ], format = "xyt" )
                >>> f = Annotation( [ 1, 2 ], format = "xy" )
                
                >>> a == b
                True
                >>> a == c
                True
                >>> a == d
                True
                
                >>> a == e
                False
                >>> a == f
                False
        """
        if Counter( self._format ) != Counter( other._format ):
            return False
        
        else:
            for v in self._format:
                if self.__getattr__( v ) != other.__getattr__( v ):
                    return False
            
            else:
                return True
    
    def __rshift__( self, p ):
        """
            Overload of the '>>' operator to calculate the distance between two
            Annotations (euclidean distance). The couple ( x, y ) is used as
            coordinates.
            
            Usage:
                >>> from NIST.fingerprint.functions import Annotation
                
                >>> a = Annotation( ( 1, 2 ), format = "xy" )
                >>> b = Annotation( ( 2, 3 ), format = "xy" )
                >>> a >> b
                1.4142135623730951
        """
        return sqrt( pow( p.x - self.x, 2 ) + pow( p.y - self.y, 2 ) )
    
################################################################################
# 
#    Annotation list class
# 
################################################################################

class AnnotationList( eobject ):
    """
        AnnotationList class; generic class to store a list of Annotation
        objects. The functions implemented in the AnnotationList class are
        (generally) a wrapper function applied to all Annotation objects stored
        in the AnnotationList object.
    """
    def __init__( self, data = None ):
        """
            Initialization of the AnnotationList object, and set the data if
            provided.
            
            :param data: Input data
            :type data: list of Annotation
        """
        if data != None:
            self._data = data
        else:
            self._data = []
    
    def set_format( self, format ):
        """
            Change the format for all Annotations stored in the AnnotationList
            object.
            
            :param format: Format to change to.
            :type format: str
            
            Usage :
            
                >>> from NIST.fingerprint.functions import AnnotationList
                >>> minutiae = AnnotationList()
                >>> minutiae.from_list( [[ 1, 7.85, 7.05, 290, 0, 'A' ], [ 2, 13.80, 15.30, 155, 0, 'A' ], [ 3, 11.46, 22.32, 224, 0, 'B' ], [ 4, 22.61, 25.17, 194, 0, 'A' ], [ 5, 6.97, 8.48, 153, 0, 'B' ], [ 6, 12.58, 19.88, 346, 0, 'A' ], [ 7, 19.69, 19.80, 111, 0, 'C' ], [ 8, 12.31, 3.87, 147, 0, 'A' ], [ 9, 13.88, 14.29, 330, 0, 'D' ], [ 10, 15.47, 22.49, 271, 0, 'D' ]], format = "ixytqd", type = 'Minutia' )
                
                >>> minutiae.set_format( 'xy' )
                >>> minutiae # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( x='7.85', y='7.05' ),
                    Minutia( x='13.8', y='15.3' ),
                    Minutia( x='11.46', y='22.32' ),
                    Minutia( x='22.61', y='25.17' ),
                    Minutia( x='6.97', y='8.48' ),
                    Minutia( x='12.58', y='19.88' ),
                    Minutia( x='19.69', y='19.8' ),
                    Minutia( x='12.31', y='3.87' ),
                    Minutia( x='13.88', y='14.29' ),
                    Minutia( x='15.47', y='22.49' )
                ]
        """
        if not format == None:
            for a in self._data:
                a.set_format( format = format )
    
    def get_format( self ):
        """
            Get the format of the first Annotation in the AnnotationList
            
            :return: List of values
            :rtype: list
        """
        try:
            return list( self._data[ 0 ]._format )
        except:
            return None
    
    def get_by_type( self, designation, format = None ):
        """
            Filter the content of the AnnotationList by type designation.
            
            :param designation: Type designation to filter upon
            :type designation: str or list
            
            :param format: Format of the AnnotationList to return
            :type format: str or lst
            
            Usage:
            
                >>> from NIST.fingerprint.functions import AnnotationList
                >>> minutiae = AnnotationList()
                >>> minutiae.from_list( [[ 1, 7.85, 7.05, 290, 0, 'A' ], [ 2, 13.80, 15.30, 155, 0, 'A' ], [ 3, 11.46, 22.32, 224, 0, 'B' ], [ 4, 22.61, 25.17, 194, 0, 'A' ], [ 5, 6.97, 8.48, 153, 0, 'B' ], [ 6, 12.58, 19.88, 346, 0, 'A' ], [ 7, 19.69, 19.80, 111, 0, 'C' ], [ 8, 12.31, 3.87, 147, 0, 'A' ], [ 9, 13.88, 14.29, 330, 0, 'D' ], [ 10, 15.47, 22.49, 271, 0, 'D' ]], format = "ixytqd", type = 'Minutia' )
                
                >>> minutiae.get_by_type( 'D' ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='9', x='13.88', y='14.29', t='330', q='0', d='D' ),
                    Minutia( i='10', x='15.47', y='22.49', t='271', q='0', d='D' )
                ]
        """
        self.set_format( format )
        
        return AnnotationList( [ a for a in self._data if a.d in designation ] )
    
    def as_list( self ):
        """
            Return the current object data as list.
            
            :return: List of Annotations
            :rtype: list
            
            Usage:
            
                >>> from NIST.fingerprint.functions import AnnotationList
                >>> minutiae = AnnotationList()
                >>> minutiae.from_list( [[ 1, 7.85, 7.05, 290, 0, 'A' ], [ 2, 13.80, 15.30, 155, 0, 'A' ], [ 3, 11.46, 22.32, 224, 0, 'B' ], [ 4, 22.61, 25.17, 194, 0, 'A' ], [ 5, 6.97, 8.48, 153, 0, 'B' ], [ 6, 12.58, 19.88, 346, 0, 'A' ], [ 7, 19.69, 19.80, 111, 0, 'C' ], [ 8, 12.31, 3.87, 147, 0, 'A' ], [ 9, 13.88, 14.29, 330, 0, 'D' ], [ 10, 15.47, 22.49, 271, 0, 'D' ]], format = "ixytqd", type = 'Minutia' )
                
                >>> minutiae.as_list()
                [[1, 7.85, 7.05, 290, 0, 'A'], [2, 13.8, 15.3, 155, 0, 'A'], [3, 11.46, 22.32, 224, 0, 'B'], [4, 22.61, 25.17, 194, 0, 'A'], [5, 6.97, 8.48, 153, 0, 'B'], [6, 12.58, 19.88, 346, 0, 'A'], [7, 19.69, 19.8, 111, 0, 'C'], [8, 12.31, 3.87, 147, 0, 'A'], [9, 13.88, 14.29, 330, 0, 'D'], [10, 15.47, 22.49, 271, 0, 'D']]

        """
        return [ a.as_list() for a in self._data ]
    
    def as_json( self ):
        """
            Return the current object as a json string.
            
            :return: Json representation of the current AnnotationList
            :rtype: str
            
            Usage:
                
                >>> from NIST.fingerprint.functions import AnnotationList
                >>> minutiae = AnnotationList()
                >>> minutiae.from_list( [[ 1, 7.85, 7.05, 290, 0, 'A' ], [ 2, 13.80, 15.30, 155, 0, 'A' ], [ 3, 11.46, 22.32, 224, 0, 'B' ], [ 4, 22.61, 25.17, 194, 0, 'A' ], [ 5, 6.97, 8.48, 153, 0, 'B' ], [ 6, 12.58, 19.88, 346, 0, 'A' ], [ 7, 19.69, 19.80, 111, 0, 'C' ], [ 8, 12.31, 3.87, 147, 0, 'A' ], [ 9, 13.88, 14.29, 330, 0, 'D' ], [ 10, 15.47, 22.49, 271, 0, 'D' ]], format = "ixytqd", type = 'Minutia' )
                
                >>> minutiae.as_json()
                '[ {"i": 1, "x": 7.85, "y": 7.05, "t": 290, "q": 0, "d": "A"}, {"i": 2, "x": 13.8, "y": 15.3, "t": 155, "q": 0, "d": "A"}, {"i": 3, "x": 11.46, "y": 22.32, "t": 224, "q": 0, "d": "B"}, {"i": 4, "x": 22.61, "y": 25.17, "t": 194, "q": 0, "d": "A"}, {"i": 5, "x": 6.97, "y": 8.48, "t": 153, "q": 0, "d": "B"}, {"i": 6, "x": 12.58, "y": 19.88, "t": 346, "q": 0, "d": "A"}, {"i": 7, "x": 19.69, "y": 19.8, "t": 111, "q": 0, "d": "C"}, {"i": 8, "x": 12.31, "y": 3.87, "t": 147, "q": 0, "d": "A"}, {"i": 9, "x": 13.88, "y": 14.29, "t": 330, "q": 0, "d": "D"}, {"i": 10, "x": 15.47, "y": 22.49, "t": 271, "q": 0, "d": "D"} ]'
        """
        data = ", ".join( [ a.as_json() for a in self._data ] )
        return "[ %s ]" % data
    
    def get( self, format = None ):
        """
            Get a copy of the current object with a specific format.
            
            :param format: Format of the AnnotationList to return.
            :type format: str or lst
            
            :return: A new AnnotationList.
            :rtype: AnnotationList
            
            Usage:
            
                >>> from NIST.fingerprint.functions import AnnotationList
                >>> minutiae = AnnotationList()
                >>> minutiae.from_list( [[ 1, 7.85, 7.05, 290, 0, 'A' ], [ 2, 13.80, 15.30, 155, 0, 'A' ], [ 3, 11.46, 22.32, 224, 0, 'B' ], [ 4, 22.61, 25.17, 194, 0, 'A' ], [ 5, 6.97, 8.48, 153, 0, 'B' ], [ 6, 12.58, 19.88, 346, 0, 'A' ], [ 7, 19.69, 19.80, 111, 0, 'C' ], [ 8, 12.31, 3.87, 147, 0, 'A' ], [ 9, 13.88, 14.29, 330, 0, 'D' ], [ 10, 15.47, 22.49, 271, 0, 'D' ]], format = "ixytqd", type = 'Minutia' )
                
                >>> tmp = minutiae.get()
                >>> tmp == minutiae
                False
            
            .. note::
            
                Since the function return a copy of the current object, the two
                objects are separate in memory, allowing to modify one and not
                the other (reason why `minutiae2` is not equal to `minutiae`,
                even if the content is the same).
        """
        tmp = deepcopy( self )
        tmp.set_format( format )
        return tmp
    
    def append( self, value ):
        """
            Function to append an element at the end of the AnnotationList.
            
            :param value: Annotation to add to the AnnotationList
            :type value: Annotation
            
            Let a the objects `a` and `tmp` be defined as follow:
            
                >>> from NIST.fingerprint.functions import AnnotationList
                
                >>> minutiae = AnnotationList()
                >>> minutiae.from_list( [[ 1, 7.85, 7.05, 290, 0, 'A' ], [ 2, 13.80, 15.30, 155, 0, 'A' ], [ 3, 11.46, 22.32, 224, 0, 'B' ], [ 4, 22.61, 25.17, 194, 0, 'A' ], [ 5, 6.97, 8.48, 153, 0, 'B' ], [ 6, 12.58, 19.88, 346, 0, 'A' ], [ 7, 19.69, 19.80, 111, 0, 'C' ], [ 8, 12.31, 3.87, 147, 0, 'A' ], [ 9, 13.88, 14.29, 330, 0, 'D' ], [ 10, 15.47, 22.49, 271, 0, 'D' ]], format = "ixytqd", type = 'Minutia' )
                
                >>> from NIST.fingerprint.functions import Minutia
                
                >>> a = Minutia( [ 11, 22.67, 1.49, 325, 0, 'A' ], format = 'ixytqd' )
                >>> tmp = minutiae.get_by_type( 'A' )
            
            Then:
            
                >>> tmp.append( a )
                >>> tmp # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A' ),
                    Minutia( i='4', x='22.61', y='25.17', t='194', q='0', d='A' ),
                    Minutia( i='6', x='12.58', y='19.88', t='346', q='0', d='A' ),
                    Minutia( i='8', x='12.31', y='3.87', t='147', q='0', d='A' ),
                    Minutia( i='11', x='22.67', y='1.49', t='325', q='0', d='A' )
                ]
        """
        self._data.append( value )
    
    def remove( self, value ):
        """
            Function to remove a particular Annotation (by value).
            
            Usage:
                
                >>> from NIST.fingerprint.functions import AnnotationList
                >>> minutiae = AnnotationList()
                >>> minutiae.from_list( [[ 1, 7.85, 7.05, 290, 0, 'A' ], [ 2, 13.80, 15.30, 155, 0, 'A' ], [ 3, 11.46, 22.32, 224, 0, 'B' ], [ 4, 22.61, 25.17, 194, 0, 'A' ], [ 5, 6.97, 8.48, 153, 0, 'B' ], [ 6, 12.58, 19.88, 346, 0, 'A' ], [ 7, 19.69, 19.80, 111, 0, 'C' ], [ 8, 12.31, 3.87, 147, 0, 'A' ], [ 9, 13.88, 14.29, 330, 0, 'D' ], [ 10, 15.47, 22.49, 271, 0, 'D' ]], format = "ixytqd", type = 'Minutia' )
                
                >>> from NIST.fingerprint.functions import Minutia
                >>> r = Minutia( [ 8, 12.31, 3.87, 147, 0, 'A' ], format = "ixytqd" )
                >>> minutiae2 = minutiae.get()
                >>> minutiae2.remove( r )
                >>> minutiae2 # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A' ),
                    Minutia( i='3', x='11.46', y='22.32', t='224', q='0', d='B' ),
                    Minutia( i='4', x='22.61', y='25.17', t='194', q='0', d='A' ),
                    Minutia( i='5', x='6.97', y='8.48', t='153', q='0', d='B' ),
                    Minutia( i='6', x='12.58', y='19.88', t='346', q='0', d='A' ),
                    Minutia( i='7', x='19.69', y='19.8', t='111', q='0', d='C' ),
                    Minutia( i='9', x='13.88', y='14.29', t='330', q='0', d='D' ),
                    Minutia( i='10', x='15.47', y='22.49', t='271', q='0', d='D' )
                ]
                
        """
        for i, v in enumerate( self._data ):
            if v == value:
                del self._data[ i ]
    
    def from_list( self, data, format = None, type = "Annotation" ):
        """
            Load the data from a list of lists.
            
            :param data: Data to load in the AnnotationList object.
            :type data: list of lists
            
            :param format: Format of the Annotations to return.
            :type format: str
            
            :param type: Type of Annotations to store in the AnnotationList (Annotation, Minutia, Core).
            :type type: str
            
            Usage:
            
                >>> from NIST.fingerprint.functions import AnnotationList
                >>> lst = [
                ...     [  1, 7.85, 7.05, 290, 0, 'A' ],
                ...     [  2, 13.80, 15.30, 155, 0, 'A' ],
                ...     [  3, 11.46, 22.32, 224, 0, 'B' ],
                ...     [  4, 22.61, 25.17, 194, 0, 'A' ],
                ...     [  5, 6.97, 8.48, 153, 0, 'B' ],
                ...     [  6, 12.58, 19.88, 346, 0, 'A' ],
                ...     [  7, 19.69, 19.80, 111, 0, 'C' ],
                ...     [  8, 12.31, 3.87, 147, 0, 'A' ],
                ...     [  9, 13.88, 14.29, 330, 0, 'D' ],
                ...     [ 10, 15.47, 22.49, 271, 0, 'D' ]
                ... ]
                >>> minutiae = AnnotationList()
                >>> minutiae.from_list( lst, format = 'ixytqd', type = 'Minutia' )
                >>> minutiae # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A' ),
                    Minutia( i='3', x='11.46', y='22.32', t='224', q='0', d='B' ),
                    Minutia( i='4', x='22.61', y='25.17', t='194', q='0', d='A' ),
                    Minutia( i='5', x='6.97', y='8.48', t='153', q='0', d='B' ),
                    Minutia( i='6', x='12.58', y='19.88', t='346', q='0', d='A' ),
                    Minutia( i='7', x='19.69', y='19.8', t='111', q='0', d='C' ),
                    Minutia( i='8', x='12.31', y='3.87', t='147', q='0', d='A' ),
                    Minutia( i='9', x='13.88', y='14.29', t='330', q='0', d='D' ),
                    Minutia( i='10', x='15.47', y='22.49', t='271', q='0', d='D' )
                ]
        """
        try:
            cls = AnnotationTypes[ type ]
            
        except KeyError:
            cls = Annotation
        
        try:
            self._data = [ cls( d, format = format ) for d in data ]
            if not "i" in format:
                for id, _ in enumerate( self._data ):
                    self._data[ id ].i = id + 1
        except:
            pass
    
    def sort_dist_point( self, p ):
        """
            Sort inplace the AnnotationList regarding the distance with a
            particular point p.
            
            Usage:
                
                >>> from NIST.fingerprint.functions import AnnotationList
                >>> minutiae = AnnotationList()
                >>> minutiae.from_list( [[ 1, 7.85, 7.05, 290, 0, 'A' ], [ 2, 13.80, 15.30, 155, 0, 'A' ], [ 3, 11.46, 22.32, 224, 0, 'B' ], [ 4, 22.61, 25.17, 194, 0, 'A' ], [ 5, 6.97, 8.48, 153, 0, 'B' ], [ 6, 12.58, 19.88, 346, 0, 'A' ], [ 7, 19.69, 19.80, 111, 0, 'C' ], [ 8, 12.31, 3.87, 147, 0, 'A' ], [ 9, 13.88, 14.29, 330, 0, 'D' ], [ 10, 15.47, 22.49, 271, 0, 'D' ]], format = "ixytqd", type = 'Minutia' )
                
                >>> from NIST.fingerprint.functions import Point
                
                >>> p = Point( ( 12, 12 ) )
                >>> minutiae.sort_dist_point( p )
                >>> minutiae.get( "xy" ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( x='13.88', y='14.29' ),
                    Minutia( x='13.8', y='15.3' ),
                    Minutia( x='6.97', y='8.48' ),
                    Minutia( x='7.85', y='7.05' ),
                    Minutia( x='12.58', y='19.88' ),
                    Minutia( x='12.31', y='3.87' ),
                    Minutia( x='11.46', y='22.32' ),
                    Minutia( x='19.69', y='19.8' ),
                    Minutia( x='15.47', y='22.49' ),
                    Minutia( x='22.61', y='25.17' )
                ]
        """
        self._data.sort( key = lambda m: m >> p )
    
    def get_n_closest_from_point( self, n, p ):
        """
            Return the n closest Annotations from a particular point p.
            
            :param n: Number of points to return
            :type n: int
            
            :param p: Point
            :type p: Annotation
        """
        tmp = self.get()
        tmp.sort_dist_point( p )
        return tmp[ 0 : n ]
    
    def get_n_furthest_from_point( self, n, p ):
        """
            Return the n closest Annotations from a particular point p.
            
            :param n: Number of points to return
            :type n: int
            
            :param p: Point
            :type p: Annotation
        """
        tmp = self.get()
        tmp.sort_dist_point( p )
        return tmp[ -n : ]
    
    ############################################################################
    
    def __str__( self ):
        """
        Function to generate a string representation of the AnnotationList
        object. This string is similar to the `pprint.pprint` function:
        
            >>> from NIST.fingerprint.functions import AnnotationList
            >>> minutiae = AnnotationList()
            >>> minutiae.from_list( [[ 1, 7.85, 7.05, 290, 0, 'A' ], [ 2, 13.80, 15.30, 155, 0, 'A' ], [ 3, 11.46, 22.32, 224, 0, 'B' ], [ 4, 22.61, 25.17, 194, 0, 'A' ], [ 5, 6.97, 8.48, 153, 0, 'B' ], [ 6, 12.58, 19.88, 346, 0, 'A' ], [ 7, 19.69, 19.80, 111, 0, 'C' ], [ 8, 12.31, 3.87, 147, 0, 'A' ], [ 9, 13.88, 14.29, 330, 0, 'D' ], [ 10, 15.47, 22.49, 271, 0, 'D' ]], format = "ixytqd", type = 'Minutia' )
            
            >>> minutiae # doctest: +NORMALIZE_WHITESPACE
            [
                Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A' ),
                Minutia( i='3', x='11.46', y='22.32', t='224', q='0', d='B' ),
                Minutia( i='4', x='22.61', y='25.17', t='194', q='0', d='A' ),
                Minutia( i='5', x='6.97', y='8.48', t='153', q='0', d='B' ),
                Minutia( i='6', x='12.58', y='19.88', t='346', q='0', d='A' ),
                Minutia( i='7', x='19.69', y='19.8', t='111', q='0', d='C' ),
                Minutia( i='8', x='12.31', y='3.87', t='147', q='0', d='A' ),
                Minutia( i='9', x='13.88', y='14.29', t='330', q='0', d='D' ),
                Minutia( i='10', x='15.47', y='22.49', t='271', q='0', d='D' )
            ]
        """
        
        return "[\n%s\n]" % ",\n".join( [ "\t" + str( m ) for m in self._data ] )
    
    def __repr__( self, *args, **kwargs ):
        """
            Object representation of the AnnotationList. Call the
            :func:`~NIST.fingerprint.functions.AnnotationList.__str__` function.
        """
        return self.__str__( *args, **kwargs )
    
    def __iter__( self ):
        """
            Return an generator function over the data contained in the list.
            
            :return: Data contained in the AnnotationList
            :rtype: generator
        """
        for a in self._data:
            yield a
    
    def __getitem__( self, index ):
        """
            Function to get a specific Annotation from the AnnotationList object.
            
            :param index: Index of the value to retrive.
            :type index: int
        """
        return self._data[ index ]
    
    def __setitem__( self, key, value ):
        """
            Set a value in the AnnotationList object.
            
            :param key: Key to set.
            :type: int
            
            :param value: Value to set.
            :type value: Annotation
        """
        self._data[ key ] = value
    
    def __len__( self ):
        """
            Get the number of Annotations in the AnnotationList.
            
            :return: Number of Annotations in the AnnotataionList object.
            :rtype: int
            
            Usage:
            
            
                >>> from NIST.fingerprint.functions import AnnotationList
                >>> minutiae = AnnotationList()
                >>> minutiae.from_list( [[ 1, 7.85, 7.05, 290, 0, 'A' ], [ 2, 13.80, 15.30, 155, 0, 'A' ], [ 3, 11.46, 22.32, 224, 0, 'B' ], [ 4, 22.61, 25.17, 194, 0, 'A' ], [ 5, 6.97, 8.48, 153, 0, 'B' ], [ 6, 12.58, 19.88, 346, 0, 'A' ], [ 7, 19.69, 19.80, 111, 0, 'C' ], [ 8, 12.31, 3.87, 147, 0, 'A' ], [ 9, 13.88, 14.29, 330, 0, 'D' ], [ 10, 15.47, 22.49, 271, 0, 'D' ]], format = "ixytqd", type = 'Minutia' )
                
                >>> len( minutiae )
                10
        """
        return len( self._data )
    
    def __iadd__( self, delta ):
        """
            Function to call the `__iadd__()` function of each element in the
            AnnotationList object, ie shifting all Annotations by a value of
            `delta`.
            
            :param delta: Offset to apply
            :type delta: tuple
            
            See :func:`NIST.fingerprint.functions.Annotation.__iadd__` for more details.
            
        """
        self.apply_to_all( "__iadd__", self._data, delta )
        
        return self
    
################################################################################
# 
#    Minutia and Core objects
# 
################################################################################

class Minutia( Annotation ):
    """
        Overload of the :func:`NIST.fingerprint.functions.Annotation` class.
    """
    defaultformat = "ixytqd"

    def default_values( self, field ):
        return {
            'i': 0,
            'x': 0,
            'y': 0,
            't': 0,
            'q': '00',
            'd': 'A'
        }[ field ]
    
    def __sub__( self, b ):
        if isinstance( b, Minutia ):
            ret = dMinutia()
            for v in [ 'x', 'y', 't' ]:
                ret.__setattr__( 'd' + v, b.__getattr__( v ) - self.__getattr__( v ) )
            
            return ret
        
        else:
            raise NotImplemented
    
    def __add__( self, b ):
        if isinstance( b, dMinutia ):
            if ifall( [ 'dx', 'dy', 'dt' ], b._format ):
                ret = Minutia( format = "xyt" )
                
                ret.x = b.x - self.x
                ret.y = b.y - self.y
                ret.t = b.t - self.t
            
            elif ifall( [ 't', 'dist' ], b._format ):
                ret = Minutia( format = "xy" )
                
                ret.x = self.x + b.dist * np.cos( b.t / 180.0 * np.pi )
                ret.y = self.y + b.dist * np.sin( b.t / 180.0 * np.pi )
            
            else:
                raise NotImplemented
            
            return ret
        
        else:
            raise NotImplemented
    
class dMinutia( Annotation ):
    defaultformat = [ "dx", "dy", "dt" ]

    def default_values( self, field ):
        return 0

class Core( Annotation ):
    """
        Overload of the :func:`NIST.fingerprint.functions.Annotation` class.
    """
    defaultformat = "xy"

class Delta( Annotation ):
    """
        Overload of the :func:`NIST.fingerprint.functions.Annotation` class.
    """
    defaultformat = "xyabc"

class Point( Annotation ):
    defaultformat = "xy"

################################################################################
# 
#    List of all Annotation objects
# 
################################################################################

AnnotationTypes = {
    'Annotation': Annotation,
    'Minutia': Minutia,
    'Core': Core,
    'dMinutia': dMinutia
}
