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
     
    def get_caseName( self, idc = -1 ):
        """
            Return the case name (field 2.007).
            
            :return: Case name.
            :rtype: str
        """
        return self.get_field( "2.007", idc )
    
    def set_caseName( self, name, idc = -1 ):
        """
            Set the case name field (field 2.007).
            
            :param name: Name of the case to set in the field 2.007
        """
        self.set_field( "2.007", name, idc )
        
    ############################################################################
    # 
    #    User defined fields
    # 
    ############################################################################
    
    def is_binary( self, ntype, tagid ):
        """
            Add some binary fields to the list of fields to format with
            :func:`NIST.traditional.functions.bindump`.
        """
        if ntype == 9 and tagid == 184:
            return True
        
        else:
            return super().is_binary( ntype, tagid )
