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
    def __init__( self, *args ):
        self.imgdir = os.path.split( os.path.abspath( __file__ ) )[ 0 ] + "/images"
        
        self.minutiaeformat = "ixytqd"
        
        super().__init__( *args )
    
    ############################################################################
    # 
    #    Cleaning and resetting functions
    # 
    ############################################################################
     
    def clean( self ):
        """
            Function to clean all unused fields in the self.data variable.
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
                4.005
                9.004
        """
        #    Type-04
        if 4 in self.get_ntype():
            for idc in self.get_idc( 4 ):
                #    4.005
                #        The minimum scanning resolution was defined in ANSI/NIST-
                #        ITL 1-2007 as "19.69 ppmm plus or minus 0.20 ppmm (500 ppi
                #        plus or minus 5 ppi)." Therefore, if the image scanning
                #        resolution corresponds to the Appendix F certification
                #        level (See Table 14 Class resolution with defined
                #        tolerance), a 0 shall be entered in this field.
                #        
                #        If the resolution of the Type-04 is in 500DPI +- 1%, then
                #        the 4.005 then field is set to 0, otherwise 1.
                debug.debug( "Set the conformity with the Appendix F certification level for Type-04 image", 1 )
                if 19.49 < float( self.get_field( "1.011" ) ) < 19.89:
                    self.set_field( "4.005", "0", idc )
                else:
                    self.set_field( "4.005", "1", idc )
         
        #    Type-09
        if 9 in self.get_ntype():
            for idc in self.get_idc( 9 ):
                #    9.004
                #        This field shall contain an "S" to indicate that the
                #        minutiae are formatted as specified by the standard Type-9
                #        logical record field descriptions. This field shall contain
                #        a "U" to indicate that the minutiae are formatted in
                #        vendor-specific or M1- 378 terms
                if any( x in [ 5, 6, 7, 8, 9, 10, 11, 12 ] for x in self.data[ 9 ][ idc ].keys() ):
                    debug.debug( "minutiae are formatted as specified by the standard Type-9 logical record field descriptions", 1 )
                    self.set_field( "9.004", "S", idc )
                else:
                    debug.debug( "minutiae are formatted in vendor-specific or M1-378 terms", 1 )
                    self.set_field( "9.004", "U", idc )
        
        #    Generic functino to patch to standard
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
            
            The parameter 'format' allow to select the data to extract:
            
                i: Index number
                x: X coordinate
                y: Y coordinate
                t: Angle theta
                d: Type designation
                q: Quality
            
            The 'format' parameter is optional. The IDC value can be passed in
            parameter even without format. The default format ('ixytdq') will be
            used.
            
            To get all information, dont speficy any format:
            
                >>> mark.get_minutiae() # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A' ),
                    Minutia( i='3', x='11.46', y='22.32', t='224', q='0', d='A' ),
                    Minutia( i='4', x='22.61', y='25.17', t='194', q='0', d='A' ),
                    Minutia( i='5', x='6.97', y='8.48', t='153', q='0', d='A' ),
                    Minutia( i='6', x='12.58', y='19.88', t='346', q='0', d='A' ),
                    Minutia( i='7', x='19.69', y='19.8', t='111', q='0', d='A' ),
                    Minutia( i='8', x='12.31', y='3.87', t='147', q='0', d='A' ),
                    Minutia( i='9', x='13.88', y='14.29', t='330', q='0', d='A' ),
                    Minutia( i='10', x='15.47', y='22.49', t='271', q='0', d='A' )
                ]
                >>> [ m.as_list() for m in mark.get_minutiae() ]
                [['1', 7.85, 7.05, 290, '0', 'A'], ['2', 13.8, 15.3, 155, '0', 'A'], ['3', 11.46, 22.32, 224, '0', 'A'], ['4', 22.61, 25.17, 194, '0', 'A'], ['5', 6.97, 8.48, 153, '0', 'A'], ['6', 12.58, 19.88, 346, '0', 'A'], ['7', 19.69, 19.8, 111, '0', 'A'], ['8', 12.31, 3.87, 147, '0', 'A'], ['9', 13.88, 14.29, 330, '0', 'A'], ['10', 15.47, 22.49, 271, '0', 'A']]
            
            The format parameter is used by the 'minutiae_filter()' function to
            sort the fields returned.
            
        """
        # Get the minutiae string, without the final <FS> character.                
        minutiae = self.get_field( "9.012", idc ).replace( FS, "" )
        
        lst = []
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
        
        if format != None:
            # If the 'format' value is an int, then the function is called
            # without the 'format' argument, but the IDC is passed instead.
            if type( format ) == int:
                idc, format = format, self.minutiaeformat
            
            for m in lst:
                m.set_format( format = format )
        
        return AnnotationList( lst )
        
    def get_minutiae_all( self, format = None ):
        """
            Return the minutiae for all 10 fingers. If the idc is not present in
            the NIST object, i.e. the finger is missing, an empty list of
            minutiae is returned, to complete the tenprint card.
            
            >>> pr.get_minutiae_all() # doctest: +NORMALIZE_WHITESPACE
                [[
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A' ),
                    Minutia( i='3', x='11.46', y='22.32', t='224', q='0', d='A' ),
                    Minutia( i='4', x='22.61', y='25.17', t='194', q='0', d='A' ),
                    Minutia( i='5', x='6.97', y='8.48', t='153', q='0', d='A' ),
                    Minutia( i='6', x='12.58', y='19.88', t='346', q='0', d='A' ),
                    Minutia( i='7', x='19.69', y='19.8', t='111', q='0', d='A' ),
                    Minutia( i='8', x='12.31', y='3.87', t='147', q='0', d='A' ),
                    Minutia( i='9', x='13.88', y='14.29', t='330', q='0', d='A' ),
                    Minutia( i='10', x='15.47', y='22.49', t='271', q='0', d='A' )
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
            
            To get the minutiae '1':
                >>> mark.get_minutia_by_id( "1" )
                Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' )

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
        """
        return self.get_minutiae( idc ).get_by_type( designation, format )
    
    def get_minutiaeCount( self, idc = -1 ):
        """
            Return the number of minutiae stored.
            
            >>> mark.get_minutiaeCount()
            10
        """
        try:
            return int( self.get_field( "9.010", idc ) )
        except:
            return 0
    
    def get_cores( self, idc = -1, format = 'xy' ):
        """
            Process and return the center coordinate.
            
            >>> mark.get_cores()
            [Core( x='12.5', y='18.7' )]
        """
        try:
            cores = self.get_field( "9.008", idc ).split( RS )
            if cores == None:
                raise Exception
            
            ret = []
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
        """
        idc = self.checkIDC( 9, idc )
        
        def format( data ):
            x, y = data
            x *= 100
            y *= 100
            
            x = int( x )
            y = int( y )
            
            return "%04d%04d" % ( x, y )
        
        if data == None or data == []:
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
            The 'data' parameter can be a minutiae-table (id, x, y, theta, quality, type) or
            the final string.
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
                    lst = AnnotationList()
                    
                    w = self.px2mm( self.get_width( idc ), idc )
                    h = self.px2mm( self.get_height( idc ), idc )
                    
                    id = 0
                    
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
                
    ############################################################################
    # 
    #    Image processing
    # 
    ############################################################################
    
    #    Size
    def get_size( self, idc = -1 ):
        """
            Get a python-tuple representing the size of the image.
            
            >>> mark.get_size()
            (500, 500)
        """
        return ( self.get_width( idc ), self.get_height( idc ) )
    
    def get_width( self, idc = -1 ):
        """
            Return the width of the Type-13 image.
            
            >>> mark.get_width()
            500
        """
        if ifany( [ 4, 13 ], self.get_ntype() ):
            try:            
                return int( self.get_field( "13.006", idc ) )
            except:
                return int( self.get_field( "4.006", idc ) )
        else:
            raise notImplemented
    
    def get_height( self, idc = -1 ):
        """
            Return the height of the Type-13 image.
            
            >>> mark.get_height()
            500
        """
        if ifany( [ 4, 13 ], self.get_ntype() ):
            try:
                return int( self.get_field( "13.007", idc ) )
            
            except:
                return int( self.get_field( "4.007", idc ) )
        
        else:
            raise notImplemented
    
    #    Resolution
    def get_resolution( self, idc = -1 ):
        """
            Return the (horizontal) resolution of the Type-13 image in dpi.
            
            >>> mark.get_resolution()
            500
        """
        if ifany( [ 4, 13 ], self.get_ntype() ):
            try:
                if self.get_field( "13.008", idc ) == '1':
                    return int( self.get_field( "13.009", idc ) )
                elif self.get_field( "13.008", idc ) == '2':
                    return int( round( float( self.get_field( "13.009", idc ) ) / 10 * 25.4 ) )
            
            except:
                return int( round( float( self.get_field( "1.011" ) ) * 25.4 ) )

        else:
            raise notImplemented
    
    def set_resolution( self, res, idc = -1 ):
        """
            Set the resolution in dpi.
        """
        res = int( res )
        
        if ifany( [ 4, 13 ], self.get_ntype() ):
            try:
                self.set_field( "13.008", "1", idc )
                self.set_field( "13.009", res, idc )
                self.set_field( "13.010", res, idc )
                
            except:
                self.set_fields( [ "1.011", "1.012" ], "%2.2f" % ( res / 25.4 ) )
        
    #    Compression
    def get_compression( self, idc = -1 ):
        """
            Get the compression used in the latent image.
            
            >>> mark.get_compression()
            'RAW'
        """
        if ifany( [ 4, 13 ], self.get_ntype() ):
            try:
                gca = self.get_field( "13.011", idc )
        
            except:
                gca = self.get_field( "4.008", idc )
        
        else:
            raise notImplemented
        
        return decode_gca( gca )
    
    ############################################################################
    # 
    #    Misc image processing
    # 
    ############################################################################
    
    def annotate( self, img, data, type = "minutiae", res = None ):
        """
            Function to annotate the image with the data passed in argument.
            
            >>> mark.annotate( mark.get_latent( 'PIL' ), mark.get_minutiae( 'xyt' ) ) # doctest: +ELLIPSIS
            <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        img = img.convert( "RGB" )
        
        if data != None and len( data ) != 0:
            width, height = img.size
            
            if res == None:
                try:
                    res, _ = img.info[ 'dpi' ]
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
                    
                    img.paste( endcolor, ( int( x - offsetx ), int( y - offsety ) ), mask = end2 )
            
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
                    
                    img.paste( centercolor, ( int( cx - offsetx ), int( cy - offsety ) ), mask = centermark )
            
            else:
                raise notImplemented
            
        return img
    
    ############################################################################
    # 
    #    Latent processing
    # 
    ############################################################################
    
    def get_latent( self, format = 'RAW', idc = -1 ):
        """
            Return the image in the format passed in parameter (RAW or PIL).
            
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
        idc = self.checkIDC( 13, idc )
        return self.get_latent( "PIL", idc ).save( f )
    
    def export_latent_annotated( self, f, idc = -1 ):
        idc = self.checkIDC( 13, idc )
        return self.get_latent_annotated( idc ).save( f )
    
    def get_latent_annotated( self, idc = -1 ):
        """
            Function to return the annotated latent.
            
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
            
            >>> mark.get_latent_diptych() # doctest: +ELLIPSIS
            <PIL.Image.Image image mode=RGB size=1000x500 at ...>
        """
        img = self.get_latent( 'PIL', idc )
        anno = self.get_latent_annotated( idc )
        
        new = Image.new( "RGB", ( img.size[ 0 ] * 2, img.size[ 1 ] ), "white" )
        
        new.paste( img, ( 0, 0 ) )
        new.paste( anno, ( img.size[ 0 ], 0 ) )
        
        return new
    
    def set_latent( self, image, res = 500, idc = -1, **options ):
        """
            Detect the type of image passed in parameter and store it in the
            13.999 field.
        """
        if type( image ) == str:
            self.set_field( "13.999", image, idc )
        
        elif isinstance( image, Image.Image ):
            self.set_latent( PILToRAW( image ), res, idc )
            self.set_size( image.size, idc )
            
        self.set_field( "13.011", "0", idc )
        self.set_resolution( res, idc )
    
    def set_latent_size( self, value, idc = -1 ):
        """
            Set the size of the latent image.
        """
        width, height = value
        
        self.set_width( 13, width, idc )
        self.set_height( 13, height, idc )
    
    def changeResolution( self, res, idc = -1 ):
        """
            Change the resolution of the latent fingermark. The minutiae are not
            affected because they are stored in mm, not px.
        """
        if not ifany( [ 4, 13 ], self.get_ntype() ):
            raise notImplemented
        
        else:
            res = float( res )
            
            if res != self.get_resolution( idc ):
                fac = res / self.get_resolution( idc )
                
                
                # Image resizing
                w, h = self.get_size( idc )
                
                img = self.get_image( "PIL", idc )
                img = img.resize( ( int( w * fac ), int( h * fac ) ), Image.BICUBIC )
                
                self.set_size( img.size )
                
                if ifany( [ 4, 13 ], self.get_ntype() ):
                    try:
                        self.set_field( "1.011", round( 100 * res / 25.4 ) / 100.0 )
                        self.set_field( "4.999", PILToRAW( img ) )
                    
                    except:
                        self.set_resolution( res )
                        self.set_field( "13.999", PILToRAW( img ) )
                        
                else:
                    raise ValueError
    
    def crop_latent( self, size, center = None, idc = -1 ):
        """
            Crop the latent image.
        """
        if 13 in self.get_ntype():
            return self.crop( size, center, 13, idc )
        
        else:
            raise notImplemented
    
    def crop_print( self, size, center = None, idc = -1 ):
        """
            Crop the print image.
        """
        for ntype in [ 4, 14 ]:
            if ntype in self.get_ntype():
                return self.crop( size, center, ntype, idc )
            
        else:
            raise notImplemented
    
    def crop( self, size, center = None, ntype = None, idc = -1 ):
        """
            Crop the latent or the print image.
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
    
    def get_print( self, format = 'WSQ', idc = -1 ):
        """
            Return the print image, WSQ or PIL format.
            
            >>> pr.get_print() # doctest: +ELLIPSIS
            <PIL.Image.Image image mode=L size=500x500 at ...>
        """
        format = upper( format )
        
        data = self.get_field( "4.999", idc )
        
        if self.get_field( "4.008", idc ) == "0":
            if format == "RAW":
                return data
            
            else:
                return RAWToPIL( data, self.get_size( idc ), self.get_resolution( idc ) )
        
        else:
            if format == "WSQ":
                return data
            
            elif format == "PIL":
                return RAWToPIL( WSQ().decode( data ), self.get_size( idc ), self.get_resolution( idc ) )
            
            else:
                raise notImplemented
    
    def export_print( self, f, idc = -1 ):
        """
            Export the print image to the file 'f' passed in parameter.
        """
        idc = self.checkIDC( 4, idc )
        return self.get_print( "PIL", idc ).save( f )
    
    def export_print_annotated( self, f, idc = -1 ):
        """
            Export the annotated print fo the file 'f'.
            
        """
        idc = self.checkIDC( 4, idc )
        return self.get_print_annotated( idc ).save( f )
    
    def get_print_annotated( self, idc = -1 ):
        """
            Function to return the annotated print.
        """
        img = self.annotate( self.get_print( 'PIL', idc ), self.get_minutiae( "xyt", idc ), "minutiae", self.get_resolution( idc ) )
        img = self.annotate( img, self.get_cores( idc ), "center", self.get_resolution( idc ) )
        
        return img
    
    def get_print_diptych( self, idc = -1 ):
        """
            Function to return the diptych of the latent fingermark (latent and
            annotated latent)
            
            >>> mark.get_latent_diptych() # doctest: +ELLIPSIS
            <PIL.Image.Image image mode=RGB size=1000x500 at ...>
        """
        img = self.get_print( 'PIL', idc )
        anno = self.get_print_annotated( idc )
        
        new = Image.new( "RGB", ( img.size[ 0 ] * 2, img.size[ 1 ] ), "white" )
        
        new.paste( img, ( 0, 0 ) )
        new.paste( anno, ( img.size[ 0 ], 0 ) )
        
        return new
    
    def set_print( self, data, res = 500, size = ( 512, 512 ), format = "WSQ", idc = -1 ):
        """
            Function to set an print image to the 4.999 field, and set the size.
        """
        if isinstance( data, Image.Image ):
            try:
                res, _ = data.info[ 'dpi' ]
            
            except:
                pass
            
            finally:
                width, height = data.size
                if format == "WSQ":
                    data = WSQ().encode( data, data.size, res )
                elif format == "RAW":
                    data = PILToRAW( data )
        
        else:
            width, height = size
            
        self.set_field( "4.999", data, idc )
        
        if format == "WSQ":
            self.set_field( "4.008", "1", idc )
        elif format == "RAW":
            self.set_field( "4.008", "0", idc )
        
        self.set_print_size( ( width, height ), idc )
    
    def set_print_size( self, value, idc = -1 ):
        width, height = value
        
        self.set_width( 4, width, idc )
        self.set_height( 4, height, idc )
        
    ############################################################################
    # 
    #    Latent and print generic functions
    # 
    ############################################################################
    
    def get_image( self, format = "PIL", idc = -1 ):
        if ifany( [ 4, 13 ], self.get_ntype() ):
            try:
                return self.get_latent( format, idc )
            
            except:
                return self.get_print( format, idc )
        
        else:
            raise notImplemented
        
    def set_width( self, ntype, value, idc = -1 ):
        self.set_field( ( ntype, "006" ), value, idc )
    
    def set_height( self, ntype, value, idc = -1 ):
        self.set_field( ( ntype, "007" ), value, idc )
    
    def set_size( self, value, idc = -1 ):
        if ifany( [ 4, 13 ], self.get_ntype() ):
            try:
                self.set_latent_size( value, idc )
                
            except:
                self.set_print_size( value, idc )
        
        else:
            raise notImplemented    
    
    def get_diptych( self, idc = -1 ):
        if ifany( [ 4, 13, 14 ], self.get_ntype() ):
            try:
                return self.get_latent_diptych( idc )
            
            except:
                return self.get_print_diptych( idc )
    
    ############################################################################
    # 
    #    Add empty records to the NIST object
    # 
    ############################################################################
    
    def add_Type04( self, idc = 1 ):
        """
            Add the Type-04 record to the NIST object.
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
            Resolution (in dpi) to a white image.
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
        
    def add_Type14( self, size = ( 500, 500 ), res = 500, idc = 1 ):
        """
            Add the Type-14 record to the NIST object.
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
            
            >>> mark.mm2px( ( 12.7, 12.7 ) )
            [250.0, 250.0]
        """
        return mm2px( data, self.get_resolution( idc ) )
    
    def px2mm( self, data, idc = -1 ):
        """
            Transformation the coordinates from pixels to millimeters
            
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
            Get the minutiae information from the field 9.137 for the IDC passed
            in argument.
             
            The parameter 'format' allow to select the data to extract:
             
                i: Index number
                x: X coordinate
                y: Y coordinate
                t: Angle theta
                d: Type designation
                q: Quality
             
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
            Return the number of minutiae stored.
        """
        try:
            return int( self.get_field( "9.136", idc ) )
        except:
            return 0
    
    def set_minutiae( self, data, idc = -1 ):
        """
            Set the minutiae in the field 9.012.
            The 'data' parameter can be a minutiae-table (id, x, y, theta, quality, type) or
            the final string.
        """
        idc = self.checkIDC( 9, idc )
        
        if type( data ) == list:
            data = lstTo137( data, self.get_resolution( idc ) )
        
        self.set_field( "9.137", data )
        
        minnum = len( data.split( RS ) ) - 1
        self.set_field( "9.136", minnum )
        
        return minnum

################################################################################
# 
#    Creation of empty default NIST objects
# 
################################################################################

def new_latent( **kwargs ):
    """
        Creation of a default latent NIST object
    """
    
    n = NISTf()
    n.add_Type01()
    n.add_Type02()
    n.add_Type13( **kwargs )
    n.add_Type09( **kwargs )
    
    return n

def new_print( **kwargs ):
    """
        Creation of a default latent NIST object
    """
    
    n = NISTf()
    n.add_Type01()
    n.add_Type02()
    n.add_Type04( **kwargs )
    n.add_Type09( **kwargs )
    
    return n

def new_NIST( **kwargs ):
    type = kwargs.pop( "type", "latent" )
    
    if type == "latent":
        return new_latent( **kwargs )
    
    elif type == "print":
        return new_print( *kwargs )
    
    else:
        raise Exception()
    
################################################################################
# 
#    Deprecated class
# 
################################################################################

class NISTf_deprecated( NISTf ):
    """
        This class define all the deprecated functions (for backward
        compatibility). To use it, load the NISTf_deprecated class instead of
        the NISTf super class.
    """
    
    @deprecated( "use crop_core( size, idc ) instead" )
    def get_center( self, idc = -1 ):
        return self.get_cores( idc )
    
    @deprecated( "use crop_latent( size, center, idc ) instead" )
    def crop( self, size, center = None, idc = -1 ):
        return self.crop_latent( self, size, center, idc )
    
    @deprecated( "use the set_identifier( 'name' ) instead" )
    def set_name( self, name ):
        return self.set_identifier( name )
    
    @deprecated( "use the get_identifier() instead" )
    def get_name( self ):
        return self.get_identifier()
    
    @deprecated( "use the get_minutiae( 'xy' ) instead" )
    def get_minutiaeXY( self, idc = -1 ):
        return self.get_minutiae( "xy", idc )
    
    @deprecated( "use the get_minutiae( 'xyt' ) instead" )
    def get_minutiaeXYT( self, idc = -1 ):
        return self.get_minutiae( "xyt", idc )
    
    @deprecated( "use the get_minutiae( 'xytq' ) instead" )
    def get_minutiaeXYTQ( self, idc = -1 ):
        return self.get_minutiae( "xytq", idc )
    
    @deprecated( "use the get_latent( 'RAW', idc ) function instead" )
    def get_RAW( self, idc = -1 ):
        return self.get_latent( "RAW", idc )
    
    @deprecated( "use the get_latent( 'PIL', idc ) function instead" )
    def get_PIL( self, idc = -1 ):
        return self.get_latent( "PIL", idc )
    
    @deprecated( "use the get_latent( format, idc ) function instead" )
    def get_image( self, format = 'RAW', idc = -1 ):
        return self.get_latent( format, idc )
    
    @deprecated( "use the set_latent( data, idc ) function instead" )
    def set_image( self, data, idc = -1 ):
        return self.set_latent( data, idc )
