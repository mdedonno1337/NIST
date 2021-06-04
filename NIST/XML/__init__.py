#!/usr/bin/python
# -*- coding: UTF-8 -*-

from collections import OrderedDict

import cStringIO
import datetime
import os
import time
import xmltodict

from MDmisc import fuckit
from MDmisc.elist import ifany
from MDmisc.eOrderedDict import eOrderedDictParser
from MDmisc.logger import debug
from MDmisc.string import join
from MDmisc.RecursiveDefaultDict import defDict

from ..core import NIST as NISTcore
from ..core.config import RS, US
from ..core.exceptions import needStringValue
from ..core.functions import tagSplitter, get_xml_tag

class NIST( NISTcore ):
    def load_auto( self, p ):
        if isinstance( p, ( str, unicode ) ):
            if ifany( [ "<", ">", "<?xml" ], p ):
                self.load( p )
            
            else:
                self.read( p )
        
        elif isinstance( p, ( cStringIO.OutputType ) ):
            self.load( p.getvalue() )
        
        elif isinstance( p, ( file ) ):
            self.load( p.read() )
    
    def load( self, data ):
        self.xmldata = xmltodict.parse( data )[ "itl:NISTBiometricInformationExchangePackage" ]
        self.xmldata = eOrderedDictParser( self.xmldata )
        
        #    NIST Type01
        debug.debug( "Type-01 parsing", 1 )
        
        self.add_ntype( 1 )
        self.add_idc( 1, 0 )
        
        t01 = get_xml_tag( self.xmldata, [ "PackageInformationRecord", "Transaction" ] )
        
        major = get_xml_tag( t01, "TransactionMajorVersionValue" )
        minor = get_xml_tag( t01, "TransactionMinorVersionValue" )
        self.set_field( "1.002", "%s%s" % ( major, minor ) )
        
        self.set_field( "1.004", get_xml_tag( t01, "TransactionCategoryCode" ), 0 )
        self.set_field( "1.005", get_xml_tag( t01, [ "TransactionDate", "Date" ] ), 0 )
        
        self.set_field( "1.006", get_xml_tag( t01, "TransactionPriorityValue" ), 0 )
            
        self.set_field( "1.007", get_xml_tag( t01, [ "TransactionDestinationOrganization", "OrganizationIdentification", "IdentificationID" ] ), 0 )
        self.set_field( "1.008", get_xml_tag( t01, [ "TransactionOriginatingOrganization", "OrganizationIdentification", "IdentificationID" ] ), 0 )
        
        DAN = get_xml_tag( t01, [ "TransactionDestinationOrganization", "OrganizationName" ], "" )
        OAN = get_xml_tag( t01, [ "TransactionOriginatingOrganization", "OrganizationName" ], "" )
        if DAN != "" or OAN != "":
            self.set_field( "1.017", join( US, [ DAN, OAN ] ), 0 )
        
        self.set_field( "1.009", get_xml_tag( t01, [ "TransactionControlIdentification", "IdentificationID" ] ), 0 )
        
        self.set_field( "1.010", get_xml_tag( t01, [ "TransactionControlReferenceIdentification", "IdentificationID" ] ), 0 )
        
        self.set_field( "1.011", get_xml_tag( t01, [ "TransactionImageResolutionDetails", "NativeScanningResolutionValue" ] ), 0 )
        self.set_field( "1.012", get_xml_tag( t01, [ "TransactionImageResolutionDetails", "NominalTransmittingResolutionValue" ] ), 0 )
        
        with fuckit:
            DNM = get_xml_tag( t01, [ "TransactionDomain", "OrganizationName" ] )
            DVN = get_xml_tag( t01, [ "TransactionDomain", "DomainVersionNumberIdentification", "IdentificationID" ] )
            
            self.set_field( "1.013", DNM + US + DVN, 0 )
        
        self.set_field( "1.014", get_xml_tag( t01, [ "TransactionUTCDate/DateTime" ] ), 0 )
        
        with fuckit:
            CSD = get_xml_tag( t01, "TransactionCharacterSetDirectory" )
            CSN = get_xml_tag( CSD, "CharacterSetCommonNameCode" )
            CSI = get_xml_tag( CSD, "CharacterSetIndexCode" )
            CSV = get_xml_tag( CSD, [ "CharacterSetVersionIdentification", "IdentificationID" ] )
            
            self.set_field( "1.015", CSI + US + CSN + US + CSV, 0 )
        
        #   NIST Type02
        debug.debug( "Type-02 parsing", 1 )
        
        self.add_ntype( 2 )
        self.add_idc( 2, 0 )
        
        t02 = get_xml_tag( self.xmldata, "PackageDescriptiveTextRecord" )
        
        if not isinstance( t02, list ):
            t02 = [ t02 ]
        
        for t02b in t02:
            if t02b != None:
                idc = int( get_xml_tag( t02b, [ "ImageReferenceIdentification", "IdentificationID" ] ) )
                self.set_field( "2.002", idc, idc )
            
            with fuckit:
                i = 3
                for key, values in get_xml_tag( t02b, "UserDefinedDescriptiveDetail" ).iteritems():
                    for detail, value in values.iteritems():
                        self.set_field( ( 2, i ), detail + US + value )
                        i += 1
    
    def get_namespaces_list( self ):
        """
            Get the list of namespaces available in the NIST object. The list
            of namespaces should only contain one used an usefull namespaces,
            but since we dont know it, this function will return the entire
            list, so the NIST.function.get_xml_tag() function can iterate over
            it.
        """
        ret = []
        
        for ns in self.xmldata.keys():
            if ns.startswith( "@xmlns" ):
                ret.append( ns.split( ":" )[ 1 ] )
        
        return ret
    
    ############################################################################
    # 
    #    Set fields
    # 
    ############################################################################
    
    def set_field( self, tag, value, idc = -1 ):
        if isinstance( value, OrderedDict ):
            raise needStringValue
        
        else:
            return super( NIST, self ).set_field( tag, value, idc )
