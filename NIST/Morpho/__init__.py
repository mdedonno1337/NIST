#!/usr/bin/python
# -*- coding: UTF-8 -*-

from future.builtins import super

from ..fingerprint import NISTf
from ..traditional.functions import bindump

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
        
    ############################################################################
    # 
    #    User defined fields
    # 
    ############################################################################
    
    def format_field( self, ntype, tagid, idc = -1 ):
        value = self.get_field( ( ntype, tagid ), idc )
        
        if ntype == 9 and tagid == 184:
            return bindump( value )
        
        else:
            return super().format_field( ntype, tagid, idc )
