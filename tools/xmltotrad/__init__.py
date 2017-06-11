#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import xmltodict
from collections import OrderedDict

file = "AN2011-FieldDefinition.xml"
d = xmltodict.parse( open( file ) )[ "FieldDefinitions" ][ "FieldDef" ]

corr = OrderedDict()

reg = re.compile( "^(?P<field>\d+\.\d+)(:X)?$" )

for e in d:
    m = reg.match( e[ "FieldID" ] )
    
    if m != None:
        field = m.group( "field" )
        
        xmlpath = e[ "XMLPath" ]
        xmlpath = re.sub( "\s+or\s+", ";", xmlpath )
        
        if xmlpath.startswith( "if " ):
            continue
        
        elif e.get( "InfoItem", None ) == "SET":
            continue
        
        elif field.endswith( ".001" ):
            continue
        
        else:
            for path in xmlpath.split( ";" ):
                corr[ path ] = field
                
print "xmltotrad = {"
print ", \n".join( [ "\t'%s': '%s'" % e for e in corr.iteritems() ] )
print "}"
