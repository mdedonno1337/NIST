#!/usr/bin/python
# -*- coding: UTF-8 -*-

from ..fingerprint import NISTf

class NIST( NISTf ):
    ############################################################################
    # 
    #    Get specific information
    # 
    ############################################################################
     
    def get_caseName( self ):
        """
            Return the case name.
        """
        return self.get_field( "2.007" )
    