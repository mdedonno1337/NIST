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
from ..fingerprint.functions import AnnotationList, Minutia, Delta, Core
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
    
    def export_cfv( self, file, idc = -1 ):
        """
            Export the CFV content to a file on disk.
            
            :param file: File to export to.
            :type file: string
            
            :param idc: IDC value.
            :type idc: int
        """
        with open( file, "wb+" ) as fp:
            fp.write( self.get_cfv( idc ) )
    
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
            if isinstance( format, int ):
                idc, format = format, self.minutiaeformat
            
            return self.process_imageenh( idc )[ 'minutiae' ].get( format )
    
    def get_delta( self, idc = -1 ):
        try:
            return self.process_imageenh( idc )[ 'delta' ]
        except:
            return None
    
    def process_imageenh( self, idc = -1 ):
        """
            Function to process the imgageenh.2 content stored in the jar field.
            This function replays the actions done by the user. The result is
            the final annotation as seen in the MBIS interface.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Dictionnary of the processed data.
            :rtype: python dict
        """
        data = self.get_jar( idc )[ 'imageenh.2' ]
        
        data = xmltodict.parse( data )
        
        try:
            ops = data[ 'enhancementHistory' ][ 'enhancements' ][ 'enhancementOperation' ]
        
        except TypeError:
            return None
        
        else:
            if not isinstance( ops, list ):
                ops = [ ops ]
            
            with nowarnings( UnicodeWarning ):
                minutiae_ops = sorted( 
                    ops,
                    key = lambda k: k.items()[ 0 ][ 1 ][ 'timestamp' ],
                    reverse = False
                )
            
            corr = {
                'autoEncode':    ( 'newMinutiaSet', ),
                'addMinutia':    ( 'addedMinutia', ),
                'moveMinutia':   ( 'movedFromMinutia', 'movedToMinutia', ),
                'rotateMinutia': ( 'rotatedFromMinutia', 'rotatedToMinutia', ),
                'deleteMinutia': ( 'deletedMinutia', ),
                
                'addDelta':      ( 'addedDelta', ),
                'moveDelta':     ( 'movedFromDelta', 'movedToDelta', ),
                'rotateDelta':   ( 'rotatedFromDelta', 'rotatedToDelta' ),
                'deleteDelta':   ( 'deletedDelta', ),
                
                'addCore':       ( 'addedCore', ),
                'moveCore':      ( 'movedFromCore', 'movedToCore' ),
                'rotateCore':    ( 'rotatedFromCore', 'rotatedToCore' ),
                'deleteCore':    ( 'deletedCore', )
            }
            
            minutiae_list = AnnotationList()
            deltas_list = AnnotationList()
            cores_list = AnnotationList()
            
            def MorphoXML2Minutia( data ):
                x = int( data[ '@x' ] )
                y = int( data[ '@y' ] )
                t = int( data[ '@angle' ] )
                if int( data[ '@minutiaType' ] ) == 1:
                    d = 'A'
                elif int( data[ '@minutiaType' ] ) == 2:
                    d = 'B'
                else:
                    d = 'D'
                    
                q = int( data[ '@confidence' ] )
                
                return Minutia( 
                    [ x, y, t, d, q ],
                    format = "xytdq"
                )
            
            def MorphoXML2Delta( data ):
                return Delta( 
                    [ int( data[ k ] ) for k in [ '@x', '@y', '@angle1', '@angle2', '@angle3' ] ],
                    format = "xyabc"
                )
            
            def MorphoXML2Core( data ):
                return Core( 
                    [ int( data[ k ] ) for k in [ '@x', '@y', '@angle', '@confidence' ] ],
                    format = "xytq"
                )
            
            for d in minutiae_ops:
                for op, value in d.items():
                    for action in corr[ op ]:
                        # Minutiae processing
                        if action == "newMinutiaSet":
                            for key, v in value[ action ].iteritems():
                                for vv in v:
                                    m = MorphoXML2Minutia( vv )
                                    m.source = "auto"
                                    minutiae_list.append( m )
                        
                        elif action in [ "addedMinutia", "movedToMinutia", "rotatedToMinutia" ]:
                            m = MorphoXML2Minutia( value[ action ] )
                            m.source = "expert"
                            minutiae_list.append( m )
                            
                        elif action in [ "deletedMinutia", "movedFromMinutia", "rotatedFromMinutia" ]:
                            m = MorphoXML2Minutia( value[ action ] )
                            minutiae_list.remove( m )
                        
                        # Delta processing
                        elif action in [ "addedDelta", "movedToDelta", "rotatedToDelta" ]:
                            m = MorphoXML2Delta( value[ action ] )
                            m.source = "expert"
                            deltas_list.append( m )
                        
                        elif action in [ "deletedDelta", "movedFromDelta", "rotatedFromDelta" ]:
                            m = MorphoXML2Delta( value[ action ] )
                            deltas_list.remove( m )
                        
                        # Core processing
                        elif action in [ "addedCore", "movedToCore", "rotatedToCore" ]:
                            m = MorphoXML2Core( value[ action ] )
                            m.source = "expert"
                            cores_list.append( m )
                        
                        elif action in [ "deletedCore", "movedFromCore", "rotatedFromCore" ]:
                            m = MorphoXML2Core( value[ action ] )
                            cores_list.remove( m )
                        
                        # Raise exception if not implemented
                        else:
                            raise notImplemented
            
            res = self.get_resolution( idc )
            height = self.get_height( idc )
            
            minutiae_return_list = AnnotationList()
            for m in minutiae_list:
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
                minutiae_return_list.append( m2 )
            
            deltas_return_list = AnnotationList()
            for m in deltas_list:
                m2 = Delta( 
                    [
                        m.x * 25.4 / res,
                        ( height - m.y ) * 25.4 / res,
                        m.a,
                        m.b,
                        m.c
                    ],
                    format = "xyabc"
                )
                m2.source = m.source
                deltas_return_list.append( m2 )
            
            cores_return_list = AnnotationList()
            for m in cores_list:
                m2 = Core( 
                    [
                        m.x * 25.4 / res,
                        ( height - m.y ) * 25.4 / res,
                        m.t,
                        m.q
                    ],
                    format = "xytq"
                )
                m2.source = m.source
                cores_return_list.append( m2 )
            
            return {
                'minutiae': minutiae_return_list,
                'deltas':   deltas_return_list,
                'cores':    cores_return_list
            }
        
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
        if data != None:
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
        
        else:
            return None
    
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
