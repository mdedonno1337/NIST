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
from ..core.functions import tagSplitter

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
        
        t01 = self.xmldata.get_r( "itl:PackageInformationRecord/biom:Transaction" )
        
        major = t01.get( "biom:TransactionMajorVersionValue" )
        minor = t01.get( "biom:TransactionMinorVersionValue" )
        self.set_field( "1.002", "%s%s" % ( major, minor ) )
        
        self.set_field( "1.004", t01.get( "biom:TransactionCategoryCode" ), 0 )
        self.set_field( "1.005", t01.get_r( "biom:TransactionDate/nc:Date" ), 0 )
        
        self.set_field( "1.006", t01.get( "biom:TransactionPriorityValue" ), 0 )
            
        self.set_field( "1.007", t01.get_r( "biom:TransactionDestinationOrganization/nc:OrganizationIdentification/nc:IdentificationID" ), 0 )
        self.set_field( "1.008", t01.get_r( "biom:TransactionOriginatingOrganization/nc:OrganizationIdentification/nc:IdentificationID" ), 0 )
        
        DAN = t01.get_r( "biom:TransactionDestinationOrganization/nc:OrganizationName", "" )
        OAN = t01.get_r( "biom:TransactionOriginatingOrganization/nc:OrganizationName", "" )
        if DAN != "" or OAN != "":
            self.set_field( "1.017", join( US, [ DAN, OAN ] ), 0 )
        
        self.set_field( "1.009", t01.get_r( "biom:TransactionControlIdentification/nc:IdentificationID" ), 0 )
        
        self.set_field( "1.010", t01.get_r( "biom:TransactionControlReferenceIdentification/nc:IdentificationID" ), 0 )
        
        self.set_field( "1.011", t01.get_r( "biom:TransactionImageResolutionDetails/biom:NativeScanningResolutionValue" ), 0 )
        self.set_field( "1.012", t01.get_r( "biom:TransactionImageResolutionDetails/biom:NominalTransmittingResolutionValue" ), 0 )
        
        with fuckit:
            DNM = t01.get_r( "biom:TransactionDomain/nc:OrganizationName" )
            DVN = t01.get_r( "biom:TransactionDomain/biom:DomainVersionNumberIdentification/nc:IdentificationID" )
            
            self.set_field( "1.013", DNM + US + DVN, 0 )
        
        self.set_field( "1.014", t01.get_r( "biom:TransactionUTCDate/nc:DateTime" ), 0 )
        
        with fuckit:
            CSD = t01.get( "biom:TransactionCharacterSetDirectory", "" )
            CSN = CSD.get( "biom:CharacterSetCommonNameCode", "" )
            CSI = CSD.get( "biom:CharacterSetIndexCode", "" )
            CSV = CSD.get_r( "biom:CharacterSetVersionIdentification/nc:IdentificationID", "" )
            
            self.set_field( "1.015", CSI + US + CSN + US + CSV, 0 )
        
        #   NIST Type02
        debug.debug( "Type-02 parsing", 1 )
        
        self.add_ntype( 2 )
        self.add_idc( 2, 0 )
        
        t02 = self.xmldata.get( "itl:PackageDescriptiveTextRecord", None )
        
        if not isinstance( t02, list ):
            t02 = [ t02 ]
        
        for t02b in t02:
            if t02b != None:
                idc = int( t02b.get_r( "biom:ImageReferenceIdentification/nc:IdentificationID" ) )
                self.set_field( "2.002", idc, idc )
            
            with fuckit:
                i = 3
                for key, values in t02b.get( "itl:UserDefinedDescriptiveDetail" ).iteritems():
                    for detail, value in values.iteritems():
                        self.set_field( ( 2, i ), detail + US + value )
                        i += 1
        
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
