#!/usr/bin/python
# -*- coding: UTF-8 -*-

from future.builtins import super

import base64
import os
import xmltodict
import zipfile

from _collections import defaultdict
from cStringIO import StringIO

from MDmisc.ewarning import nowarnings

from ..fingerprint import NISTf
from ..fingerprint.functions import AnnotationList, Minutia
from ..traditional.exceptions import notImplemented
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
    
    def get_minutiae( self, format = None, idc = -1 ):
        """
            Overload of the NISTf.get_minutiae() function to extract the
            information from the JAR stored in the 9.184 field. The minutiae
            coordinates are converted in the correct format (mm in this case),
            and stored in an AnnoationList object. All functions based on this
            function should work normaly.
            
            .. see:: :func:`NIST.fingerprint.NISTf.get_minutiae()`
        """
        try:
            return super().get_minutiae( format = format, idc = idc )
        
        except AttributeError:
            if type( format ) == int:
                idc, format = format, self.minutiaeformat
                
            data = self.get_jar( idc )[ 'imageenh.2' ]
            
            data = xmltodict.parse( data )
            
            try:
                ops = data[ 'enhancementHistory' ][ 'enhancements' ][ 'enhancementOperation' ]
            
            except TypeError:
                return None
            
            else:
                if type( ops ) != list:
                    ops = [ ops ]
                
                with nowarnings( UnicodeWarning ):
                    minutiae_ops = sorted( 
                        ops,
                        key = lambda k: k.items()[ 0 ][ 1 ][ 'timestamp' ],
                        reverse = False
                    )
                
                corr = {
                    'autoEncode': ( 'newMinutiaSet', ),
                    'addMinutia': ( 'addedMinutia', ),
                    'moveMinutia': ( 'movedFromMinutia', 'movedToMinutia', ),
                    'rotateMinutia': ( 'rotatedFromMinutia', 'rotatedToMinutia', ),
                    'deleteMinutia': ( 'deletedMinutia', )
                }
                
                lst = AnnotationList()
                
                def MorphoXML2Annotation( data ):
                    return Minutia( 
                        [ int( data[ k ] ) for k in [ '@x', '@y', '@angle', '@minutiaType', '@confidence' ] ],
                        format = "xytdq"
                    )
                
                for d in minutiae_ops:
                    for op, value in d.items():
                        for action in corr[ op ]:
                            if action == "newMinutiaSet":
                                for key, v in value[ action ].iteritems():
                                    for vv in v:
                                        m = MorphoXML2Annotation( vv )
                                        m.source = "auto"
                                        lst.append( m )
                                
                            elif action in [ "deletedMinutia", "movedFromMinutia", "rotatedFromMinutia" ]:
                                m = MorphoXML2Annotation( value[ action ] )
                                lst.remove( m )
                            
                            elif action in [ "addedMinutia", "movedToMinutia", "rotatedToMinutia" ]:
                                m = MorphoXML2Annotation( value[ action ] )
                                m.source = "expert"
                                lst.append( m )
                            
                            else:
                                raise notImplemented
                
                res = self.get_resolution( idc )
                height = self.get_height( idc )
                
                lst2 = AnnotationList()
                for m in lst:
                    m2 = Minutia( 
                        [
                            m.x * 25.4 / res,
                            ( height - m.y ) * 25.4 / res,
                            ( m.t + 180 ) % 360,
                            m.d,
                            m.q
                        ],
                        format = "xytdq"
                    )
                    m2.source = m.source
                    lst2.append( m2 )
                
                return lst2
        
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
