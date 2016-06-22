#!/usr/bin/python
# -*- coding: UTF-8 -*-

from _collections import defaultdict
from collections import OrderedDict
from string import join, upper
import inspect
import os
 
from lib.misc.binary import binstring_to_int, int_to_binstring
from lib.misc.boxer import boxer
from lib.misc.deprecated import deprecated
from lib.misc.logger import debug
from lib.misc.stringIterator import stringIterator

from .labels import LABEL
from .config import *
from .functions import *
from .exceptions import *

################################################################################
#
#    Python library for:
#
#            Data Format for the Interchange of Fingerprint, Facial
#                         & Other Biometric Information
#
#                  NIST Special Publication 500-290 Rev1 (2013)
#    
#    
#    The aim of the python library is to open, modify and write Biometric
#    Information files based on the standard proposed by the NIST (for short:
#    NIST format).
#    
#    The standard propose the following type of biometric data:
#    
#        Type-01 : Transaction information
#        Type-02 : User-defined descriptive text
#        Type-03 : (Deprecated)
#        Type-04 : High-resolution grayscale fingerprint image
#        Type-05 : (Deprecated)
#        Type-06 : (Deprecated)
#        Type-07 : User-defined image
#        Type-08 : Signature image
#        Type-09 : Minutiae data
#        Type-10 : Photographic body part imagery (including face and SMT)18
#        Type-11 : Forensic and investigatory voice data19
#        Type-12 : Forensic dental and oral data19
#        Type-13 : Variable-resolution latent friction ridge image
#        Type-14 : Variable-resolution fingerprint image
#        Type-15 : Variable-resolution palm print image
#        Type-16 : User-defined variable-resolution testing image
#        Type-17 : Iris image
#        Type-18 : DNA data
#        Type-19 : Variable-resolution plantar image
#        Type-20 : Source representation
#        Type-21 : Associated context
#        Type-22 : Non-photographic imagery19
#        Type-98 : Information assurance
#        Type-99 : CBEFF biometric data record
#
#        The Type-23 to Type-97 are reserved for future use.
# 
#        This library is (almost at 100%) compatible (read and write) with the
#        standard is used correctly (compatibility tested with "BioCTS for ANSI
#        /NIST-ITL v2") and the Sample Data provided by the NIST.
# 
#        Some functions are added to simplify some operation, especially
#        regarding the fingerprint processing (extraction of image, annotation
#        of minutiae on the image,...).
# 
# 
#                                         Marco De Donno
#                                         marco.dedonno@unil.ch
#                                         mdedonno1337@gmail.com
#                                        
#                                         School of Criminal Justice
#                                         University of Lausanne - Batochime
#                                         CH-1015 Lausanne-Dorigny
#                                         Switzerland
# 
#    Copyright (c) 2016 Marco De Donno
# 
################################################################################


################################################################################
# 
#    NIST object class
# 
################################################################################

