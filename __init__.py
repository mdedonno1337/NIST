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
    #    Dumping
    # 
    ############################################################################
    
    def dump_record( self, ntype, idc = -1, fullname = False ):
        if idc < 0:
            d = self.data[ ntype ]
        else:
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
        debug.info( "Dumping NIST" )
        
        s = ""
        
        for ntype in self.get_ntype():
            debug.debug( "NIST Type-%02d" % ntype, 1 )
            
            if ntype == 1:
                s += "NIST Type-%02d\n" % ntype
                s += self.dump_record( ntype, -1, fullname ) 
            else:
                for idc in self.get_idc( ntype ):
                    s += "NIST Type-%02d (IDC %d)\n" % ( ntype, idc )
                    s += self.dump_record( ntype, idc, fullname )
        
        return s
    
    ############################################################################
    # 
    #    Generic functions
    # 
    ############################################################################
    
    def clean( self ):
        debug.info( "Cleaning the NIST object" )
        
        for ntype in self.get_ntype():
            if ntype == 1:
                for tagid in self.data[ ntype ].keys():
                    value = self.data[ ntype ][ tagid ]
                    if value == "" or value == None:
                        debug.debug( "Field %02d.%03d deleted" % ( ntype, tagid ), 2 )
                        del( self.data[ ntype ][ tagid ] )
                        
            else:
                for idc in self.data[ ntype ].keys():
                    for tagid in self.data[ ntype ][ idc ].keys():
                        value = self.data[ ntype ][ idc ][ tagid ]
                        if value == "" or value == None:
                            debug.debug( "Field %02d.%03d IDC %d deleted" % ( ntype, tagid, idc ), 2 )
                            del( self.data[ ntype ][ idc ][ tagid ] )
    
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
        index = 0
        void = "   "
    else:
        index = 1
        void = ""
    
    if LABEL.has_key( ntype ) and LABEL[ ntype ].has_key( tagid ):
        return LABEL[ ntype ][ tagid ][ index ]
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
    
