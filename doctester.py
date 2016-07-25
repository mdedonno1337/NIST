#!/usr/bin/python
# -*- coding: UTF-8 -*-

import doctest
import unittest

import NIST.traditional.__init__
import NIST.traditional.functions

import NIST.fingerprint.__init__
import NIST.fingerprint.functions

def NISTtests():
    tests = unittest.TestSuite()
    
    nt = NIST.traditional.__init__.NIST()
    nt.set_identifier( "Doctester NIST object" )
    nt.add_Type01()
    nt.add_Type02()
    
    tests.addTests( doctest.DocTestSuite( NIST.traditional.__init__, { 'n': nt } ) )
    tests.addTests( doctest.DocTestSuite( NIST.traditional.functions ) )
    
    nf = NIST.fingerprint.__init__.NISTf()
    nf.add_Type01()
    nf.add_Type02()
    nf.add_Type09( 1 )
    nf.add_Type13( ( 500, 500 ), 500, 1 )
    
    tests.addTests( doctest.DocTestSuite( NIST.fingerprint.__init__, { 'n': nf } ) )
    tests.addTests( doctest.DocTestSuite( NIST.fingerprint.functions ) )
    
    return tests

if __name__ == "__main__":
    unittest.TextTestRunner( verbosity = 2 ).run( NISTtests() )
else:
    def load_tests( loader, tests, ignore ):
        return NISTtests()
