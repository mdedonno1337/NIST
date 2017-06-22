#!/usr/bin/python
# -*- coding: UTF-8 -*-

import datetime
import inspect
import json
import os
import time

from collections import OrderedDict
from copy import deepcopy

from MDmisc.binary import myhex, hex_to_int
from MDmisc.boxer import boxer
from MDmisc.deprecated import deprecated
from MDmisc.elist import replace_r, ifany
from MDmisc.logger import debug
from MDmisc.map_r import map_r
from MDmisc.multimap import multimap
from MDmisc.RecursiveDefaultDict import defDict
from MDmisc.string import join, upper, stringIterator, split_r

from .binary import binary_fields
from .config import RS, US
from .exceptions import *
from .functions import bindump, default_origin, get_label
from .voidType import voidType
from ..core.functions import leveler, printableFieldSeparator, split, tagSplitter

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
        
        self.stdver = ""
        
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
        self.id = str( id )
    
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
                <class 'NIST.core.__init__.NIST'>
            
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
        
        if data[ 0 ] == "{" and data[ -1 ] == "}":
            self.from_json( data )
        
        else:
            self.load( data )
    
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
            :func:`~NIST.core.NIST.merge` function.
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
        if isinstance( ntype, str ):
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
    
    def is_binary( self, ntype, tagid ):
        """
            Check if the particular field ( ntype, tagid ) is stored as binary
            data or not.
            
            :param ntype: ntype
            :type ntype: int
            
            :param tagid: field id
            :type tagid: ind
            
            Usage:
            
                >>> n.is_binary( 13, 999 )
                True
                >>> n.is_binary( 1, 3 ) 
                False
        """
        if tagid == 999:
            return True
        
        else:
            return ( ntype, tagid ) in binary_fields
    
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
        
        if self.is_binary( ntype, tagid ):
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
                    02.001 LEN: 00000038
                    02.002 IDC: 0
                    02.004    : ...
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
    
    def to_dict( self ):
        """
            Return a dictionnary from the variable NIST.data.
            
            :return: Data
            :rtype: dict
        """
        return self.data.to_dict()
    
    def to_json( self, return_bin = True, **options ):
        """
            Export the content of the NIST object to JSON.
            
            :param return_bin: Include binary data in the JSON string. 
            :type return_bin: boolean
            
            :param options: Options to pass to the :func:`json.dumps()` function.
            :type options: kwargs
            
            :return: JSON string.
            :rtype: str
            
            .. note:: If the binary data is included in the JSON string, the data will be exported as hexadecimal representation.
            
        """
        self.clean()
        databis = defDict()
        for ntype, idc, tagid in self.get_all_tagid():
            value = self.get_field( ( ntype, tagid ), idc )
            
            if self.is_binary( ntype, tagid ):
                if return_bin:
                    databis[ ntype ][ idc ][ tagid ] = join( multimap( [ ord, myhex ], value ) )
                
            else:
                databis[ ntype ][ idc ][ tagid ] = value 
        
        databis = databis.to_dict()
        
        return json.dumps( databis, **options )
    
    def from_json( self, data ):
        """
            Load the data from a JSON file. If some binary filds are present in
            the JSON file, the data will be converted from hexadecimal format to
            binary.
            
            :param data: JSON file or JSON string to import.
            :type data: str
            
            :return: NIST object.
            :rtype: NIST object
            
            Usage:
            
                >>> from NIST import NIST
                >>> n = NIST()
                >>> n.from_json( "sample/mark-pairing-nobinary.json" )
                >>> n
                NIST object, Type-01, Type-02, Type-09, Type-13
        """
        if isinstance( data, str ) and os.path.isfile( data ):
            with open( data ) as fp:
                data = json.load( fp )
        
        elif isinstance( data, str ):
            data = json.loads( data )
        
        self.data = defDict()
        
        for ntype, idcs in data.iteritems():
            ntype = int( ntype )
            self.add_ntype( ntype )
             
            for idc, tagids in idcs.iteritems():
                idc = int( idc )
                self.add_idc( ntype, idc )
                 
                for tagid, value in tagids.iteritems():
                    tagid = int( tagid )
                    
                    if self.is_binary( ntype, tagid ):
                        value = join( multimap( [ hex_to_int, chr ], split( value, 2 ) ) )
                    
                    self.set_field( ( ntype, tagid ), value, idc )
    
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
                        
    def patch_to_standard( self ):
        return
        
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
        ntype, tagid = tagSplitter( tag )
        
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
        ntype, tagid = tagSplitter( tag )
        
        try:
            idc = self.checkIDC( ntype, idc )
        
        except recordNotFound:
            try:
                self.add_ntype( ntype )
                self.add_idc( ntype, idc )
            except:
                raise recordNotFound
        
        except idcNotFound:
            try:
                self.add_idc( ntype, idc )
            except:
                raise idcNotFound
        
        if not isinstance( value, str ):
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
            
            .. seealso:: :func:`~NIST.core.NIST.set_field`
        """
        for field in fields:
            self.set_field( field, value, idc )
    
    def get_field_multi_idc( self, tag, idcs ):
        """
            Get a field for multiples IDC.
            
            :param tag: Tag to retrieve.
            :type tag: str (or tuple)
            
            :param idcs: List of IDC to process.
            :type idcs: list of int
            
            :return: List of fields value for all IDC passed in argument.
            :rtype: list of str 
        """
        return [ self.get_field( tag, idc ) for idc in idcs ]
    
    def get_fields_multi_idc( self, tags, idcs ):
        """
            Get multiples fields for multiples IDC.
            
            :param tag: List of tags to retrieve.
            :type tag: list of str (or list of tuple)
            
            :param idcs: List of IDC to process.
            :type idcs: list of int
            
            :return: List of fields value for all tagid for all IDC passed in argument.
            :rtype: list of list of str
        """
        return [ self.get_fields( tags, idc ) for idc in idcs ]
    
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
            provided by the `NIST.core.voidType` module.
            
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
    
    def add_Type02( self, idc = 0 ):
        """
            Add the Type-02 record to the NIST object, and set the Date.
        """
        ntype = 2
        
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
    
    def get_tagsid( self, ntype, idc ):
        return sorted( self.data[ ntype ][ idc ].keys() )
    
    def get_all_tagid( self ):
        """
            Get the list of all fields in the format ( ntype, idc, tagid ).
            
            :return: List of ( ntype, idc, tagid ).
            :rtype: List of tuples
            
            Usage:
            
                >>> n.get_all_tagid()
                [(1, 0, 1), (1, 0, 2), (1, 0, 3), (1, 0, 4), (1, 0, 5), (1, 0, 6), (1, 0, 7), (1, 0, 8), (1, 0, 9), (1, 0, 11), (1, 0, 12), (2, 0, 1), (2, 0, 2), (2, 0, 4)]
        """
        lst = []
        for ntype, idcs in self.data.iteritems():
            for idc, tagids in idcs.iteritems():
                for tagid in tagids.keys():
                    lst.append( ( ntype, idc, tagid ) )
        
        return lst
    
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
                    02.001 LEN: 00000038
                    02.002 IDC: 0
                    02.004    : ...
        """
        try:
            return self.dump()
        
        except recordNotFound:
            return "NIST object not initialized..."
    
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
