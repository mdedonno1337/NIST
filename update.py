#!/usr/bin/python
# -*- coding: UTF-8 -*-

import doctester
import subprocess
import unittest

from MDmisc.eprint import eprint

################################################################################
# 
################################################################################

def _exe( cmd, wd ):
    return subprocess.Popen( cmd, cwd = wd, stdout = subprocess.PIPE, stderr = subprocess.PIPE ).communicate()

################################################################################
# 
#    Version determination
# 
################################################################################

try:
    import versioneer
    version = versioneer.get_version()

except:
    version = "dev"
    
finally:
    import os
    os.chdir( os.path.split( os.path.abspath( __file__ ) )[ 0 ] )
    
    with open( "doc/version.py", "w+" ) as fp:
        fp.write( "__version__ = '%s'" % version )

################################################################################
# 
################################################################################

unittest.TextTestRunner( verbosity = 2 ).run( doctester.NISTtests() )

################################################################################
# 
################################################################################

wd = os.path.abspath( "./doc" )

cmd = [ 'make', 'html' ]

stdout, stderr = _exe( cmd, wd )

print( stdout )
eprint( stderr )