class NIST( object ):
    def __init__( self, init = None ):
        """
            Initialization of the NIST Object.
            
            All biometric information are stored in the self.data recursive
            default dictionary object. The information is stored as following:
            
                self.data[ ntype ][ idc ][ tagid ]
            
            To get and set data, use the self.get_field() and self_set_field()
            functions.
        """
        debug.info( "Initialization of the NIST object" )
        
        self.filename = None
        self.data = defaultdict( dict )
        
        self.ntypeInOrder = []
        
        if init != None:
            self.load_auto( init )
        
    ############################################################################
    #
    #    Loading functions
    #
    ############################################################################
    
    @deprecated( "user the read() function instead" )
    def loadFromFile( self, infile ):
        return self.read( infile )
    
    def read( self, infile ):
        """
            Open the 'infile' file and transmit the data to the 'load' function.
        """
        debug.info( "Reading from file : %s" % infile )
        
        self.filename = infile
    
        with open( infile, "rb" ) as fp:
            data = fp.read()
        
        self.load( data )
    
    def load_auto( self, p ):
        """
            Function to detect and load automatically the 'p' value passed in
            parameter. The argument 'p' can be a string (URI to the file to
            load) or a NIST object (a copy will be done in the current object).
        """
        if type( p ) == str:
            self.read( p )
            
        elif isinstance( p, NIST ):
            # Get the list of all attributes stored in the NIST object.
            attributes = inspect.getmembers( p, lambda a: not( inspect.isroutine( a ) ) )
            
            # Copy all the values to the current NIST object. 
            for name, value in [ a for a in attributes if not( a[ 0 ].startswith( '__' ) and a[ 0 ].endswith( '__' ) ) ]:
                super( NIST, self ).__setattr__( name, value )
    
    def load( self, data ):
        """
            Load from the data passed in parameter, and populate all internal dictionaries.
        """
        debug.info( "Loading object" )
        
        records = data.split( FS )
        
        #    NIST Type01
        debug.debug( "Type-01 parsing", 1 )
        
        t01 = records[ 0 ].split( GS )
        record01 = {}
        
        for field in t01:
            tag, ntype, tagid, value = fieldSplitter( field )
            
            if tagid == 1:
                LEN = int( value )
            
            if tagid == 3:
                self.process_fileContent( value )
            
            debug.debug( "%d.%03d:\t%s" % ( ntype, tagid, value ), 2 )
            record01[ tagid ] = value
        
        self.data[ 1 ][ 0 ] = record01  # Store in IDC = 0 even if the standard implies no IDC for Type-01
        data = data[ LEN: ]
        
        #    NIST Type02 and after
        debug.debug( "Expected Types : %s" % ", ".join( map( str, self.ntypeInOrder ) ), 1 )
        
        for ntype in self.ntypeInOrder:
            debug.debug( "Type-%02d parsing" % ntype, 1 )
            LEN = 0
            
            if ntype in [ 2, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 98, 99 ]:
                current_type = data.split( FS )
                
                tx = current_type[ 0 ].split( GS )
                
                recordx = {}
                offset = 0
                idc = -1
                
                for t in tx:
                    try:
                        tag, ntype, tagid, value = fieldSplitter( t )
                    except:
                        tagid = 999
                    
                    if tagid == 1:
                        LEN = int( value )
                    elif tagid == 2:
                        idc = int( value )
                    elif tagid == 999:
                        if ntype == 9:
                            end = LEN
                        else:
                            end = LEN - 1
                        
                        offset += len( tag ) + 1
                        
                        value = data[ offset : end ]
                        debug.debug( "%d.%03d:\t%s" % ( ntype, tagid, bindump( value ) ), 2 )
                        recordx[ tagid ] = value
                        break
                        
                    debug.debug( "%d.%03d:\t%s" % ( ntype, tagid, value ), 2 )
                    recordx[ tagid ] = value
                    offset += len( t ) + 1
                    
                self.data[ ntype ][ idc ] = recordx
            
            elif ntype == 4:
                iter = stringIterator( data )
                
                LEN = binstring_to_int( iter.take( 4 ) )
                IDC = binstring_to_int( iter.take( 1 ) )
                IMP = binstring_to_int( iter.take( 1 ) )
                FGP = binstring_to_int( iter.take( 1 ) )
                iter.take( 5 )
                ISR = binstring_to_int( iter.take( 1 ) )
                HLL = binstring_to_int( iter.take( 2 ) )
                VLL = binstring_to_int( iter.take( 2 ) )
                GCA = binstring_to_int( iter.take( 1 ) )
                DAT = iter.take( LEN - 18 )
                
                LEN = str( LEN )
                IDC = str( IDC )
                IMP = str( IMP )
                FGP = str( FGP )
                ISR = str( ISR )
                HLL = str( HLL )
                VLL = str( VLL )
                GCA = str( GCA )
                
                debug.debug( "Parsing Type-04 IDC %s" % IDC, 2 )
                debug.debug( "LEN: %s" % LEN, 3 )
                debug.debug( "IDC: %s" % IDC, 3 )
                debug.debug( "IMP: %s" % IMP, 3 )
                debug.debug( "FGP: %s" % FGP, 3 )
                debug.debug( "ISR: %s" % ISR, 3 )
                debug.debug( "HLL: %s" % HLL, 3 )
                debug.debug( "VLL: %s" % VLL, 3 )
                debug.debug( "GCA: %s (%s)" % ( GCA, decode_gca( GCA ) ), 3 )
                debug.debug( "DAT: %s" % bindump( DAT ), 3 )
                
                nist04 = {
                    1:   LEN,
                    2:   IDC,
                    3:   IMP,
                    4:   FGP,
                    5:   ISR,
                    6:   HLL,
                    7:   VLL,
                    8:   GCA,
                    999: DAT
                }
                
                IDC = int( IDC )
                self.data[ ntype ][ IDC ] = nist04
                
                LEN = int( LEN )
            
            else:
                debug.critical( boxer( "Unknown Type-%02d" % ntype, "The Type-%02d is not supported. It will be skipped in the pasing process. Contact the developer for more information." % ntype ) )
                
                if data.startswith( str( ntype ) ):
                    _, _, _, LEN = fieldSplitter( data[ 0 : data.find( GS ) ] )
                    LEN = int( LEN )
                else:
                    LEN = binstring_to_int( data[ 0 : 4 ] )
            
            data = data[ LEN: ]
            
    def process_fileContent( self, data ):
        """
            Function to process the 1.003 field passed in parameter.
        """
        data = map( lambda x: map( int, x.split( US ) ), data.split( RS ) )
        
        self.nbLogicalRecords = data[ 0 ][ 1 ]
        
        for ntype, idc in data[ 1: ]:
            self.ntypeInOrder.append( ntype )
    
    ############################################################################
    # 
    #    Content delete
    # 
    ############################################################################
    
    def delete( self, ntype = None, idc = -1 ):
        """
            Function to delete a specific Type-'ntype', IDC or field.
            
            To delete the Type-09 record:
                n.delete( 9 )
            
            To delete the Type-09 IDC 0:
                n.delete( 9, 0 )
            
            To delete the field "9.012":
                n.delete( "9.012" )
            
            To delete the field "9.012" IDC 0:
                n.delete( "9.012", 0 )
            
        """
        if type( ntype ) == str:
            tag = ntype
            self.delete_tag( tag, idc )
        else:
            if idc < 0:
                self.delete_ntype( ntype )
            else:
                self.delete_idc( ntype, idc )
        
    def delete_ntype( self, ntype ):
        """
            Delete the 'ntype' record.
        """
        if self.data.has_key( ntype ):
            del( self.data[ ntype ] )
        else:
            raise ntypeNotFound
    
    def delete_idc( self, ntype, idc ):
        """
            Delete the specific IDC passed in parameter from 'ntype' record.
        """
        if self.data.has_key( ntype ) and self.data[ ntype ].has_key( idc ):
            del( self.data[ ntype ][ idc ] )
        else:
            raise idcNotFound
    
    def delete_tag( self, tag, idc = -1 ):
        """
            Delete the field 'tag' from the specific IDC.
        """
        ntype, tagid = tagSplitter( tag )
        
        idc = self.checkIDC( ntype, idc )
        
        if self.data.has_key( ntype ) and self.data[ ntype ].has_key( idc ):
            del( self.data[ ntype ][ idc ][ tagid ] )
        else:
            raise tagNotFound
    
    ############################################################################
    # 
    #    Dumping
    # 
    ############################################################################
    
    def dump_record( self, ntype, idc = 0, fullname = False ):
        """
            Dump a specific ntype - IDC record.
        """
        d = self.data[ ntype ][ idc ]
        
        ret = []
        for t in sorted( d.keys() ):
            lab = get_label( ntype, t, fullname )
            header = "%02d.%03d %s" % ( ntype, t, lab )
            
            if t == 999:
                field = bindump( d[ t ] )
            else:
                if ntype == 18 and t == 19:
                    field = bindump( d[ t ] )
                else:
                    field = d[ t ]
            
            debug.debug( "%s: %s" % ( header, field ), 2 )
            ret.append( leveler( "%s: %s\n" % ( header, field ), 1 ) )
        
        return "".join( ret )
    
    def dump( self, fullname = False ):
        """
            Return a readable version of the NIST object. Printable on screen.
        """
        debug.info( "Dumping NIST" )
        
        ret = []
        
        for ntype in self.get_ntype():
            debug.debug( "NIST Type-%02d" % ntype, 1 )
            
            for idc in self.get_idc( ntype ):
                ret.append( "NIST Type-%02d" % ntype )
                if ntype != 1:
                    ret.append( " (IDC %d)" % idc )
                ret.append( "\n" )
                ret.append( self.dump_record( ntype, idc, fullname ) )
        
        return "".join( ret )
    
    def dumpbin( self ):
        """
            Return a binary dump of the NIST object. Writable in a file ("wb" mode).
        """
        debug.info( "Dumping NIST in binary" )
        
        self.clean()
        self.patch_to_standard()
        
        outnist = []
        
        for ntype in self.get_ntype():
            for idc in self.get_idc( ntype ):
                if ntype == 4:
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 1 ] ), 4 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 2 ] ), 1 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 3 ] ), 1 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 4 ] ), 1 * 8 ) )
                    outnist.append( ( chr( 0xFF ) * 5 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 5 ] ), 1 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 6 ] ), 2 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 7 ] ), 2 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 8 ] ), 1 * 8 ) )
                    outnist.append( self.data[ ntype ][ idc ][ 999 ] )
                else:
                    od = OrderedDict( sorted( self.data[ ntype ][ idc ].items() ) )
                    outnist.append( join( [ tagger( ntype, tagid ) + value for tagid, value in od.iteritems() ], GS ) + FS )
        
        return "".join( outnist )
    
    @deprecated( "use the write() function instead" )
    def saveToFile( self, outfile ):
        return self.write( outfile )
    
    def write( self, outfile ):
        """
            Write the NIST object to a specific file.
        """
        debug.info( "Write the NIST object to '%s'" % outfile )
        
        if not os.path.isdir( os.path.dirname( os.path.realpath( outfile ) ) ):
            os.makedirs( os.path.dirname( os.path.realpath( outfile ) ) )
        
        with open( outfile, "wb+" ) as fp:
            fp.write( self.dumpbin() )
    
    ############################################################################
    # 
    #    Cleaning and resetting functions
    # 
    ############################################################################
    
    def clean( self ):
        """
            Function to clean all unused fields in the self.data variable.
        """
        debug.info( "Cleaning the NIST object" )
        
        #     Delete all empty fields.
        for ntype in self.get_ntype():
            for idc in self.data[ ntype ].keys():
                for tagid in self.data[ ntype ][ idc ].keys():
                    value = self.get_field( "%d.%03d" % ( ntype, tagid ), idc )
                    if value == "" or value == None:
                        debug.debug( "Field %02d.%03d IDC %d deleted" % ( ntype, tagid, idc ), 1 )
                        del( self.data[ ntype ][ idc ][ tagid ] )
        
        #    Recheck the content of the NIST object and udpate the 1.003 field
        content = []
        for ntype in self.get_ntype()[ 1: ]:
            for idc in self.get_idc( ntype ):
                debug.debug( "Type-%02d, IDC %d present" % ( ntype, idc ), 1 )
                content.append( "%s%s%s" % ( ntype, US, idc ) )
                
        content.insert( 0, "%s%s%s" % ( 1, US, len( content ) ) )
        self.set_field( "1.003", join( content, RS ) )
        
        #    Reset the length of each ntype record (n.001 fields)
        for ntype in self.get_ntype():
            for idc in self.get_idc( ntype ):
                if ntype == 4:
                    self.reset_binary_length( ntype, idc )
                else:
                    self.reset_alpha_length( ntype, idc )
        
    def patch_to_standard( self ):
        """
            Check some requirements for the NIST file. Fields checked:
                1.002
                1.011
                1.012
                4.005
                9.004
        """
        debug.info( "Patch some fields regaring the ANSI/NIST-ITL standard" )
        
        #    1.002 : Standard version:
        #        0300 : ANSI/NIST-ITL 1-2000
        #        0400 : ANSI/NIST-ITL 1-2007
        #        0500 : ANSI/NIST-ITL 1-2011
        #        0501 : ANSI/NIST-ITL 1-2011 Update: 2013 Traditional Encoding
        #        0502 : ANSI/NIST-ITL 1-2011 Update: 2015 Traditional Encoding
        debug.debug( "set version to 0501 (ANSI/NIST-ITL 1-2011 Update: 2013 Traditional Encoding)", 1 )
        self.set_field( "1.002", "0501" )
        
        #    1.011 and 1.012
        #        For transactions that do not contain Type-3 through Type-7
        #        fingerprint image records, this field shall be set to "00.00")
        if not 4 in self.get_ntype():
            debug.debug( "Fields 1.011 and 1.012 patched: no Type04 in this NIST file", 1 )
            self.set_field( "1.011", "00.00" )
            self.set_field( "1.012", "00.00" )
        
        #    Type-04
        if 4 in self.get_ntype():
            for idc in self.get_idc( 4 ):
                #    4.005
                #        The minimum scanning resolution was defined in ANSI/NIST-
                #        ITL 1-2007 as "19.69 ppmm plus or minus 0.20 ppmm (500 ppi
                #        plus or minus 5 ppi)." Therefore, if the image scanning
                #        resolution corresponds to the Appendix F certification
                #        level (See Table 14 Class resolution with defined
                #        tolerance), a 0 shall be entered in this field.
                #        
                #        If the resolution of the Type-04 is in 500DPI +- 1%, then
                #        the 4.005 then field is set to 0, otherwise 1.
                debug.debug( "Set the conformity with the Appendix F certification level for Type-04 image", 1 )
                if 19.49 < float( self.get_field( "1.011" ) ) < 19.89:
                    self.set_field( "4.005", "0", idc )
                else:
                    self.set_field( "4.005", "1", idc )
        
        #    Type-09
        if 9 in self.get_ntype():
            for idc in self.get_idc( 9 ):
                #    9.004
                #        This field shall contain an "S" to indicate that the
                #        minutiae are formatted as specified by the standard Type-9
                #        logical record field descriptions. This field shall contain
                #        a "U" to indicate that the minutiae are formatted in
                #        vendor-specific or M1- 378 terms
                if any( x in [ 5, 6, 7, 8, 9, 10, 11, 12 ] for x in self.data[ 9 ][ idc ].keys() ):
                    debug.debug( "minutiae are formatted as specified by the standard Type-9 logical record field descriptions", 1 )
                    self.set_field( "9.004", "S", idc )
                else:
                    debug.debug( "minutiae are formatted in vendor-specific or M1-378 terms", 1 )
                    self.set_field( "9.004", "U", idc )
        
    def reset_alpha_length( self, ntype, idc = 0 ):
        """
            Recalculate the LEN field of the ntype passed in parameter.
            Only for ASCII ntype.
        """
        debug.debug( "Resetting the length of Type-%02d" % ntype )
        
        self.set_field( "%d.001" % ntype, "%08d" % 0, idc )
        
        # %d.%03d:<data><GS>
        lentag = len( "%d" % ntype ) + 6
        
        recordsize = 0
        for t in self.data[ ntype ][ idc ].keys():
            recordsize += len( self.data[ ntype ][ idc ][ t ] ) + lentag
        
        diff = 8 - len( str( recordsize ) )
        recordsize -= diff
        
        self.set_field( "%d.001" % ntype, "%d" % recordsize, idc )
        
    def reset_binary_length( self, ntype, idc = 0 ):
        """
            Recalculate the LEN field of the ntype passed in parameter.
            Only for binary ntype.
        """
        debug.debug( "Resetting the length of Type-%02d" % ntype )
        
        if ntype == 4:
            recordsize = 18
            
            if self.data[ ntype ][ idc ].has_key( 999 ):
                recordsize += len( self.data[ ntype ][ idc ][ 999 ] )
                
        self.set_field( "%d.001" % ntype, "%d" % recordsize, idc )
    
    ############################################################################
    # 
    #    Minutiae functions
    # 
    ############################################################################
    
    def get_minutiae( self, format = "ixytdq", idc = -1 ):
        """
            Get the minutiae information from the field 9.012 for the IDC passed
            in argument.
            
            The parameter 'format' allow to select the data to extract:
            
                i: Index number
                x: X coordinate
                y: Y coordinate
                t: Angle theta
                d: Type designation
                q: Quality
            
            The 'format' parameter is optional. The IDC value can be passed in
            parameter even without format. The default format ('ixytdq') will be
            used.
        """
        # If the 'format' value is an int, then the function is called without
        # the 'format' argument, but the IDC is passed instead.
        if type( format ) == int:
            idc = format
            format = "ixytdq"
        
        # Get the minutiae string, without the final <FS> character.                
        minutiae = self.get_field( "9.012", idc )[ :-1 ]
        
        if minutiae == None:
            return []
        else:
            ret = []

            for m in minutiae.split( RS ):
                try:
                    id, xyt, d, q = m.split( US )
                    
                    tmp = []
                    
                    for c in format:
                        if c == "i":
                            tmp.append( id )
                        
                        if c == "x":
                            tmp.append( int( xyt[ 0:4 ] ) / 100.0 )
                        
                        if c == "y":
                            tmp.append( int( xyt[ 4:8 ] ) / 100.0 )
                        
                        if c == "t":
                            tmp.append( int( xyt[ 8:11 ] ) )
                        
                        if c == "d":
                            tmp.append( d )
                        
                        if c == "q":
                            tmp.append( q )
        
                    ret.append( tmp )
                except:
                    raise minutiaeFormatNotSupported
                
            return ret
    
    @deprecated( "use the get_minutiae( 'xy' ) instead" )
    def get_minutiaeXY( self, idc = -1 ):
        return self.get_minutiae( "xy", idc )
    
    @deprecated( "use the get_minutiae( 'xyt' ) instead" )
    def get_minutiaeXYT( self, idc = -1 ):
        return self.get_minutiae( "xyt", idc )
    
    @deprecated( "use the get_minutiae( 'xytq' ) instead" )
    def get_minutiaeXYTQ( self, idc = -1 ):
        return self.get_minutiae( "xytq", idc )
    
    def get_center( self, idc = -1 ):
        """
            Process and return the center coordinate.
        """
        c = self.get_field( "9.008", idc )

        if c == None:
            return None
        else:
            x = int( c[ 0:4 ] ) / 100.0
            y = int( c[ 4:8 ] ) / 100.0

            return ( x, y )
    
    def set_minutiae( self, data ):
        """
            Set the minutiae in the field 9.012.
            The 'data' parameter can be a minutiae-table (id, x, y, theta, quality, type) or
            the final string.
        """
        if type( data ) == list:
            data = lstTo012( data )
            
        self.set_field( "9.012", data )
        
        minnum = len( data.split( RS ) ) - 1
        self.set_field( "9.010", minnum )
        
        return minnum
    
    ############################################################################
    # 
    #    Image processing
    # 
    ############################################################################
    
    #    Size
    def get_size( self, idc = -1 ):
        """
            Get a python-tuple representing the size of the image.
        """
        return ( self.get_width( idc ), self.get_height( idc ) )
    
    def get_width( self, idc = -1 ):
        """
            Return the width of the Type-13 image.
        """
        return int( self.get_field( "13.006", idc ) )
        
    def get_height( self, idc = -1 ):
        """
            Return the height of the Type-13 image.
        """
        return int( self.get_field( "13.007", idc ) )
    
    #    Resolution
    def get_resolution( self, idc = -1 ):
        """
            Return the (horizontal) resolution of the Type-13 image in dpi.
        """
        return self.get_horizontalResolution( idc )

    def get_horizontalResolution( self, idc = -1 ):
        """
            Return the horizontal resolution of the Type-13 image.
            If the resolution is stored in px/cm, the conversion to dpi is done.
        """
        if self.get_field( "13.008", idc ) == '1':
            return int( self.get_field( "13.009" ) )
        elif self.get_field( "13.008", idc ) == '2':
            return int( self.get_field( "13.009" ) / 10.0 * 25.4 )

    def get_verticalResolution( self, idc = -1 ):
        """
            Return the vertical resolution of the Type-13 image.
            If the resolution is stored in px/cm, the conversion to dpi is done.
        """
        if self.get_field( "13.008", idc ) == '1':
            return int( self.get_field( "13.010" ) )
        elif self.get_field( "13.008", idc ) == '2':
            return int( self.get_field( "13.010" ) / 10.0 * 25.4 )
    
    def set_resolution( self, res, idc = -1 ):
        """
            Set the resolution in dpi.
        """
        res = int( res )
        
        self.set_horizontalResolution( res, idc )
        self.set_verticalResolution( res, idc )
        
        self.set_field( "13.008", "1", idc )

    def set_horizontalResolution( self, value, idc = -1 ):
        """
            Set the horizontal resolution.
        """
        self.set_field( "13.009", value, idc )
        
    def set_verticalResolution( self, value, idc = -1 ):
        """
            Set the vertical resolution.
        """
        self.set_field( "13.010", value, idc )
        
    #    Compression
    def get_compression( self, idc = -1 ):
        """
            Get the compression used in the latent image.
        """
        gca = self.get_field( "13.011", idc )
        return decode_gca( gca )
    
    #    Image
    @deprecated( "use the get_image( 'RAW', idc ) function instead" )
    def get_RAW( self, idc = -1 ):
        return self.get_image( "RAW", idc )
    
    @deprecated( "use the get_image( 'PIL', idc ) function instead" )
    def get_PIL( self, idc = -1 ):
        return self.get_image( "PIL", idc )
    
    def get_image( self, format = 'RAW', idc = -1 ):
        """
            Return the image in the format passed in parameter (RAW or PIL)
        """
        format = upper( format )
        
        raw = self.get_field( "13.999", idc )
        
        if format == "RAW":
            return raw
        elif format == "PIL":
            return Image.frombytes( "L", self.get_size( idc ), raw )
        else:
            raise NotImplemented
    
    def set_image( self, data, idc = -1 ):
        """
            Detect the type of image passed in parameter and store it in the
            13.999 field.
        """
        if type( data ) == str:
            self.set_field( "13.999", data, idc )
            
        elif isinstance( data, Image.Image ):
            self.set_RAW( PILToRAW( data ) )
            self.set_size( data.size )
            
            try:
                self.set_resolution( data.info[ 'dpi' ][ 0 ] )
            except:
                self.set_resolution( 500 )
    
    ############################################################################
    # 
    #    Access to the fields value
    # 
    ############################################################################
    
    def get_field( self, tag, idc = -1 ):
        """
            Get the content of a specific tag in the NIST object.
        """
        ntype, tagid = tagSplitter( tag )
        
        idc = self.checkIDC( ntype, idc )
    
        try:
            return self.data[ ntype ][ idc ][ tagid ]
        except:
            return None
    
    def set_field( self, tag, value, idc = -1 ):
        """
            Set the value of a specific tag in the NIST object.
        """
        ntype, tagid = tagSplitter( tag )
        
        idc = self.checkIDC( ntype, idc )
        
        if type( value ) != str:
            value = str( value )
        
        self.data[ ntype ][ idc ][ tagid ] = value
    
    def get_fields( self, tags, idc = -1 ):
        """
            Get the content of multiples fields at the same time.
        """
        return [ self.get_field( tag, idc ) for tag in tags ]
    
    def set_fields( self, fields, value, idc = -1 ):
        """
            Set the value of multiples fields to the same value.
        """
        for field in fields:
            self.set_field( field, value, idc )
    
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
    
    ############################################################################
    # 
    #    Generic functions
    # 
    ############################################################################
    
    def get_ntype( self ):
        """
            Return all ntype presents in the NIST object.
        """
        return sorted( self.data.keys() )
    
    def get_idc( self, ntype ):
        """
            Return all IDC for a specific ntype.
        """
        return sorted( self.data[ ntype ].keys() )
    
    def checkIDC( self, ntype, idc ):
        """
            Check if the IDC passed in parameter exists for the specific ntype,
            and if the value is numeric. If the IDC is negative, then the value
            is searched in the ntype field and returned only if the value is
            unique; if multiple IDC are stored for the specific ntype, an
            exception is raised.
        """
        if idc < 0:
            idc = self.get_idc( ntype )
            
            if len( idc ) > 1:
                raise needIDC
            else:
                idc = idc[ 0 ]
            
        if type( idc ) != int:
            raise intIDC
        
        if not idc in self.get_idc( ntype ):
            raise idcNotFound
        
        return idc
    
    def __str__( self ):
        """
            Return the printable version of the NIST object.
        """
        return self.dump()
    
    def __repr__( self ):
        """
            Return unambiguous description.
        """
        return "NIST object, " + ", ".join( [ "Type-%02d" % x for x in self.get_ntype() if x > 2 ] )
