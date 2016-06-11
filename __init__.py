#!/usr/bin/env python

from _collections import defaultdict
import logging


class MyLogger:
    def __init__( self ):
        self.mode = logging.CRITICAL
        self.format = "%(asctime)s -- %(levelname)s -- %(message)s"
        logging.basicConfig( level = self.mode, format = self.format )
        self.log = logging.getLogger( "NIST library" )
    
    def setMode( self, mode ):
        mode = mode.lower()
        
        if mode == "debug":
            self.mode = logging.DEBUG
        elif mode == "info":
            self.mode = logging.INFO
        elif mode == "warning":
            self.mode = logging.WARNING
        elif mode == "error":
            self.mode = logging.ERROR
        elif mode == "critical":
            self.mode = logging.CRITICAL
        else:
            raise Exception( "debug level unknown : %s" % mode )
        
        self.log.setLevel( self.mode )
    
    def leveler( self, msg, level ):
        return "\t" * level + msg
    
    def debug( self, msg, level = 0 ):
        msg = self.leveler( msg, level )
        self.log.debug( msg )
    
    def info( self, msg, level = 0 ):
        msg = self.leveler( msg, level )
        self.log.info( msg )
    
    def warning( self, msg, level = 0 ):
        msg = self.leveler( msg, level )
        self.log.warning( msg )
        
    def error( self, msg, level = 0 ):
        msg = self.leveler( msg, level )
        self.log.error( msg )
    
    def critical( self, msg, level = 0 ):
        msg = self.leveler( msg, level )
        self.log.critical( msg )
    
debug = MyLogger()

################################################################################
# 
################################################################################

def bindump( data ):
    return "%02x%02x%02x%02x ... %02x%02x%02x%02x (%d bytes)" % ( 
        ord( data[0] ), ord( data[1] ), ord( data[2] ), ord( data[3] ),
        ord( data[-4] ), ord( data[-3] ), ord( data[-2] ), ord( data[-1] ), len( data )
    )

################################################################################
# 
################################################################################

LABEL = {
    1: {
        1: "LEN",
        2: "VER",
        3: "CNT",
        4: "TOT",
        5: "DAT",
        6: "PRY",
        7: "DAI",
        8: "ORI",
        9: "TCN",
        10: "TCR",
        11: "NSR",
        12: "NTR",
        13: "DOM",
        14: "GMT",
        15: "DCS",
    },
    2: {
        1: "LEN",
        2: "IDC",
        3: "SYS",
    },
    9: {
        1: "LEN",
        2: "IDC",
        3: "IMP",
        4: "FMT",
        128: "HLL",
        129: "VLL",
        130: "SLC",
        131: "HPS",
        132: "VPS",
        134: "FGP",
        999: "DAT",
    },
    13: {
        1: "LEN",
        2: "IDC",
        3: "IMP",
        4: "SRC",
        5: "LCD",
        6: "HLL",
        7: "VLL",
        8: "SLC",
        9: "HPS",
        10: "VPS",
        11: "GCA",
        12: "BPX",
        13: "FGP",
        14: "SPD",
        15: "PPC",
        20: "COM",
        24: "LQM",
        999: "DAT",
    }
}

FULLLABEL = {
    1: {
        1: "Logical record length",
        2: "Version number",
        3: "File content",
        4: "Type of transaction",
        5: "Date",
        6: "Priority",
        7: "Destination agency identifier",
        8: "Originating agency identifier",
        9: "Transaction control number",
        10: "Transaction control reference",
        11: "Native scanning resolution",
        12: "Nominal transmitting resolution",
        13: "Domain name",
        14: "Greenwich mean time",
        15: "Directory of character sets"
    },
    2: {
        1: "Logical record length",
        2: "Image designation character"
    },
    9: {
        1: "Logical record length",
        2: "Image designation character",
        3: "Impression type",
        4: "Minutiae format",
        5: "Originating fingerprint reading system",
        6: "Finger position",
        7: "Fingerprint pattern classification",
        8: "Core position",
        9: "Delta(s) position",
        10: "Number of minutiae",
        11: "Minutiae ridge count indicator",
        12: "Minutiae and ridge count data"
    },
    13: {
        1: "Logical record length",
        2: "Image designation character",
        3: "Impression type",
        4: "Source agency / ORI",
        5: "Latent capture date",
        6: "Horizontal line length",
        7: "Vertical line length",
        8: "Scale units",
        9: "Scale units",
        10: "Scale units",
        11: "Compression algorithm",
        12: "Bits per pixel",
        13: "Finger / palm position",
        14: "Search Position Descriptors",
        15: "Print Position Coordinates",
        16: "Scanned horizontal pixel scale",
        17: "Scanned vertical pixel scale",
        20: "Comment",
        24: "Latent quality metric",
        999: "Image data",
    }
}

################################################################################
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
################################################################################

class NIST:
    def __init__( self ):
        debug.info( "initialization of the NIST object" )
        
        self.filename = None
        self.data = defaultdict( dict )
        
        return
    
    def loadFromFile( self, infile ):
        debug.info( "Reading from file : %s" % infile )
        
        self.filename = infile
    
        with open( infile, "rb" ) as fp:
            data = fp.read()
        
        self.load( data )
    
    def load( self, data ):
        debug.info( "Loading object" )
        
        records = data.split( FS )
        expected = []
        
        ########################################################################
        #    NIST Type01
        ########################################################################
        
        debug.info( "Type01 parsing", 1 )
        
        t01 = records[0].split( GS )
        record01 = {}
        
        for field in t01:
            tag, ntype, tagid, value = fieldSplitter( field )
            
            if tagid == 1:
                LEN = int( value )
            
            if tagid == 3:
                for cnt in value.split( RS ):
                    expected.append( map( int, cnt.split( US ) ) )
            
            record01[ tagid ] = value
        
        self.data[ 1 ] = record01
        data = data[ LEN: ]
        
        ########################################################################
        #    NIST Type02 and after
        ########################################################################
        
        debug.debug( "Expected Types : %s" % ", ".join( [ str( ntype ) for ntype, _ in expected[ 1: ] ] ), 1 )
        
        for ntype, _ in expected[ 1: ]:
            debug.info( "Type%02d parsing" % ntype, 1 )
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
            
            data = data[ LEN: ]
            
        ########################################################################
        # 
        ########################################################################
        
        return

################################################################################
#    Functions
################################################################################

def fieldSplitter( f ):
    tag, value = f.split( CO )
    ntype, tagid = tag.split( DO )
    ntype = int( ntype )
    tagid = int( tagid )
    
    return tag, ntype, tagid, value
