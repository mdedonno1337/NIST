#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from future.builtins import super

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
            
except:
    debug.critical( boxer( "ULWLQMetric module not found", "Have you installed the ULWLQMetric library?" ) )
