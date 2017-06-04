#!/usr/bin/python
# -*- coding: UTF-8 -*-

import doctest
import unittest

from MDmisc.string import join_r
from NIST.core.config import US, RS

################################################################################
#
#    Import of the modules to test
#
################################################################################

import NIST.core.functions
import NIST.traditional.__init__

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
    lst = [
        [ 12.5, 18.7 ],
        [ 10.0, 12.7 ]
    ]
    
    cores = AnnotationList()
    cores.from_list( lst, "xy", "Core" )
    
    ############################################################################
    
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
    pr.add_Type04( 2 )
    pr.set_print( idc = 2 )

    pr.add_Type09( 1 )
    pr.set_minutiae( minutiae, 1 )
    
    pr.add_Type09( 2 )
    pr.set_minutiae( minutiae, 2 )
    
    ############################################################################
    
    vars = {
        'mark': mark,
        'pr': pr,
        'minutiae': minutiae,
        'cores': cores
    }
    
    tests.addTests( doctest.DocTestSuite( NIST.fingerprint.__init__, vars ) )
    tests.addTests( doctest.DocTestSuite( NIST.fingerprint.functions, vars ) )
    
    ############################################################################
    # 
    #    Test for the MDD module
    # 
    ############################################################################
    
    mark.changeClassTo( NIST.MDD.NIST_MDD )
    
    data = [
        ( '1', '1' ), # Minutiae '1' nammed '1'
        ( '2', '2' ), # Minutiae '2' nammed '2'
        ( '3', '3' ) # Minutiae '3' nammed '3'
    ]
    pairing = AnnotationList()
    pairing.from_list( data, format = "in", type = "Pairing" )
    
    mark.set_pairing( pairing )
    
    ############################################################################
    
    vars = {
        'mark': mark,
        'pr': pr,
        'minutiae': minutiae
    }
    
    tests.addTests( doctest.DocTestSuite( NIST.MDD.__init__, vars ) )
    
    return tests

if __name__ == "__main__":
    unittest.TextTestRunner( verbosity = 2 ).run( NISTtests() )
else:
    def load_tests( loader, tests, ignore ):
        return NISTtests()
