#!/usr/bin/env python

from _collections import defaultdict
from collections import OrderedDict
import logging

from lib.misc.logger import debug


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
#    NIST object class
# 
################################################################################

class NIST:
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
    #    Loading functions
    ############################################################################
    
    def loadFromFile( self, infile ):
        """
            Open the 'infile' file and transmit the data to the 'load' function.
        """
        debug.info( "Reading from file : %s" % infile )
        
        self.filename = infile
    
        with open( infile, "rb" ) as fp:
            data = fp.read()
        
        self.load( data )

    def load( self, data ):
        """
            Load from the data passed in parameter, and populate all internal dictionnaries.
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
        
        self.data[ 1 ] = record01
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
        
        self.ntypeInOrder = set( self.ntypeInOrder )
        
    ############################################################################
    # 
    #    Generic functions
    # 
    ############################################################################
    
    def get_ntype( self ):
        return sorted( self.data.keys() )
    
    def get_idc( self, ntype ):
        return sorted( self.data[ ntype ].keys() )
    
################################################################################
#
#    Generic functions
#
################################################################################

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
    
def fieldSplitter( data ):
    """
        Split the input data in a ( tag, ntype, tagid, value ) tuple
        
        >>> fieldSplitter( "1.002:0501" )
        ('1.002', 1, 2, '0501')
        
    """
    tag, value = data.split( CO )
    ntype, tagid = tag.split( DO )
    ntype = int( ntype )
    tagid = int( tagid )
    
    return tag, ntype, tagid, value

def get_label( ntype, tagid, fullname = False ):
    if fullname == False:
        lab = LABEL
        void = "   "
    else:
        lab = FULLLABEL
        void = ""
    
    if lab.has_key( ntype ) and lab[ ntype ].has_key( tagid ):
        return lab[ ntype ][ tagid ]
    else:
        return void

def leveler( msg, level ):
    return "\t" * level + msg
    
################################################################################
#
#    Main
#
################################################################################

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    