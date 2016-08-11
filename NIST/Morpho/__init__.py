#!/usr/bin/python
# -*- coding: UTF-8 -*-

from ..fingerprint import NISTf

class NIST_Morpho( NISTf ):
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
    
    def set_caseName( self, name ):
        """
            Set the case name field.
        """
        self.set_field( "2.007", name )
