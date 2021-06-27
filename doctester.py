#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy
import doctest
import sys
import unittest

import NIST.core.__init__
import NIST.core.functions

import NIST.traditional.__init__

import NIST.fingerprint.__init__
import NIST.fingerprint.functions

def NISTtests():
    tests = unittest.TestSuite()
    
    sample_all_supported_types = NIST.traditional.__init__.NIST( "./sample/all-supported-types.an2" )
    sample_type_1 = NIST.fingerprint.__init__.NISTf( "./sample/type-1.an2" )
    sample_type_4_tpcard = NIST.fingerprint.__init__.NISTf( "./sample/type-4-tpcard.an2" )
    sample_type_9_10_14 = NIST.fingerprint.__init__.NISTf( "./sample/type-9-10-14.an2" )
    sample_type_13 = NIST.fingerprint.__init__.NISTf( "./sample/type-13.an2" )
    sample_type_15_palms = NIST.fingerprint.__init__.NISTf( "./sample/type-15-palms.an2" )
    sample_type_17_iris = NIST.fingerprint.__init__.NISTf( "./sample/type-17-iris.an2" )
    
    var = {
        "sample_all_supported_types": sample_all_supported_types,
        "sample_type_1": sample_type_1,
        "sample_type_4_tpcard": sample_type_4_tpcard,
        "sample_type_9_10_14": sample_type_9_10_14,
        "sample_type_13": sample_type_13,
        "sample_type_17_iris": sample_type_17_iris,
        "sample_type_15_palms": sample_type_15_palms,
    }
    
    def setUpfunction( test ):
        test.globs.update( copy.deepcopy( var ) )
        
    tests.addTests( doctest.DocTestSuite( NIST.core.__init__, var, setUp = setUpfunction ) )
    tests.addTests( doctest.DocTestSuite( NIST.core.functions, var, setUp = setUpfunction ) )
    tests.addTests( doctest.DocTestSuite( NIST.fingerprint.__init__, var, setUp = setUpfunction ) )
    tests.addTests( doctest.DocTestSuite( NIST.fingerprint.functions, var, setUp = setUpfunction ) )
    
    return tests

if __name__ == "__main__":
    ret = not unittest.TextTestRunner( verbosity = 2 ).run( NISTtests() ).wasSuccessful()
    sys.exit( ret )
else:
    def load_tests( loader, tests, ignore ):
        return NISTtests()
