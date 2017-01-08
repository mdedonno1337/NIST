#!/usr/bin/python
# -*- coding: UTF-8 -*-

from future.builtins import super

import base64
import os
import zipfile

from _collections import defaultdict
from cStringIO import StringIO

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
    #    MorphiBIS specific functions
    # 
    ############################################################################
    
    def get_cfv( self, idc = -1 ):
        """
            Return the CFV files used for by the matcher.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Binary CFV file.
            :rtype: Bitstring
        """
        return self.get_jar( idc )[ 'features' ]
    
    def get_jar( self, idc = -1 ):
        """
            Get the content of all files present in the JAR file stored in the
            field 9.184. The returned dictionnary contains the as follow::
                
                {
                    'file name': 'file content',
                    ...
                }
            
            The content of the files are not parsed, but returned as string value.
            
            :param idc: IDC value.
            :type idc: int
                        
            :return: Content of all files stored in the JAR file.
            :rtype: dict
        """
        idc = self.checkIDC( 9, idc )
        
        data = self.get_field( "9.184", idc )
        data = base64.decodestring( data )
        
        buffer = StringIO()
        buffer.write( data )
        
        ret = defaultdict()
        
        with zipfile.ZipFile( buffer, "r" ) as zip:
            for f in zip.namelist():
                name, _ = os.path.splitext( f )
                
                with zip.open( f, "r" ) as fp:
                    ret[ name ] = fp.read()
        
        return dict( ret )
    
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
