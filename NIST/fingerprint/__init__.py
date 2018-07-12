#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import absolute_import, division

from cStringIO import StringIO
from math import cos, pi, sin
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor
from scipy.spatial.qhull import ConvexHull

import fuckit
import os
import numpy as np

from MDmisc.deprecated import deprecated
from MDmisc.ebool import xor
from MDmisc.eint import str_int_cmp
from MDmisc.elist import ifany, map_r
from MDmisc.imageprocessing import RAWToPIL
from MDmisc.logger import debug
from MDmisc.string import upper, split_r, join
from PMlib.misc import minmaxXY, shift_list

from .exceptions import minutiaeFormatNotSupported
from .functions import *
from .voidType import voidType
from ..core.config import RS, US, FS, default_origin
from ..core.exceptions import *
from ..core.functions import decode_gca
from ..traditional import NIST as NIST_traditional

try:
    from WSQ import WSQ
    wsq_enable = True

except:
    class WSQ( object ):
        def __init__( self ):
            raise Exception( "WSQ not supported" )
    
    wsq_enable = False

voidType.update( voidType )

################################################################################
# 
#    Automatic detection of NIST format
# 
################################################################################

def NISTf_auto( *args, **kwargs ):
    for t in [ NISTf ]:
        try:
            return t( *args, **kwargs )
        except:
            continue
    
    else:
        raise Exception( "NIST format not detected" )

################################################################################
# 
#    Traditional fingerprint NIST object
# 
################################################################################

