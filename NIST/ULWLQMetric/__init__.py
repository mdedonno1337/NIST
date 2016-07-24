#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from future.builtins import super

from MDmisc.boxer import boxer
from MDmisc.logger import debug
from SoftPillow import Image
    
from ..fingerprint import NISTf
    
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
        
        def get_latent_triptych( self, idc = -1 ):
            """
                Get the triptych : latent, annotated latent, quality map (ULW).
            """
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
            
except:
    debug.critical( boxer( "ULWLQMetric module not found", "Have you installed the ULWLQMetric library?" ) )
