#!/usr/bin/python
# -*- coding: UTF-8 -*-

import doctest
import unittest

import NIST.__init__

def NISTtests():
    tests = unittest.TestSuite()
    
    tests.addTests( doctest.DocTestSuite( NIST.__init__, { 'n': NIST.__init__.NIST() } ) )
    tests.addTests( doctest.DocTestSuite( NIST.functions ) )
    
    return tests

if __name__ == "__main__":
    unittest.TextTestRunner( verbosity = 2 ).run( NISTtests() )
else:
    def load_tests( loader, tests, ignore ):
        return NISTtests()
