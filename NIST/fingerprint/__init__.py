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
from MDmisc.logger import debug
from MDmisc.string import upper, split_r
from NIST.traditional.config import FS
from WSQ import WSQ

from ..traditional import NIST
from ..traditional.config import RS, US, default_origin
from ..traditional.exceptions import needIDC, notImplemented, idcNotFound
from ..traditional.functions import decode_gca
from .exceptions import minutiaeFormatNotSupported
from .functions import lstTo012, lstTo137, PILToRAW, mm2px, px2mm
from .voidType import voidType


voidType.update( voidType )

class NISTf( NIST ):
    def __init__( self, *args ):
        self.imgdir = os.path.split( os.path.abspath( __file__ ) )[ 0 ] + "/images"
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
    #    Minutiae functions
    # 
    ############################################################################
    
    def get_minutiae( self, format = "ixytqd", idc = -1 ):
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
        """
        # If the 'format' value is an int, then the function is called without
        # the 'format' argument, but the IDC is passed instead.
        if type( format ) == int:
            idc, format = format, "ixytdq"
        
        # Get the minutiae string, without the final <FS> character.                
        minutiae = self.get_field( "9.012", idc ).replace( FS, "" )
        
        if minutiae == None:
            return []
        else:
            ret = []
            
            for m in minutiae.split( RS ):
                if len( m ) != 0:
                    try:
                        id, xyt, q, d = m.split( US )
                        
                        tmp = []
                        
                        for c in format:
                            if c == "i":
                                tmp.append( id )
                            
                            if c == "x":
                                tmp.append( int( xyt[ 0:4 ] ) / 100 )
                            
                            if c == "y":
                                tmp.append( int( xyt[ 4:8 ] ) / 100 )
                            
                            if c == "t":
                                tmp.append( int( xyt[ 8:11 ] ) )
                            
                            if c == "d":
                                tmp.append( d )
                            
                            if c == "q":
                                tmp.append( q )
                        
                        ret.append( tmp )
                    except:
                        raise minutiaeFormatNotSupported
            
            return ret
    
    def get_minutiae_all( self, format, idc = -1 ):
        """
            Return the minutiae for all 10 fingers. If the idc is not present in
            the NIST object, i.e. the finger is missing, an empty list of
            minutiae is returned, to complete the tenprint card.
        """
        if ifany( [ 4, 14 ], self.get_ntype() ):
            ret = []
            
            for idc in xrange( 1, 11 ):
                try:
                    ret.append( self.get_minutiae( format, idc ) )
                except idcNotFound:
                    ret.append( [] )
            
            return ret
        else:
            raise notImplemented
    
    def get_minutiaeCount( self, idc = -1 ):
        """
            Return the number of minutiae stored.
        """
        try:
            return int( self.get_field( "9.010", idc ) )
        except:
            return 0
    
    def get_center( self, idc = -1 ):
        """
            Process and return the center coordinate.
        """
        c = self.get_field( "9.008", idc )
        
        if c == None:
            return None
        else:
            x = int( c[ 0:4 ] ) / 100
            y = int( c[ 4:8 ] ) / 100
            
            return ( x, y )
    
    def set_minutiae( self, data, idc = -1 ):
        """
            Set the minutiae in the field 9.012.
            The 'data' parameter can be a minutiae-table (id, x, y, theta, quality, type) or
            the final string.
        """
        idc = self.checkIDC( 9, idc )
        
        if type( data ) == list:
            data = lstTo012( data )
        
        self.set_field( "9.012", data, idc )
        
        minnum = len( data.split( RS ) ) - 1
        self.set_field( "9.010", minnum, idc )
        
        return minnum
    
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
            if self.get_minutiaeCount( idc ) == 0:
                return
            else:
                lst = []
                
                w = self.px2mm( self.get_width( idc ), idc )
                h = self.px2mm( self.get_height( idc ), idc )
                
                id = 0
                
                for x, y, theta, quality, t in self.get_minutiae( "xytqd", idc ):
                    if ( not x < 0 and not x > w ) and ( not y < 0 and not y > h ):
                        id += 1
                        lst.append( [ "%03d" % id, x, y, theta, quality, t ] )
                
                lst = lstTo012( lst )    
                
                self.set_field( "9.010", id, idc )
                self.set_field( "9.012", lst, idc )
    
    ############################################################################
    # 
    #    Image processing
    # 
    ############################################################################
    
    #    Size
    def get_size( self, idc = -1 ):
        """
            Get a python-tuple representing the size of the image.
            
            >>> n.get_size()
            (500, 500)
        """
        return ( self.get_width( idc ), self.get_height( idc ) )
    
    def get_width( self, idc = -1 ):
        """
            Return the width of the Type-13 image.
            
            >>> n.get_width()
            500
        """
        if 13 in self.get_ntype():
            return int( self.get_field( "13.006", idc ) )
        
        elif 4 in self.get_ntype():
            return int( self.get_field( "4.006", idc ) )
        
        else:
            raise notImplemented
    
    def get_height( self, idc = -1 ):
        """
            Return the height of the Type-13 image.
            
            >>> n.get_height()
            500
        """
        if 13 in self.get_ntype():
            return int( self.get_field( "13.007", idc ) )
        
        elif 4 in self.get_ntype():
            return int( self.get_field( "4.007", idc ) )
        
        else:
            raise notImplemented
    
    #    Resolution
    def get_resolution( self, idc = -1 ):
        """
            Return the (horizontal) resolution of the Type-13 image in dpi.
            
            >>> n.get_resolution()
            500
        """
        return self.get_horizontalResolution( idc )
    
    def get_horizontalResolution( self, idc = -1 ):
        """
            Return the horizontal resolution.
            If the resolution is stored in px/cm, the conversion to dpi is done.
            
            >>> n.get_horizontalResolution()
            500
        """
        if 13 in self.get_ntype():
            if self.get_field( "13.008", idc ) == '1':
                return int( self.get_field( "13.009", idc ) )
            elif self.get_field( "13.008", idc ) == '2':
                return int( round( self.get_field( "13.009", idc ) / 10 * 25.4 ) )
        
        elif 4 in self.get_ntype():
            return int( round( float( self.get_field( "1.011" ) ) * 25.4 ) )
        
        else:
            raise notImplemented
    
    def get_verticalResolution( self, idc = -1 ):
        """
            Return the vertical resolution of the Type-13 image.
            If the resolution is stored in px/cm, the conversion to dpi is done.
            
            >>> n.get_verticalResolution()
            500
        """
        
        if 13 in self.get_ntype():
            if self.get_field( "13.008", idc ) == '1':
                return int( self.get_field( "13.010", idc ) )
            elif self.get_field( "13.008", idc ) == '2':
                return int( round( self.get_field( "13.010", idc ) / 10 * 25.4 ) )
        
        elif 4 in self.get_ntype():
            return int( round( float( self.get_field( "1.011" ) ) * 25.4 ) )
        
        else:
            raise notImplemented
    
    def set_resolution( self, res, idc = -1 ):
        """
            Set the resolution in dpi.
        """
        res = int( res )
        
        self.set_horizontalResolution( res, idc )
        self.set_verticalResolution( res, idc )
        
        self.set_field( "13.008", "1", idc )
    
    def set_horizontalResolution( self, value, idc = -1 ):
        """
            Set the horizontal resolution.
        """
        self.set_field( "13.009", value, idc )
    
    def set_verticalResolution( self, value, idc = -1 ):
        """
            Set the vertical resolution.
        """
        self.set_field( "13.010", value, idc )
    
    #    Compression
    def get_compression( self, idc = -1 ):
        """
            Get the compression used in the latent image.
            
            >>> n.get_compression()
            'RAW'
        """
        if 13 in self.get_ntype():
            gca = self.get_field( "13.011", idc )
        
        elif 4 in self.get_ntype():
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
            
            >>> n.annotate( n.get_latent( 'PIL' ), n.get_minutiae() ) # doctest: +ELLIPSIS
            <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
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
        
        # Image
        img = img.convert( "RGB" )
        
        if type == "minutiae":
            # Minutiae
            endmark = Image.open( self.imgdir + "/end.png" )
            newsize = ( int( endmark.size[ 0 ] * fac ), int( endmark.size[ 1 ] * fac ) )
            endmark = endmark.resize( newsize, Image.BICUBIC )
            
            if len( data ) != 0:
                for x, y, theta in data: 
                    x = x / 25.4 * res
                    y = y / 25.4 * res
                    
                    y = height - y
                    
                    x = int( x )
                    y = int( y )
                    
                    end2 = endmark.rotate( theta, Image.BICUBIC, True )
                    offsetx = int( end2.size[ 0 ] / 2 )
                    offsety = int( end2.size[ 1 ] / 2 )
                    
                    endcolor = Image.new( 'RGBA', end2.size, red )
                    
                    img.paste( endcolor, ( x - offsetx, y - offsety ), mask = end2 )
        
        elif type == "center":
            # Center
            if data != None:
                cx, cy = data
                
                cx = cx / 25.4 * res
                cy = cy / 25.4 * res
                cy = height - cy
                
                cx = int( cx )
                cy = int( cy )
                
                centermark = Image.open( self.imgdir + "/center.png" )
                newsize = ( int( centermark.size[ 0 ] * fac ), int( centermark.size[ 1 ] * fac ) )
                centermark = centermark.resize( newsize, Image.BICUBIC )
                
                offsetx = centermark.size[ 0 ] / 2
                offsety = centermark.size[ 1 ] / 2
                
                centercolor = Image.new( 'RGBA', centermark.size, red )
                
                img.paste( centercolor, ( cx - offsetx, cy - offsety ), mask = centermark )
        
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
            
            >>> n.get_latent( 'PIL' ) # doctest: +ELLIPSIS
            <PIL.Image.Image image mode=L size=500x500 at ...>
            
            >>> raw = n.get_latent( 'RAW' ) # doctest: +ELLIPSIS
            >>> raw == '\\xFF' * 250000
            True
        """
        format = upper( format )
        
        idc = self.checkIDC( 13, idc )
        
        gca = decode_gca( self.get_field( "13.011", idc ) )
        
        imgdata = self.get_field( "13.999", idc )
        
        if gca == "JP2":
            buff = StringIO( imgdata )
            img = Image.open( buff )
            
            if format == "PIL":
                return img
            
            elif format == "RAW":
                return PILToRAW( img )
            
            elif format == "JP2":
                return buff
        
        elif gca == "RAW":
            if format == "RAW":
                return imgdata
            
            elif format == "PIL":
                return RAWToPIL( imgdata, self.get_size( idc ), self.get_resolution( idc ) )
            
            else:
                raise NotImplemented
    
    def export_latent( self, f, idc = -1 ):
        idc = self.checkIDC( 13, idc )
        
        return self.get_latent( "PIL", idc ).save( f )
    
    def get_latent_annotated( self, idc = -1 ):
        """
            Function to return the annotated latent.
            
            >>> n.get_latent_annotated() # doctest: +ELLIPSIS
            <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        img = self.annotate( self.get_latent( 'PIL', idc ), self.get_minutiae( "xyt", idc ), "minutiae" )
        img = self.annotate( img, self.get_center( idc ), "center" )
        
        return img
    
    def get_latent_diptych( self, idc = -1 ):
        """
            Function to return the diptych of the latent fingermark (latent and
            annotated latent)
            
            >>> n.get_latent_diptych() # doctest: +ELLIPSIS
            <PIL.Image.Image image mode=RGB size=1000x500 at ...>
        """
        img = self.get_latent( 'PIL', idc )
        anno = self.get_latent_annotated( idc )
        
        new = Image.new( "RGB", ( img.size[ 0 ] * 2, img.size[ 1 ] ), "white" )
        
        new.paste( img, ( 0, 0 ) )
        new.paste( anno, ( img.size[ 0 ], 0 ) )
        
        return new
    
    def set_latent( self, data, res = 500, idc = -1 ):
        """
            Detect the type of image passed in parameter and store it in the
            13.999 field.
        """
        if type( data ) == str:
            self.set_field( "13.999", data, idc )
        
        elif isinstance( data, Image.Image ):
            self.set_latent( PILToRAW( data ), res, idc )
            self.set_size( data.size, idc )
            
        self.set_field( "13.011", "0", idc )
        self.set_resolution( res, idc )
    
    def set_latent_size( self, value, idc = -1 ):
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
                w, h = self.get_size()
                
                img = self.get_image( "PIL", idc )
                img = img.resize( ( int( w * fac ), int( h * fac ) ), Image.BICUBIC )
                
                self.set_size( img.size )
                
                if 4 in self.get_ntype():
                    self.set_field( "1.011", round( 100 * res / 25.4 ) / 100.0 )
                    self.set_field( "4.999", PILToRAW( img ) )
                    
                elif 13 in self.get_ntype():
                    # Change resolution
                    self.set_resolution( res )
                
                    self.set_field( "13.999", PILToRAW( img ) )
                    
                else:
                    raise ValueError
    
    def crop( self, size, center = None, idc = -1 ):
        """
            Crop an latent of print image.
        """
        if 13 in self.get_ntype():
            ntype = 13
        elif 4 in self.get_ntype():
            ntype = 4
        else:
            raise notImplemented
        
        idc = self.checkIDC( ntype, idc )
        
        if center == None:
            center = self.get_size( idc )
            center = map( lambda x: int( 0.5 * x ), center )
            center = map( int, center )
        
        img = self.get_image( "PIL", idc )
        
        offset = ( ( size[ 0 ] / 2 ) - center[ 0 ], ( size[ 1 ] / 2 ) - center[ 1 ] )
        offset = tuple( map( int, offset ) )
        
        offsetmin = ( ( size[ 0 ] / 2 ) - center[ 0 ], ( -( self.get_height( idc ) + ( size[ 1 ] / 2 ) - center[ 1 ] - size[ 1 ] ) ) )
        
        # Image cropping
        new = Image.new( 'L', size, 255 )
        new.paste( img, offset )
        
        self.set_size( new.size, idc )

        offset = map( lambda x: x * 25.4 / self.get_resolution( idc ), offsetmin )
        
        self.set_field( ( ntype, 999 ), PILToRAW( new ), idc )
        
        # Minutiae cropping
        minu = self.get_minutiae( "ixytqd", idc )
        
        for i, value in enumerate( minu ):
            minu[ i ][ 1 ] += offsetmin[ 0 ] * 25.4 / self.get_resolution( idc )
            minu[ i ][ 2 ] += offsetmin[ 1 ] * 25.4 / self.get_resolution( idc )
        
        self.set_minutiae( minu, idc )
    
    ############################################################################
    # 
    #    Print processing
    # 
    ############################################################################
    
    def get_print( self, format = 'WSQ', idc = -1 ):
        """
            Return the print image, WSQ or PIL format.
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
    
    def get_print_annotated( self, idc = -1 ):
        """
            Function to return the annotated print.
        """
        img = self.annotate( self.get_print( 'PIL', idc ), self.get_minutiae( "xyt", idc ), "minutiae", self.get_resolution( idc ) )
        img = self.annotate( img, self.get_center( idc ), "center", self.get_resolution( idc ) )
        
        return img
    
    def get_print_diptych( self, idc = -1 ):
        """
            Function to return the diptych of the latent fingermark (latent and
            annotated latent)
            
            >>> n.get_latent_diptych() # doctest: +ELLIPSIS
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
        if 13 in self.get_ntype():
            return self.get_latent( format, idc )
        
        elif 4 in self.get_ntype():
            return self.get_print( format, idc )
        
        else:
            raise notImplemented
        
    def set_width( self, ntype, value, idc = -1 ):
        self.set_field( ( ntype, "006" ), value, idc )
    
    def set_height( self, ntype, value, idc = -1 ):
        self.set_field( ( ntype, "007" ), value, idc )
    
    def set_size( self, value, idc = -1 ):
        if 13 in self.get_ntype():
            self.set_latent_size( value, idc )
        
        elif 4 in self.get_ntype():
            self.set_print_size( value, idc )
        
        else:
            raise notImplemented    
    
    ############################################################################
    # 
    #    Add empty records to the NIST object
    # 
    ############################################################################
    
    def add_Type04( self, idc = -1 ):
        """
            Add the Type-04 record to the NIST object.
        """
        ntype = 4
        
        if type( idc ) == list:
            for i in idc:
                self.add_default( ntype, i )
        
        else:
            self.add_default( ntype, idc )
    
    def add_Type09( self, minutiae = None, idc = -1 ):
        """
            Add the Type-09 record to the NIST object, and set the Date.
        """
        ntype = 9
        
        if type( minutiae ) == int:
            idc, minutiae = minutiae, None
        
        self.add_default( ntype, idc )
        
        if minutiae != None:
            self.set_minutiae( minutiae, idc )
    
    def add_Type13( self, size = ( 500, 500 ), res = 500, idc = -1 ):
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
    
    ############################################################################
    #    
    #    Coordinates system
    #    
    ############################################################################
    
    def mm2px( self, data, idc = -1 ):
        """
            Transformation the coordinates from pixel to millimeters
            
            >>> n.mm2px( ( 12.7, 12.7 ) )
            [250.0, 250.0]
        """
        return mm2px( data, self.get_resolution( idc ) )
    
    def px2mm( self, data, idc = -1 ):
        """
            Transformation the coordinates from pixels to millimeters
            
            >>> n.px2mm( ( 250.0, 250.0 ) )
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
#    Deprecated class
# 
################################################################################

class NISTf_deprecated( NISTf ):
    """
        This class define all the deprecated functions (for backward
        compatibility). To use it, load the NISTf_deprecated class instead of
        the NISTf super class.
    """
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
