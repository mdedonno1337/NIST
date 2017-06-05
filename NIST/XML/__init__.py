#!/usr/bin/python
# -*- coding: UTF-8 -*-

import datetime
import os
import time
import xmltodict

from MDmisc import fuckit
from MDmisc.RecursiveDefaultDict import defDict
from MDmisc.elist import ifany
from MDmisc.logger import debug
from MDmisc.string import join

from ..core import NIST as NISTcore
from ..core.config import RS, US
from ..core.functions import tagSplitter

class NIST( NISTcore ):
    def load_auto( self, p ):
        if isinstance( p, ( str, unicode ) ):
            if ifany( [ "<", ">", "<?xml" ], p ):
                self.load( p )
            
            else:
                self.read( p )
    
    def load( self, data ):
        data = xmltodict.parse( data )[ "itl:NISTBiometricInformationExchangePackage" ]
        
        #    NIST Type01
        debug.debug( "Type-01 parsing", 1 )
        
        self.add_ntype( 1 )
        self.add_idc( 1, 0 )
        
        t01 = data[ "itl:PackageInformationRecord" ][ "biom:Transaction" ]
        
        major = t01[ "biom:TransactionMajorVersionValue" ]
        minor = t01[ "biom:TransactionMinorVersionValue" ]
        self.set_field( "1.002", "%s%s" % ( major, minor ) )
        
        self.set_field( "1.004", t01[ "biom:TransactionCategoryCode" ], 0 )
        self.set_field( "1.005", t01[ "biom:TransactionDate" ][ "nc:Date" ], 0 )
        
        with fuckit:
            self.set_field( "1.006", t01[ "biom:TransactionPriorityValue" ], 0 )
            
        self.set_field( "1.007", t01[ "biom:TransactionDestinationOrganization" ][ "nc:OrganizationIdentification" ][ "nc:IdentificationID" ], 0 )
        self.set_field( "1.008", t01[ "biom:TransactionOriginatingOrganization" ][ "nc:OrganizationIdentification" ][ "nc:IdentificationID" ], 0 )
        
        DAN = t01[ "biom:TransactionDestinationOrganization" ].get( "nc:OrganizationName", "" ) or ""
        OAN = t01[ "biom:TransactionOriginatingOrganization" ].get( "nc:OrganizationName", "" ) or ""
        if DAN != "" or OAN != "":
            self.set_field( "1.017", join( US, [ DAN, OAN ] ), 0 )
        
        self.set_field( "1.009", t01[ "biom:TransactionControlIdentification" ][ "nc:IdentificationID" ], 0 )
        
        with fuckit:
            self.set_field( "1.010", t01[ "biom:TransactionControlReferenceIdentification" ][ "nc:IdentificationID" ], 0 )
        
        self.set_field( "1.011", t01[ "biom:TransactionImageResolutionDetails" ][ "biom:NativeScanningResolutionValue" ], 0 )
        self.set_field( "1.012", t01[ "biom:TransactionImageResolutionDetails" ][ "biom:NominalTransmittingResolutionValue" ], 0 )
        
        with fuckit:
            DNM = t01[ "biom:TransactionDomain" ].get( "nc:OrganizationName", "" )
            DVN = t01[ "biom:TransactionDomain" ][ "biom:DomainVersionNumberIdentification" ][ "nc:IdentificationID" ]
            
            self.set_field( "1.013", DNM + US + DVN, 0 )
        
        with fuckit:
            self.set_field( "1.014", t01[ "biom:TransactionUTCDate" ][ "nc:DateTime" ], 0 )
        
        with fuckit:
            CSD = t01[ "biom:TransactionCharacterSetDirectory" ]
            CSN = CSD[ "biom:CharacterSetCommonNameCode" ]
            CSI = CSD.get( "biom:CharacterSetIndexCode", "" )
            try:
                CSV = CSD[ "biom:CharacterSetVersionIdentification" ][ "nc:IdentificationID" ]
            except:
                CSV = ""
            
            self.set_field( "1.015", CSI + US + CSN + US + CSV, 0 )
        
        #   NIST Type02
        debug.debug( "Type-02 parsing", 1 )
        
        self.add_ntype( 2 )
        self.add_idc( 2, 0 )
        
        t02 = data.get( "itl:PackageDescriptiveTextRecord", None )
        if t02 != None:
            self.set_field( "2.002", t02[ "biom:ImageReferenceIdentification" ][ "nc:IdentificationID" ] )
        
        with fuckit:
            i = 3
            for key, values in t02[ "itl:UserDefinedDescriptiveDetail" ].iteritems():
                for detail, value in values.iteritems():
                    self.set_field( ( 2, i ), detail + US + value )
                    i += 1
