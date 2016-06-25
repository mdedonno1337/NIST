#!/usr/bin/python
# -*- coding: UTF-8 -*-

import doctest
import unittest

import NIST.traditional.__init__
import NIST.traditional.functions

def NISTtests():
    tests = unittest.TestSuite()
    
    tests.addTests( doctest.DocTestSuite( NIST.traditional.__init__, { 'n': NIST.traditional.__init__.NIST() } ) )
    tests.addTests( doctest.DocTestSuite( NIST.traditional.functions ) )
    
    return tests

if __name__ == "__main__":
    unittest.TextTestRunner( verbosity = 2 ).run( NISTtests() )
else:
    def load_tests( loader, tests, ignore ):
        return NISTtests()
