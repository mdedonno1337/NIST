#!/usr/bin/python
# -*- coding: UTF-8 -*-

from future.builtins import super

from MDmisc.string import split_r

from ..fingerprint import NISTf
from ..traditional.config import RS
from ..traditional.config import US

################################################################################
# 
#    Wrapper around the NISTf object to work with the supplementaty information
#    added in the user-definded fields.
# 
################################################################################

class NIST_MDD( NISTf ):
    def get_pairing( self, idc = -1 ):
        """
            Return the pairing information ( minutia id, pairing id ). This
            information is stored in the field 9.255.
        """
        return split_r( [ RS, US ], self.get_field( "9.255", idc ) )
    
    def get_minutiae_paired( self, idc = -1 ):
        """
            Return all minutiae which are paired. The pairing information is not
            returned here.
        """
        return [ self.get_minutia_by_id( minutiaid, idc ) for minutiaid, _ in self.get_pairing( idc ) ]
