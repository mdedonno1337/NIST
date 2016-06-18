#!/usr/bin/env python
#  *-* coding: utf-8 *-*

from _collections import defaultdict
from collections import OrderedDict
from lib.misc.binary import binstring_to_int, int_to_binstring
from lib.misc.boxer import boxer
from lib.misc.deprecated import deprecated
from lib.misc.logger import debug
from lib.misc.stringIterator import stringIterator
from string import join, upper
import inspect
import os

from PIL import Image


################################################################################
#
#    Record type specifications
#
#        Abbreviation and full name of all Record type. 
#        Based on the publication of the NIST:
#
#            ANSI/NIST-ITL 1-2011:
#                UPDATE 2013 NIST Special Publication 500-290 Version 2 (2013) 
#
################################################################################
LABEL = {
    1: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'VER', 'Version number' ),
        3:   ( 'CNT', 'File content' ),
        4:   ( 'TOT', 'Type of transaction' ),
        5:   ( 'DAT', 'Date' ),
        6:   ( 'PRY', 'Priority' ),
        7:   ( 'DAI', 'Destination agency identifier' ),
        8:   ( 'ORI', 'Originating agency identifier' ),
        9:   ( 'TCN', 'Transaction control number' ),
        10:  ( 'TCR', 'Transaction control reference' ),
        11:  ( 'NSR', 'Native scanning resolution' ),
        12:  ( 'NTR', 'Nominal transmitting resolution' ),
        13:  ( 'DOM', 'Domain name' ),
        14:  ( 'GMT', 'Greenwich mean time' ),
        15:  ( 'DCS', 'Directory of character sets' )
    },
    
    2: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Image designation character' )
    },
    
    9: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Image designation character' ),
        3:   ( 'IMP', 'Impression type' ),
        4:   ( 'FMT', 'Minutiae format' ),
        5:   ( 'OFR', 'Originating fingerprint reading system' ),
        6:   ( 'FGP', 'Finger position' ),
        7:   ( 'FPC', 'Fingerprint pattern classification' ),
        8:   ( 'CRP', 'Core position' ),
        9:   ( 'DLT', 'Delta(s) position' ),
        10:  ( 'MIN', 'Number of minutiae' ),
        11:  ( 'RDG', 'Minutiae ridge count indicator' ),
        12:  ( 'MRC', 'Minutiae and ridge count data' ),
        128: ( 'HLL', 'M1 horizontal line length' ),
        129: ( 'VLL', 'M1 vertical line length' ),
        130: ( 'SLC', 'M1 scale units' ),
        131: ( 'HPS', 'M1 transmitted horizontal pixel scale' ),
        132: ( 'VPS', 'M1 transmitted vertical pixel scale' ),
        134: ( 'FGP', 'M1 friction ridge generalized position' ),
        999: ( 'DAT', 'Plantar image / DATA' )
    },
    
    13: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Image designation character' ),
        3:   ( 'IMP', 'Impression type' ),
        4:   ( 'SRC', 'Source agency / ORI' ),
        5:   ( 'LCD', 'Latent capture date' ),
        6:   ( 'HLL', 'Horizontal line length' ),
        7:   ( 'VLL', 'Vertical line length' ),
        8:   ( 'SLC', 'Scale units' ),
        9:   ( 'HPS', 'Scale units' ),
        10:  ( 'VPS', 'Scale units' ),
        11:  ( 'GCA', 'Compression algorithm' ),
        12:  ( 'BPX', 'Bits per pixel' ),
        13:  ( 'FGP', 'Finger / palm position' ),
        14:  ( 'SPD', 'Search Position Descriptors' ),
        15:  ( 'PPC', 'Print Position Coordinates' ),
        16:  ( 'SHPS', 'Scanned horizontal pixel scale' ),
        17:  ( 'SVPS', 'Scanned vertical pixel scale' ),
        20:  ( 'COM', 'Comment' ),
        24:  ( 'LQM', 'Latent quality metric' ),
        999: ( 'DAT', 'Image data' )
    }
}

################################################################################
#
#    Special delimiters
#
################################################################################

FS = chr( 28 )
GS = chr( 29 )
RS = chr( 30 )
US = chr( 31 )
CO = ':'
DO = '.'

################################################################################
# 
#    Exceptions
# 
################################################################################

class needIDC( BaseException ):
    pass

class intIDC( BaseException ):
    pass

class nonexistingIDC( BaseException ):
    pass

class minutiaeFormatNotSupported( BaseException ):
    pass

class notImplemented( BaseException ):
    pass

################################################################################
# 
#    NIST object class
# 
################################################################################

