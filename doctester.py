#!/usr/bin/python
# -*- coding: UTF-8 -*-

import doctest
import unittest

from MDmisc.string import join_r
from NIST.traditional.config import US
from NIST.traditional.config import RS

################################################################################
#
#    Import of the modules to test
#
################################################################################

import NIST.traditional.__init__
import NIST.traditional.functions

import NIST.fingerprint.__init__
import NIST.fingerprint.functions

import NIST.MDD.__init__
from NIST.fingerprint.functions import AnnotationList

################################################################################
# 
#    Tests
# 
################################################################################

def NISTtests():
    tests = unittest.TestSuite()
    
    ############################################################################
    # 
    #    Test for empty NIST object
    # 
    ############################################################################
    
    n = NIST.traditional.__init__.NIST()
    n.set_identifier( "Doctester NIST object" )
    n.add_Type01()
    n.add_Type02()
    
    tests.addTests( doctest.DocTestSuite( NIST.traditional.__init__, { 'n': n } ) )
    tests.addTests( doctest.DocTestSuite( NIST.traditional.functions ) )
    
    ############################################################################
    # 
    #    Test for Mark and Print NIST object
    # 
    ############################################################################

    lst = [
        [  1, 7.85, 7.05, 290, 0, 'A' ],
        [  2, 13.80, 15.30, 155, 0, 'A' ],
        [  3, 11.46, 22.32, 224, 0, 'B' ],
        [  4, 22.61, 25.17, 194, 0, 'A' ],
        [  5, 6.97, 8.48, 153, 0, 'B' ],
        [  6, 12.58, 19.88, 346, 0, 'A' ],
        [  7, 19.69, 19.80, 111, 0, 'C' ],
        [  8, 12.31, 3.87, 147, 0, 'A' ],
        [  9, 13.88, 14.29, 330, 0, 'D' ],
        [ 10, 15.47, 22.49, 271, 0, 'D' ]
    ]
    
    minutiae = AnnotationList()
    minutiae.from_list( lst, format = "ixytqd", type = 'Minutia' )
    
    ############################################################################
    
    mark = NIST.fingerprint.__init__.NISTf()
    mark.add_Type01()
    mark.add_Type02()
    
    mark.add_Type09( 1 )
    mark.set_minutiae( minutiae, 1 )
    mark.set_cores( [ [ 12.5, 18.7 ] ], 1 )
    
    mark.add_Type13( ( 500, 500 ), 500, 1 )
    
    ############################################################################
    
    pr = NIST.fingerprint.__init__.NISTf()
    pr.add_Type01()
    pr.add_Type02()

    pr.add_Type04( 1 )
    pr.set_print( "\x00" * ( 500 * 500 ), 500, ( 500, 500 ), "RAW", 1 )

    pr.add_Type09( 1 )
    pr.set_minutiae( minutiae, 1 )
    
    ############################################################################
    
    vars = {
        'mark': mark,
        'pr': pr,
        'minutiae': minutiae
    }
    
    tests.addTests( doctest.DocTestSuite( NIST.fingerprint.__init__, vars ) )
    tests.addTests( doctest.DocTestSuite( NIST.fingerprint.functions, vars ) )
    
    ############################################################################
    # 
    #    Test for the MDD module
    # 
    ############################################################################
    
    mark.changeClassTo( NIST.MDD.NIST_MDD )
    mark.set_field( "9.255", join_r( [ US, RS ], [ [ '1', '1' ], [ '2', '2' ], [ '3', '3' ] ] ), 1 )
    
    tests.addTests( doctest.DocTestSuite( NIST.MDD.__init__, { 'mark': mark, 'pr': pr } ) )
    
    return tests

if __name__ == "__main__":
    unittest.TextTestRunner( verbosity = 2 ).run( NISTtests() )
else:
    def load_tests( loader, tests, ignore ):
        return NISTtests()
