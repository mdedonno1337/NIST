#!/usr/bin/python
# -*- coding: UTF-8 -*-

################################################################################
#
#    Python library for:
#
#            Data Format for the Interchange of Fingerprint, Facial
#                         & Other Biometric Information
#
#                  NIST Special Publication 500-290 Rev1 (2013)
#    
#    
#    The aim of the python library is to open, modify and write Biometric
#    Information files based on the standard proposed by the NIST (for short:
#    NIST format).
#    
#    The standard propose the following type of biometric data:
#    
#        Type-01 : Transaction information
#        Type-02 : User-defined descriptive text
#        Type-03 : (Deprecated)
#        Type-04 : High-resolution grayscale fingerprint image
#        Type-05 : (Deprecated)
#        Type-06 : (Deprecated)
#        Type-07 : User-defined image
#        Type-08 : Signature image
#        Type-09 : Minutiae data
#        Type-10 : Photographic body part imagery (including face and SMT)
#        Type-11 : Forensic and investigatory voice data
#        Type-12 : Forensic dental and oral data
#        Type-13 : Variable-resolution latent friction ridge image
#        Type-14 : Variable-resolution fingerprint image
#        Type-15 : Variable-resolution palm print image
#        Type-16 : User-defined variable-resolution testing image
#        Type-17 : Iris image
#        Type-18 : DNA data
#        Type-19 : Variable-resolution plantar image
#        Type-20 : Source representation
#        Type-21 : Associated context
#        Type-22 : Non-photographic imagery
#        Type-98 : Information assurance
#        Type-99 : CBEFF biometric data record
#
#        The Type-23 to Type-97 are reserved for future use.
# 
#        This library is (almost at 100%) compatible (read and write) with the
#        standard is used correctly (compatibility tested with "BioCTS for ANSI
#        /NIST-ITL v2") and the Sample Data provided by the NIST.
# 
#        Some functions are added to simplify some operation, especially
#        regarding the fingerprint processing (extraction of image, annotation
#        of minutiae on the image, ...).
# 
# 
#                                         Marco De Donno
#                                         marco.dedonno@unil.ch
#                                         mdedonno1337@gmail.com
#                                        
#                                         School of Criminal Justice
#                                         University of Lausanne - Batochime
#                                         CH-1015 Lausanne-Dorigny
#                                         Switzerland
# 
#    Copyright (c) 2016 Marco De Donno
# 
################################################################################

from .fingerprint import NISTf
from .traditional import NIST


try:
    from .version import __version__
except:
    __version__ = "dev"
