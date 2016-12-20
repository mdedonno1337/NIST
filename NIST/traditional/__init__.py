#!/usr/bin/python
# -*- coding: UTF-8 -*-

import datetime
import inspect
import os
import time

from collections import OrderedDict
from copy import deepcopy

from MDmisc.binary import binstring_to_int, int_to_binstring
from MDmisc.boxer import boxer
from MDmisc.deprecated import deprecated
from MDmisc.elist import replace_r, ifany
from MDmisc.logger import debug
from MDmisc.map_r import map_r
from MDmisc.RecursiveDefaultDict import defDict
from MDmisc.string import join, upper, stringIterator, split_r

from .config import *
from .exceptions import *
from .functions import *
from .voidType import voidType

################################################################################
# 
#    NIST object class
# 
################################################################################

class NIST( object ):
    """
        This is the main NIST object parser. This class is build to be main
        core/processing unit of any NIST implementation (ie. the application for
        Fingerprint, DNA, ...). Any new application have to inherit from this
        class, add new methods, and overload some other methods if needed. The
        main API of this class have to be consistent to allow cross usability
        between particular implementations.
        
        This class implement all function to work with Traditional format AN2K
        files, aka NIST files. A description of this standard can be found at:
        
            https://www.nist.gov/itl/iad/image-group/ansinist-itl-standard-references
            
        The XML format is (for the moment) not supported.
        
        :cvar str stdver: Version of the NIST standard used.
        :cvar str fileuri: Path to the file, if loaded from disk.
        :cvar defDict data: NIST data.
        :cvar datetime date: Creation date (YYYY-mm-dd).
        :cvar int timestamp: creation timestamp (UNIX time).
    """
    def __init__( self, init = None ):
        """
            Initialization of the NIST Object.
            
            :param init: Initialization data. Can be a NIST object, a file link, or a raw string.
            :type init: NIST or str
            
            All biometric information are stored in the self.data recursive
            default dictionary object. The information is stored as following:
            
                self.data[ ntype ][ idc ][ tagid ]
            
            To get and set data, use the :func:`~NIST.traditional.NIST.get_field`
            and :func:`~NIST.traditional.NIST.set_field()` functions.
        """
        debug.info( "Initialization of the NIST object" )
        
        self.stdver = "0300"
        
        self.fileuri = None
        self.filename = None
        self.data = defDict()
        
        self.date = datetime.datetime.now().strftime( "%Y%m%d" )
        self.timestamp = int( time.time() )
        
        if init != None:
            self.load_auto( init )
    
    ############################################################################
    # 
    #    General informations
    # 
    ############################################################################
    
    def set_identifier( self, id ):
        """
            Set the identifier of the current NIST object. Not stored in the
            NIST file if written to disk.
            
            :param id: Identifier to set to the NIST object.
            :type id: anything
        """
        self.id = id
    
    def get_identifier( self ):
        """
            Get the identifier of the current object.
            
            :return: NIST Object identifier.
            :rtype: anything
        """
        try:
            return self.id
        except:
            return None
    
    ############################################################################
    # 
    #    Changing the class type
    # 
    ############################################################################
    
    def changeClassTo( self, newclass ):
        """
            Change on the fly the class of the current object. The functions
            associated with the new class are, of course, available in the
            current object after the change.
            
            Let `n` be a NIST object as follow:
            
                >>> type( n )
                <class 'NIST.traditional.__init__.NIST'>
            
            To change the type to `NISTf` type, use the following commands:
                
                >>> from NIST import NISTf
                >>> n.changeClassTo( NISTf )
                >>> type( n )
                <class 'NIST.fingerprint.NISTf'>
        """
        self.__class__ = newclass
    
    ############################################################################
    #
    #    Loading functions
    #
    ############################################################################
    
    def read( self, infile ):
        """
            Open the 'infile' file and transmit the data to the 'load' function.
            
            :param infile: URI of the NIST file to read and load.
            :type infile: str
            
            Usage:
                
                >>> from NIST import NIST
                >>> n = NIST()
                >>> n.read( "./sample/pass-type-9-13-m1.an2" )
                >>> n
                NIST object, Type-01, Type-02, Type-09, Type-13
        """
        debug.info( "Reading from file : %s" % infile )
        
        self.fileuri = infile
        self.filename = os.path.splitext( os.path.basename( infile ) )[ 0 ]
    
        with open( infile, "rb" ) as fp:
            data = fp.read()
        
        self.load( data )
    
    def load_auto( self, p ):
        """
            Function to detect and load automatically the 'p' value passed in
            parameter. The argument 'p' can be a string (URI to the file to
            load) or a NIST object (a copy will be done in the current object).
            
            :param p: Input data to parse to NIST object.
            :type p: NIST or str
        """
        if type( p ) == str:
            if ifany( [ FS, GS, RS, US ], p ):
                self.load( p )
                
            else:
                self.read( p )
            
        elif isinstance( p, NIST ):
            # Get the list of all attributes stored in the NIST object.
            attributes = inspect.getmembers( p, lambda a: not( inspect.isroutine( a ) ) )
            
            # Copy all the values to the current NIST object. 
            for name, value in [ a for a in attributes if not( a[ 0 ].startswith( '__' ) and a[ 0 ].endswith( '__' ) ) ]:
                super( NIST, self ).__setattr__( name, value )
    
    def load( self, data ):
        """
            Load from the data passed in parameter, and populate all internal
            dictionaries. This function is the main function doing the decoding
            of the NIST file.
            
            :param data: Raw data read from file.
            :type data: str
        """
        debug.info( "Loading object" )
        
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
            
            :param data: Content of the field 1.003.
            :type data: str
            
            :return: List of ntypes present in the NIST file, except the Type01.
            :rtype: lst
            
            Usage:
            
                >>> fileContent = n.get_field( "1.003" )
                >>> n.process_fileContent( fileContent )
                [2]
        """
        try:
            data = map( lambda x: map( int, x.split( US ) ), data.split( RS ) )
        except:
            data = replace_r( split_r( [ RS, US ], data ), '', '1' )
            data = map_r( int, data )
        
        self.nbLogicalRecords = data[ 0 ][ 1 ]
        
        return [ ntype for ntype, idc in data[ 1: ] ]
    
    ############################################################################
    # 
    #    Update NIST object
    # 
    ############################################################################
    
    def update( self, b ):
        """
            Update the fields from the current NIST object with a NIST object
            passed in parameter. If the field already exist and is not empty,
            the value is updated, otherwise, the field is created.
            
            :param b: Second NIST object from wich collect the new information.
            :type b: NIST
        """
        for ntype in b.get_ntype():
            for idc in b.get_idc( ntype ):
                for tagid, value in b.data[ ntype ][ idc ].iteritems():
                    self.data[ ntype ][ idc ][ tagid ] = value
        
        self.clean()
    
    def merge( self, other, update = False, ignore = False ):
        """
            Merge two NIST files together.
            
            :param other: Second NIST object.
            :type other: NIST
            
            :param update: Update the fields if already existing in the first NIST object.
            :type update: boolean
            
            :param ignore: Ignore the IDC content if already in the first NIST object.
            :type ignore: boolean
            
            :return: Merged NIST object.
            :rtype: NIST
        """
        ret = deepcopy( self )
        
        for ntype in other.get_ntype():
            if ntype != 1:
                for idc in other.get_idc( ntype ):
                    if ret.data[ ntype ].has_key( idc ) and not update:
                        if ignore:
                            continue
                        else:
                            raise Exception
                    
                    else:
                        if not ntype in ret.get_ntype():
                            ret.add_ntype( ntype ) 
                        
                        if not idc in self.get_idc( ntype ):
                            ret.add_idc( ntype, idc )
                        
                        for tagid, value in other.data[ ntype ][ idc ].iteritems():
                            ret.set_field( ( ntype, tagid ), value, idc )
        
        return ret
    
    def __add__( self, other ):
        """
            Overload of the '+' operator. Call of the
            :func:`~NIST.traditional.NIST.merge` function.
        """
        return self.merge( other )
    
    ############################################################################
    # 
    #    Content delete
    # 
    ############################################################################
    
    def delete( self, ntype = None, idc = -1 ):
        """
            Function to delete a specific Type-'ntype', IDC or field.
            
            :param ntype: ntype (or tagid) to delete.
            :type ntype: int (str)
            
            :param idc: IDC value.
            :type idc: int
            
            To delete the Type-09 record::
            
                n.delete( 9 )
            
            To delete the Type-09 IDC 0::
            
                n.delete( 9, 0 )
            
            To delete the field "9.012"::
            
                n.delete( "9.012" )
            
            To delete the field "9.012" IDC 0::
            
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
            Delete a specific 'ntype' record.
            
            :param ntype: ntype to delete.
            :type ntype: int
            
            :raise ntypeNotFound: if the ntype is not present in the NIST object
        """
        if self.data.has_key( ntype ):
            del( self.data[ ntype ] )
        else:
            raise ntypeNotFound
    
    def delete_idc( self, ntype, idc ):
        """
            Delete the specific IDC passed in parameter from 'ntype' record.
            
            :param ntype: ntype to delete.
            :type ntype: int
            
            :param idc: IDC value.
            :type idc: int
            
            :raise idcNotFound: if the IDC for the ntype is not present in the NIST object
        """
        if self.data.has_key( ntype ) and self.data[ ntype ].has_key( idc ):
            del( self.data[ ntype ][ idc ] )
        else:
            raise idcNotFound
    
    def delete_tag( self, tag, idc = -1 ):
        """
            Delete the field 'tag' from the specific IDC.
            
            :param tag: tagid to delete.
            :type tag: str
            
            :param idc: IDC value.
            :type idc: int
            
            :raise tagNotFound: if the tagid is not present in the NIST object
        """
        ntype, tagid = tagSplitter( tag )
        
        idc = self.checkIDC( ntype, idc )
        
        if self.data.has_key( ntype ) and self.data[ ntype ].has_key( idc ):
            del( self.data[ ntype ][ idc ][ tagid ] )
        else:
            raise tagNotFound
    
    def move_idc( self, ntype, idcfrom, idcto ):
        """
            Move an IDC to an other value.
            
            :param ntype: ntype value.
            :type ntype: int
            
            :param idcfrom: IDC to move.
            :type idcfrom: int
            
            :param idcto: destination IDC.
            :type idcfrom: int
        """
        self.data[ ntype ][ idcto ] = self.data[ ntype ][ idcfrom ]
        del self.data[ ntype ][ idcfrom ]
    
    ############################################################################
    # 
    #    Dumping
    # 
    ############################################################################
    
    def format_field( self, ntype, tagid, idc = -1 ):
        """
            Return the value or the hexadecimal representation of the value for
            binary fields.
            
            :param ntype: ntype value.
            :type ntype: int
            
            :param tagid: fild name.
            :type tagid: str
            
            :param idc: IDC value
            :type idc: int
            
            :return: Formatted field.
            :rtype: str
            
            Usage:
            
                >>> n.format_field( 1, 8 )
                'UNIL'
        """
        value = self.get_field( ( ntype, tagid ), idc )
        
        if tagid == 999:
            return bindump( value )
        
        elif ntype == 18 and tagid == 19:
            return bindump( value )
            
        else:
            return value
    
    def dump_record( self, ntype, idc = 0, fullname = False ):
        """
            Dump a specific ntype - IDC record.
            
            :param ntype: ntype value.
            :type ntype: int
            
            :param idc: IDC value
            :type idc: int
            
            :param fullname: Get the full name of the field.
            :type fullname: boolean
            
            :return: Printable string.
            :rtype: str
            
            Usage:
            
                >>> dump = n.dump_record( 1, 0 )
                >>> print( dump ) # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
                NIST Type-01
                    01.001 LEN: 00000136
                    01.002 VER: 0300
                    01.003 CNT: 1<US>1<RS>2<US>0
                    01.004 TOT: USA
                    01.005 DAT: ...
                    01.006 PRY: 1
                    01.007 DAI: FILE
                    01.008 ORI: UNIL
                    01.009 TCN: ...
                    01.011 NSR: 00.00
                    01.012 NTR: 00.00
        """
        d = self.data[ ntype ][ idc ]
        
        ret = []
        
        if ntype != 1:
            ret.append( "NIST Type-%02d (IDC %d)" % ( ntype, idc ) )
        else:
            ret.append( "NIST Type-%02d" % ntype )
                
        for tagid, value in iter( sorted( d.iteritems() ) ):
            lab = get_label( ntype, tagid, fullname )
            header = "%02d.%03d %s" % ( ntype, tagid, lab )
            
            field = self.format_field( ntype, tagid, idc )
            
            debug.debug( "%s: %s" % ( header, field ), 2 )
            ret.append( leveler( "%s: %s" % ( header, field ), 1 ) )
        
        return printableFieldSeparator( join( "\n", ret ) )
    
    def dump( self, fullname = False ):
        """
            Return a readable version of the NIST object. Printable on screen.
            
            :param fullname: Get the fullname of the fields.
            :type fullname: boolean
            
            :return: Printable representation of the NIST object.
            :rtype: str
            
            Usage:
            
                >>> dump = n.dump()
                >>> print( dump ) # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
                Informations about the NIST object:
                    Obj ID:  Doctester NIST object
                    Records: Type-01, Type-02
                    Class:   NISTf
                <BLANKLINE>
                NIST Type-01
                    01.001 LEN: 00000136
                    01.002 VER: 0300
                    01.003 CNT: 1<US>1<RS>2<US>0
                    01.004 TOT: USA
                    01.005 DAT: ...
                    01.006 PRY: 1
                    01.007 DAI: FILE
                    01.008 ORI: UNIL
                    01.009 TCN: ...
                    01.011 NSR: 00.00
                    01.012 NTR: 00.00
                NIST Type-02 (IDC 0)
                    02.001 LEN: 00000062
                    02.002 IDC: 0
                    02.003    : 0300
                    02.004    : ...
                    02.054    : 0300<US><US>
        """
        debug.info( "Dumping NIST" )
        
        self.clean()
        
        ret = [
            "Informations about the NIST object:",
        ]
        
        if self.fileuri != None:
            ret.append( leveler( "File:    " + self.fileuri, 1 ) )
        
        if self.get_identifier() != None:
            ret.append( leveler( "Obj ID:  " + self.get_identifier(), 1 ) )
        
        ret.extend( [
            leveler( "Records: " + ", ".join( [ "Type-%02d" % x for x in self.get_ntype() ] ), 1 ),
            leveler( "Class:   " + self.__class__.__name__, 1 ),
            ""
        ] )
        
        for ntype in self.get_ntype():
            debug.debug( "NIST Type-%02d" % ntype, 1 )
            
            for idc in self.get_idc( ntype ):
                ret.append( self.dump_record( ntype, idc, fullname ) )
        
        return join( "\n", ret )
    
    def dumpbin( self ):
        """
            Return a binary dump of the NIST object. Writable in a file ("wb" mode).
            
            :return: Binary representation of the NIST object.
            :rtype: str
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
                    outnist.append( join( GS, [ tagger( ntype, tagid ) + value for tagid, value in od.iteritems() ] ) + FS )
        
        return "".join( outnist )
    
    def write( self, outfile ):
        """
            Write the NIST object to a specific file.
            
            :param outfile: URI of the file to write to.
            :type outfile: str
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
            Function to clean all unused fields in the self.data variable. This
            function should check the content of the NIST file only for fields
            described in the NIST standard. For all particular implementations
            and implementation specific fields, overload this function in a new
            class.
            
            Check done in this function:
            
                * Delete all empty records, IDC and fields
                * Recalculate the content of the field 1.003
                * Check the IDC field for every ntype (fields x.002)
                * Reset all lengths (fields x.001)
        """
        debug.info( "Cleaning the NIST object" )
        
        #     Delete all empty data.
        for ntype in self.get_ntype():
            for idc in self.data[ ntype ].keys():
                
                #    Fields
                for tagid in self.data[ ntype ][ idc ].keys():
                    value = self.get_field( "%d.%03d" % ( ntype, tagid ), idc )
                    if value == "" or value == None:
                        debug.debug( "Field %02d.%03d IDC %d deleted" % ( ntype, tagid, idc ), 1 )
                        del( self.data[ ntype ][ idc ][ tagid ] )
                
                #    IDC
                if len( self.data[ ntype ][ idc ] ) == 0:
                    debug.debug( "%02d IDC %d deleted" % ( ntype, idc ), 1 )
                    del( self.data[ ntype ][ idc ] )
            
            #    ntype
            if len( self.data[ ntype ] ) == 0:
                debug.debug( "%02d deleted" % ( ntype ), 1 )
                del( self.data[ ntype ] )
                
        #    Recheck the content of the NIST object and udpate the 1.003 field
        content = []
        for ntype in self.get_ntype()[ 1: ]:
            for idc in self.get_idc( ntype ):
                debug.debug( "Type-%02d, IDC %d present" % ( ntype, idc ), 1 )
                content.append( "%s%s%s" % ( ntype, US, idc ) )
                
        content.insert( 0, "%s%s%s" % ( 1, US, len( content ) ) )
        self.set_field( "1.003", join( RS, content ) )
        
        #    Check the IDC values for all records
        for ntype in self.get_ntype()[ 1: ]:
            for idc in self.get_idc( ntype ):
                debug.debug( "Type-%02d, IDC %d: update the IDC field (%02d.%03d)" % ( ntype, idc, ntype, 2 ), 1 )
                self.set_field( ( ntype, 2 ), idc, idc )
                        
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
            
                * 1.002
                * 1.011
                * 1.012
        """
        debug.info( "Patch some fields regaring the ANSI/NIST-ITL standard" )
        
        #    1.002 : Standard version:
        #        0300 : ANSI/NIST-ITL 1-2000
        #        0400 : ANSI/NIST-ITL 1-2007
        #        0500 : ANSI/NIST-ITL 1-2011
        #        0501 : ANSI/NIST-ITL 1-2011 Update: 2013 Traditional Encoding
        #        0502 : ANSI/NIST-ITL 1-2011 Update: 2015 Traditional Encoding
        debug.debug( "set version to 0300 (ANSI/NIST-ITL 1-2000)", 1 )
        self.set_field( "1.002", self.stdver )
        
        #    1.011 and 1.012
        #        For transactions that do not contain Type-3 through Type-7
        #        fingerprint image records, this field shall be set to "00.00"
        if not ifany( [ 3, 4, 5, 6, 7 ], self.get_ntype() ):
            debug.debug( "Fields 1.011 and 1.012 patched: no Type-03 through Type-07 in this NIST file", 1 )
            self.set_field( "1.011", "00.00" )
            self.set_field( "1.012", "00.00" )
        
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
    
    ############################################################################
    # 
    #    Access to the fields value
    # 
    ############################################################################
    
    def get_field( self, tag, idc = -1 ):
        """
            Get the content of a specific tag in the NIST object.
            
            :param tag: tag value.
            :type tag: int
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Content of the field.
            :rtype: str or None
            
            :raise notImplemented: if the 'tag' field is not a str or a tuple
            
            Usage:
            
                >>> n.get_field( "1.002" )
                '0300'
        """
        if type( tag ) == str:
            ntype, tagid = tagSplitter( tag )
            
        elif type( tag ) == tuple:
            ntype, tagid = tag
        
        else:
            raise notImplemented
        
        idc = self.checkIDC( ntype, idc )
    
        try:
            return self.data[ ntype ][ idc ][ tagid ]
        except:
            return None
    
    def set_field( self, tag, value, idc = -1 ):
        """
            Set the value of a specific tag in the NIST object.
            
            :param tag: Tag to set.
            :type tag: int
            
            :param value: Value to set.
            :type value: str (or int)
            
            :param idc: IDC value.
            :type idc: int
            
            Usage:
            
                >>> n.set_field( "1.002", "0300" )
        """
        if type( tag ) == str:
            ntype, tagid = tagSplitter( tag )
        else:
            ntype, tagid = map( int, tag )
        
        idc = self.checkIDC( ntype, idc )
        
        if type( value ) != str:
            value = str( value )
        
        if len( value ) == 0:
            return
        else:
            self.data[ ntype ][ idc ][ tagid ] = value
    
    def get_fields( self, tags, idc = -1 ):
        """
            Get the content of multiples fields at the same time.
            
            :param tags: List of tags.
            :type tags: int
            
            :param idc: IDC value
            :type idc: int
            
            :return: List of values.
            :rtype: list
            
            Usage:
            
                >>> n.get_fields( [ "1.002", "1.004" ] )
                ['0300', 'USA']
        """
        return [ self.get_field( tag, idc ) for tag in tags ]
    
    def set_fields( self, fields, value, idc = -1 ):
        """
            Set the value of multiples fields to the same value.
            
            :param fields: List of fields to set.
            :type tags: list
            
            :param value: Value to set.
            :type value: str (or int)
            
            :param idc: IDC value
            :type idc: int
            
            .. seealso:: :func:`~NIST.traditional.NIST.set_field`
        """
        for field in fields:
            self.set_field( field, value, idc )
    
    ############################################################################
    # 
    #    Add ntype and idc
    # 
    ############################################################################
    
    def add_ntype( self, ntype ):
        """
           Add an empty ntype to the NIST object.
           
           :param ntype: ntype to add.
           :type ntype: int
           
           Usage:
           
               >>> tmp = n.get()
               >>> tmp.add_ntype( 18 )
               >>> tmp
               NIST object, Type-01, Type-02, Type-18
        """
        if not ntype in self.get_ntype():
            self.data[ ntype ] = {}
    
    def add_idc( self, ntype, idc ):
        """
            Add a empty IDC field for a particular ntype.
            
            :param ntype: ntype to set.
            :type ntype: int
            
            :param idc: IDC value.
            :type idc: int
            
            :raise idcNotFound: if the IDC is not found in the NIST object.
            :raise idcAlreadyExisting: if the IDC value already exists in the NIST object.
            :raise needIDC: if an IDC value have to be provided.
        """
        if not ntype in self.get_ntype():
            raise idcNotFound
        
        elif idc in self.get_idc( ntype ):
            raise idcAlreadyExisting
        
        elif idc < 0:
            raise needIDC
        
        else:
            self.data[ ntype ][ idc ] = { 1: '' }
    
    def get_idc_dict( self, ntype, idc ):
        """
            Return the value of a particular ntype / IDC value.
            
            :param ntype: ntype to set.
            :type ntype: int
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Content of the IDC.
            :rtype: dict
        """
        return self.data[ ntype ][ idc ]
    
    def update_idc( self, ntype, idc, value ):
        """
            Update the value of a particular ntype / IDC.
            
            :param ntype: ntype to set.
            :type ntype: int
            
            :param idc: IDC value.
            :type idc: int
            
            :param value: Value to set.
            :type value: dict
        """
        self.data[ ntype ][ idc ].update( value )
    
    ############################################################################
    # 
    #    Add empty records to the NIST object
    # 
    ############################################################################
    
    def add_default( self, ntype, idc ):
        """
            Add the default values in the ntype record. The default values are
            provided by the `NIST.traditional.voidType` module.
            
            :param ntype: ntype to set.
            :type ntype: int
            
            :param idc: IDC value.
            :type idc: int
            
        """
        self.add_ntype( ntype )
        self.add_idc( ntype, idc )
        
        self.update_idc( ntype, idc, voidType[ ntype ] )
        
        if ntype != 1:
            self.set_field( ( ntype, 2 ), idc, idc )
        
    def add_Type01( self ):
        """
            Add the Type-01 record to the NIST object, and set the Date,
            Originating Agency Identifier and the Transaction Control Number
        """
        ntype = 1
        idc = 0
        
        self.add_default( ntype, idc )
        
        self.set_field( "1.005", self.date, idc )
        self.set_field( "1.008", default_origin, idc )
        self.set_field( "1.009", self.timestamp, idc )
        
        return
    
    def add_Type02( self ):
        """
            Add the Type-02 record to the NIST object, and set the Date.
        """
        ntype = 2
        idc = 0
        
        self.add_default( ntype, idc )
        
        self.set_field( "2.004", self.date, idc )
        
        return
    
    ############################################################################
    # 
    #    Generic functions
    # 
    ############################################################################
    
    def get_ntype( self ):
        """
            Return all ntype presents in the NIST object.
            
                >>> n.get_ntype()
                [1, 2]
        """
        return sorted( self.data.keys() )
    
    def get_idc( self, ntype ):
        """
            Return all IDC for a specific ntype.
            
                >>> n.get_idc( 2 ) # doctest: +NORMALIZE_WHITESPACE
                [0]
        """
        return sorted( self.data[ ntype ].keys() )
    
    def checkIDC( self, ntype, idc ):
        """
            Check if the IDC passed in parameter exists for the specific ntype,
            and if the value is numeric. If the IDC is negative, then the value
            is searched in the ntype field and returned only if the value is
            unique; if multiple IDC are stored for the specific ntype, an
            exception is raised.
            
                >>> n.checkIDC( 1, 0 )
                0
                
                >>> n.checkIDC( 1, -1 )
                0
                
                >>> n.checkIDC( 1, 1 ) # doctest: +IGNORE_EXCEPTION_DETAIL
                Traceback (most recent call last):
                idcNotFound
        """
        try:
            idc = int( idc )
        except:
            raise intIDC
        
        if idc < 0:
            idc = self.get_idc( ntype )
            
            if len( idc ) > 1:
                raise needIDC
            elif len( idc ) == 1:
                return idc[ 0 ]
            else:
                raise recordNotFound
            
        if not idc in self.get_idc( ntype ):
            raise idcNotFound
        
        return idc
    
    def __str__( self ):
        """
            Return the printable version of the NIST object.
            
                >>> print n # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
                Informations about the NIST object:
                    Obj ID:  Doctester NIST object
                    Records: Type-01, Type-02
                    Class:   NIST
                <BLANKLINE>
                NIST Type-01
                    01.001 LEN: 00000136
                    01.002 VER: 0300
                    01.003 CNT: 1<US>1<RS>2<US>0
                    01.004 TOT: USA
                    01.005 DAT: ...
                    01.006 PRY: 1
                    01.007 DAI: FILE
                    01.008 ORI: UNIL
                    01.009 TCN: ...
                    01.011 NSR: 00.00
                    01.012 NTR: 00.00
                NIST Type-02 (IDC 0)
                    02.001 LEN: 00000062
                    02.002 IDC: 0
                    02.003    : 0300
                    02.004    : ...
                    02.054    : 0300<US><US>
        """
        return self.dump()
    
    def __repr__( self ):
        """
            Return unambiguous description.
            
                >>> n
                NIST object, Type-01, Type-02
        """
        return "NIST object, " + ", ".join( [ "Type-%02d" % x for x in self.get_ntype() ] )
    
    def get( self ):
        """
            Get a copy of the current NIST object.
            
            :return: A new NIST object.
            :rtype: NIST
            
            Usage:
            
                >>> tmp = n.get()
                >>> tmp == n
                False
            
            .. note::
            
                Since the function return a copy of the current object, the two
                objects are separate in memory, allowing to modify one and not
                the other (reason why `tmp` is not equal to `n`, even if the
                content is the same).
        """
        return deepcopy( self )
    
class NIST_deprecated( NIST ):
    """
        This class define all the deprecated functions (for backward
        compatibility). To use it, load the NISTf_deprecated class instead of
        the NISTf super class.
    """
    @deprecated( "user the read() function instead" )
    def loadFromFile( self, infile ):
        return self.read( infile )
    
    @deprecated( "use the write() function instead" )
    def saveToFile( self, outfile ):
        return self.write( outfile )
