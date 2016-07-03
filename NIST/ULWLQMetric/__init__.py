#!/usr/bin/env python
#  *-* coding: cp850 *-*

from future.builtins import super
from PIL import Image

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
            idc = self.checkIDC( 9, idc )
            self.data[ 9 ][ idc ].update( super().ULWLQMetric_encode( 'EFS' ) )
            self.clean()
        
        def get_latent_triptych( self, idc = -1 ):
            diptych = self.get_latent_diptych( idc )
            
            qmap = super().ULWLQMetric_encode( "image" )
            
            qmap = qmap.scale( 4 )
            
            
            new = Image.new( "RGB", ( self.get_width( idc ) * 3, self.get_height( idc ) ), "white" )
            
            new.paste( diptych, ( 0, 0 ) )
            new.paste( qmap, ( diptych.size[ 0 ], 0 ) )
            
            return new
            
except:
    debug.critical( boxer( "ULWLQMetric module not found", "Have you installed the ULWLQMetric library?" ) )