class NISTf( NIST_traditional ):
    """
        Overload of the :class:`NIST.traditional.NIST` class. This class
        overload the main class to implement fingerprint oriented functions.
        
        :cvar str imgdir: Directory to strore the images (minutiae annotations).
        :cvar str minutiaeformat: Default minutia format. 
    """
    def __init__( self, *args, **kwargs ):
        """
            Constructor function. Call the constructor of the
            :func:`NIST.traditional.NIST` module, and try to initiate a new
            latent or print object (see :func:`NIST.fingerprint.NISTf.init_new`
            for more details).
        """
        self.imgdir = os.path.split( os.path.abspath( __file__ ) )[ 0 ] + "/images"
        
        self.minutiaeformat = "ixytqd"
        
        super( NISTf, self ).__init__( *args, **kwargs )
        
        if kwargs:
            try:
                self.init_new( *args, **kwargs )
            except:
                pass
        
    ############################################################################
    # 
    #    Cleaning and resetting functions
    # 
    ############################################################################
     
    def clean( self ):
        """
            Function to clean all unused fields in the self.data variable. This
            function try to clean the minutiae stored in the current NIST
            object, and call the :func:`NIST.traditional.NIST.clean` function.
            
            Usage:
                
                >>> mark2 = mark.get()
                >>> mark2.clean()
        """
        debug.info( "Cleaning the NIST object" )
        
        #    Check the minutiae
        if 9 in self.get_ntype():
            self.checkMinutiae()
        
        #    Super cleaning
        super( NISTf, self ).clean()
        
    def patch_to_standard( self ):
        """
            Check some requirements for the NIST file. Fields checked:
            
                * 1.011 and 1.012
                * 4.005
                * 9.004
            
            This function call the :func:`NIST.traditional.NIST.patch_to_standard`
            function afterward.
        """
        ntypes = self.get_ntype()
        
        #    Type-01
        #    1.011 and 1.012
        #        For transactions that do not contain Type-3 through Type-7
        #        fingerprint image records, this field shall be set to "00.00"
        if not ifany( [ 3, 4, 5, 6, 7 ], ntypes ):
            debug.debug( "Fields 1.011 and 1.012 patched: no Type-03 through Type-07 in this NIST file", 1 )
            self.set_field( "1.011", "00.00" )
            self.set_field( "1.012", "00.00" )
        
        #    Type-04
        if 4 in ntypes:
            for idc in self.get_idc( 4 ):
                #    4.005
                #        The minimum scanning resolution was defined in
                #        ANSI/NIST- ITL 1-2007 as "19.69 ppmm plus or minus 0.20
                #        ppmm (500 ppi plus or minus 5 ppi)." Therefore, if the
                #        image scanning resolution corresponds to the Appendix F
                #        certification level (See Table 14 Class resolution with
                #        defined tolerance), a 0 shall be entered in this field.
                #        
                #        If the resolution of the Type-04 is in 500DPI +- 1%,
                #        then the 4.005 then field is set to 0, otherwise 1.
                debug.debug( "Set the conformity with the Appendix F certification level for Type-04 image", 1 )
                if 19.49 < float( self.get_field( "1.011" ) ) < 19.89:
                    self.set_field( "4.005", "0", idc )
                else:
                    self.set_field( "4.005", "1", idc )
         
        #    Type-09
        if 9 in ntypes:
            for idc in self.get_idc( 9 ):
                #    9.004
                #        This field shall contain an "S" to indicate that the
                #        minutiae are formatted as specified by the standard
                #        Type-9 logical record field descriptions. This field
                #        shall contain a "U" to indicate that the minutiae are
                #        formatted in vendor-specific or M1-378 terms
                if any( x in [ 5, 6, 7, 8, 9, 10, 11, 12 ] for x in self.data[ 9 ][ idc ].keys() ):
                    debug.debug( "minutiae are formatted as specified by the standard Type-9 logical record field descriptions", 1 )
                    self.set_field( "9.004", "S", idc )
                else:
                    debug.debug( "minutiae are formatted in vendor-specific or M1-378 terms", 1 )
                    self.set_field( "9.004", "U", idc )
        
        #    Generic function to patch to standard
        super( NISTf, self ).patch_to_standard()
    
    ############################################################################
    # 
    #    Misc functions
    # 
    ############################################################################
    
    def get_idc_for_fpc( self, ntype, fpc ):
        idc = None
        
        fields = {
            4: 4,
            13: 13,
            14: 13,
            15: 13,
        }
        
        if ntype not in fields.keys():
            raise notImplemented
        
        else:
            idcs = self.data[ ntype ].keys()
            
            for idc in idcs:
                if int( self.get_field( ( ntype, fields[ ntype ] ), idc ) ) == int( fpc ):
                    return idc
            
            else:
                raise idcNotFound
        
    ############################################################################
    #
    #    Minutia functions
    #
    ############################################################################
    
    def get_minutiae( self, format = None, idc = -1, **options ):
        """
            Get the minutiae information from the field 9.012 for the IDC passed
            in argument.
            
            :param format: Format of the minutiae to return.
            :type format: str or list
            
            :param idc: IDC value.
            :type idc: int
            
            :return: List of minutiae
            :rtype: AnnotationList
            
            The parameter 'format' allow to select the data to extract:
            
                * i: Index number
                * x: X coordinate
                * y: Y coordinate
                * t: Angle theta
                * d: Type designation
                * q: Quality
            
            The 'format' parameter is optional. The IDC value can be passed in
            parameter even without format. The default format ('ixytdq') will be
            used.
            
            To get all information, dont speficy any format:
            
                >>> mark2 = mark.get()
                >>> mark2.get_minutiae() # doctest: +NORMALIZE_WHITESPACE
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
                >>> [ m.as_list() for m in mark.get_minutiae() ]
                [['1', 7.85, 7.05, 290, '0', 'A'], ['2', 13.8, 15.3, 155, '0', 'A'], ['3', 11.46, 22.32, 224, '0', 'B'], ['4', 22.61, 25.17, 194, '0', 'A'], ['5', 6.97, 8.48, 153, '0', 'B'], ['6', 12.58, 19.88, 346, '0', 'A'], ['7', 19.69, 19.8, 111, '0', 'C'], ['8', 12.31, 3.87, 147, '0', 'A'], ['9', 13.88, 14.29, 330, '0', 'D'], ['10', 15.47, 22.49, 271, '0', 'D']]
            
            The format parameter is used by the :func:`~NIST.fingerprint.functions.AnnotationsList`
            object to sort the fields returned.
        """
        # If the 'format' value is an int, then the function is called without
        # the 'format' argument, but the IDC is passed instead.
        if isinstance( format, int ):
            idc, format = format, self.minutiaeformat
        
        # Options processing
        field = options.get( "field", None )
        
        if field == None:
            for tag in [ "9.012", "9.023", "9.311" ]:
                if self.has_tag( tag, idc ):
                    field = tag
                    break
                
            else:
                return AnnotationList()
        
        asfield = options.get( "asfield", None ) or field
        
        # Minutiae data
        minutiae = self.get_field( field, idc )
        lst = self.process_minutiae_field( minutiae, asfield, idc )
        lst.set_format( format )
        return lst
    
    def get_minutiae_all( self, format = None ):
        """
            Return the minutiae for all 10 fingers. If the idc is not present in
            the NIST object, i.e. the finger is missing, an empty list of
            minutiae is returned, to complete the tenprint card.
            
            :param format: Format of the Minutiae to return.
            :type format: str or tuple
            
            :return: List of AnnotationList
            :rtype: list
            
            To get all minutiae for all finger stored in a NIST object:
            
                >>> pr.get_minutiae_all() # doctest: +NORMALIZE_WHITESPACE
                [[
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
                ], [
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
                ], [], [], [], [], [], [], [], []]
            
            If the NIST object does not contain a Type04, Type14 or Type13
            record, the function will rise an notImplemented exception:
            
                >>> mark2 = mark.get()
                >>> mark2.get_minutiae_all() # doctest: +NORMALIZE_WHITESPACE
                [[
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
                ], [], [], [], [], [], [], [], [], []]
        """
        if ifany( [ 4, 14 ], self.get_ntype() ):
            if format == None:
                format = self.minutiaeformat
                
            ret = []
            
            for idc in xrange( 1, 11 ):
                try:
                    ret.append( self.get_minutiae( format = format, idc = idc ) )
                except idcNotFound:
                    ret.append( [] )
            
            return ret
        
        elif 13 in self.get_ntype():
            ret = [ [] ] * 10
            ret[ 0 ] = self.get_minutiae( format = format )
            return ret
        
        else:
            raise notImplemented
    
    def process_minutiae_field( self, minutiae, field, idc = -1 ):
        lst = AnnotationList()
        
        if minutiae != None:
            if field == "9.012":
                # Get the minutiae string, without the final <FS> character.
                minutiae = minutiae.replace( FS, "" )
                
                for m in split_r( [ RS, US ], minutiae ):
                    if m == [ '' ]:
                        break
                    
                    else:
                        id, xyt, q, d = m
                        
                        d = d.upper()
                        
                        x = int( xyt[ 0:4 ] ) / 100
                        y = int( xyt[ 4:8 ] ) / 100
                        t = int( xyt[ 8:11 ] )
            
                        lst.append( Minutia( [ id, x, y, t, q, d ], format = "ixytqd" ) )
            
            elif field == "9.023":
                # Get the minutiae string, without the final <FS> character.
                minutiae = minutiae.replace( FS, "" )
                
                h = self.get_height( idc ) * 25.4 / self.get_resolution( idc )
                
                for m in split_r( [ RS, US ], minutiae ):
                    if m == [ '' ]:
                        break
                    
                    else:
                        id, xyt, q, d = m
                        
                        d = d.upper()
                        
                        x = int( xyt[ 0:4 ] ) / 100
                        y = int( xyt[ 4:8 ] ) / 100
                        t = int( xyt[ 8:11 ] )
                        
                        y = h - y
                        t = ( t + 180 ) % 360
                        
                        lst.append( Minutia( [ id, x, y, t, q, d ], format = "ixytqd" ) )
                
            elif field == "9.331":
                for m in split_r( [ RS, US ], minutiae ):
                    if m == [ '' ]:
                        break
                    
                    else:
                        x, y, theta, d, dr, dt = m
                        
                        x = int( x ) / 100
                        y = int( y ) / 100
                        y = ( self.get_height( idc ) / self.get_resolution( idc ) * 25.4 ) - y
                        theta = ( int( theta ) + 180 ) % 360 
                        
                        dr = int( dr )
                        dt = int( dt )
                        
                        lst.append( Minutia( [ x, y, theta, d, dr, dt ], format = "xytdab" ) )
            
        return lst
            
    def get_minutia_by_id( self, id, format = None, idc = -1 ):
        """
            Return a minutia based on the id
            
            :param id: Identifier of the minutia
            :type id: str or int
            
            :param format: Format of the minutiae to return.
            :type format: str or list
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Particular Minutia
            :rtype: Minutia
            
            To get the minutiae '1':
            
                >>> mark2 = mark.get()
                >>> mark2.get_minutia_by_id( "1" )
                Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' )
            
            The format can also be specified as follow:
            
                >>> mark2.get_minutia_by_id( "1", "xy" )
                Minutia( x='7.85', y='7.05' )
            
            If the IDC value is specified instead of the 'format' parameter, the
            format is set to the defalut value:
            
                >>> mark2.get_minutia_by_id( "1", 1 )
                Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' )
                
            If the id is not found in the NIST object, the value 'None' is returned:
            
                >>> mark2.get_minutia_by_id( "1337" ) == None
                True
        """
        if isinstance( format, int ):
            idc, format = format, self.minutiaeformat
        
        if format == None:
            format = self.minutiaeformat
        
        for m in self.get_minutiae( idc = idc ):
            if int( m.i ) == int( id ):
                t = Minutia( m )
                t.set_format( format = format )
                return t
        
        else:
            return None
    
    def get_minutiae_by_type( self, designation, format = None, idc = -1 ):
        """
            Filter the minutiae list by type
            
            :param designation: Type designation to keep
            :type designation: str or list
            
            :param format: Format of the minutiae to return.
            :type format: str or list
            
            :param idc: IDC value.
            :type idc: int
            
            :return: List of minutiae
            :rtype: AnnotationList
            
            To get only the minutiae with the type designation set as 'D' (unknown):
            
                >>> mark.get_minutiae_by_type( "D" ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='9', x='13.88', y='14.29', t='330', q='0', d='D' ),
                    Minutia( i='10', x='15.47', y='22.49', t='271', q='0', d='D' )
                ]
        """
        return self.get_minutiae( idc = idc ).get_by_type( designation, format )
    
    def get_minutiaeCount( self, idc = -1 ):
        """
            Return the number of minutiae stored in the current NIST object.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Number of minutiae
            :rtype: int
            
            Usage:
                >>> mark2 = mark.get()
                >>> mark2.get_minutiaeCount()
                10
            
                >>> mark2.delete_ntype( 9 )
                >>> mark2.get_minutiaeCount() == None
                True
        """
        try:
            return int( self.get_field( "9.010", idc ) )
        except:
            return None
    
    def get_cores( self, idc = -1 ):
        """
            Process and return the coordinate of the cores.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: List of cores
            :rtype: AnnotationList
            
            Usage:
            
                >>> mark.get_cores() # doctest: +NORMALIZE_WHITESPACE
                [
                    Core( x='12.5', y='18.7' )
                ]
            
            The function returns 'None' if no cores are stored in the NIST object.
            
                >>> pr.get_cores() == None
                True
        """
        try:
            cores = self.get_field( "9.008", idc ).split( RS )
            
            ret = AnnotationList()
            for c in cores:
                x = int( c[ 0:4 ] ) / 100
                y = int( c[ 4:8 ] ) / 100
                
                ret.append( Core( [ x, y ] ) )
                
            return ret
        
        except:
            return None
    
    def get_delta( self, idc = -1 ):
        """
            Process and return the coordinate of the deltas.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: List of deltas
            :rtype: AnnotationList
        """
        try:
            deltas = self.get_field( "9.009", idc ).split( RS )
            
            ret = AnnotationList()
            for c in deltas:
                x = int( c[ 0:4 ] ) / 100
                y = int( c[ 4:8 ] ) / 100
                
                ret.append( Delta( [ x, y ] ) )
                
            return ret
        
        except:
            return None
    
    def set_cores( self, data, idc = -1 ):
        """
            Set the core position in field 9.008. The data passed in parameter
            can be a single core position, or a list of cores (the cores will be
            stored in the field 9.008, separated by a RS separator).
            
            :param data: List of cores coordinates
            :type data: list
            
            :param idc: IDC value.
            :type idc: int
            
            :return: If the value have been set (without double check).
            :rtype: boolean
            
            Usage:
            
                >>> mark2 = mark.get()
                >>> pr2 = pr.get()
            
            The cores can be set with a simple list (or tuple):
            
                >>> mark2.set_cores( [ 10.0, 12.7 ], 1 )
                True
                >>> mark2.get_cores() # doctest: +NORMALIZE_WHITESPACE
                [
                    Core( x='10.0', y='12.7' )
                ]
            
            A list of lists (for multiples cores):
            
                >>> mark2.set_cores( [ [ 12.5, 18.7 ], [ 10.0, 12.7 ] ], 1 )
                True
                >>> mark2.get_cores() # doctest: +NORMALIZE_WHITESPACE
                [
                    Core( x='12.5', y='18.7' ),
                    Core( x='10.0', y='12.7' )
                ]
            
            With an AnnotationList object:
            
                >>> cores # doctest: +NORMALIZE_WHITESPACE
                [
                    Core( x='12.5', y='18.7' ),
                    Core( x='10.0', y='12.7' )
                ]                
                >>> pr2.set_cores( cores, 1 )
                True
                >>> pr2.get_cores( 1 ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Core( x='12.5', y='18.7' ),
                    Core( x='10.0', y='12.7' )
                ]
            
            If no data is passed to the function, 'False' is returned:
                
                >>> mark2.set_cores( None )
                False
                >>> mark2.set_cores( [] )
                False
            
            If the format is not supported, the functions raises an
            formatNotSupported Exception:
            
                >>> mark2.set_cores( "sample/cores.txt" )
                Traceback (most recent call last):
                ...
                formatNotSupported
        """
        idc = self.checkIDC( 9, idc )
        
        def format( data ):
            x, y = data
            x *= 100
            y *= 100
            
            x = int( x )
            y = int( y )
            
            return "%04d%04d" % ( x, y )
        
        if data == None or len( data ) == 0:
            return False
        
        elif isinstance( data[ 0 ], ( int, float ) ):
            data = [ format( data ) ]
        
        elif isinstance( data[ 0 ], ( Core, list, tuple ) ):
            data = map( format, data )
        
        else:
            raise formatNotSupported
        
        data = join( RS, data )
        
        self.set_field( "9.008", data, idc )
        
        return True
    
    def set_minutiae( self, data, idc = -1 ):
        """
            Set the minutiae in the field 9.012.
            
            :param data: List of minutiae coordinates
            :type data: AnnotationList or str
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Number of minutiae added to the NIST object
            :rtype: int
            
            :raise minutiaeFormatNotSupported: if the format is not supported
            
            Usage:
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
                >>> mark2 = mark.get()
                >>> mark2.set_minutiae( minutiae, 1 )
                10
            
            The parameter 'data' can be a list or an AnnotationList. Otherwise,
            the function will raise a minutiaeFormatNotSupported Exception.
            
                >>> mark2.set_minutiae( [ 12, 13, 14 ], 1 )
                Traceback (most recent call last):
                ...
                minutiaeFormatNotSupported
        """
        idc = self.checkIDC( 9, idc )
        
        if isinstance( data, AnnotationList ):
            data = lstTo012( data )
        
        if data == "":
            with fuckit:
                self.delete( "9.012", idc )
                self.delete( "9.010", idc )
                
            return 0
        
        if isinstance( data, str ):
            self.set_field( "9.012", data, idc )
            
            minnum = len( data.split( RS ) )
            self.set_field( "9.010", minnum, idc )
            
            return minnum
        
        else:
            raise minutiaeFormatNotSupported
    
    def checkMinutiae( self, idc = -1 ):
        """
            Check if all minutiae are on the image. If a minutiae is outside the
            image, it will be removed.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: List of minutiae after clean-up
            :rtype: AnnotationList
            
            
            >>> mark2 = mark.get()
            >>> mark2.checkMinutiae() # doctest: +NORMALIZE_WHITESPACE
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
            >>> pr2 = pr.get()
            >>> pr2.checkMinutiae() # doctest: +NORMALIZE_WHITESPACE
            [[
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
            ], [
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
            ]]
        """
        try:
            idc = self.checkIDC( 9, idc )
        except needIDC:
            return [ self.checkMinutiae( idc ) for idc in self.get_idc( 9 ) ]
        else:
            try:
                if self.get_field( "9.012", idc ) == None:
                    return None
                
                elif self.get_minutiaeCount( idc ) == 0:
                    return
                else:
                    try:
                        w = self.px2mm( self.get_width( idc ), idc )
                        h = self.px2mm( self.get_height( idc ), idc )
                    
                    except notImplemented:
                        return self.get_minutiae( idc = idc )
                      
                    else:
                        id = 0
                        lst = AnnotationList()
                        
                        for m in self.get_minutiae( idc = idc ):
                            if ( not m.x < 0 and not m.x > w ) and ( not m.y < 0 and not m.y > h ):
                                id += 1
                                m.i = id
                                lst.append( m )
                        
                        self.set_field( "9.010", id, idc )
                        self.set_field( "9.012", lstTo012( lst ), idc )
                        
                        return lst
            
            except idcNotFound:
                debug.error( "checkMinutiae() : IDC %s not found - Checks ignored" )
    
    def filter_minutiae( self, idc = -1, invert = False, inplace = False, *args, **kwargs ):
        """
            Filter the AnnotationList of minutiae according to the parameters
            passed as kwarg.
            
            :param idc: IDC value.
            :type idc: int
            
            :param invert: Invert (or not) the criteria of filtering
            :type invert: boolean
            
            :param inplace: Make the changes in-place
            :type inplace: boolean
            
            :param args: Positional arguments
            :param kwargs: Keyword arguments
            
            To get the list filtered by designation, retriving only Ridge ending (A)
            and Bifurcation (B):
            
                >>> mark2 = mark.get()
                >>> mark2.filter_minutiae( d = "AB" ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A' ),
                    Minutia( i='3', x='11.46', y='22.32', t='224', q='0', d='B' ),
                    Minutia( i='4', x='22.61', y='25.17', t='194', q='0', d='A' ),
                    Minutia( i='5', x='6.97', y='8.48', t='153', q='0', d='B' ),
                    Minutia( i='6', x='12.58', y='19.88', t='346', q='0', d='A' ),
                    Minutia( i='8', x='12.31', y='3.87', t='147', q='0', d='A' )
                ]
            
            To get the list filtered by designation, removing Type undetermined (D):
            
                >>> mark2.filter_minutiae( d = "D", invert = True ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A' ),
                    Minutia( i='3', x='11.46', y='22.32', t='224', q='0', d='B' ),
                    Minutia( i='4', x='22.61', y='25.17', t='194', q='0', d='A' ),
                    Minutia( i='5', x='6.97', y='8.48', t='153', q='0', d='B' ),
                    Minutia( i='6', x='12.58', y='19.88', t='346', q='0', d='A' ),
                    Minutia( i='7', x='19.69', y='19.8', t='111', q='0', d='C' ),
                    Minutia( i='8', x='12.31', y='3.87', t='147', q='0', d='A' )
                ]
                
            To get only the Minutiae id 1 and 5:
            
                >>> mark2.filter_minutiae( i = [ "1", "5" ] ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='5', x='6.97', y='8.48', t='153', q='0', d='B' )
                ]
        """
        tofilter = [ ( key, value ) for key, value in kwargs.iteritems() ]
        if len( tofilter ) == 0:
            return self.get_minutiae( idc = idc )
        
        else:
            lst = AnnotationList()
            for m in self.get_minutiae( idc = idc ):
                for key, value in tofilter: 
                    if xor( m.__getattr__( key ) in value, invert ):
                        if m not in lst:
                            lst.append( m )
            
            if inplace:
                self.set_minutiae( lst, idc )
            
            return lst
    
    ############################################################################
    # 
    #    Image processing
    # 
    ############################################################################
    
    #    Size
    def get_size( self, idc = -1 ):
        """
            Get a python-tuple representing the size of the image.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Horizontal and vertical size in px.
            :rtype: tuple of int
            
            Usage:
            
                >>> mark.get_size()
                (500, 500)
        """
        return ( self.get_width( idc ), self.get_height( idc ) )
    
    def get_width( self, idc = -1 ):
        """
            Return the width of the image.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Width
            :rtype: int
            
            Usage:
            
                >>> mark.get_width()
                500
        """
        ntypes = self.get_ntype()
        
        for ntype in [ 13, 4, 14, 15, 16 ]:
            if ntype in ntypes:
                try:
                    return int( self.get_field( ( ntype, 6 ), idc ) )
                except:
                    continue
        
        else:
            raise notImplemented
    
    def get_height( self, idc = -1 ):
        """
            Return the height of the image.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Height
            :rtype: int
            
            Usage:
            
                >>> mark.get_height()
                500
        """
        ntypes = self.get_ntype()
        
        for ntype in [ 13, 4, 14, 15, 16 ]:
            if ntype in ntypes:
                try:
                    return int( self.get_field( ( ntype, 7 ), idc ) )
                except:
                    continue
            
        else:
            raise notImplemented
    
    #    Resolution
    def get_resolution( self, idc = -1 ):
        """
            Return the (horizontal) resolution of image in DPI.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Resolution in DPI
            :rtype: int
            
            Usage:
            
                >>> mark.get_resolution()
                500
        """
        ntypes = self.get_ntype()
        
        if 4 in ntypes and self.has_idc( 4, idc ):
            return int( round( float( self.get_field( "1.011" ) ) * 25.4 ) )
        
        else:
            for ntype in [ 13, 14, 15 ]:
                try:
                    c = self.get_field( ( ntype, 8 ), idc )
                    d = self.get_field( ( ntype, 9 ), idc )
                    
                    if c == '1':
                        return int( d )
                    else:
                        return int( round( float( d / 10 * 25.4 ) ) )
                
                except:
                    continue
        
            else:
                raise notImplemented
    
    def set_resolution( self, res, idc = -1 ):
        """
            Set the resolution in DPI.
            
            :param idc: IDC value.
            :type idc: int
            
            Usage:
                
                >>> mark2 = mark.get()
                >>> mark2.set_resolution( 500 )
                
        """
        ntypes = self.get_ntype()
        res = int( res )
        
        if 4 in ntypes:
            self.set_fields( [ "1.011", "1.012" ], "%2.2f" % ( res / 25.4 ) )
            
        elif 13 in ntypes:
            self.set_field( "13.008", "1", idc )
            self.set_field( "13.009", res, idc )
            self.set_field( "13.010", res, idc )
            
        elif 14 in ntypes:
            self.set_field( "14.008", "1", idc )
            self.set_field( "14.009", res, idc )
            self.set_field( "14.010", res, idc )
            
        else:
            raise notImplemented 
    
    #    Compression
    def get_compression( self, idc = -1 ):
        """
            Get the compression used in the latent image.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Compression method
            :rtype: str
            
            Usage:
            
                >>> mark.get_compression()
                'RAW'
        """
        ntypes = self.get_ntype()
        
        if 13 in ntypes:
            gca = self.get_field( "13.011", idc )
        
        elif 4 in ntypes:
            gca = self.get_field( "4.008", idc )
        
        else:
            raise notImplemented
        
        return decode_gca( gca )
    
    ############################################################################
    # 
    #    Misc image processing
    # 
    ############################################################################
    
    def annotate( self, image, data, type = None, res = None, idc = -1, **options ):
        """
            Function to annotate the image with the data passed in argument.
            
            :param image: Non annotated image
            :type image: PIL.Image
            
            :param data: Data used to annotate the image
            :type data: AnnotationList
            
            :param type: Type of annotation (minutiae or center).
            :type type: str
            
            :param res: Resolution in DPI.
            :type res: int
            
            Usage:
            
                >>> mark.annotate( mark.get_latent( 'PIL' ), mark.get_minutiae(), "minutiae" ) # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        if isinstance( data, Annotation ):
            data = AnnotationList( [ data ] )
        
        if data != None and len( data ) != 0:
            # Input image
            image = image.convert( "RGBA" )
            width, height = image.size
            
            # Annotation layer
            annotationLayer = Image.new( 'RGBA', ( width, height ), ( 255, 255, 255, 0 ) )
            annotationLayerDraw = ImageDraw.Draw( annotationLayer )
            
            # Colors
            colour = options.get( "colour", "red" )
            if isinstance( colour, str ):
                colour = ImageColor.getrgb( colour )
            
            alpha = options.get( "alpha", 255 )
            if alpha != 255:
                if isinstance( alpha, float ):
                    if alpha < 1.0:
                        alpha *= 255
                    
                    alpha = int( alpha )
                
                colour += ( alpha, )
            
            yellow = ( 255, 255, 50, alpha )
            black = ( 0, 0, 0, alpha )
            
            # Resolution determination
            if res == None:
                try:
                    res, _ = image.info[ 'dpi' ]
                except:
                    res = self.get_resolution( idc )
            
            # Resize factor for the minutiae
            fac = res / 2000
            
            # Markers
            markers = {}
            for file in [ "end", "bifurcation", "center", "undetermined" ]:
                tmp = Image.open( self.imgdir + "/" + file + ".png" )
                newsize = ( int( tmp.size[ 0 ] * fac ), int( tmp.size[ 1 ] * fac ) )
                markers[ file ] = tmp.resize( newsize, Image.BICUBIC ).convert( "L" )
            
            # Annotations processing
            if type == "minutiae":
                for m in data: 
                    cx = m.x / 25.4 * res
                    cy = m.y / 25.4 * res
                    cy = height - cy
                    
                    theta = m.t
                    
                    if m.d == 'A':
                        markertype = 'end'
                    elif m.d == 'B':
                        markertype = 'bifurcation'
                    else:
                        markertype = 'undetermined'
                    
                    markerminutia = markers[ markertype ].rotate( theta, Image.BICUBIC, True )
                    offsetx = markerminutia.size[ 0 ] / 2
                    offsety = markerminutia.size[ 1 ] / 2
                    
                    endcolor = Image.new( 'RGBA', markerminutia.size, colour )
                    
                    annotationLayer.paste( endcolor, ( int( cx - offsetx ), int( cy - offsety ) ), mask = markerminutia )
            
            elif type == "minutiadata" or "variable" in options.keys():
                fontfactor = options.get( "size", 1 )
                font = ImageFont.truetype( "./fonts/arial.ttf", size = int( fontfactor * self.get_resolution( idc ) * 15 / 500 ) )
                
                dx, dy = options.get( "offset", ( 0, 0 ) )
                variable = options.get( "variable", "i" )
                
                for m in data:
                    cx = m.x / 25.4 * res
                    cy = m.y / 25.4 * res
                    cy = height - cy
                    
                    annotationLayerDraw.text( 
                        ( cx + dx, cy + dy ),
                        str( m.get( variable, "" ) ),
                        colour,
                        font = font
                    )
                
            elif type == "center":
                for m in data:
                    cx = m.x / 25.4 * res
                    cy = m.y / 25.4 * res
                    cy = height - cy
                    
                    offsetx = markers[ 'center' ].size[ 0 ] / 2
                    offsety = markers[ 'center' ].size[ 1 ] / 2
                    
                    centercolor = Image.new( 'RGBA', markers[ 'center' ].size, yellow )
                    
                    annotationLayer.paste( centercolor, ( int( cx - offsetx ), int( cy - offsety ) ), mask = markers[ 'center' ] )
            
            elif type == "delta":
                for m in data:
                    cx = m.x / 25.4 * res
                    cy = m.y / 25.4 * res
                    cy = height - cy
                    
                    for theta in [ m.a, m.b, m.c ]:
                        end2 = markers[ 'end' ].rotate( theta + 180, Image.BICUBIC, True )
                        offsetx = end2.size[ 0 ] / 2
                        offsety = end2.size[ 1 ] / 2
                        
                        endcolor = Image.new( 'RGBA', end2.size, yellow )
                        
                        annotationLayer.paste( endcolor, ( int( cx - offsetx ), int( cy - offsety ) ), mask = end2 )
            
            elif type == "title":
                imagedraw = ImageDraw.Draw( image )
                font = ImageFont.truetype( "./fonts/arial.ttf", size = int( self.get_resolution( idc ) * 15 / 500 ) )
                colour = options.get( "colour", black )
                pos = options.get( "offset", ( 0, 0 ) )
                imagedraw.text( 
                    pos,
                    str( data ),
                    colour,
                    font = font
                )
            
            elif type == None:
                return image
            
            else:
                raise notImplemented
            
            image = Image.alpha_composite( image, annotationLayer )
            image = image.convert( "RGB" )
        
        return image
    
    ############################################################################
    # 
    #    Latent processing
    # 
    ############################################################################
    
    def get_latent( self, format = 'RAW', idc = -1 ):
        """
            Return the image in the format passed in parameter (RAW or PIL).
            
            :param format: Format of the returned image
            :type format: str
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Latent image
            :rtype: PIL.Image
            
            Usage:
            
                >>> mark.get_latent( 'PIL' ) # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=L size=500x500 at ...>
                
                >>> raw = mark.get_latent( 'RAW' )
                >>> raw == '\\xFF' * 250000
                True
        """
        format = upper( format )
        
        idc = self.checkIDC( 13, idc )
        
        gca = decode_gca( self.get_field( "13.011", idc ) )
        
        imgdata = self.get_field( "13.999", idc )
        
        if imgdata == None:
            imgdata = Image.new( "L", self.get_size( idc ), 255 )
            
        return changeFormatImage( 
            imgdata,
            format,
            size = self.get_size( idc ),
            res = self.get_resolution( idc )
        )

    def export_latent( self, f, idc = -1 ):
        """
            Export the latent fingermark image to a file on disk.
            
            :param f: Output file
            :type f: str
            
            :param idc: IDC value.
            :type idc: int
            
            :return: File correctly written on disk
            :rtype: boolean
            
            Usage:
            
                >>> mark.export_latent( "./tmp/mark.jpeg" )
                True
        """
        idc = self.checkIDC( 13, idc )
        res = self.get_resolution( idc )
        
        with fuckit:
            os.makedirs( os.path.dirname( f ) )
        
        self.get_latent( "PIL", idc ).save( f, dpi = ( res, res ) )
        return os.path.isfile( f )
    
    def export_latent_annotated( self, f, idc = -1 ):
        """
            Export the latent fingermark annotated to file.
            
            :param f: Output file
            :type f: str
            
            :param idc: IDC value.
            :type idc: int
            
            :return: File correctly written on disk
            :rtype: boolean
            
            Usage:
            
                >>> mark.export_latent( "./tmp/mark-annotated.jpeg" )
                True
        """
        idc = self.checkIDC( 13, idc )
        res = self.get_resolution( idc )
        
        with fuckit:
            os.makedirs( os.path.dirname( f ) )
        
        self.get_latent_annotated( idc ).save( f, dpi = ( res, res ) )
        return os.path.isfile( f )
    
    def export_latent_diptych( self, f, idc = -1 ):
        """
            Export the latent diptych to file.
            
            :param f: Output file
            :type f: str
        """
        self.get_latent_diptych( idc ).save( f )
    
    def get_latent_annotated( self, idc = -1, **options ):
        """
            Function to return the annotated latent.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Annotated fingermark
            :rtype: PIL.Image
            
            Usage:
            
                >>> mark.get_latent_annotated() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        img = options.get( "img", self.get_latent( 'PIL', idc ) )
        res = self.get_resolution( idc )
        
        with fuckit:
            img = self.annotate( img, self.get_minutiae( idc = idc, **options ), "minutiae", res, idc, **options )
        
        with fuckit:
            img = self.annotate( img, self.get_cores( idc ), "center", res, idc, **options )
        
        with fuckit:
            img = self.annotate( img, self.get_delta( idc ), "delta", res, idc, **options )
        
        return img
    
    def get_latent_hull( self, idc = -1, linewidth = None, **options ):
        """
            Annotate the convex Hull on the latent image. This convex Hull is
            calculated based on the minutiae stored in the NIST object.
             
            :param idc: IDC value.
            :type idc: int
             
            :param linewidth: Width of the convex Hull line.
            :type linewidth: int
             
            :return: Latent annotated with the convex Hull
            :rtype: PIL.Image
             
            Usage:
                 
                >>> mark.get_latent_hull() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        img = options.get( "img", self.get_latent( "PIL", idc ) )
        img = img.convert( "RGB" )
        draw = ImageDraw.Draw( img )
        
        try:
            xy = [ ( m.x, m.y ) for m in self.get_minutiae( idc = idc ) ]
            xy = np.asarray( xy )
            
            dilatation_factor = options.get( "dilatation_factor", 1 )
            if dilatation_factor != 1:
                delta = minmaxXY( xy )
                tmp = shift_list( xy, delta, True )
                tmp = np.asarray( tmp )
                tmp *= dilatation_factor
                tmp = shift_list( tmp, delta )
                xy = np.asarray( tmp )
            
            hull = ConvexHull( xy )
              
            res = self.get_resolution( idc )
            height = self.get_height()
              
            if linewidth == None:
                linewidth = res / 40
            linewidth = int( linewidth )
              
            for simplex in hull.simplices:
                t1, t2 = xy[ simplex, ] * res / 25.4
                a, b = t1
                c, d = t2
                  
                b = height - b
                d = height - d
                  
                a, b, c, d = map( int, ( a, b, c, d ) )
                  
                draw.line( ( a, b, c, d ), fill = ( 255, 0, 0 ), width = linewidth )
        except:
            pass
              
        return img
    
    def get_latent_diptych( self, idc = -1, **options ):
        """
            Function to return the diptych of the latent fingermark (latent and
            annotated latent)
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Latent fingermark diptych
            :rtype: PIL.Image
            
            Usage:
            
                >>> mark.get_latent_diptych() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=1000x500 at ...>
        """
        img = self.get_latent( 'PIL', idc )
        anno = self.get_latent_annotated( idc, **options )
        
        new = Image.new( "RGB", ( img.size[ 0 ] * 2, img.size[ 1 ] ), "white" )
        
        new.paste( img, ( 0, 0 ) )
        new.paste( anno, ( img.size[ 0 ], 0 ) )
        
        return new
     
    def get_latent_triptych( self, content = None, idc = -1, **options ):
        idc = self.checkIDC( 13, idc )
          
        if content == "hull":
            third = self.get_latent_hull( idc )
          
            diptych = self.get_latent_diptych( idc, **options )
              
            new = Image.new( "RGB", ( self.get_width( idc ) * 3, self.get_height( idc ) ), "white" )
            new.paste( diptych, ( 0, 0 ) )
            new.paste( third, ( diptych.size[ 0 ], 0 ) )
              
            return new
        
        else:
            raise notImplemented
    
    def set_latent( self, image = None, res = 500, idc = -1, **options ):
        """
            Detect the type of image passed in parameter and store it in the
            13.999 field. If no image is passed in argument, an empty image is
            set in the NIST object.
            
            :param image: Input image to store in the NIST object.
            :type image: PIL.Image or str
            
            :param res: Image resolution in DPI.
            :type res: int
            
            :param idc: IDC value.
            :type idc: int
            
            Set an PIL.Image image:
                
                >>> from PIL import Image
                >>> image = Image.new( "L", ( 500, 500 ), 255 )
                >>> mark2 = mark.get()
                >>> mark2.set_latent( image )
            
            Set an string image (RAW format):
            
                >>> mark2 = mark.get()
                >>> mark2.set_latent( chr( 255 ) * 500 * 500 )
        """
        if image == None:
            image = Image.new( "L", ( res, res ), 255 )
        
        try:
            if isinstance( image, str ) and os.path.isfile( image ):
                image = Image.open( image )
        except:
            pass
        
        if isinstance( image, str ):
            self.set_field( "13.999", image, idc )
        
        elif isinstance( image, Image.Image ):
            self.set_latent( PILToRAW( image ), res, idc )
            self.set_size( image.size, idc )
        
        else:
            raise formatNotSupported
        
        self.set_field( "13.011", "0", idc )
        self.set_resolution( res, idc )
    
    def set_latent_size( self, value, idc = -1 ):
        """
            Set the size of the latent image.
            
            :param value: Size of the image ( width, height )
            :type value: tuple
            
            :param idc: IDC value.
            :type idc: int
            
            Usage:
                
                >>> mark2 = mark.get()
                >>> mark2.set_latent_size( ( 500, 500 ) )
        """
        width, height = value
        
        self.set_width( 13, width, idc )
        self.set_height( 13, height, idc )
    
    def changeResolution( self, res, idc = -1 ):
        """
            Change the resolution of the latent fingermark. The minutiae are not
            affected because they are stored in mm, not px.
            
            :param res: Output resolution in DPI
            :type res: int
            
            :param idc: IDC value.
            :type idc: int
            
            :raise notImplemented: if the ntype is not 4, 13, or 14. 
            
            Usage:
                
                >>> mark2 = mark.get()
                >>> mark2.changeResolution( 500 )
        """
        res = float( res )
        ntypes = self.get_ntype()
        
        objectres = self.get_resolution( idc )
        
        if res != objectres:
            fac = res / objectres
            
            # Image resizing
            w, h = self.get_size( idc )
            
            img = self.get_image( "PIL", idc )
            img = img.resize( ( int( w * fac ), int( h * fac ) ), Image.BICUBIC )
            
            self.set_size( img.size, idc )
            
            if 4 in ntypes:
                self.set_field( "1.011", round( 100 * res / 25.4 ) / 100.0 )
                self.set_field( "1.012", round( 100 * res / 25.4 ) / 100.0 )
                self.set_field( "4.999", PILToRAW( img ), idc )
                
            elif 13 in ntypes:
                self.set_resolution( res, idc )
                self.set_field( "13.999", PILToRAW( img ), idc )
            
            elif 14 in ntypes:
                self.set_resolution( res, idc )
                self.set_field( "14.999", PILToRAW( img ), idc )
            
            else:
                raise notImplemented
    
    def crop_latent( self, size, center = None, idc = -1, **options ):
        """
            Crop the latent image.
            
            :param size: Size of the output image.
            :type size: tuple
            
            :param center: Coordinate of the center of the image, in mm.
            :type center: tuple
            
            :param idc: IDC value.
            :type idc: int
            
            :raise notImplemented: if the NIST object does not contain Type13 data
            
            Usage:
            
                >>> mark2 = mark.get()
                >>> mark2.crop_latent( ( 500, 500 ), ( 12.7, 12.7 ) )
        """
        if 13 in self.get_ntype():
            return self.crop( size, center, 13, idc )
        
        else:
            raise notImplemented
    
    def crop_print( self, size, center = None, idc = -1, **options ):
        """
            Crop the print image.
            
            :param size: Size of the output image.
            :type size: tuple
            
            :param center: Coordinate of the center of the image, in mm.
            :type center: tuple
            
            :param idc: IDC value.
            :type idc: int
            
            :raise notImplemented: if the NIST object does not contain Type04 or Type14 data
            
            Usage:
            
                >>> pr2 = pr.get()
                >>> pr2.crop_print( ( 500, 500 ), ( 12.7, 12.7 ), 1 )
        """
        ntypes = self.get_ntype()
        if 4 in ntypes:
            ntype = 4
            
        elif 14 in ntypes:
            ntype = 14
        
        else:
            raise notImplemented
        
        return self.crop( size, center, ntype, idc )
    
    def crop_auto( self, *args, **kwargs ):
        try:
            self.crop_latent( *args, **kwargs )
        except:
            self.crop_print( *args, **kwargs )
    
    def crop( self, size, center = None, ntype = None, idc = -1, **options ):
        """
            Crop the latent or the print image.
            
            :param size: Size of the output image.
            :type size: tuple
            
            :param center: Coordinate of the center of the image, in mm.
            :type center: tuple
            
            :param ntype: ntype to crop (4, 13 or 14).
            :type ntype: int
            
            :param idc: IDC value.
            :type idc: int
            
            :raise notImplemented: if the crop_latent() or crop_print() function raise an notImplemented Exception
            
            Usage:
            
                >>> mark2 = mark.get()
                >>> mark2.crop( ( 500, 500 ), ( 12.7, 12.7 ), 13 )
                >>> pr2 = pr.get()
                >>> pr2.crop( ( 500, 500 ), ( 12.7, 12.7 ), 4, 1 )
        """
        idc = self.checkIDC( ntype, idc )
        
        unit = options.get( "unit", None )
        if unit == "mm":
            size = map( lambda x: int( round( x / 25.4 * self.get_resolution( idc ) ) ), size )
        
        if len( size ) == 4:
            a, b, c, d = size
            size = ( abs( c - a ), abs( d - b ) )
            center = ( px2mm( 0.5 * ( a + c ), self.get_resolution( idc ) ) , px2mm( 0.5 * ( b + d ), self.get_resolution( idc ) ) )
        
        if center in [ None, [] ]:
            center = self.get_size( idc )
            center = map( lambda x: int( 0.5 * x ), center )
            center = map( int, center )
        else:
            if isinstance( center[ 0 ], list ):
                center = center[ 0 ]
                
            cx, cy = mm2px( center, self.get_resolution( idc ) )
            cy = self.get_height( idc ) - cy
            center = ( cx, cy )
            center = map( int, center )
        
        img = self.get_image( "PIL", idc )
        
        offset = ( ( size[ 0 ] / 2 ) - center[ 0 ], ( size[ 1 ] / 2 ) - center[ 1 ] )
        offset = tuple( map( int, offset ) )
        
        offsetmin = ( ( size[ 0 ] / 2 ) - center[ 0 ], ( -( self.get_height( idc ) + ( size[ 1 ] / 2 ) - center[ 1 ] - size[ 1 ] ) ) )
        offsetmin = map( lambda x: x * 25.4 / self.get_resolution( idc ), offsetmin )
        
        # Image cropping
        new = Image.new( 'L', size, 255 )
        new.paste( img, offset )
        
        self.set_size( new.size, idc )
        
        self.set_field( ( ntype, 999 ), PILToRAW( new ), idc )
        
        # Minutia cropping
        minu = self.get_minutiae( self.minutiaeformat, idc, **options )
        
        for i, _ in enumerate( minu ):
            minu[ i ] += offsetmin
        
        self.set_minutiae( minu, idc )
        
        # Core cropping
        cores = self.get_cores( idc )
        if cores != None:
            for i, _ in enumerate( cores ):
                cores[ i ] += offsetmin
            
            self.set_cores( cores, idc )
        
    ############################################################################
    # 
    #    Print processing
    # 
    ############################################################################
    
    def get_print( self, format = 'PIL', idc = -1, fpc = None ):
        """
            Return the print image, WSQ or PIL format.
            
            :param format: Format of the returned image.
            :type format: str
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Print image
            :rtype: PIL.Image or str
            
            :raise notImplemented: if the NIST object does not contain Type04 or Type14
            :raise notImplemented: if the image format is not supported
            
            Usage:
            
                >>> pr.get_print( "PIL", 1 ) # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=L size=500x500 at ...>
        """
        format = upper( format )
        ntypes = self.get_ntype()
        
        if 4 in ntypes:
            if fpc != None:
                idc = self.get_idc_for_fpc( 4, fpc )
            
            imgdata = self.get_field( "4.999", idc )
            gca = decode_gca( self.get_field( "4.008", idc ) )
            
        elif 14 in ntypes:
            if fpc != None:
                idc = self.get_idc_for_fpc( 14, fpc )
            
            imgdata = self.get_field( "14.999", idc )
            gca = decode_gca( self.get_field( "14.011", idc ) )
        
        else:
            raise notImplemented
        
        if gca == "WSQ":
            imgdata = WSQ().decode( imgdata )
        
        return changeFormatImage( 
            imgdata,
            format,
            size = self.get_size( idc ),
            res = self.get_resolution( idc )
        )
        
    def get_palmar( self, format = 'PIL', idc = -1, fpc = None ):
        format = upper( format )
        ntypes = self.get_ntype()
        
        if 15 in ntypes:
            if fpc != None:
                idc = self.get_idc_for_fpc( 15, fpc )
            
            imgdata = self.get_field( "15.999", idc )
            gca = decode_gca( self.get_field( "15.011", idc ) )
            
        else:
            raise notImplemented
        
        if gca == "WSQ":
            imgdata = WSQ().decode( imgdata )
        
        h = int( self.get_field( "15.006", idc ) )
        w = int( self.get_field( "15.007", idc ) )
        size = ( h, w )
        res = int( self.get_field( "15.009", idc ) )
        
        return changeFormatImage( 
            imgdata,
            format,
            size = size,
            res = res
        )
        
    def export_print( self, f, idc = -1 ):
        """
            Export the print image to the file 'f' passed in parameter.
            
            :param f: Output file.
            :type f: str
            
            :param idc: IDC value.
            :type idc: int
            
            :return: File written on disk.
            :rtype: boolean
            
            :raise notImplemented: if the NIST object does not contain Type04 or Type14
            
            Usage:
                
                >>> pr.export_print( "./tmp/print.jpeg", 1 )
                True
        """
        ntypes = self.get_ntype()
        
        if 4 in ntypes:
            ntype = 4
            
        elif 14 in ntypes:
            ntype = 14
            
        else:
            raise notImplemented
        
        idc = self.checkIDC( ntype, idc )
        self.get_print( "PIL", idc ).save( f )
        return os.path.isfile( f )
    
    def export_print_annotated( self, f, idc = -1 ):
        """
            Export the annotated print to the file 'f'.
            
            :param f: Output file.
            :type f: str
            
            :param idc: IDC value.
            :type idc: int
            
            :return: File written on disk.
            :rtype: boolean
            
            :raise notImplemented: if the NIST object does not contain Type04 or Type14
            
            Usage:
                
                >>> pr.export_print_annotated( "./tmp/print_annotated.jpeg", 1 )
                True
        """
        ntypes = self.get_ntype()
        
        if 4 in ntypes:
            ntype = 4
            
        elif 14 in ntypes:
            ntype = 14
        
        else:
            raise notImplemented
        
        idc = self.checkIDC( ntype, idc )
        res = self.get_resolution( idc )
        
        self.get_print_annotated( idc ).save( f, dpi = ( res, res ) )
        return os.path.isfile( f )
    
    def get_print_annotated( self, idc = -1 ):
        """
            Function to return the annotated print.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Annotated fingerprint image
            :rtype: PIL.Image
            
            Usage:
            
                >>> pr.get_print_annotated( 1 ) # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        img = self.get_print( 'PIL', idc )
        res = self.get_resolution( idc )
        
        with fuckit:
            img = self.annotate( img, self.get_minutiae( idc = idc ), "minutiae", res, idc )

        with fuckit:
            img = self.annotate( img, self.get_cores( idc ), "center", res, idc )
        
        with fuckit:
            img = self.annotate( img, self.get_delta( idc ), "delta", res, idc )
        
        return img
    
    def get_print_diptych( self, idc = -1 ):
        """
            Function to return the diptych of the latent fingermark (latent and
            annotated latent)
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Fingerprint diptych (fingerprint and fingerprint annotated)
            :rtype: PIL.Image
            
            Usage:
            
                >>> pr.get_print_diptych( 1 ) # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=1000x500 at ...>
        """
        img = self.get_print( 'PIL', idc )
        anno = self.get_print_annotated( idc )
        
        new = Image.new( "RGB", ( img.size[ 0 ] * 2, img.size[ 1 ] ), "white" )
        
        new.paste( img, ( 0, 0 ) )
        new.paste( anno, ( img.size[ 0 ], 0 ) )
        
        return new
    
    def export_print_diptych( self, f, idc = -1 ):
        """
            Function to export the reference diptych
        """
        self.get_print_diptych( idc ).save( f )
    
    def set_print( self, image = None, res = None, size = ( 512, 512 ), format = "WSQ", idc = -1, **options ):
        """
            Function to set an print image to the 4.999 field, and set the size.
            
            :param image: Image to set in the NIST object.
            :type image: PIL.Image or str
            
            :param res: Resolution of the image in DPI.
            :type res: int
            
            :param size: Size of the image.
            :type size: tuple
            
            :param format: Format of the image (WSQ or RAW).
            :type format: str
            
            :param idc: IDC value
            :type idc: int
            
            Usage:
                
                >>> from PIL import Image
                >>> image = Image.new( "L", ( 500, 500 ), 255 )
                >>> pr.set_print( image, format = "RAW", idc = 1 )
            
        """
        resold = res
        
        if res == None:
            res = 500
        
        if image == None:
            image = Image.new( "L", ( res, res ), 255 )
        
        if isinstance( image, Image.Image ):
            if resold == None:
                try:
                    res, _ = image.info[ 'dpi' ]
                
                except:
                    res = 500
             
            width, height = image.size
            if format == "WSQ":
                image = WSQ().encode( image, image.size, res )
            elif format == "RAW":
                image = PILToRAW( image )
        
        else:
            width, height = size
            
        self.set_field( "4.999", image, idc )
        
        if format == "WSQ":
            self.set_field( "4.008", "1", idc )
        elif format == "RAW":
            self.set_field( "4.008", "0", idc )
        
        self.set_print_size( ( width, height ), idc )
        self.set_resolution( res, idc )
    
    def set_print_size( self, value, idc = -1 ):
        """
            Set the size of the fingerprint image. 
        
            :param value: Size of the image ( width, height ).
            :type value: tuple
            
            :param idc: IDC value.
            :type idc: int
            
            :raise notImplemented: if the NIST object does not contain Type04 or Type14 data
            
            Usage:
            
                >>> pr2 = pr.get()
                >>> pr2.set_print_size( ( 500, 500 ), 1 )
        """
        width, height = value
        ntypes = self.get_ntype()
        
        if 4 in ntypes:
            self.set_width( 4, width, idc )
            self.set_height( 4, height, idc )
        
        elif 14 in ntypes:
            self.set_width( 14, width, idc )
            self.set_height( 14, height, idc )
        
        else:
            raise notImplemented
        
    ############################################################################
    # 
    #    Latent and print generic functions
    # 
    ############################################################################
    
    def get_image( self, format = "PIL", idc = -1 ):
        """
            Get the appropriate image (latent fingermark, of fingerprint).
            
            :param format: Format of the returened image.
            :type format: str
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Fingermark of fingerprint Image
            :rtype: PIL.Image or str
            
            :raise notImplemented: if no Type13, Type04 or Type14 data
            
            Usage:
            
                >>> mark.get_image() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=L size=500x500 at ...>
            
            If no image is available, the function will raise an notImplemented Exception.
            
                >>> mark2 = mark.get()
                >>> mark2.delete_ntype( 13 )
                >>> mark2.get_image()
                Traceback (most recent call last):
                ...
                notImplemented
                
        """
        ntypes = self.get_ntype()
        
        if 13 in ntypes:
            return self.get_latent( format, idc )
        
        elif ifany( [ 4, 14 ], ntypes ):
            return self.get_print( format, idc )
        
        else:
            raise notImplemented
    
    def get_image_annotated( self, idc ):
        ntypes = self.get_ntype()
        
        if 13 in ntypes:
            return self.get_latent_annotated( idc )
        
        elif ifany( [ 4, 14 ], ntypes ):
            return self.get_print_annotated( idc )
        
        else:
            raise notImplemented
    
    def set_width( self, ntype, value, idc = -1 ):
        """
            Set the image width for the ntype specified in parameter.
            
            :param ntype: ntype to set the image size.
            :type ntype: int
            
            :param value: width of the image.
            :type value: int or str
            
            :param idc: IDC value.
            :type idc: int
            
            :raise notImplemented: if the NIST object does not contain Type04, Type13 or Type14 data.
            
            Usage:
            
                >>> mark2 = mark.get()
                >>> mark2.set_width( 13, 500 )
        """
        if ntype in [ 4, 13, 14 ]:
            self.set_field( ( ntype, "006" ), value, idc )
        
        else:
            raise notImplemented
    
    def set_height( self, ntype, value, idc = -1 ):
        """
            Set the image height for the ntype specified in parameter.
            
            :param ntype: ntype to set the image size.
            :type ntype: int
            
            :param value: height of the image.
            :type value: int or str
            
            :param idc: IDC value.
            :type idc: int
            
            :raise notImplemented: if the NIST object does not contain Type04, Type13 or Type14 data.
            
            Usage:
            
                >>> mark2 = mark.get()
                >>> mark2.set_height( 13, 500 )
        """
        if ntype in [ 4, 13, 14 ]:
            self.set_field( ( ntype, "007" ), value, idc )
        
        else:
            raise notImplemented
    
    def set_size( self, value, idc = -1 ):
        """
            Set the image size ( width, height ) for the ntype specified in parameter.
            
            :param ntype: ntype to set the image size.
            :type ntype: int
            
            :param value: Siez ( width, height ) of the image.
            :type value: int or str
            
            :param idc: IDC value.
            :type idc: int
            
            :raise notImplemented: if the NIST object does not contain Type04, Type13 or Type14 data.
            
            Usage:
            
                >>> mark2 = mark.get()
                >>> mark2.set_size( ( 500, 500 ) )
        """
        ntypes = self.get_ntype()
        
        if 13 in ntypes:
            self.set_latent_size( value, idc )
            
        elif ifany( [ 4, 14 ], ntypes ):
            self.set_print_size( value, idc )
            
        else:
            raise notImplemented    
    
    def get_diptych( self, idc = -1 ):
        """
            Get the automatic diptych (fingermark or fingerprint).
            
            :param idc: IDC value
            :type idc: int
            
            :raise notImplemented: if the NIST object does not contain Type04, Type13 or Type14 data.
            
            Usage:
            
                >>> mark.get_diptych() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=1000x500 at ...>
            
            .. seealso::
            
                :func:`~NIST.fingerprint.NISTf.get_latent_diptych`
                :func:`~NIST.fingerprint.NISTf.get_print_diptych`
        """
        ntypes = self.get_ntype()
        
        if 13 in ntypes:
            return self.get_latent_diptych( idc )
            
        elif ifany( [ 4, 14 ], ntypes ):
            return self.get_print_diptych( idc )
        
        else:
            raise notImplemented
    
    ############################################################################
    # 
    #    Tenprint image
    # 
    ############################################################################
    
    def get_tenprint_annotated( self ):
        """
            Return the tenprint image annoated.
            
            ..see: :func:`get_tenprint()` function
        """
        return self.get_tenprint( annotated = True )
    
    def get_tenprint( self, annotated = False ):
        """
            Function to return the tenprint image of the current NIST fingerprint
            object (only the rolled finger 1 to 10, two rows of 5 images).
            
            :return: Tenprint image.
            :rtype: PIL.Image
            
            Usage:
            
                >>> pr.get_tenprint() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=L size=2500x1000 at ...>
        """
        maxh, maxw = ( 0, 0 )
        for idc in xrange( 1, 11 ):
            try:
                w, h = self.get_size( idc )
                maxw = max( maxw, w )
                maxh = max( maxh, h )
            
            except:
                pass
            
        size = ( 5 * maxw, 2 * maxh )
        
        if not annotated:
            mode = "L"
            col = 255
        else:
            mode = "RGB"
            col = ( 255, 255, 255 )
            
        ret = Image.new( mode, size, col )
        
        for idc in xrange( 1, 11 ):
            try:
                if annotated:
                    img = self.get_print_annotated( idc )
                
                else:
                    img = self.get_print( "PIL", idc ) 
            
            except:
                img = Image.new( "L", ( maxw, maxh ), 250 )
            
            ret.paste( img, ( int( ( ( ( idc - 1 ) % 5 ) * maxw ) ), int( ( idc - 1 ) / 5 ) * maxh ) )
        
        return ret
    
    def get_tenprintcard_front( self, outres = 1000 ):
        """
            Return the tenprint card for the rolled fingers 1 to 10 (no slaps
            for the moment). This function return an ISO-A4 European tenprint
            card (Swiss).
            
            :param outres: Output resolution of the tenprint card, in DPI.
            :type outres: int
            
            :return: Tenprint card.
            :rtype: PIL.Image
            
            Usage:
                
                >>> pr.get_tenprintcard_front() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=L size=8268x11692 at ...>
        """
        Image.MAX_IMAGE_PIXELS = 1000000000
        
        card = Image.open( self.imgdir + "/tenprint_front.png" )
        card = card.convert( "L" )
        
        cardres, _ = card.info[ 'dpi' ]
        
        fac = outres / cardres
        if fac != 1:
            w, h = card.size
            card = card.resize( ( int( w * fac ), int( h * fac ) ), Image.BICUBIC )
        
        fingerpos = {
            1: ( 8.763, 118.9736, 51.4858, 158.4452 ),
            2: ( 51.8922, 118.9736, 89.408, 158.4452 ),
            3: ( 89.8144, 118.9736, 126.9746, 158.4452 ),
            4: ( 127.381, 118.9736, 165.2524, 158.4452 ),
            5: ( 165.6842, 118.9736, 200.533, 158.4452 ),
            6: ( 8.763, 169.3164, 51.4858, 208.5594 ),
            7: ( 51.8922, 169.3164, 89.408, 208.5594 ),
            8: ( 89.8144, 169.3164, 126.9746, 208.5594 ),
            9: ( 127.381, 169.3164, 165.2524, 208.5594 ),
            10: ( 165.6842, 169.3164, 200.533, 208.5594 ),
            11: ( 105, 227, 135, 279 ),
            12: ( 75, 227, 105, 279 ),
            13: ( 135, 221, 208, 279 ),
            14: ( 2, 221, 75, 279 ),
        }
        
        for fpc in xrange( 1, 15 ):
            try:
                p = self.get_print( "PIL", fpc = fpc )
                
                try:
                    res, _ = p.info[ 'dpi' ]
                except:
                    res = self.get_resolution( self.get_idc_for_fpc( 14, fpc ) )
                
                w, h = p.size
                fac = outres / res
                if fac != 1:
                    p = p.resize( ( int( w * fac ), int( h * fac ) ), Image.BICUBIC )
                
                ink = Image.new( "L", ( int( w * fac ), int( h * fac ) ), 0 )
                
                x1, y1, x2, y2 = [ int( mm2px( v, outres ) ) for v in fingerpos[ fpc ] ]
                
                alpha = x1 + int( ( x2 - x1 - ( w * fac ) ) / 2 )
                beta = y1 + int( ( y2 - y1 - ( h * fac ) ) / 2 )
                
                card.paste( ink, ( alpha, beta ), ImageOps.invert( p ) )
            
            except:
                continue
            
        return card
    
    def get_tenprintcard_back( self, outres = 1000 ):
        """
            Return the tenprint card for the palmar print. This function return
            an ISO-A4 European tenprint card (Swiss).
            
            :param outres: Output resolution of the tenprint card, in DPI.
            :type outres: int
            
            :return: Tenprint card.
            :rtype: PIL.Image
        """
        Image.MAX_IMAGE_PIXELS = 1000000000
        
        card = Image.open( self.imgdir + "/tenprint_back.png" )
        card = card.convert( "L" )
        
        cardres, _ = card.info[ 'dpi' ]
        
        fac = outres / cardres
        if fac != 1:
            w, h = card.size
            card = card.resize( ( int( w * fac ), int( h * fac ) ), Image.BICUBIC )
        
        palmpos = {
            22: ( 150.4, 31.4, 200.6, 157.9 ),
            24: ( 8.8, 158.2, 57.7, 287.9 ),
            27: ( 58.2, 158.3, 200.6, 287.9 ),
            25: ( 8.9, 31.4, 150.0, 157.8 ),
        }
        
        for fpc in [ 22, 24, 25, 27 ]:
            try:
                p = self.get_palmar( "PIL", fpc = fpc )
                
                try:
                    res, _ = p.info[ 'dpi' ]
                except:
                    res = self.get_resolution( self.get_idc_for_fpc( 15, fpc ) )
                
                w, h = p.size
                fac = outres / res
                if fac != 1:
                    p = p.resize( ( int( w * fac ), int( h * fac ) ), Image.BICUBIC )
                
                ink = Image.new( "L", ( int( w * fac ), int( h * fac ) ), 0 )
                
                x1, y1, x2, y2 = [ int( mm2px( v, outres ) ) for v in palmpos[ fpc ] ]
                
                alpha = x1 + int( ( x2 - x1 - ( w * fac ) ) / 2 )
                beta = y1 + int( ( y2 - y1 - ( h * fac ) ) / 2 )
                
                card.paste( ink, ( alpha, beta ), ImageOps.invert( p ) )
            
            except:
                continue
            
        return card
    
    ############################################################################
    # 
    #    Automatic selection functions
    # 
    ############################################################################
    
    def export_auto( self, f, idc = -1 ):
        try:
            self.export_print( f, idc )
        
        except:
            self.export_latent( f, idc )
    
    def export_auto_annotated( self, f, idc = -1 ):
        try:
            self.export_print_annotated( f, idc )
        
        except:
            self.export_latent_annotated( f, idc )
    
    ############################################################################
    # 
    #    Initialization of latent and print NIST objects
    # 
    ############################################################################
    
    def init_latent( self, *args, **kwargs ):
        """
            Initialize an latent fingermark NIST object. If the correct data is
            passed as keyword arguments (ie with the same names as in the
            :func:`add_Type09()`, :func:`add_Type13()` and :func:`set_latent()`
            functions), the corresponding fields will be populated.
            
            :return: Latent NIST object
            :rtype: NISTf
            
            Usage:
            
                >>> from NIST import NISTf
                >>> params = {
                ...     'minutiae': minutiae,
                ...     'cores': [ [ 12.5, 18.7 ] ]
                ... }
                >>> mark = NISTf().init_latent( **params )
            
            .. seealso ::
            
                :func:`~NIST.traditional.NIST.add_Type01`
                :func:`~NIST.traditional.NIST.add_Type02`
                :func:`~NIST.fingerprint.NISTf.add_Type09`
                :func:`~NIST.fingerprint.NISTf.add_Type13`
                :func:`~NIST.fingerprint.NISTf.set_latent`
        """
        self.add_Type01()
        self.add_Type02()
        self.add_Type09( **kwargs )
        self.add_Type13( **kwargs )
        self.set_latent( **kwargs )
        
        return self
    
    def init_print( self, *args, **kwargs ):
        """
            Initialize an fingerprint NIST object. If the correct data is passed
            as keyword arguments (ie with the same names as in the
            :func:`add_Type04()`, :func:`add_Type09()` and :func:`set_print()`
            functions), the corresponding fields will be populated.
            
            :return: Print NIST object
            :rtype: NISTf
            
            Usage:
                
                >>> from NIST import NISTf
                >>> params = {
                ...     'minutiae': minutiae,
                ...     'cores': [ [ 12.5, 18.7 ] ]
                ... }
                >>> pr = NISTf().init_print( **params )
            
            .. seealso ::
            
                :func:`~NIST.traditional.NIST.add_Type01`
                :func:`~NIST.traditional.NIST.add_Type02`
                :func:`~NIST.fingerprint.NISTf.add_Type04`
                :func:`~NIST.fingerprint.NISTf.set_print`
                :func:`~NIST.fingerprint.NISTf.add_Type09`
        """
        self.add_Type01()
        self.add_Type02()
        self.add_Type04( **kwargs )
        self.set_print( **kwargs )
        self.add_Type09( **kwargs )
        
        return self
    
    def init_new( self, *args, **kwargs ):
        """
            Initialize a new latent fingermark or fingerprint NIST object. See
            the functions :func:`~NIST.fingerprint.NISTf.init_latent` and
            :func:`~NIST.fingerprint.NISTf.init_print` for more details.
            
            :return: Latent or print fingerprint NIST object.
            :rtype: NISTf
            
            :raise notImplemented: if the NIST object does not contain Type04, Type13 or Type14 data.
            
            New latent fingermark:
            
                >>> from NIST import NISTf
                >>> params = {
                ...     'type': 'latent',
                ...     'minutiae': minutiae,
                ...     'cores': [ [ 12.5, 18.7 ] ]
                ... }
                >>> mark = NISTf().init_latent( **params )
                >>> print( mark ) # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
                Informations about the NIST object:
                    Records: Type-01, Type-02, Type-09, Type-13
                    Class:   NISTf
                <BLANKLINE>
                NIST Type-01
                    01.001 LEN: 00000145
                    01.002 VER: 0300
                    01.003 CNT: 1<US>3<RS>2<US>0<RS>9<US>0<RS>13<US>0
                    01.004 TOT: USA
                    01.005 DAT: ...
                    01.006 PRY: 1
                    01.007 DAI: FILE
                    01.008 ORI: UNIL
                    01.009 TCN: ...
                    01.011 NSR: 00.00
                    01.012 NTR: 00.00
                NIST Type-02 (IDC 0)
                    02.001 LEN: 00000038
                    02.002 IDC: 0
                    02.004    : ...
                NIST Type-09 (IDC 0)
                    09.001 LEN: 00000266
                    09.002 IDC: 0
                    09.003 IMP: 4
                    09.004 FMT: S
                    09.007    : U
                    09.008    : 12501870
                    09.010    : 10
                    09.011    : 0
                    09.012    : 1<US>07850705290<US>0<US>A<RS>2<US>13801530155<US>0<US>A<RS>3<US>11462232224<US>0<US>B<RS>4<US>22612517194<US>0<US>A<RS>5<US>06970848153<US>0<US>B<RS>6<US>12581988346<US>0<US>A<RS>7<US>19691980111<US>0<US>C<RS>8<US>12310387147<US>0<US>A<RS>9<US>13881429330<US>0<US>D<RS>10<US>15472249271<US>0<US>D
                NIST Type-13 (IDC 0)
                    13.001 LEN: 00250150
                    13.002 IDC: 0
                    13.003 IMP: 4
                    13.004 SRC: UNIL
                    13.005 LCD: ...
                    13.006 HLL: 500
                    13.007 VLL: 500
                    13.008 SLC: 1
                    13.009 THPS: 500
                    13.010 TVPS: 500
                    13.011 CGA: 0
                    13.012 BPX: 8
                    13.013 FGP: 0
                    13.999 DATA: FFFFFFFF ... FFFFFFFF (250000 bytes)
            
            New fingerprint:
               
                >>> from NIST import NISTf
                >>> params = {
                ...     'type': 'print',
                ...     'minutiae': minutiae,
                ...     'cores': [ [ 12.5, 18.7 ] ]
                ... }
                >>> pr = NISTf().init_print( **params )
                >>> print( pr ) # doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
                Informations about the NIST object:
                    Records: Type-01, Type-02, Type-04, Type-09
                    Class:   NISTf
                <BLANKLINE>
                NIST Type-01
                    01.001 LEN: 00000144
                    01.002 VER: 0300
                    01.003 CNT: 1<US>3<RS>2<US>0<RS>4<US>1<RS>9<US>0
                    01.004 TOT: USA
                    01.005 DAT: ...
                    01.006 PRY: 1
                    01.007 DAI: FILE
                    01.008 ORI: UNIL
                    01.009 TCN: ...
                    01.011 NSR: 19.69
                    01.012 NTR: 19.69
                NIST Type-02 (IDC 0)
                    02.001 LEN: 00000038
                    02.002 IDC: 0
                    02.004    : ...
                NIST Type-04 (IDC 1)
                    04.001 LEN: 673
                    04.002 IDC: 1
                    04.003 IMP: 3
                    04.004 FGP: 0
                    04.005 ISR: 1
                    04.006 HLL: 500
                    04.007 VLL: 500
                    04.008 CGA: 1
                    04.999    : FFA0FFA8 ... 0301FFA1 (655 bytes)
                NIST Type-09 (IDC 0)
                    09.001 LEN: 00000266
                    09.002 IDC: 0
                    09.003 IMP: 4
                    09.004 FMT: S
                    09.007    : U
                    09.008    : 12501870
                    09.010    : 10
                    09.011    : 0
                    09.012    : 1<US>07850705290<US>0<US>A<RS>2<US>13801530155<US>0<US>A<RS>3<US>11462232224<US>0<US>B<RS>4<US>22612517194<US>0<US>A<RS>5<US>06970848153<US>0<US>B<RS>6<US>12581988346<US>0<US>A<RS>7<US>19691980111<US>0<US>C<RS>8<US>12310387147<US>0<US>A<RS>9<US>13881429330<US>0<US>D<RS>10<US>15472249271<US>0<US>D
        
        """
        type = kwargs.pop( "type", "latent" )
        
        if type in [ 'mark', 'latent' ]:
            self.init_latent( *args, **kwargs )
            return self
        
        elif type == 'print':
            self.init_print( *args, **kwargs )
            return self
        
        else:
            raise notImplemented
    
    ############################################################################
    # 
    #    Add empty records to the NIST object
    # 
    ############################################################################
    
    def add_Type04( self, idc = 1, **options ):
        """
            Add the Type-04 record to the NIST object.
            
            :param idc: IDC value.
            :type idc: int
        """
        ntype = 4
        
        if isinstance( idc, list ):
            for i in idc:
                self.add_default( ntype, i )
        
        else:
            self.add_default( ntype, idc )
    
    def add_Type09( self, minutiae = None, idc = 0, **options ):
        """
            Add the Type-09 record to the NIST object, and set the Date.
            
            :param minutiae: AnnotationList with the minutiae data.
            :type minutiae: AnnotationList
            
            :param idc: IDC value.
            :type idc: int
        """
        ntype = 9
        
        if isinstance( minutiae, int ):
            idc, minutiae = minutiae, None
        
        self.add_default( ntype, idc )
        
        if minutiae != None:
            self.set_minutiae( minutiae, idc )
        
        cores = options.get( "cores", None ) 
        if cores != None:
            self.set_cores( cores, idc )
    
    def add_Type13( self, size = ( 500, 500 ), res = 500, idc = 0, **options ):
        """
            Add an empty Type-13 record to the NIST object, and set the
            resolution (in DPI). Set by default the image to a white image.
            
            :param size: Size of the latent fingermark image to set.
            :type size: tuple
            
            :param res: Resolution of the image, in dot-per-inch.
            :type res: int
            
            :param idc: IDC value.
            :type idc: int
        """
        ntype = 13
        
        self.add_default( ntype, idc )
        
        self.set_field( "13.002", idc, idc )
        self.set_field( "13.005", self.date, idc )
        
        self.set_field( "13.004", default_origin, idc )
        
        self.set_field( "13.008", 1, idc )
        self.set_field( "13.009", res, idc )
        self.set_field( "13.010", res, idc )
        
        w, h = size
        self.set_field( "13.999", chr( 255 ) * w * h, idc )
        self.set_field( "13.006", w, idc )
        self.set_field( "13.007", h, idc )
        
    def add_Type14( self, size = ( 500, 500 ), res = 500, idc = 1, **options ):
        """
            Add the Type-14 record to the NIST object.
            
            :param size: Size of the fingerprint image to set.
            :type size: tuple of int
            
            :param res: Resolution of the image, in dot-per-inch.
            :type res: int
            
            :param idc: IDC value.
            :type idc: int
        """
        ntype = 14
        
        if isinstance( idc, list ):
            for i in idc:
                self.add_default( ntype, i )
        
        else:
            self.add_default( ntype, idc )
            
            self.set_field( "14.005", self.date, idc )
            
            with fuckit:
                w, h = size
                self.set_field( "14.006", w, idc )
                self.set_field( "14.007", h, idc )
                
                self.set_field( "14.009", res, idc )
                self.set_field( "14.010", res, idc )
                
                imgdata = options.get( "img" )
                self.set_field( "14.999", imgdata, idc )
            
            with fuckit:
                fpc = options.get( "fpc" )
                self.set_field( "14.013", fpc, idc )
            
            with fuckit:
                gca = options.get( "gca" )
                self.set_field( "14.011", gca, idc )
            
    def add_Type15( self, idc = 1, **options ):
        """
            Add the Type-15 record to the NIST object.
            
            :param idc: IDC value.
            :type idc: int
        """
        ntype = 15
        
        if isinstance( idc, list ):
            for i in idc:
                self.add_default( ntype, i )
        
        else:
            self.add_default( ntype, idc )
    
    ############################################################################
    # 
    #    Migrate a Type04 record to Type14
    # 
    ############################################################################
    
    def migrate_Type04_to_Type14( self ):
        """
            Migration of the Type04 fingerprint record to Type14 record. This
            function make a copy of the fingerprint images informations. The
            minutiae are not modified. The Type04 records are deleted after
            conversion.
            
            The Type14 fingerprint are stored in RAW format. The WSQ compression
            is not supported for the moment.
            
            Usage:
            
                >>> pr2 = pr.get()
                >>> pr2.migrate_Type04_to_Type14()
                >>> pr2
                NIST object, Type-01, Type-02, Type-09, Type-14
        """
        for idc in self.get_idc( 4 ):
            size = self.get_size( idc )
            res = self.get_resolution( idc )
            image = self.get_print( "RAW", idc )
            
            self.add_Type14( size, res, idc )
            self.set_field( "14.999", image, idc )
            
            self.delete_idc( 4, idc )
        
        self.delete_ntype( 4 )
            
    ############################################################################
    #    
    #    Coordinates system
    #    
    ############################################################################
    def mm2px( self, data, idc = -1 ):
        """
            Transformation the coordinates from pixel to millimeters
            
            :param data: Coordinate value.
            :type data: tuple
            
            :param idc: IDC value.
            :type idc: int
            
            Usage:
            
                >>> mark.mm2px( ( 12.7, 12.7 ) )
                [250.0, 250.0]
        """
        return mm2px( data, self.get_resolution( idc ) )
    
    def px2mm( self, data, idc = -1 ):
        """
            Transformation the coordinates from pixels to millimeters
            
            :param data: Coordinate value.
            :type data: tuple
            
            :param idc: IDC value.
            :type idc: int
            
            Usage:
            
                >>> mark.px2mm( ( 250.0, 250.0 ) )
                [12.7, 12.7]
        """
        return px2mm( data, self.get_resolution( idc ) )

