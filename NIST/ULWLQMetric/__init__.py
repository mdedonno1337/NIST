#!/usr/bin/env python
#  *-* coding: cp850 *-*

from future.builtins import super
from PIL import Image

from MDmisc.boxer import boxer
from MDmisc.logger import debug
    
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
            img = self.get_latent( 'PIL', idc )
            anno = self.get_latent_annotated( idc )
            qmap = super().ULWLQMetric_encode( "image" )
            
            qmap = qmap.resize( img.size, Image.ANTIALIAS )
            
            new = Image.new( "RGB", ( img.size[ 0 ] * 3, img.size[ 1 ] ), "white" )
            
            new.paste( img, ( 0, 0 ) )
            new.paste( anno, ( img.size[ 0 ], 0 ) )
            new.paste( qmap, ( img.size[ 0 ] * 2, 0 ) )
            
            return new
            
except:
    debug.critical( boxer( "ULWLQMetric module not found", "Have you installed the ULWLQMetric library?" ) )
