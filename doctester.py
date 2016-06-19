#!/usr/bin/env python
#  *-* coding: utf-8 *-*

import sys

if __name__ == "__main__":
    import doctest
    from __init__ import NIST
    
    doctest.testmod( 
        sys.modules.get( '__init__' ),
        extraglobs = { 'n': NIST() },
        verbose = True
    )

