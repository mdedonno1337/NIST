#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import division

from future.builtins import super

from MDmisc.boxer import boxer
from MDmisc.logger import debug
from MDmisc.map_r import map_r
from MDmisc.string import split_r, split
from PMlib.formatConverter import cooNIST2PIL
from SoftPillow import Image
    
from ..fingerprint import NISTf
from ..fingerprint import AnnotationList, Minutia
from ..traditional import RS, US
from ..traditional import needNtype
    
try:
    from ULWLQMetric import ULWLQMetric

    class NISTULWLQMetric( NISTf, ULWLQMetric ):
        """
            Wrapper for the ULWLQMetric module, to be directly integrated in the
            NIST object.
        """
        @property
        def img( self ): 
            return self.get_latent( 'PIL' )
        
        def ULWLQMetric_update_data( self, idc = -1 ):
            """
                Encode the quality of the image, and update the correspondings
                filds in the NIST object.
            """
            idc = self.checkIDC( 9, idc )
            self.data[ 9 ][ idc ].update( super().ULWLQMetric_encode( 'EFS' ) )
            self.clean()
        
        def get_minutiae( self, format = None, idc = -1, field = None ):
            """
                Overload of the `NIST.fingerprint.NISTf.get_minutiae()` function
                to extract the information from the 9.331 field if not present
                in the 9.012 field.
                
                .. see:: :func:`NIST.fingerprint.NISTf.get_minutiae()`
            """
            if field == None and self.get_field( "9.012", idc ) != None and self.get_field( "9.331", idc ) != None:
                raise needNtype( "Field 9.012 and 9.331 present. Need to specify the one to use in parameter" )
            
            else:
                if field == None:
                    if self.get_field( "9.012", idc ) != None:
                        field = "9.012"
                        
                    elif self.get_field( "9.331", idc ) != None:
                        field = "9.331"
                
                lst = AnnotationList()

                if field == "9.012":
                    lst = super().get_minutiae( format = format, idc = idc )
                
                elif field == "9.331":
                    # Process the 9.331 field
                    for m in split_r( [ RS, US ], self.get_field( "9.331", idc ) ):
                        if m == [ '' ]:
                            break
                        
                        else:
                            x, y, theta, d, dr, dt = m
                            
                            x = int( x ) / 100
                            y = int( y ) / 100
                            y = ( self.get_height( idc ) / self.get_resolution( idc ) * 25.4 ) - y
                            theta = ( int( theta ) + 180 ) % 360 
                            
                            dr = int( dr )
                            dt = int( dt )
                            
                            lst.append( Minutia( [ x, y, theta, d, dr, dt ], format = "xytdab" ) )
                    
                # Add the LQMetric quality 
                qmap = self.get_field( "9.308" )
                if qmap != None:
                    qmap = map( list, split( RS, qmap ) )
                    h = self.get_height( idc )
                    res = self.get_resolution( idc )
                    
                    for m in lst:
                        coo = cooNIST2PIL( ( m.x, m.y ), h, res )
                        x, y = map_r( lambda x: int( x / 4 ), coo )
                        m.LQM = int( qmap[ y ][ x ] )
                    
                    newformat = list( lst[ 0 ]._format )
                    newformat.append( "LQM" )
                    
                    lst.set_format( newformat )
                
                return lst
        
        def get_minutiae_by_LQM( self, criteria, higher = True, format = None, idc = -1, field = None ):
            """
                Filter out the minutiae based on the LQMetric value
            """
            lst = AnnotationList()
            
            for m in self.get_minutiae( format, idc, field ):
                if m.LQM >= criteria and higher:
                    lst.append( m )
                
                elif m.LQM <= criteria and not higher:
                    lst.append( m )
            
            return lst
        
        def get_latent_triptych( self, content = "quality", idc = -1 ):
            """
                Get the triptych : latent, annotated latent, quality map (ULW).
            """
            if content == "quality":
                diptych = self.get_latent_diptych( idc )
                
                qmap = super().ULWLQMetric_encode( "image" )
                
                qmap = qmap.chroma( ( 0, 0, 0 ) )
                qmap = qmap.transparency( 0.5 )
                qmap = qmap.scale( self.get_resolution( idc ) * 4 / 500.0 )
                
                latentqmap = self.get_latent( 'PIL', idc )
                latentqmap = latentqmap.convert( "RGBA" )
                latentqmap.paste( qmap, ( 0, 0 ), mask = qmap )
                
                new = Image.new( "RGB", ( self.get_width( idc ) * 3, self.get_height( idc ) ), "white" )
                
                new.paste( diptych, ( 0, 0 ) )
                new.paste( latentqmap, ( diptych.size[ 0 ], 0 ) )
                
                return new
            
            else:
                super().get_latent_triptych( content, idc )
            
except:
    debug.critical( boxer( "ULWLQMetric module not found", "Have you installed the ULWLQMetric library?" ) )
