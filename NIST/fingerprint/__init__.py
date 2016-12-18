#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import absolute_import, division

from cStringIO import StringIO
from future.builtins.misc import super
from math import cos, pi, sin
from PIL import Image, ImageDraw, ImageFont

import os

from MDmisc.deprecated import deprecated
from MDmisc.imageprocessing import RAWToPIL
from MDmisc.ebool import xor
from MDmisc.elist import ifany, map_r
from MDmisc.eint import str_int_cmp
from MDmisc.logger import debug
from MDmisc.string import upper, split_r, join
from WSQ import WSQ

from ..traditional import NIST
from ..traditional.config import RS, US, FS, default_origin
from ..traditional.exceptions import *
from ..traditional.functions import decode_gca
from .exceptions import minutiaeFormatNotSupported
from .functions import lstTo012, lstTo137, PILToRAW, mm2px, px2mm
from .functions import Minutia, Core, AnnotationList
from .voidType import voidType

voidType.update( voidType )

class NISTf( NIST ):
    def __init__( self, *args, **kwargs ):
        """
            Constructor function. Call the constructor of the
            :func:`NIST.traditional.NIST` module, and try to initiate a new
            latent or print object (see :func:`NIST.fingerprint.NISTf.init_new`
            for more details).
        """
        self.imgdir = os.path.split( os.path.abspath( __file__ ) )[ 0 ] + "/images"
        
        self.minutiaeformat = "ixytqd"
        
        super().__init__( *args, **kwargs )
        
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
            object, and call the NIST.traditional.NIST
            :func:`~NIST.traditional.NIST.clean` function.
            
            Usage:
                
                >>> mark.clean()
        """
        debug.info( "Cleaning the NIST object" )
        
        #    Check the minutiae
        if 9 in self.get_ntype():
            self.checkMinutiae()
        
        #    Call the super().clean() functions
        super().clean()
        
    def patch_to_standard( self ):
        """
            Check some requirements for the NIST file. Fields checked:
            
                * 4.005
                * 9.004
            
            This function call the :func:`NIST.traditional.NIST.patch_to_standard`
            function afterward.
        """
        ntypes = self.get_ntype()
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
        super().patch_to_standard()
        
    ############################################################################
    #
    #    Minutia functions
    #
    ############################################################################
    
    def get_minutiae( self, format = None, idc = -1 ):
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
            
                >>> mark.get_minutiae() # doctest: +NORMALIZE_WHITESPACE
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
        if type( format ) == int:
            idc, format = format, self.minutiaeformat
        
        # Get the minutiae string, without the final <FS> character.
        minutiae = self.get_field( "9.012", idc ).replace( FS, "" )
        
        lst = AnnotationList()
        for m in split_r( [ RS, US ], minutiae ):
            try:
                id, xyt, q, d = m
                
                d = d.upper()
                
                x = int( xyt[ 0:4 ] ) / 100
                y = int( xyt[ 4:8 ] ) / 100
                t = int( xyt[ 8:11 ] )

                lst.append( Minutia( [ id, x, y, t, q, d ] ) )

            except:
                pass
        
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
                    ], [], [], [], [], [], [], [], [], []]
        """
        if ifany( [ 4, 14 ], self.get_ntype() ):
            if format == None:
                format = self.minutiaeformat
                
            ret = []
            
            for idc in xrange( 1, 11 ):
                try:
                    ret.append( self.get_minutiae( format, idc ) )
                except idcNotFound:
                    ret.append( [] )
            
            return ret
        else:
            raise notImplemented
    
    def get_minutiae_by_name( self, name, format = None, idc = -1 ):
        """
            Return the minuiae by name
            
            :param name: Name of the minutia
            :type name: str
            
            :param format: Format of the minutiae to return.
            :type format: str or list
            
            :param idc: IDC value.
            :type idc: int
            
            :return: List of minutiae
            :rtype: AnnotationList
            
            To get the minutiae '001' and '002':
            
                >>> mark.get_minutiae_by_name( [ "001", "002" ] ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A' )
                ]
        """
        return AnnotationList( [ m for m in self.get_minutiae( format, idc ) if str_int_cmp( m.n, name ) ] )
    
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
            
                >>> mark.get_minutia_by_id( "1" )
                Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' )
            
            The format can also be specified as follow:
            
                >>> mark.get_minutia_by_id( "1", "xy" )
                Minutia( x='7.85', y='7.05' )
        """
        if type( format ) == int:
            idc, format = format, self.minutiaeformat
        
        elif format == None:
            format = self.minutiaeformat
        
        for m in self.get_minutiae( idc ):
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
        return self.get_minutiae( idc ).get_by_type( designation, format )
    
    def get_minutiaeCount( self, idc = -1 ):
        """
            Return the number of minutiae stored in the current NIST object.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Number of minutiae
            :rtype: int
            
            Usage:
                >>> mark.get_minutiaeCount()
                10
        """
        try:
            return int( self.get_field( "9.010", idc ) )
        except:
            return 0
    
    def get_cores( self, idc = -1, format = 'xy' ):
        """
            Process and return the coordinate of the cores.
            
            :param idc: IDC value.
            :type idc: int
            
            :param format: Format of the cores to return.
            :type format: str or list
            
            :return: List of cores
            :rtype: AnnotationList
            
            Usage:
            
                >>> mark.get_cores() # doctest: +NORMALIZE_WHITESPACE
                [
                    Core( x='12.5', y='18.7' )
                ]
        """
        try:
            cores = self.get_field( "9.008", idc ).split( RS )
            if cores == None:
                raise Exception
            
            ret = AnnotationList()
            for c in cores:
                x = int( c[ 0:4 ] ) / 100
                y = int( c[ 4:8 ] ) / 100
                
                ret.append( Core( [ x, y ], format = format ) )
                
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
            
            Usage:
            
                >>> mark.set_cores( [ [ 12.5, 18.7 ] ], 1 )
            
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
            return
        
        elif isinstance( data[ 0 ], ( Core, list ) ):
            data = map( format, data )
        
        else:
            data = format( data )
        
        data = join( RS, data )
        
        self.set_field( "9.008", data, idc )
    
    def set_minutiae( self, data, idc = -1 ):
        """
            Set the minutiae in the field 9.012.
            
            :param data: List of minutiae coordinates
            :type data: AnnotationList or str
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Number of minutiae added to the NIST object
            :rtype: int
            
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
                >>> mark.set_minutiae( minutiae, 1 )
                10
        """
        idc = self.checkIDC( 9, idc )
        
        if isinstance( data, AnnotationList ):
            data = lstTo012( data )
        
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
        """
        try:
            idc = self.checkIDC( 9, idc )
        except needIDC:
            for idc in self.get_idc( 9 ):
                self.checkMinutiae( idc )
        else:
            try:
                if self.get_minutiaeCount( idc ) == 0:
                    return
                else:
                    try:
                        w = self.px2mm( self.get_width( idc ), idc )
                        h = self.px2mm( self.get_height( idc ), idc )
                    
                    except notImplemented:
                        return self.get_minutiae( idc )
                      
                    else:
                        id = 0
                        lst = AnnotationList()
                        
                        for m in self.get_minutiae( idc ):
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
            
                >>> mark.filter_minutiae( d = "AB" ) # doctest: +NORMALIZE_WHITESPACE
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
            
                >>> mark.filter_minutiae( d = "D", invert = True ) # doctest: +NORMALIZE_WHITESPACE
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
            
                >>> mark.filter_minutiae( i = [ "1", "5" ] ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='5', x='6.97', y='8.48', t='153', q='0', d='B' )
                ]
        """
        tofilter = [ ( key, value ) for key, value in kwargs.iteritems() ]
        if len( tofilter ) == 0:
            return self.get_minutiae( idc )
        
        else:
            lst = AnnotationList()
            for m in self.get_minutiae( idc ):
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
            
            :return: Horizontal and vertical size
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
        
        if 13 in ntypes:
            return int( self.get_field( "13.006", idc ) )
        
        elif 4 in ntypes: 
            return int( self.get_field( "4.006", idc ) )
        
        elif 14 in ntypes: 
            return int( self.get_field( "14.006", idc ) )
        
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
        
        if 13 in ntypes: 
            return int( self.get_field( "13.007", idc ) )
        
        elif 4 in ntypes: 
            return int( self.get_field( "4.007", idc ) )
        
        elif 14 in ntypes: 
            return int( self.get_field( "14.007", idc ) )
        
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
        
        if 4 in ntypes:
            return int( round( float( self.get_field( "1.011" ) ) * 25.4 ) )
        
        elif 13 in ntypes:
            if self.get_field( "13.008", idc ) == '1':
                return int( self.get_field( "13.009", idc ) )
            elif self.get_field( "13.008", idc ) == '2':
                return int( round( float( self.get_field( "13.009", idc ) ) / 10 * 25.4 ) )
            
        elif 14 in ntypes:
            if self.get_field( "14.008", idc ) == '1':
                return int( self.get_field( "14.009", idc ) )
            elif self.get_field( "14.008", idc ) == '2':
                return int( round( float( self.get_field( "14.009", idc ) ) / 10 * 25.4 ) )
        
        else:
            raise notImplemented
    
    def set_resolution( self, res, idc = -1 ):
        """
            Set the resolution in DPI.
            
            :param idc: IDC value.
            :type idc: int
            
            Usage:
                
                >>> mark.set_resolution( 500 )
                
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
    
    def annotate( self, image, data, type = "minutiae", res = None ):
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
            
                >>> mark.annotate( mark.get_latent( 'PIL' ), mark.get_minutiae( 'xyt' ) ) # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        image = image.convert( "RGB" )
        
        if data != None and len( data ) != 0:
            width, height = image.size
            
            if res == None:
                try:
                    res, _ = image.info[ 'dpi' ]
                except:
                    res = self.get_resolution()
            
            # Resize factor for the minutiae
            fac = res / 2000
            
            # Colors
            red = ( 250, 0, 0 )
            
            if type == "minutiae":
                # Minutia
                endmark = Image.open( self.imgdir + "/end.png" )
                newsize = ( int( endmark.size[ 0 ] * fac ), int( endmark.size[ 1 ] * fac ) )
                endmark = endmark.resize( newsize, Image.BICUBIC )
                
                for x, y, theta in data: 
                    x = x / 25.4 * res
                    y = y / 25.4 * res
                    
                    y = height - y
                    
                    end2 = endmark.rotate( theta, Image.BICUBIC, True )
                    offsetx = end2.size[ 0 ] / 2
                    offsety = end2.size[ 1 ] / 2
                    
                    endcolor = Image.new( 'RGBA', end2.size, red )
                    
                    image.paste( endcolor, ( int( x - offsetx ), int( y - offsety ) ), mask = end2 )
            
            elif type == "center":
                centermark = Image.open( self.imgdir + "/center.png" )
                newsize = ( int( centermark.size[ 0 ] * fac ), int( centermark.size[ 1 ] * fac ) )
                centermark = centermark.resize( newsize, Image.BICUBIC )
                    
                # Center
                for cx, cy in data:
                    cx = cx / 25.4 * res
                    cy = cy / 25.4 * res
                    cy = height - cy
                    
                    offsetx = centermark.size[ 0 ] / 2
                    offsety = centermark.size[ 1 ] / 2
                    
                    centercolor = Image.new( 'RGBA', centermark.size, red )
                    
                    image.paste( centercolor, ( int( cx - offsetx ), int( cy - offsety ) ), mask = centermark )
            
            else:
                raise notImplemented
            
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
        
        if gca in [ "JP2", "PNG" ]:
            buff = StringIO( imgdata )
            img = Image.open( buff )
            
            if format == "PIL":
                return img
            
            elif format == "RAW":
                return PILToRAW( img )
            
            elif format in [ "JP2", "PNG" ]:
                return buff
        
        elif gca == "RAW":
            if format == "RAW":
                return imgdata
            
            elif format == "PIL":
                return RAWToPIL( imgdata, self.get_size( idc ), self.get_resolution( idc ) )
            
            else:
                raise notImplemented
    
        else:
            raise notImplemented
    
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
        self.get_latent( "PIL", idc ).save( f )
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
        self.get_latent_annotated( idc ).save( f )
        return os.path.isfile( f )
    
    def get_latent_annotated( self, idc = -1 ):
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
        img = self.get_latent( 'PIL', idc )
        
        try:
            img = self.annotate( img, self.get_minutiae( "xyt", idc ), "minutiae" )
            img = self.annotate( img, self.get_cores( idc ), "center" )
        except recordNotFound:
            pass
        
        return img
    
    def get_latent_diptych( self, idc = -1 ):
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
        anno = self.get_latent_annotated( idc )
        
        new = Image.new( "RGB", ( img.size[ 0 ] * 2, img.size[ 1 ] ), "white" )
        
        new.paste( img, ( 0, 0 ) )
        new.paste( anno, ( img.size[ 0 ], 0 ) )
        
        return new
    
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
                >>> mark.set_latent( image )
            
            Set an string image (RAW format):
            
                >>> mark.set_latent( chr( 255 ) * 500 * 500 )
        """
        if image == None:
            image = Image.new( "L", ( res, res ), 255 )
            
        if type( image ) == str:
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
                
                >>> mark.set_latent_size( ( 500, 500 ) )
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
                
                >>> mark.changeResolution( 500 )
        """
        res = float( res )
        ntypes = self.get_ntype()
        
        if res != self.get_resolution( idc ):
            fac = res / self.get_resolution( idc )
            
            # Image resizing
            w, h = self.get_size( idc )
            
            img = self.get_image( "PIL", idc )
            img = img.resize( ( int( w * fac ), int( h * fac ) ), Image.BICUBIC )
            
            self.set_size( img.size )
            
            if 4 in ntypes:
                self.set_field( "1.011", round( 100 * res / 25.4 ) / 100.0 )
                self.set_field( "4.999", PILToRAW( img ) )
                
            elif 13 in ntypes:
                self.set_resolution( res )
                self.set_field( "13.999", PILToRAW( img ) )
            
            elif 14 in ntypes:
                self.set_resolution( res )
                self.set_field( "14.999", PILToRAW( img ) )
            
            else:
                raise notImplemented
    
    def crop_latent( self, size, center = None, idc = -1 ):
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
            
                >>> mark.crop_latent( ( 500, 500 ), ( 12.7, 12.7 ) )
        """
        if 13 in self.get_ntype():
            return self.crop( size, center, 13, idc )
        
        else:
            raise notImplemented
    
    def crop_print( self, size, center = None, idc = -1 ):
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
            
                >>> pr.crop_print( ( 500, 500 ), ( 12.7, 12.7 ) )
        """
        ntypes = self.get_ntype()
        if 4 in ntypes:
            ntype = 4
            
        elif 14 in ntypes:
            ntype = 14
        
        else:
            raise notImplemented
        
        return self.crop( size, center, ntype, idc )
    
    def crop( self, size, center = None, ntype = None, idc = -1 ):
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
            
                >>> mark.crop( ( 500, 500 ), ( 12.7, 12.7 ), 13 )
                >>> pr.crop( ( 500, 500 ), ( 12.7, 12.7 ), 4 )
        """
        idc = self.checkIDC( ntype, idc )
        
        if center == None:
            center = self.get_size( idc )
            center = map( lambda x: int( 0.5 * x ), center )
            center = map( int, center )
        else:
            if type( center[ 0 ] ) == list:
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
        minu = self.get_minutiae( self.minutiaeformat, idc )
        
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
    
    def get_print( self, format = 'PIL', idc = -1 ):
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
            
                >>> pr.get_print( "PIL" ) # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=L size=500x500 at ...>
        """
        format = upper( format )
        ntypes = self.get_ntype()
        
        if 4 in ntypes:
            imgdata = self.get_field( "4.999", idc )
            gca = decode_gca( self.get_field( "4.008", idc ) )
            
        elif 14 in ntypes:
            imgdata = self.get_field( "14.999", idc )
            gca = decode_gca( self.get_field( "14.011", idc ) )
        
        else:
            raise notImplemented
        
        if gca in [ "JP2", "PNG" ]:
            buff = StringIO( imgdata )
            img = Image.open( buff )
            
            if format == "PIL":
                return img
            
            elif format == "RAW":
                return PILToRAW( img )
            
            elif format in [ "JP2", "PNG" ]:
                return buff

        elif gca == "RAW":
            if format == "RAW":
                return imgdata
        
            elif format == "PIL":
                return RAWToPIL( imgdata, self.get_size( idc ), self.get_resolution( idc ) )
            
            else:
                raise notImplemented
        
        elif gca == "WSQ":
            img = WSQ().decode( imgdata )
            
            if format == "RAW":
                return img
            
            elif format == "PIL":
                return RAWToPIL( img, self.get_size( idc ), self.get_resolution( idc ) )
            
            else:
                raise notImplemented
        
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
                
                >>> pr.export_print( "./tmp/print.jpeg" )
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
                
                >>> pr.export_print_annotated( "./tmp/print_annotated.jpeg" )
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
        self.get_print_annotated( idc ).save( f )
        return os.path.isfile( f )
    
    def get_print_annotated( self, idc = -1 ):
        """
            Function to return the annotated print.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Annotated fingerprint image
            :rtype: PIL.Image
            
            Usage:
            
                >>> pr.get_print_annotated() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        img = self.annotate( self.get_print( 'PIL', idc ), self.get_minutiae( "xyt", idc ), "minutiae", self.get_resolution( idc ) )
        img = self.annotate( img, self.get_cores( idc ), "center", self.get_resolution( idc ) )
        
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
            
                >>> pr.get_print_diptych() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=1000x500 at ...>
        """
        img = self.get_print( 'PIL', idc )
        anno = self.get_print_annotated( idc )
        
        new = Image.new( "RGB", ( img.size[ 0 ] * 2, img.size[ 1 ] ), "white" )
        
        new.paste( img, ( 0, 0 ) )
        new.paste( anno, ( img.size[ 0 ], 0 ) )
        
        return new
    
    def set_print( self, image = None, res = 500, size = ( 512, 512 ), format = "WSQ", idc = -1, **options ):
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
        if image == None:
            image = Image.new( "L", ( res, res ), 255 )
        
        if isinstance( image, Image.Image ):
            try:
                res, _ = image.info[ 'dpi' ]
            
            except:
                pass
            
            finally:
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
            
                >>> pr.set_print_size( ( 500, 500 ) )
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
        """
        ntypes = self.get_ntype()
        
        if 13 in ntypes:
            return self.get_latent( format, idc )
        
        elif ifany( [ 4, 14 ], ntypes ):
            return self.get_print( format, idc )
        
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
            
            :raise notImplemented: if the NIST object does not contain Type04, Type 13 or Type14 data.
            
            Usage:
            
                >>> mark.set_width( 13, 500 )
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
            
            :raise notImplemented: if the NIST object does not contain Type04, Type 13 or Type14 data.
            
            Usage:
            
                >>> mark.set_height( 13, 500 )
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
            
            :raise notImplemented: if the NIST object does not contain Type04, Type 13 or Type14 data.
            
            Usage:
            
                >>> mark.set_size( ( 500, 500 ) )
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
            
            :raise notImplemented: if the NIST object does not contain Type04, Type 13 or Type14 data.
            
            Usage:
            
                >>> mark.get_diptych() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=1000x500 at ...>
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
            
            See :
                * :func:`NIST.traditional.NIST.add_Type01`
                * :func:`NIST.traditional.NIST.add_Type02`
                * :func:`NIST.fingerprint.NISTf.add_Type09`
                * :func:`NIST.fingerprint.NISTf.add_Type13`
                * :func:`NIST.fingerprint.NISTf.set_latent`
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
            
            See :
                * :func:`NIST.fingerprint.NISTf.add_Type01`
                * :func:`NIST.fingerprint.NISTf.add_Type02`
                * :func:`NIST.fingerprint.NISTf.add_Type04`
                * :func:`NIST.fingerprint.NISTf.set_print`
                * :func:`NIST.fingerprint.NISTf.add_Type09`
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
            
            :raise notImplemented: if the NIST object does not contain Type04, Type 13 or Type14 data.
            
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
                    01.002 VER: 0501
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
                    02.001 LEN: 00000062
                    02.002 IDC: 0
                    02.003    : 0300
                    02.004    : ...
                    02.054    : 0300<US><US>
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
                    01.002 VER: 0501
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
                    02.001 LEN: 00000062
                    02.002 IDC: 0
                    02.003    : 0300
                    02.004    : ...
                    02.054    : 0300<US><US>
                NIST Type-04 (IDC 1)
                    04.001 LEN: 673
                    04.002 IDC: 1
                    04.003 IMP: 3
                    04.004 FGP: 0
                    04.005 ISR: 1
                    04.006 HLL: 500
                    04.007 VLL: 500
                    04.008 CGA: 1
                    04.999    : FFA0FFA8 ... 01FFA1FF (655 bytes)
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
        
        if type( idc ) == list:
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
        
        if type( minutiae ) == int:
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
            :type size: tuple
            
            :param res: Resolution of the image, in dot-per-inch.
            :type res: int
            
            :param idc: IDC value.
            :type idc: int
        """
        ntype = 14
        
        if type( idc ) == list:
            for i in idc:
                self.add_default( ntype, i )
        
        else:
            self.add_default( ntype, idc )
            
            self.set_field( "14.005", self.date, idc )
            
            w, h = size
            self.set_field( "14.006", w, idc )
            self.set_field( "14.007", h, idc )
            self.set_field( "14.999", chr( 255 ) * h * w, idc )
            
            self.set_field( "14.009", res, idc )
            self.set_field( "14.010", res, idc )
            
            self.set_field( "14.013", idc, idc )
    
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
            if type( format ) == int:
                idc, format = format, "ixytdq"
            
            # Check the IDC value
            idc = self.checkIDC( 9, idc )
            
            # Get and process the M1 finger minutiae data field
            data = self.get_field( "9.137", idc )
            data = split_r( [ RS, US ], data )
            data = map_r( int, data )
            
            # Select the information to retrun
            ret = []
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
        
        if type( data ) == list:
            data = lstTo137( data, self.get_resolution( idc ) )
        
        self.set_field( "9.137", data )
        
        minnum = len( data.split( RS ) ) - 1
        self.set_field( "9.136", minnum )
        
        return minnum
