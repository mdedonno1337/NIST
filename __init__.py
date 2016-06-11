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
