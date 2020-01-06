#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import division

from PIL import Image

from MDmisc.boxer import boxer
from MDmisc.logger import debug
from MDmisc.map_r import map_r
from MDmisc.string import split_r, split
from PMlib.formatConverter import cooNIST2PIL

from .functions import RLE_encode, RLE_decode

from ...core import needNtype
from ...fingerprint import NISTf
from ...fingerprint import AnnotationList, Minutia
from ...traditional import RS, US

class NISTULWLQMetric( object ):
    def __init__( self ):
        debug.critical( boxer( "ULWLQMetric module not found", "Have you installed the ULWLQMetric library?" ) )
 
try:
    from ULWLQMetric import ULWLQMetric

    class NISTULWLQMetric( NISTf, ULWLQMetric ):
        """
            Wrapper for the ULWLQMetric module, to be directly integrated in the
            NIST object.
        """
        @property
        def img( self ): 
            return self.get_latent( 'PIL' )
        
        def ULWLQMetric_update_data( self, idc = -1 ):
            """
                Encode the quality of the image, and update the correspondings
                filds in the NIST object.
            """
            idc = self.checkIDC( 9, idc )
            
            options = {}
            res = self.get_resolution( idc )
            if res != None:
                options[ 'res' ] = ( res, res )
                
            self.data[ 9 ][ idc ].update( super( NISTULWLQMetric, self ).ULWLQMetric_encode( 'EFS', **options ) )
        
        def get_LQMetric_map( self, idc = -1 ):
            """
                Get the LQMetric map of quality (field 9.308).
                
                :param idc: IDC value.
                :type idc: int
                
                :return: Quality map
                :rtype: str
            """
            return super( NISTULWLQMetric, self ).ULWLQMetric_encode( "EFS" )[ 308 ]
        
        def add_LQMetric_data( self, lst, idc = -1 ):
            """
                Add the ULW LQMetric for each Annotation passed in parameter.
                The LQMetric is evaluated from the quality map stored in the
                NIST object (in the field 9.308). 
            """
            if len( lst ) != 0:
                # Add the LQMetric quality 
                qmap = self.get_field( "9.308" )
                
                if qmap != None:
                    try:
                        gridSize, compression = self.get_field( "9.309", idc ).split( US )
                    except:
                        gridSize, compression = 20, "UNC"
                    
                    qmap = split( RS, qmap )
                    if compression == 'RLE':
                        qmap = RLE_decode( qmap )
                    
                    qmap = map( list, qmap )
                    
                    h = self.get_height( idc )
                    res = self.get_resolution( idc )
                    fac = int( round( int( gridSize ) / 100 * self.get_resolution( idc ) / 25.4 ) )
                    
                    for m in lst:
                        coo = cooNIST2PIL( ( m.x, m.y ), h, res )
                        x, y = map_r( lambda x: int( x / fac ), coo )
                        try:
                            m.LQM = int( qmap[ y ][ x ] )
                        except:
                            m.LQM = None
                    
                    newformat = list( lst[ 0 ]._format )
                    if "LQM" not in newformat:
                        newformat.append( "LQM" )
                    
                    lst.set_format( newformat )
                
            return lst
        
        def get_minutiae( self, format = None, idc = -1, **options ):
            return self.ULW_get_minutiae( format = format, idc = idc, **options )
        
        def ULW_get_minutiae( self, format = None, idc = -1, **options ):
            """
                Overload of the get_minutiae function to add the LQMetric information.
            """
            lst = super( NISTULWLQMetric, self ).get_minutiae( format = format, idc = idc, **options )
            
            try:
                lst = self.add_LQMetric_data( lst )
            except:
                pass
            
            lst.set_format( format )
            return lst
        
        def get_minutiae_by_LQM( self, criteria, higher = True, format = None, idc = -1, field = None ):
            """
                Filter out the minutiae based on the LQMetric value
            """
            lst = AnnotationList()
            
            minu = self.get_minutiae( format, idc = idc, field = field )
            
            for m in minu:
                if m.LQM >= criteria and higher:
                    lst.append( m )
                
                elif m.LQM <= criteria and not higher:
                    lst.append( m )
            
            return lst
        
        def get_latent_lqmap( self, idc = -1, **options ):
            data = self.get_field( "9.308" )
            
            if data != None:
                img = Image.new( "RGBA", self.get_size(), ( 0, 0, 0, 0 ) )
                pixels = img.load()
                
                alpha = int( options.get( "alpha", 100 ) )
                
                ULWcolour = {
                    '0': ( 0, 0, 0, alpha ),
                    '1': ( 255, 0, 0, alpha ),
                    '2': ( 255, 255, 0, alpha ),
                    '3': ( 0, 255, 0, alpha ),
                    '4': ( 0, 0, 255, alpha ),
                    '5': ( 0, 240, 240, alpha )
                }
                
                try:
                    gridSize, compression = self.get_field( "9.309", idc ).split( US )
                except:
                    gridSize, compression = 20, "UNC"
                
                data = split( RS, data )
                if compression == 'RLE':
                    data = map( RLE_decode, data )
                
                data = [ list( s ) for s in data ]
                
                fac = int( round( int( gridSize ) / 100 * self.get_resolution( idc ) / 25.4 ) )
                toplot = options.get( "q", [ '1', '2', '3', '4', '5' ] )
                toplot = map( str, toplot )
                
                for y, v in enumerate( data ):
                    for x, vv in enumerate( v ):
                        if vv in toplot:
                            for a in xrange( 0, fac ):
                                for b in xrange( 0, fac ):
                                    pixels[ fac * x + a, fac * y + b ] = ULWcolour[ vv ]
                
                latent = options.get( "img", self.get_latent( "PIL", idc ) )
                latent = latent.convert( "RGBA" )
                latent.paste( img, ( 0, 0 ), mask = img )
                
                return latent
            
            else:
                return None 
        
        def get_latent_triptych( self, content = "quality", idc = -1, **options ):
            """
                Get the triptych : latent, annotated latent, quality map (ULW).
            """
            if content == "quality":
                diptych = self.get_latent_diptych( idc, **options )
                
                qmap = self.get_latent_lqmap( idc )
                if qmap == None:
                    qmap = super( NISTULWLQMetric, self ).ULWLQMetric_encode( "image" ) 
                    qmap = qmap.chroma( ( 0, 0, 0 ) )
                    qmap = qmap.transparency( 0.5 )
                    
                    try:
                        gridSize = self.get_field( "9.309", idc ).split( US )[ 0 ]
                    except:
                        gridSize = 20
                    
                    fac = int( round( int( gridSize ) / 100 * self.get_resolution( idc ) / 25.4 ) )
                    qmap = qmap.scale( fac )
                
                latentqmap = self.get_latent( 'PIL', idc )
                latentqmap = latentqmap.convert( "RGBA" )
                latentqmap.paste( qmap, ( 0, 0 ), mask = qmap )
                
                new = Image.new( "RGB", ( self.get_width( idc ) * 3, self.get_height( idc ) ), "white" )
                
                new.paste( diptych, ( 0, 0 ) )
                new.paste( latentqmap, ( diptych.size[ 0 ], 0 ) )
                
                return new
            
            else:
                super( NISTULWLQMetric, self ).get_latent_triptych( content, idc )
            
except:
    pass