class NIST( object ):
    def __init__( self ):
        """
            Initialization of the NIST Object.
        """
        debug.info( "initialization of the NIST object" )
        
        self.filename = None
        self.data = defaultdict( dict )
        
        self.idcInOrder = []
        self.idcByNType = defaultdict( list )
        self.ntypeInOrder = []
        self.nbLogicalRecords = 0
        
        return
    
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
        if type( p ) == str:
            self.read( p )
        elif isinstance( p, NIST ):
            attributes = inspect.getmembers( p, lambda a:not( inspect.isroutine( a ) ) )
            for name, value in [a for a in attributes if not( a[0].startswith( '__' ) and a[0].endswith( '__' ) )]:
                super( NIST, self ).__setattr__( name, value )
    
    def load( self, data ):
        """
            Load from the data passed in parameter, and populate all internal dictionaries.
        """
        debug.info( "Loading object" )
        
        records = data.split( FS )
        
        #    NIST Type01
        debug.debug( "Type-01 parsing", 1 )
        
        t01 = records[0].split( GS )
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
            
            if ntype in [ 2, 9, 13 ]:
                current_type = data.split( FS )
                
                tx = current_type[0].split( GS )
                
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
                        data = data[ end: ]
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
                    1: LEN,
                    2: IDC,
                    3: IMP,
                    4: FGP,
                    5: ISR,
                    6: HLL,
                    7: VLL,
                    8: GCA,
                    999:DAT
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
            
        return
    
    def process_fileContent( self, data ):
        """
            Function to process the 1.003 field passed in parameter.
        """
        data = map( lambda x: map( int, x.split( US ) ), data.split( RS ) )
        
        self.nbLogicalRecords = data[0][1]
        
        for ntype, idc in data[ 1: ]:
            self.idcInOrder.append( ( ntype, idc ) )
            self.idcByNType[ ntype ].append( idc )
            self.ntypeInOrder.append( ntype )
        
        self.ntypeInOrder = sorted( self.ntypeInOrder )
    
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
        
        s = ""
        for t in sorted( d.keys() ):
            lab = get_label( ntype, t, fullname )
            header = "%02d.%03d %s" % ( ntype, t, lab )
            
            if t == 999:
                field = bindump( d[ t ] )
            else:
                field = d[ t ]
            
            debug.debug( "%s: %s" % ( header, field ), 2 )
            s = s + leveler( "%s: %s\n" % ( header, field ), 1 )
        
        return s
    
    def dump( self, fullname = False ):
        """
            Return a readable version of the NIST object. Printable on screen.
        """
        debug.info( "Dumping NIST" )
        
        s = ""
        
        for ntype in self.get_ntype():
            debug.debug( "NIST Type-%02d" % ntype, 1 )
            
            if ntype == 1:
                s += "NIST Type-%02d\n" % ntype
                s += self.dump_record( ntype, 0, fullname ) 
            else:
                for idc in self.get_idc( ntype ):
                    s += "NIST Type-%02d (IDC %d)\n" % ( ntype, idc )
                    s += self.dump_record( ntype, idc, fullname )
        
        return s
    
    def dumpbin( self ):
        """
            Return a binary dump of the NIST object. Writable in a file ("wb" mode).
        """
        debug.info( "Dumping NIST in binary" )
        
        self.clean()
        self.patch_to_standard()
        
        outnist = ""
        
        for ntype in self.get_ntype():
            for idc in self.get_idc( ntype ):
                if ntype == 4:
                    self.reset_binary_length( ntype, idc )
                    
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 1 ] ), 4 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 2 ] ), 1 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 3 ] ), 1 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 4 ] ), 1 * 8 )
                    outnist += ( chr( 0xFF ) * 5 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 5 ] ), 1 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 6 ] ), 2 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 7 ] ), 2 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 8 ] ), 1 * 8 )
                    outnist += self.data[ ntype ][ idc ][ 999 ]
                else:
                    self.reset_alpha_length( ntype, idc )
                    
                    od = OrderedDict( sorted( self.data[ ntype ][ idc ].items() ) )
                    outnist += join( [ tagger( ntype, tagid ) + value for tagid, value in od.iteritems() ], GS ) + FS
        
        return outnist
    
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
        
        for ntype in self.get_ntype():
            for idc in self.data[ ntype ].keys():
                for tagid in self.data[ ntype ][ idc ].keys():
                    value = self.get_field( "%d.%03d" % ( ntype, tagid ), idc )
                    if value == "" or value == None:
                        debug.debug( "Field %02d.%03d IDC %d deleted" % ( ntype, tagid, idc ), 2 )
                        del( self.data[ ntype ][ idc ][ tagid ] )
    
    def patch_to_standard( self ):
        """
            Check some requirements for the NIST file. Fields checked:
                1.002
                1.011
                1.012
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
        
        #    Type-09
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
                debug.debug( "minutiae are formatted in vendor-specific or M1- 378 terms" )
                self.set_field( "9.004", "U", idc )
        
        return
    
    def reset_alpha_length( self, ntype, idc = 0 ):
        """
            Recalculate the LEN field of the ntype passed in parameter.
            Only for ASCII ntype.
        """
        debug.info( "Resetting the length of Type-%02d" % ntype )
        
        self.set_field( "%d.001" % ntype, "%08d" % 0, idc )
        
        # %d.%03d:<data><GS>
        lentag = len( "%d" % ntype ) + 6
        
        recordsize = 0
        for t in self.data[ ntype ][ idc ].keys():
            recordsize += len( self.data[ ntype ][ idc ][ t ] ) + lentag
        
        diff = 8 - len( str( recordsize ) )
        recordsize -= diff
        
        self.set_field( "%d.001" % ntype, "%d" % recordsize, idc )
        
        return
    
    def reset_binary_length( self, ntype, idc = 0 ):
        """
            Recalculate the LEN field of the ntype passed in parameter.
            Only for binary ntype.
        """
        debug.info( "Resetting the length of Type-%02d" % ntype )
        
        if ntype == 4:
            recordsize = 18
            
            if self.data[ ntype ][ idc ].has_key( 999 ):
                recordsize += len( self.data[ ntype ][ idc ][999] )
                
        self.set_field( "%d.001" % ntype, "%d" % recordsize, idc )
    
    ############################################################################
    # 
    #    Minutiae functions
    # 
    ############################################################################
    
    def get_minutiae( self, format = "ixytdq", idc = -1 ):
        """
            Get the minutiae information from the field 9.012.
            
            The parameter 'format' allow to select the data to extract:
            
                i: Index number
                x: X coordinate
                y: Y coordinate
                t: Angle theta
                d: Type designation
                q: Quality
        """
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
                            tmp.append( int( xyt[0:4] ) / 100.0 )
                        
                        if c == "y":
                            tmp.append( int( xyt[4:8] ) / 100.0 )
                        
                        if c == "t":
                            tmp.append( int( xyt[8:11] ) )
                        
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
            raise nonexistingIDC
        
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
    
################################################################################
#
#    Generic functions
#
################################################################################

#    Grayscale Compression Algorithm
GCA = {
    'NONE': "RAW",
    '0': "RAW",
    '1': "WSQ",
    '2': "JPEGB",
    '3': "JPEGL",
    '4': "JP2",
    '5': "JP2L",
    '6': "PNG"
}

def decode_gca( code ):
    """
        Function to decode the 'Grayscale Compression Algorithm' value passed in
        parameter.
        
        >>> decode_gca( 'NONE' )
        'RAW'
    """
    return GCA[ str( code ) ]

#    Binary print
def bindump( data ):
    """
        Return the first and last 4 bytes of a binary data.
        
        >>> bindump( chr(255) * 250000 )
        'ffffffff ... ffffffff (250000 bytes)'
        
    """
    return "%02x%02x%02x%02x ... %02x%02x%02x%02x (%d bytes)" % ( 
        ord( data[0] ), ord( data[1] ), ord( data[2] ), ord( data[3] ),
        ord( data[-4] ), ord( data[-3] ), ord( data[-2] ), ord( data[-1] ), len( data )
    )

#    Field split
def fieldSplitter( data ):
    """
        Split the input data in a ( tag, ntype, tagid, value ) tuple.
        
        >>> fieldSplitter( "1.002:0501" )
        ('1.002', 1, 2, '0501')
        
    """
    tag, value = data.split( CO )
    ntype, tagid = tag.split( DO )
    ntype = int( ntype )
    tagid = int( tagid )
    
    return tag, ntype, tagid, value

#    Get label name
def get_label( ntype, tagid, fullname = False ):
    """
        Return the name of a specific field.
        
        >>> get_label( 1, 2 )
        'VER'
    """
    index = int( fullname )
    
    try:
        return LABEL[ ntype ][ tagid ][ index ]
    except:
        if not fullname:
            return "   "
        else:
            return ""

#    Alignement function
def leveler( msg, level = 1 ):
    """
        Return an indented string.
        
        >>> leveler( "1.002" )
        '    1.002'
    """
    return "    " * level + msg

#    Tag function
def tagger( ntype, tagid ):
    """
        Return the tag value from a ntype and tag value in parameter.
        
        >>> tagger( 1, 2 )
        '1.002:'
        
    """
    return "%d.%03d:" % ( ntype, tagid )

def tagSplitter( tag ):
    """
        Split a tag in a list of [ ntype, tagid ].
        
        >>> tagSplitter( "1.002" )
        [1, 2]
    """
    return map( int, tag.split( DO ) )

#    Field 9.012 to list (and reverse)
def lstTo012field( lst ):
    """
        Function to convert a minutiae from the minutiae-table to a 9.012 sub-field.
    """
    id, x, y, theta, quality, t = lst
    
    return join( 
        [
            id,
            "%04d%04d%03d" % ( round( float( x ) * 100 ), round( float( y ) * 100 ), theta ),
            quality,
            t
        ],
        US
    )

def lstTo012( lst ):
    """
        Convert the entire minutiae-table to the 9.012 field format.
    """
    lst = map( lstTo012field, lst )
    lst = join( lst, RS )
     
    return lst

################################################################################
# 
#    Image processing functions
# 
################################################################################

def RAWToPIL( raw, size = ( 500, 500 ) ):
    return Image.frombytes( 'L', size, raw )

def PILToRAW( pil ):
    return pil.convert( 'L' ).tobytes()

################################################################################
#
#    Main
#
################################################################################

if __name__ == "__main__":
    import doctest
    doctest.testmod()