################################################################################
# 
#    Overload of the NISTf class to use the 'int INCITS 378' standard developed
#    by the INCITS Technical Committee M1. The term 'M1' is used in lieu of
#    INCITS 378 to shorten the field names.
# 
################################################################################

class NIST_M1( NISTf ):
    def get_minutiae( self, format = "ixytdq", idc = -1, unit = "mm" ):
        """
            Get the minutiae information from the field 9.012 for the IDC passed
            in argument.
            
            :param format: Format of the minutiae to return.
            :type format: str or list
            
            :param idc: IDC value.
            :type idc: int
            
            :return: List of minutiae
            :rtype: AnnotationList
            
            The parameter 'format' allow to select the data to extract:
            
                * i: Index number
                * x: X coordinate
                * y: Y coordinate
                * t: Angle theta
                * d: Type designation
                * q: Quality
            
            The 'format' parameter is optional. The IDC value can be passed in
            parameter even without format. The default format ('ixytdq') will be
            used.
        """
        if not unit in [ 'mm', 'px' ]:
            raise notImplemented
        
        else:
            # If the 'format' value is an int, then the function is called without
            # the 'format' argument, but the IDC is passed instead.
            if isinstance( format, int ):
                idc, format = format, "ixytdq"
            
            # Check the IDC value
            idc = self.checkIDC( 9, idc )
            
            # Get and process the M1 finger minutiae data field
            data = self.get_field( "9.137", idc )
            data = split_r( [ RS, US ], data )
            data = map_r( int, data )
            
            # Select the information to retrun
            ret = AnnotationList()
            for i, x, y, t, d, q in data:
                tmp = []
                
                t = ( 2 * t + 180 ) % 360
                y = self.get_height( idc ) - y
                
                if unit == "mm":
                    x = self.px2mm( x, idc )
                    y = self.px2mm( y, idc )
                
                for c in format:
                    if c == "i":
                        tmp.append( i )
                    
                    elif c == "x":
                        tmp.append( x )
                    
                    elif c == "y":
                        tmp.append( y )
                    
                    elif c == "t":
                        tmp.append( t )
                    
                    elif c == "d":
                        tmp.append( d )
                    
                    elif c == "q":
                        tmp.append( q )
                    
                ret.append( tmp )
            
            return ret
        
    def get_minutiaeCount( self, idc = -1 ):
        """
            Return the number of minutiae stored in the current NIST object.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Number of minutiae
            :rtype: int
        """
        try:
            return int( self.get_field( "9.136", idc ) )
        except:
            return 0
    
    def set_minutiae( self, data, idc = -1 ):
        """
            Set the minutiae in the field 9.137.
            
            :param data: List of minutiae coordinates
            :type data: AnnotationList or str
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Number of minutiae added to the NIST object
            :rtype: int
        """
        idc = self.checkIDC( 9, idc )
        
        if isinstance( data, list ):
            data = lstTo137( data, self.get_resolution( idc ) )
        
        self.set_field( "9.137", data, idc )
        
        minnum = len( data.split( RS ) ) - 1
        self.set_field( "9.136", minnum, idc )
        
        return minnum
