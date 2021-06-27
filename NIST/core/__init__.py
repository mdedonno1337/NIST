#!/usr/bin/python
# -*- coding: UTF-8 -*-

import datetime
import inspect
import json
import os
import textwrap
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
from .functions import bindump, default_origin, get_label, decode_fgp, encode_fgp
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
    def __init__( self, init = None, *args, **kwargs ):
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
        debug.debug( "Initialization of the NIST object" )
        
        self.stdver = ""
        
        self.fileuri = None
        self.filename = None
        self.data = defDict()
        
        self.date = datetime.datetime.now().strftime( "%Y%m%d" )
        self.timestamp = int( time.time() )
        
        if init != None:
            self.load_auto( init )
            self.clean()
    
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
            
                >>> sample_all_supported_types.get_identifier()
                'be2ca2c9a173dc456afc2bbb0cbb6cf8'
        """
        try:
            return self.id
        except:
            return self.hash()
    
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
            
                >>> type( sample_all_supported_types )
                <class 'NIST.traditional.__init__.NIST'>
            
            To change the type to `NISTf` type, use the following commands:
                
                >>> from NIST import NISTf
                >>> sample_all_supported_types.changeClassTo( NISTf )
                >>> type( sample_all_supported_types )
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
                >>> n.read( "./sample/all-supported-types.an2" )
                >>> n
                NIST object, Type-01, Type-02, Type-04, Type-09, Type-10, Type-13, Type-14, Type-15, Type-16, Type-17, Type-18, Type-19, Type-20, Type-21, Type-98, Type-99
        """
        debug.debug( "Reading from file : %s" % infile )
        
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
            
                >>> from NIST import NIST
                >>> n = NIST()
                >>> n.read( "./sample/all-supported-types.an2" )
                >>> fileContent = n.get_field( "1.003" )
                >>> n.process_fileContent( fileContent )
                [2, 4, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 20, 21, 21, 98, 99]
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
            
            
            Doctest:
            
                >>> sample_type_9_10_14.delete( "9.012", 1 )
                >>> sample_type_9_10_14.hash()
                'ebf6d02d53abe91d1e6decdc5d0abae8'
                
                >>> sample_type_9_10_14.delete( "9.010" )
                >>> sample_type_9_10_14.hash()
                '1140b62ca4a59e9e821855a75953c74b'
                
                >>> sample_type_9_10_14.delete( 9, 1 )
                >>> sample_type_9_10_14.hash()
                '2077d129437f74ed151dbb793b014447'
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
    
    def delete_tags( self, tags, idc = -1 ):
        if isinstance( tags, list ):
            for tag in tags:
                self.delete_tag( tag, idc )
    
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
            
                >>> sample_type_13.is_binary( 13, 999 )
                True
                >>> sample_type_13.is_binary( 1, 3 )
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
            
                >>> sample_all_supported_types.format_field( 1, 8 )
                'ORI'
        """
        value = self.get_field( ( ntype, tagid ), idc )
        
        if self.is_binary( ntype, tagid ):
            return bindump( value )
        
        if ntype in [ 3, 4, 5, 6 ] and tagid == 4:
            return decode_fgp( value )
        
        else:
            return value
    
    def dump_record( self, ntype, idc = 0, fullname = False, maxwidth = None ):
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
            
                >>> dump = sample_all_supported_types.dump_record( 1 )
                >>> print( dump ) # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
                NIST Type-01
                    01.001 LEN: 00000349
                    01.002 VER: 0500
                    01.003 CNT: 1<US>17<RS>2<US>0<RS>4<US>1<RS>9<US>10<RS>10<US>2<RS>13<US>1<RS>14<US>3<RS>15<US>4<RS>16<US>17<RS>17<US>5<RS>18<US>13<RS>19<US>16<RS>20<US>6<RS>20<US>7<RS>21<US>8<RS>21<US>9<RS>98<US>11<RS>99<US>12
                    01.004 TOT: A
                    01.005 DAT: 20120726
                    01.006 PRY: 9
                    01.007 DAI: DAI
                    01.008 ORI: ORI
                    01.009 TCN: TCN
                    01.010 TCR: t15
                    01.011 NSR: 19.30
                    01.012 NTR: 19.30
                    01.013 DOM: DOM<US>1.00
                    01.014 GMT: 20120726111545Z
                    01.015 DCS: 0<US>ASCII<US>1
                    01.016 APS: ORG<US>APSNAME<US>1.0.0<RS>ORG2<US>APS2NAME<US>version three
                    01.017 ANM: DAI Name<US>ORI Name
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
            if maxwidth != None:
                field = printableFieldSeparator( field )
                field = "\n                ".join( textwrap.wrap( field, int( maxwidth ) ) )
            
            debug.debug( "%s: %s" % ( header, field ), 2 )
            ret.append( leveler( "%s: %s" % ( header, field ), 1 ) )
        
        return printableFieldSeparator( join( "\n", ret ) )
    
    def dump( self, fullname = False, maxwidth = None ):
        """
            Return a readable version of the NIST object. Printable on screen.
            
            :param fullname: Get the fullname of the fields.
            :type fullname: boolean
            
            :return: Printable representation of the NIST object.
            :rtype: str
            
            Usage:
            
                >>> dump = sample_all_supported_types.dump()
                >>> print( dump ) # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
                Informations about the NIST object:
                    File:    ...
                    Obj ID:  be2ca2c9a173dc456afc2bbb0cbb6cf8
                    Records: Type-01, Type-02, Type-04, Type-09, Type-10, Type-13, Type-14, Type-15, Type-16, Type-17, Type-18, Type-19, Type-20, Type-21, Type-98, Type-99
                    Class:   NIST
                <BLANKLINE>
                NIST Type-01
                    01.001 LEN: 00000349
                    01.002 VER: 0500
                    01.003 CNT: 1<US>17<RS>2<US>0<RS>4<US>1<RS>9<US>10<RS>10<US>2<RS>13<US>1<RS>14<US>3<RS>15<US>4<RS>16<US>17<RS>17<US>5<RS>18<US>13<RS>19<US>16<RS>20<US>6<RS>20<US>7<RS>21<US>8<RS>21<US>9<RS>98<US>11<RS>99<US>12
                    01.004 TOT: A
                    01.005 DAT: 20120726
                    01.006 PRY: 9
                    01.007 DAI: DAI
                    01.008 ORI: ORI
                    01.009 TCN: TCN
                    01.010 TCR: t15
                    01.011 NSR: 19.30
                    01.012 NTR: 19.30
                    01.013 DOM: DOM<US>1.00
                    01.014 GMT: 20120726111545Z
                    01.015 DCS: 0<US>ASCII<US>1
                    01.016 APS: ORG<US>APSNAME<US>1.0.0<RS>ORG2<US>APS2NAME<US>version three
                    01.017 ANM: DAI Name<US>ORI Name
                NIST Type-02 (IDC 0)
                    02.001 LEN: 00000023
                    02.002 IDC: 0
                NIST Type-04 (IDC 1)
                    04.001 LEN: 104277
                    04.002 IDC: 1
                    04.003 IMP: 8
                    04.004 FGP: 0/1/2/3/4/5
                    04.005 ISR: 1
                    04.006 HLL: 1608
                    04.007 VLL: 1000
                    04.008 CGA: 1
                    04.999    : FFA0FFA8 ... 01DFFFA1 (104259 bytes)
                NIST Type-09 (IDC 10)
                    09.001 LEN: 00000548
                    09.002 IDC: 10
                    09.003 IMP: 20
                    09.004 FMT: S
                    09.005    : Originator's Name<US>E<US>@N
                    09.006    : 0<RS>20
                    09.007    : T<US>PW<RS>T<US>WN<RS>U<US>UWHRL
                    09.008    : 22221000<RS>10002222
                    09.009    : 10003000<RS>10003000
                    09.010    : 3
                    09.011    : 1
                    09.012    : 1<US>09880910180<US>2<US>A<US>2,3<US>3,5<RS>2<US>59781010100<US>0<US>B<US>1,3<US>3,4<RS>3<US>54016007359<US>1<US>D<US>1,5<US>2,4
                    09.300 ROI: 983<US>983<US>75<US>100<US>0,0-0,1-0,12
                    09.302 FPP: 0<US>UNK<US><US><RS>1<US>DST<US><US>
                    09.308 RQM: 000000000000000000000000
                    09.309 RQF: 41<US>UNC
                    09.310 RFM: 000102030405060708090A0B0C0D0E0F1011121314151617
                    09.311 RFF: 41<US>UNC
                    09.312 RWM: 010203040506070809XX1011121314010203040506070809XX
                    09.313 RWF: 40<US>UNC
                    09.314 TRV: N
                    09.322 CDR: 1<US>2<US>10<US>50<RS>L<US>R<US>5<US>
                    09.323 CPR: 0<US>-70<US>100<US><RS>0<US>200<US>0<US>
                NIST Type-10 (IDC 2)
                    10.001 LEN: 00069624
                    10.002 IDC: 2
                    10.003 IMT: FACE
                    10.004 SRC: SRC
                    10.005 PHD: 20120730
                    10.006 HLL: 480
                    10.007 VLL: 640
                    10.008 SLC: 2
                    10.009 THPS: 299
                    10.010 TVPS: 299
                    10.011 CGA: JPEGB
                    10.012 CSP: RGB
                    10.013 SAP: 20
                    10.014 FIP: 1<US>480<US>1<US>480<US>H
                    10.015 FPFI: C<US>2<US>0<US>0<US>1<US>1
                    10.016 SHPS: 72
                    10.017 SVPS: 72
                    10.018 DIST: Pincushion<US>E<US>Mild
                    10.019 LAF: F<RS>H<RS>R
                    10.020 POS: A
                    10.021 POA: 180
                    10.023 PAS: VENDOR<US>Vendor Description
                    10.024 SQS: 0<US>0000<US>1<RS>254<US>FFFF<US>65535
                    10.025 SPA: -180<US>0<US>180<US>0<US>45<US>90
                    10.026 SXS: MOUTH OPEN<RS>EYES AWAY<RS>SQUINTING<RS>BEARD
                    10.027 SEC : MUL
                    10.028 SHC: STR<RS>RED
                    10.029 FFP: 1<US>2.1<US>5<US>9<RS>2<US>obs<US>1<US>1
                    10.030 DMM: OBSERVED
                    10.031 TMC: 5
                    10.032 3DF: 1<US>2.1<US>5<US>9<US>9<RS>2<US>obs<US>1<US>1<US>1
                    10.033 FEC: eyetop<US>3<US>0<US>0<US>1<US>1<US>0<US>4<RS>chin<US>3<US>5<US>5<US>10<US>24<US>3<US>5
                    10.038 COM: This transaction represents test data used to test the ANSI/NIST 1-2011 Conformace Test Suite Developed by NIST for the BioCTS
                    10.044 ITX: AGE<RS>ILLUM
                    10.045 OCC: T<US>H<US>3<US>0<US>0<US>1<US>1<US>100<US>100<RS>S<US>O<US>3<US>0<US>0<US>1<US>1<US>100<US>100
                    10.200    : USER DEFINED
                    10.902 ANN: 20120731000000Z<US>NAV<US>OWN<US>PRO<RS>20120801000000Z<US>NAV2<US>OWN2<US>PRO2
                    10.903 DUI: M213456789012
                    10.904 MMS: Make<US>Model<US>Serial Number
                    10.993 SAN: Source Agency Name
                    10.995 ASC: 1<US>1<RS>2<US>99
                    10.996 HAS: 6A92879FDAAFBAC0F554A8992C5E3DCD351CFF2BC3F9ADAFF355F97FB4ADB388
                    10.997 SOR: 1<US>1<RS>2<US>
                    10.998 GEO: 20120725120000Z<US>39<US>37<US>45.8394<US>79<US>57<US>21.96<US>380<US>WGS84<US>17S<US>589588<US>4387146<US>211 Walnut Street<US>UTM-MGRS<US>UTM with MGRS latitude band
                    10.999 DATA: FFD8FFE0 ... 94D8FFD9 (68453 bytes)
                NIST Type-13 (IDC 1)
                    13.001 LEN: 00876647
                    13.002 IDC: 1
                    13.003 IMP: 4
                    13.004 SRC: SRC
                    13.005 LCD: 20120730
                    13.006 HLL: 1608
                    13.007 VLL: 1000
                    13.008 SLC: 0
                    13.009 THPS: 72
                    13.010 TVPS: 72
                    13.011 CGA: PNG
                    13.012 BPX: 8
                    13.013 FGP: 0<RS>19
                    13.014 SPD: 0<US>FV1
                    13.015 PPC: FV1<US>NA<US>100<US>100<US>100<US>100
                    13.016 SHPS: 990
                    13.017 SVPS: 990
                    13.020 COM: Comment
                    13.024 LQM: 0<US>90<US>0000<US>1<RS>19<US>95<US>FFFF<US>65535
                    13.999 DATA: 89504E47 ... AE426082 (876377 bytes)
                NIST Type-14 (IDC 3)
                    14.001 LEN: 00050620
                    14.002 IDC: 3
                    14.003 IMP: 0
                    14.004 SRC: SRC
                    14.005 FCD: 20120730
                    14.006 HLL: 804
                    14.007 VLL: 1000
                    14.008 SLC: 2
                    14.009 THPS: 193
                    14.010 TVPS: 193
                    14.011 CGA: WSQ20
                    14.012 BPX: 8
                    14.013 FGP: 19
                    14.014 PPD: 1<US>EJI
                    14.015 PPC: FV1<US>NA<US>100<US>105<US>100<US>105
                    14.016 SHPS: 197
                    14.017 SVPS: 197
                    14.018 AMP: 1<US>XX
                    14.020 COM: Comment
                    14.022 NQM: 1<US>2
                    14.023 SQM: 1<US>0<US>0000<US>1
                    14.024 FQM: 1<US>0<US>0000<US>1
                    14.025 ASEG: 1<US>3<US>0<US>0<US>35<US>55<US>12<US>85
                    14.026 SCF: 1
                    14.027 SIF: Y
                    14.030 DMM: UNKNOWN
                    14.031 FAP: 10
                    14.999 DATA: FFA0FFA8 ... 917FFFA1 (50256 bytes)
                NIST Type-15 (IDC 4)
                    15.001 LEN: 00050629
                    15.002 IDC: 4
                    15.003 IMP: 10
                    15.004 SRC: SRC
                    15.005 PCD: 20120730
                    15.006 HLL: 804
                    15.007 VLL: 1000
                    15.008 SLC: 2
                    15.009 THPS: 197
                    15.010 TVPS: 197
                    15.011 CGA: WSQ20
                    15.012 BPX: 8
                    15.013 FGP: 20
                    15.016 SHPS: 197
                    15.017 SVPS: 197
                    15.018 AMP: 21<US>XX
                    15.020 COM: Comment
                    15.024 PQM: 84<US>0<US>0000<US>1
                    15.030 DMM: UNKNOWN
                    15.998 GEO: 20120725120000Z<US>39<US>37<US>45.8394<US>79<US>57<US>21.96<US>380<US>WGS84<US>19C<US>589588<US>4387146<US>211 Walnut Street<US>UTM-MGRS<US>UTM with MGRS latitude band
                    15.999 DATA: FFA0FFA8 ... 917FFFA1 (50256 bytes)
                NIST Type-16 (IDC 17)
                    16.001 LEN: 00051455
                    16.002 IDC: 17
                    16.003 UDI: ear
                    16.004 SRC: NIST
                    16.005 UTD: 20150101
                    16.006 HLL: 302
                    16.007 VLL: 568
                    16.008 SLC: 1
                    16.009 THPS: 500
                    16.010 TVPS: 500
                    16.011 CGA: JPEGB
                    16.012 BPX: 8
                    16.013 CSP: UNK
                    16.999 DATA: FFD8FFE0 ... E47FFFD9 (51296 bytes)
                NIST Type-17 (IDC 5)
                    17.001 LEN: 00107497
                    17.002 IDC: 5
                    17.003 ELR: 0
                    17.004 SRC: SRC
                    17.005 ICD: 20120730
                    17.006 HLL: 449
                    17.007 VLL: 312
                    17.008 SLC: 2
                    17.009 THPS: 29
                    17.010 TVPS: 29
                    17.011 CGA: PNG
                    17.012 BPX: 8
                    17.013 CSP: UNK
                    17.014 RAE: 0000
                    17.015 RAU: 0000
                    17.016 IPC: 0<US>0<US>0
                    17.017 DUI: MABCDEF123456
                    17.019 MMS: MAK<US>MOD<US>SER
                    17.020 ECL: XXX
                    17.021 COM: COM
                    17.022 SHPS: 29
                    17.023 SVPS: 29
                    17.024 IQS: 0<US>0000<US>1
                    17.025 EAS: DEFINED
                    17.026 IRD: 100
                    17.027 SSV: 500<US>510
                    17.028 DME: MA
                    17.030 DMM: UNKNOWN
                    17.031 IAP: 20
                    17.032 ISF: 1
                    17.033 IPB: C<US>2<US>50<US>50<US>30<US>40
                    17.034 ISB: C<US>2<US>50<US>50<US>30<US>40
                    17.035 UEB: P<US>3<US>50<US>50<US>30<US>40<US>10<US>15
                    17.036 LEB: P<US>3<US>50<US>50<US>30<US>40<US>10<US>15
                    17.037 NEO: T<US>L<US>3<US>50<US>30<US>40<US>10<US>45<US>15
                    17.040 RAN: 150
                    17.041 GAZ: 5
                    17.999 DATA: 89504E47 ... AE426082 (106971 bytes)
                NIST Type-18 (IDC 13)
                    18.001 LEN: 00278745
                    18.002 IDC: 13
                    18.003 DLS: 1<US>G<US>0<US>NIST<US>Joseph Konczal, 301-975-3285, joe.konczal@nist.gov<US>USA<US>NONE
                    18.004 SRC: MDNISTIMG
                    18.005 NAL: 1
                    18.006 SDI: 1<US>F<US>20000101<US>20000101<US>Caucasian<US><US><US>
                    18.007 COPR: 1
                    18.008 VRS: 1
                    18.009 PED: Pedigree ID<US>Member<US>K<US>Sample ID<US>0<US>1<US>Pedigree Comment
                    18.010 STY: 0<US>NS
                    18.011 STI: 0<RS>1<RS>2<RS>3<RS>4
                    18.012 SCM: blood donation
                    18.013 SCD: 20000101120000Z
                    18.014 PSD: 20010101120000Z
                    18.015 DPD: 0<US><US>NIST_SRM2391b_9947A<US><US>This is an anonymous sample used to populate these examples of DNA records.
                    18.016 STR: 0<US>48<US>1<US>1<US>1<US>13<US>13<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>24<US>1<US>1<US>1<US>30<US>30<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>45<US>1<US>1<US>1<US>10<US>11<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>3<US>1<US>1<US>1<US>10<US>12<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>31<US>1<US>1<US>1<US>14<US>15<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>62<US>1<US>1<US>1<US>8<US>9.3<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>10<US>1<US>1<US>1<US>11<US>11<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>12<US>1<US>1<US>1<US>11<US>12<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>27<US>1<US>1<US>1<US>19<US>23<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>17<US>1<US>1<US>1<US>14<US>15<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>64<US>1<US>1<US>1<US>17<US>18<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>63<US>1<US>1<US>1<US>8<US>8<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>15<US>1<US>1<US>1<US>15<US>19<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>1<US>1<US>1<US>1<US>1.1<US>99.9<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>40<US>1<US>1<US>1<US>11<US>11<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US><RS>0<US>54<US>1<US>1<US>1<US>23<US>24<US><US><US><US>?<US>8<US>Identifiler<US>Life Technologies<US>
                    18.017 DMD: AGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCT<US>AGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCTAGCTRYMKSWHBVDN-AGCT<US>1<US>2<US>10<US>20<US>3<US>7
                    18.018 UDP: <US><RS><US>
                    18.019 EPD: 3939391F ... 67673D3D (276036 bytes)
                    18.020 DGD: 1
                    18.021 GAP: 1<US>1.1,20<US>0
                    18.022 COM: Comments
                    18.023 EPL: Ref<US>Stor<US>Desc<US>BASE64VALUE<US>BASE64VALUE<RS>Ref2<US>Str2<US>Desc2<US>BASE64VALUE<US>BASE64VALUE
                NIST Type-19 (IDC 16)
                    19.001 LEN: 00000102
                    19.002 IDC: 16
                    19.003 IMP: 29
                    19.004 SRC: Source Agency
                    19.005 PCD: 20150625
                    19.013 FGP: 60
                    19.018 AMP: 61<US>UP<RS>62<US>UP
                NIST Type-20 (IDC 6)
                    20.001 LEN: 00000243
                    20.002 IDC: 6
                    20.003 CAR: S
                    20.004 SRC: Source Agency
                    20.014 AQS: 13<US>description of analog to digital equipment and sample rate<US><US>
                    20.015 SFT: png<US>
                    20.016 SEG: 1<US>Reference<US>
                    20.019 TIX: 00:00:00.000<US>00:00:00.001<RS>00:20:05.000<US>01:00:00.500
                    20.021 SRN: 1
                    20.994 EFR: Reference
                NIST Type-20 (IDC 7)
                    20.001 LEN: 00000157
                    20.002 IDC: 7
                    20.003 CAR: S
                    20.004 SRC: Source Agency
                    20.014 AQS: 23<US><US>format description<US>
                    20.015 SFT: png<US>
                    20.019 TIX: 00:00:00.000<US>02:30:57.000
                    20.021 SRN: 2
                    20.994 EFR: Reference
                NIST Type-21 (IDC 8)
                    21.001 LEN: 00000125
                    21.002 IDC: 8
                    21.004 SRC: Source Agency
                    21.015 AFT: DAT<US>Decoding Instructions
                    21.016 SEG: 1<US>Reference<US>
                    21.021 ACN: 1
                    21.994 EFR: Reference
                NIST Type-21 (IDC 9)
                    21.001 LEN: 00000126
                    21.002 IDC: 9
                    21.004 SRC: Source Agency
                    21.015 AFT: DAT<US>Decoding Instructions
                    21.016 SEG: 99<US>Reference<US>
                    21.021 ACN: 2
                    21.994 EFR: Reference
                NIST Type-98 (IDC 11)
                    98.001 LEN: 00000229
                    98.002 IDC: 11
                    98.003 DFO: 0000
                    98.004 SRC: Source Agency
                    98.005 DFT: Data Format Type
                    98.006 DCD: 20150520000000Z
                    98.900 ALF: Added<US><US>8,21.016,NA,NA<US>BioCTS Testing<US><RS>Deleted<US><US>6,20.016,NA,-NOP<US>BioCTS Testing<US>2
                    98.901 ARN: 1
                    98.993 SAN: Source Agency Name
                NIST Type-99 (IDC 12)
                    99.001 LEN: 00000166
                    99.002 IDC: 12
                    99.004 SRC: Source Agency
                    99.005 BCD: 20150101
                    99.100 HDV: 0101
                    99.101 BTY: 00000000
                    99.102 BDQ: 100<US>FF00<US>65000<RS>255<US>000A<US>1024
                    99.103 BFO: 0000
                    99.104 BFT: 0000
                    99.999 DATA: 42444244 ... 44415441 (7 bytes)
        """
        debug.debug( "Dumping NIST" )
        
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
                ret.append( self.dump_record( ntype, idc, fullname, maxwidth ) )
        
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
        """
        #TODO: Add documentation
        
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
        debug.debug( "Cleaning the NIST object" )
        
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
            
                >>> sample_all_supported_types.get_field( "1.002" )
                '0500'
        """
        ntype, tagid = tagSplitter( tag )
        
        idc = self.checkIDC( ntype, idc )
    
        try:
            return self.data[ ntype ][ idc ][ tagid ]
        except:
            return None
    
    def set_field( self, tag, value, idc = -1 ):
        """
            Set the value of a specific tag in the NIST object. If the value is
            None, the function does not set the field.
            
            :param tag: Tag to set.
            :type tag: int
            
            :param value: Value to set.
            :type value: str (or int)
            
            :param idc: IDC value.
            :type idc: int
            
            Usage:
            
                >>> sample_all_supported_types.set_field( "1.002", "0300" )
                >>> dump = sample_all_supported_types.dump_record( 1 )
                >>> print( dump ) # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
                NIST Type-01
                    01.001 LEN: 00000349
                    01.002 VER: 0300
                    01.003 CNT: 1<US>17<RS>2<US>0<RS>4<US>1<RS>9<US>10<RS>10<US>2<RS>13<US>1<RS>14<US>3<RS>15<US>4<RS>16<US>17<RS>17<US>5<RS>18<US>13<RS>19<US>16<RS>20<US>6<RS>20<US>7<RS>21<US>8<RS>21<US>9<RS>98<US>11<RS>99<US>12
                    01.004 TOT: A
                    ...
        """
        if value == None:
            try:
                self.delete_tag( tag, idc )
            except:
                pass
            
            return
        
        else:
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
            
            if ntype in [ 3, 4, 5, 6 ] and tagid == 4:
                value = encode_fgp( value )
                
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
            
                >>> sample_all_supported_types.get_fields( [ "1.002", "1.004" ] )
                ['0500', 'A']
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
           
                >>> sample_type_1.data.keys()
                [1, 2]
                >>> sample_type_1.add_ntype( 18 )
                >>> sample_type_1.data.keys()
                [1, 2, 18]
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
            self.add_ntype( ntype )
        
        if idc in self.get_idc( ntype ):
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
            
                >>> sample_all_supported_types.get_ntype()
                [1, 2, 4, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 98, 99]
        """
        lst = []
        
        for ntype in sorted( self.data.keys() ):
            if( len( self.data[ ntype ] ) ):
                lst.append( ntype )
        
        return lst
    
    def get_idc( self, ntype ):
        """
            Return all IDC for a specific ntype.
            
                >>> sample_all_supported_types.get_idc( 4 )
                [1]
                
                >>> sample_type_4_tpcard.get_idc( 4 )
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
                
                >>> sample_all_supported_types.get_idc( 0 ) +IGNORE_EXCEPTION_DETAIL
                Traceback (most recent call last):
                ntypeNotFound
        """
        if ntype not in self.data.keys():
            raise ntypeNotFound
        else:
            return sorted( self.data[ ntype ].keys() )
    
    def get_tagsid( self, ntype, idc = -1 ):
        """
            Get the list of tags for a particular ntype and idc.
            
                >>> sample_all_supported_types.get_tagsid( 1, 0 )
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
                
                >>> sample_all_supported_types.get_tagsid( 1 )
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
                
                >>> sample_type_4_tpcard.get_tagsid( 4 ) +IGNORE_EXCEPTION_DETAIL
                Traceback (most recent call last):
                needIDC
                
                >>> sample_type_4_tpcard.get_tagsid( 4, 1 )
                [1, 2, 3, 4, 5, 6, 7, 8, 999]
                
                >>> sample_all_supported_types.get_tagsid( 0 ) +IGNORE_EXCEPTION_DETAIL
                Traceback (most recent call last):
                ntypeNotFound
        """
        idc = self.checkIDC( ntype, idc )
        return sorted( self.data[ ntype ][ idc ].keys() )
    
    def get_all_tagid( self ):
        """
            Get the list of all fields in the format ( ntype, idc, tagid ).
            
            :return: List of ( ntype, idc, tagid ).
            :rtype: List of tuples
            
            Usage:
            
                >>> sample_type_1.get_all_tagid()
                [(1, 0, 1), (1, 0, 2), (1, 0, 3), (1, 0, 4), (1, 0, 5), (1, 0, 6), (1, 0, 7), (1, 0, 8), (1, 0, 9), (1, 0, 10), (1, 0, 11), (1, 0, 12), (1, 0, 13), (1, 0, 14), (1, 0, 15), (1, 0, 16), (1, 0, 17), (2, 0, 1), (2, 0, 2)]
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
            and if the value is numeric. If the IDC is "-1", then the value is
            searched in the ntype field and returned only if the value is
            unique; if multiple IDC are stored for the specific ntype, an
            exception is raised.
            
            :param ntype: ntype to search in
            :type ntype: int
            
            :param idc: idc to check
            :type idc: int
            
            :return: checked IDC
            :rtype: int
            
            :raise recordNotFound: if the ntype is not found
            :raise idcNotFound: if the IDC is not valid
            :raise intIDC: if the IDC can not be casted to int
            
                >>> sample_type_1.checkIDC( 1, 0 )
                0
                
                >>> sample_type_1.checkIDC( 1, -1 )
                0
                
                >>> sample_type_1.checkIDC( 1, 1 )
                Traceback (most recent call last):
                    ...
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
    
    def has_idc( self, ntype, idc ):
        """
            Check if the particular ntype has the IDC passed in parameter. If
            the IDC value is '-1', i.e. not defined, the function return True.
            
            :param ntype: ntype to serach in
            :type ntype: int
            
            :param idc: IDC to search
            :type idc: int
            
            :return: Is the IDC in the ntype record
            :rtype: boolean
        """
        if idc == -1:
            return True
        else:
            return idc in self.data[ ntype ]
    
    def has_tag( self, tag, idc = -1 ):
        return self.get_field( tag, idc ) != None
    
    def __str__( self ):
        """
            Return the printable version of the NIST object.
            
                >>> print( sample_type_1 ) # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
                Informations about the NIST object:
                    File:    ...
                    Obj ID:  d42ad80daed390c357667d1e85164298
                    Records: Type-01, Type-02
                    Class:   NISTf
                <BLANKLINE>
                NIST Type-01
                    01.001 LEN: 00000264
                    01.002 VER: 0500
                    01.003 CNT: 1<US>1<RS>2<US>0
                    01.004 TOT: A
                    01.005 DAT: 20120726
                    01.006 PRY: 9
                    01.007 DAI: DAI
                    01.008 ORI: ORI
                    01.009 TCN: TCN
                    01.010 TCR: t15
                    01.011 NSR: 00.00
                    01.012 NTR: 00.00
                    01.013 DOM: DOM<US>1.00
                    01.014 GMT: 20120726111545Z
                    01.015 DCS: 0<US>ASCII<US>1
                    01.016 APS: ORG<US>APSNAME<US>1.0.0<RS>ORG2<US>APS2NAME<US>version three
                    01.017 ANM: DAI Name<US>ORI Name
                NIST Type-02 (IDC 0)
                    02.001 LEN: 00000023
                    02.002 IDC: 0
                
                >>> from NIST import NISTf
                >>> n = NISTf()
                >>> print n
                NIST object not initialized...
        """
        try:
            return self.dump()
        
        except ( recordNotFound, ntypeNotFound ):
            return "NIST object not initialized..."
    
    def __repr__( self ):
        """
            Return unambiguous description.
            
                >>> sample_type_1
                NIST object, Type-01, Type-02
        """
        return "NIST object, " + ", ".join( [ "Type-%02d" % x for x in self.get_ntype() ] )
    
    def get( self ):
        """
            Get a copy of the current NIST object.
            
            :return: A new NIST object.
            :rtype: NIST
            
            Usage:
            
                >>> tmp = sample_type_1.get()
                >>> tmp == sample_type_1
                False
            
            .. note::
            
                Since the function return a copy of the current object, the two
                objects are separate in memory, allowing to modify one and not
                the other (reason why `tmp` is not equal to `n`, even if the
                content is the same).
        """
        return deepcopy( self )
    
    def is_initialized( self ):
        try:
            self.get_field( "1.003" )
            return True
        
        except:
            return False
