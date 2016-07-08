#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import absolute_import

from future.builtins.misc import super
from math import cos, pi, sin
from PIL import Image, ImageDraw, ImageFont

from MDmisc.deprecated import deprecated
from MDmisc.imageprocessing import RAWToPIL
from MDmisc.elist import ifany
from MDmisc.logger import debug
from MDmisc.string import upper
from NIST.traditional.config import FS
from WSQ import WSQ

from ..traditional import NIST
from ..traditional.config import RS, US, default_origin
from ..traditional.exceptions import needIDC, notImplemented, idcNotFound
from ..traditional.functions import decode_gca
from .exceptions import minutiaeFormatNotSupported
from .functions import lstTo012, PILToRAW, mm2px, px2mm
from .voidType import voidType


voidType.update( voidType )

class NISTf( NIST ):
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
        
        #    Call the super().patch_to_standard()
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
            idc = format
            format = "ixytdq"
         
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
                                tmp.append( int( xyt[ 0:4 ] ) / 100.0 )
                             
                            if c == "y":
                                tmp.append( int( xyt[ 4:8 ] ) / 100.0 )
                             
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
            x = int( c[ 0:4 ] ) / 100.0
            y = int( c[ 4:8 ] ) / 100.0
 
            return ( x, y )
     
    def set_minutiae( self, data ):
        """
            Set the minutiae in the field 9.012.
            The 'data' parameter can be a minutiae-table (id, x, y, theta, quality, type) or
            the final string.
        """
        if type( data ) == list:
            data = lstTo012( data )
             
        self.set_field( "9.012", data )
         
        minnum = len( data.split( RS ) ) - 1
        self.set_field( "9.010", minnum )
         
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
            Return the horizontal resolution of the Type-13 image.
            If the resolution is stored in px/cm, the conversion to dpi is done.
            
            >>> n.get_horizontalResolution()
            500
        """
        if 13 in self.get_ntype():
            if self.get_field( "13.008", idc ) == '1':
                return int( self.get_field( "13.009", idc ) )
            elif self.get_field( "13.008", idc ) == '2':
                return int( round( self.get_field( "13.009", idc ) / 10.0 * 25.4 ) )
            
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
                return int( round( self.get_field( "13.010", idc ) / 10.0 * 25.4 ) )
            
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
            res, _ = img.info[ 'dpi' ]
        
        pointSize = res / 50
        fontsize = int( 0.8 * pointSize )
    
        # Image
        img = img.convert( "RGB" )
        font = ImageFont.truetype( "arial.ttf", fontsize )
        draw = ImageDraw.Draw( img )
        
        if type == "minutiae":
            # Minutiae
            i = 0
            if len( data ) != 0:
                 
                for x, y, theta in data: 
                    x = x / 25.4 * res
                    y = y / 25.4 * res
                     
                    y = height - y
                     
                    i += 1
                     
                    xc = int( x ) - ( pointSize / 2 )
                    yc = int( y ) - ( pointSize / 2 )
                     
                    theta = -theta + 180
                     
                    x2 = x + 2 * pointSize * cos( theta / 180.0 * pi )
                    y2 = y + 2 * pointSize * sin( theta / 180.0 * pi )
                     
                    txt = Image.new( 'RGB', ( pointSize, pointSize ), ( 255, 0, 0 ) )
                    d = ImageDraw.Draw( txt )
                    d.text( ( 0, 0 ), "%s" % i, font = font, fill = ( 255, 255, 255 ) )
                    img.paste( txt, ( xc, yc ) )
    
                    draw.line( ( x, y, x2, y2 ), fill = ( 255, 0, 0 ), width = 3 )

        elif type == "center":
            # Center
            if data != None:
                cx, cy = data
                 
                cx = cx / 25.4 * res
                cy = cy / 25.4 * res
                cy = height - cy
                 
                yellow = Image.new( "RGB", ( pointSize, pointSize ), ( 255, 255, 0 ) )
                 
                img.paste( yellow, ( int( data[0] ) - 5, int( data[1] ) - 5 ) )
        
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
         
        raw = self.get_field( "13.999", idc )
         
        if format == "RAW":
            return raw
        
        elif format == "PIL":
            return RAWToPIL( raw, self.get_size( idc ), self.get_resolution( idc ) )

        else:
            raise NotImplemented
    
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
    
    def set_print_size( self, value, idc = -1 ):
        width, height = value
        
        self.set_width( 4, width, idc )
        self.set_height( 4, height, idc )
        
    ############################################################################
    # 
    #    Latent and print generic functions
    # 
    ############################################################################
    
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
     
    def add_Type09( self, minutiae = None, idc = -1 ):
        """
            Add the Type-09 record to the NIST object, and set the Date.
        """
        ntype = 9
        
        if type( minutiae ) == int:
            idc, minutiae = minutiae, None
        
        self.add_default( ntype, idc )
        
        if minutiae != None:
            self.set_field( "9.010", minutiae.count( RS ), idc )
            self.set_field( "9.012", minutiae, idc )
     
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
#    Deprecated class
# 
################################################################################

class NISTf_deprecated( NISTf ):
    """
        This class define all the deprecated functions (for backward
        compatibility). To use it, load the NISTf_deprecated class instead of
        the NISTf super class.
    """
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
