#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import division

from future.builtins import super

from MDmisc.boxer import boxer
from MDmisc.logger import debug
from MDmisc.string import split_r
from SoftPillow import Image
    
from ..fingerprint import NISTf
from ..fingerprint import AnnotationList, Minutia
from ..traditional import RS, US
    
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
        
        def ULWLQMetric_encode( self, idc = -1 ):
            """
                Encode the quality of the image, and update the correspondings
                filds in the NIST object.
            """
            idc = self.checkIDC( 9, idc )
            self.data[ 9 ][ idc ].update( super().ULWLQMetric_encode( 'EFS' ) )
            self.clean()
        
        def get_minutiae( self, format = None, idc = -1 ):
            """
                Overload of the `NIST.fingerprint.NISTf.get_minutiae()` function
                to extract the information from the 9.331 field if not present
                in the 9.012 field.
                
                .. see:: :func:`NIST.fingerprint.NISTf.get_minutiae()`
            """
            try:
                return super().get_minutiae( format = format, idc = idc )
            
            except AttributeError:
                lst = AnnotationList()
                
                for m in split_r( [ RS, US ], self.get_field( "9.331", idc ) ):
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
        
        def get_latent_triptych( self, content = "quality", idc = -1 ):
            """
                Get the triptych : latent, annotated latent, quality map (ULW).
            """
            if content == "quality":
                diptych = self.get_latent_diptych( idc )
                
                qmap = super().ULWLQMetric_encode( "image" )
                
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
                super().get_latent_triptych( content, idc )
            
except:
    debug.critical( boxer( "ULWLQMetric module not found", "Have you installed the ULWLQMetric library?" ) )
