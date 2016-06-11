#!/usr/bin/env python

from _collections import defaultdict

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
        self.filename = None
        self.data = defaultdict( dict )
        
        return
    
    def loadFromFile( self, infile ):
        self.filename = infile
    
        with open( infile, "rb" ) as fp:
            data = fp.read()
        
        self.load( data )
    
    def load( self, data ):
        records = data.split( FS )
        expected = []
        
        ########################################################################
        #    NIST Type01
        ########################################################################
        
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
        
        for ntype, _ in expected[ 1: ]:
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
                        recordx[ tagid ] = value
                        data = data[ end: ]
                        break
                        
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
