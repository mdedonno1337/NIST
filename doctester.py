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
    
    minutiae = [
        [  1, 7.85, 7.05, 290, 0, 'A' ],
        [  2, 13.80, 15.30, 155, 0, 'A' ],
        [  3, 11.46, 22.32, 224, 0, 'A' ],
        [  4, 22.61, 25.17, 194, 0, 'A' ],
        [  5, 6.97, 8.48, 153, 0, 'A' ],
        [  6, 12.58, 19.88, 346, 0, 'A' ],
        [  7, 19.69, 19.80, 111, 0, 'A' ],
        [  8, 12.31, 3.87, 147, 0, 'A' ],
        [  9, 13.88, 14.29, 330, 0, 'A' ],
        [ 10, 15.47, 22.49, 271, 0, 'A' ]
    ]
    
    mark = NIST.fingerprint.__init__.NISTf()
    mark.add_Type01()
    mark.add_Type02()
    mark.add_Type09( 1 )
    mark.add_Type13( ( 500, 500 ), 500, 1 )
    
    mark.set_minutiae( minutiae, 1 )
    
    pr = NIST.fingerprint.__init__.NISTf()
    pr.add_Type01()
    pr.add_Type02()
    pr.add_Type04( 1 )
    pr.add_Type09( 1 )
    
    pr.set_minutiae( minutiae, 1 )
    
    tests.addTests( doctest.DocTestSuite( NIST.fingerprint.__init__, { 'mark': mark, 'pr': pr } ) )
    tests.addTests( doctest.DocTestSuite( NIST.fingerprint.functions ) )
    
    return tests

if __name__ == "__main__":
    unittest.TextTestRunner( verbosity = 2 ).run( NISTtests() )
else:
    def load_tests( loader, tests, ignore ):
        return NISTtests()
