#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import division

from MDmisc import fuckit
from MDmisc.boxer import boxer
from MDmisc.logger import debug
from MDmisc.map_r import map_r
from MDmisc.string import split_r, split
from PMlib.formatConverter import cooNIST2PIL
from SoftPillow import Image
    
from ..fingerprint import NISTf
from ..fingerprint import AnnotationList, Minutia
from ..traditional import RS, US
from ..traditional import needNtype
    
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
            self.data[ 9 ][ idc ].update( super( NISTULWLQMetric, self ).ULWLQMetric_encode( 'EFS' ) )
        
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
            # Add the LQMetric quality 
            qmap = self.get_field( "9.308" )
            
            if qmap != None:
                qmap = map( list, split( RS, qmap ) )
                
                h = self.get_height( idc )
                res = self.get_resolution( idc )
                
                for m in lst:
                    coo = cooNIST2PIL( ( m.x, m.y ), h, res )
                    x, y = map_r( lambda x: int( x / 4 ), coo )
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
            return self.ULW_get_minutiae( self, format = format, idc = idc, **options )
        
        def ULW_get_minutiae( self, format = None, idc = -1, **options ):
            """
                Overload of the get_minutiae function to add the LQMetric information.
            """
            lst = super( NISTULWLQMetric, self ).get_minutiae( format = format, idc = idc, **options )
            
            with fuckit:
                lst = self.add_LQMetric_data( lst )
            
            lst.set_format( format )
            return lst
            
        def get_minutiae_by_LQM( self, criteria, higher = True, format = None, idc = -1, field = None ):
            """
                Filter out the minutiae based on the LQMetric value
            """
            lst = AnnotationList()
            
            minu = self.ULW_get_minutiae( format, idc = idc, field = field )
            
            for m in minu:
                if m.LQM >= criteria and higher:
                    lst.append( m )
                
                elif m.LQM <= criteria and not higher:
                    lst.append( m )
            
            return lst
        
        def get_latent_lqmap( self, idc = -1, **options ):
            data = self.get_field( "9.308" )
            
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
            
            data = [ list( s ) for s in data.split( RS ) ]
            fac = int( self.get_resolution( idc ) * 4 / 500 )
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
        
        def get_latent_triptych( self, content = "quality", idc = -1 ):
            """
                Get the triptych : latent, annotated latent, quality map (ULW).
            """
            if content == "quality":
                diptych = self.get_latent_diptych( idc )
                
                qmap = super( NISTULWLQMetric, self ).ULWLQMetric_encode( "image" )
                
                qmap = qmap.chroma( ( 0, 0, 0 ) )
                qmap = qmap.transparency( 0.5 )
                qmap = qmap.scale( self.get_resolution( idc ) * 4 / 500.0 )
                
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
    debug.critical( boxer( "ULWLQMetric module not found", "Have you installed the ULWLQMetric library?" ) )
