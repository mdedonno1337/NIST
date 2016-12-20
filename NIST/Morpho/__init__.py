#!/usr/bin/python
# -*- coding: UTF-8 -*-

from future.builtins import super

from ..fingerprint import NISTf
from ..traditional.functions import bindump

class NIST_Morpho( NISTf ):
    """
        Overload of the :func:`NIST.fingerprint.NISTf` class to implement
        functions specific to Morpho NIST files.
    """
    ############################################################################
    # 
    #    Get specific information
    # 
    ############################################################################
     
    def get_caseName( self ):
        """
            Return the case name (field 2.007).
            
            :return: Case name.
            :rtype: str
        """
        return self.get_field( "2.007" )
    
    def set_caseName( self, name ):
        """
            Set the case name field (field 2.007).
            
            :param name: Name of the case to set in the field 2.007
        """
        self.set_field( "2.007", name )
        
    ############################################################################
    # 
    #    User defined fields
    # 
    ############################################################################
    
    def format_field( self, ntype, tagid, idc = -1 ):
        """
            Add some binary fields to the list of fields to format with
            :func:`NIST.traditional.functions.bindump`.
        """
        value = self.get_field( ( ntype, tagid ), idc )
        
        if ntype == 9 and tagid == 184:
            return bindump( value )
        
        else:
            return super().format_field( ntype, tagid, idc )
