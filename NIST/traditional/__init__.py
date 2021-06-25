#!/usr/bin/python
# -*- coding: UTF-8 -*-

from collections import OrderedDict
import cStringIO
import hashlib
import os

from MDmisc.binary import binstring_to_int, int_to_binstring
from MDmisc.boxer import boxer
from MDmisc.elist import ifany
from MDmisc.logger import debug
from MDmisc.string import stringIterator, join

from ..core import NIST as NIST_Core
from ..core.config import FS, GS, RS, US
from ..core.functions import fieldSplitter, bindump, decode_gca, tagger, decode_fgp

class NIST( NIST_Core ):
    def load_auto( self, p ):
        """
            Function to detect and load automatically the 'p' value passed in
            parameter. The argument 'p' can be a string (URI to the file to
            load) or a NIST object (a copy will be done in the current object).
            
            :param p: Input data to parse to NIST object.
            :type p: NIST or str
        """
        if isinstance( p, ( str, unicode ) ):
            if ifany( [ FS, GS, RS, US ], p ):
                self.load( p )
                
            else:
                self.read( p )
        
        elif isinstance( p, ( cStringIO.OutputType ) ):
            self.load( p.getvalue() )
        
        elif isinstance( p, ( file ) ):
            self.load( p.read() )
        
        elif isinstance( p, ( NIST, dict ) ):
            if isinstance( p, NIST ):
                p = p.data
            
            for ntype, tmp in p.iteritems():
                ntype = int( ntype )
                self.add_ntype( ntype )
                
                for idc, tmp2 in tmp.iteritems():
                    idc = int( idc )
                    self.add_idc( ntype, idc )
                    
                    for tagid, value in tmp2.iteritems():
                        tagid = int( tagid )
                        
                        self.set_field( ( ntype, tagid ), value, idc )
        
    def load( self, data ):
        """
            Load from the data passed in parameter, and populate all internal
            dictionaries. This function is the main function doing the decoding
            of the NIST file.
            
            :param data: Raw data read from file.
            :type data: str
        """
        debug.debug( "Loading object" )
        
        records = data.split( FS )
        
        #    NIST Type01
        debug.debug( "Type-01 parsing", 1 )
        
        t01 = records[ 0 ].split( GS )
        record01 = {}
        
        ntypeInOrder = []
        
        for field in t01:
            tag, ntype, tagid, value = fieldSplitter( field )
            
            if tagid == 1:
                LEN = int( value )
            
            if tagid == 3:
                ntypeInOrder = self.process_fileContent( value )
            
            debug.debug( "%d.%03d:\t%s" % ( ntype, tagid, value ), 2 )
            record01[ tagid ] = value
        
        self.data[ 1 ][ 0 ] = record01 # Store in IDC = 0 even if the standard implies no IDC for Type-01
        data = data[ LEN: ]
        
        #    NIST Type02 and after
        debug.debug( "Expected Types : %s" % ", ".join( map( str, ntypeInOrder ) ), 1 )
        
        for ntype in ntypeInOrder:
            debug.debug( "Type-%02d parsing" % ntype, 1 )
            LEN = 0
            
            if ntype in [ 2, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 98, 99 ]:
                current_type = data.split( FS )
                
                tx = current_type[ 0 ].split( GS )
                
                recordx = {}
                offset = 0
                idc = -1
                
                for t in tx:
                    if len( t ) == 0:
                        continue
                    
                    try:
                        tag, ntype, tagid, value = fieldSplitter( t )
                    except:
                        tagid = 999
                        tag = "%s.%s" % ( ntype, tagid )
                    
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
                FGP = binstring_to_int( iter.take( 6 ) )
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
                debug.debug( "GCA: %s" % ( GCA ), 3 )
                debug.debug( "GCA decoded: %s" % ( decode_gca( GCA ) ), 3 )
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
                if data.startswith( str( ntype ) ):
                    _, _, _, LEN = fieldSplitter( data[ 0 : data.find( GS ) ] )
                    LEN = int( LEN )
                else:
                    LEN = binstring_to_int( data[ 0 : 4 ] )
            
            data = data[ LEN: ]

    def dumpbin( self ):
        """
            Return a binary dump of the NIST object. Writable in a file ("wb" mode).
            
            :return: Binary representation of the NIST object.
            :rtype: str
        """
        debug.debug( "Dumping NIST in binary" )
        
        self.clean()
        self.patch_to_standard()
        
        outnist = []
        
        for ntype in self.get_ntype():
            for idc in self.get_idc( ntype ):
                if ntype == 4:
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 1 ] ), 4 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 2 ] ), 1 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 3 ] ), 1 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 4 ] ), 6 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 5 ] ), 1 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 6 ] ), 2 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 7 ] ), 2 * 8 ) )
                    outnist.append( int_to_binstring( int( self.data[ ntype ][ idc ][ 8 ] ), 1 * 8 ) )
                    outnist.append( self.data[ ntype ][ idc ][ 999 ] )
                else:
                    od = OrderedDict( sorted( self.data[ ntype ][ idc ].items() ) )
                    outnist.append( join( GS, [ tagger( ntype, tagid ) + value for tagid, value in od.iteritems() ] ) + FS )
        
        return "".join( outnist )

    def write( self, outfile ):
        """
            Write the NIST object to a specific file.
            
            :param outfile: URI of the file to write to.
            :type outfile: str
        """
        debug.debug( "Write the NIST object to '%s'" % outfile )
        
        if not os.path.isdir( os.path.dirname( os.path.realpath( outfile ) ) ):
            os.makedirs( os.path.dirname( os.path.realpath( outfile ) ) )
        
        with open( outfile, "wb+" ) as fp:
            fp.write( self.dumpbin() )
    
    def hash( self ):
        return hashlib.md5( self.dumpbin() ).hexdigest()
    
    ############################################################################
    # 
    #    Cleaning and resetting functions
    # 
    ############################################################################
    
    def clean( self ):
        super( NIST, self ).clean()
        
        #    Reset the length of each ntype record (n.001 fields)
        for ntype in self.get_ntype():
            for idc in self.get_idc( ntype ):
                if ntype == 4:
                    self.reset_binary_length( ntype, idc )
                else:
                    self.reset_alpha_length( ntype, idc )
    
    def reset_alpha_length( self, ntype, idc = 0 ):
        """
            Recalculate the LEN field of the ntype passed in parameter.
            Only for ASCII ntype.
            
            :param ntype: ntype to reset.
            :type ntype: int
            
            :param idc: IDC value
            :type idc: int
        """
        debug.debug( "Resetting the length of Type-%02d" % ntype )
        
        debug.debug( "Resseting %d.001 to %08d" % ( ntype, 0 ), 1 )
        self.set_field( "%d.001" % ntype, "%08d" % 0, idc )
        
        # %d.%03d:<data><GS>
        lentag = len( "%d" % ntype ) + 6
        debug.debug( "Taglen %d : %d" % ( ntype, lentag ), 1 )
        
        # Iteration over all IDC
        debug.debug( "Iterate over fields in the IDC-%d" % idc, 1 )
        recordsize = 0
        for tagid, value in self.data[ ntype ][ idc ].iteritems():
            recordsize += len( value ) + lentag
            debug.debug( "Field %d.%03d : added % 9d to the recordsize (now %d)" % ( ntype, tagid, len( value ) + lentag, recordsize ), 2 )
        
        self.set_field( "%d.001" % ntype, "%08d" % recordsize, idc )
    
    def reset_binary_length( self, ntype, idc = 0 ):
        """
            Recalculate the LEN field of the ntype passed in parameter.
            Only for binary ntype.
            
            :param ntype: ntype to reset.
            :type ntype: int
            
            :param idc: IDC value.
            :type idc: int
        """
        debug.debug( "Resetting the length of Type-%02d" % ntype )
        
        if ntype == 4:
            recordsize = 18
            
            if self.data[ ntype ][ idc ].has_key( 999 ):
                recordsize += len( self.data[ ntype ][ idc ][ 999 ] )
                
        self.set_field( "%d.001" % ntype, "%d" % recordsize, idc )
    
    
