#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import division

from future.builtins import super

from PIL import Image

from MDmisc.string import split_r

from ..fingerprint import NISTf
from ..traditional.config import RS
from ..traditional.config import US

################################################################################
# 
#    Wrapper around the NISTf object to work with the supplementaty information
#    added in the user-definded fields.
# 
################################################################################

class NIST_MDD( NISTf ):
    def get_pairing( self, idc = -1 ):
        """
            Return the pairing information ( minutia id, pairing id ). This
            information is stored in the field 9.255.
            
                >>> mark.get_pairing()
                [['1', '1'], ['2', '2'], ['3', '3']]
        """
        return split_r( [ RS, US ], self.get_field( "9.255", idc ) )
    
    def get_minutiae_paired( self, format = None, idc = -1 ):
        """
            Return all minutiae which are paired. The pairing information is not
            returned here.
            
                >>> mark.get_minutiae_paired()
                [['1', 7.85, 7.05, 290, '0', 'A'], ['2', 13.8, 15.3, 155, '0', 'A'], ['3', 11.46, 22.32, 224, '0', 'A']]
            
            It is also possible to filter out the interesting fields:
            
                >>> mark.get_minutiae_paired( 'xy' )
                [[7.85, 7.05], [13.8, 15.3], [11.46, 22.32]]
        """
        if type( format ) == int:
            idc, format = format, self.minutiaeformat
        
        elif format == None:
            format = self.minutiaeformat
        
        try:
            return [ self.get_minutia_by_id( minutiaid, format, idc ) for minutiaid, _ in self.get_pairing( idc ) ]
         
        except TypeError:
            return None
        
    def get_latent_annotated( self, idc = -1 ):
        """
            Overloading of the NISTf.get_latent_annotated() function to
            incorporate a special annotation for paired minutiae.
            
                >>> mark.get_latent_annotated() #doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        
        img = super().get_latent_annotated( idc = idc )
        
        ########################################################################
        
        try:
            res, _ = img.info[ 'dpi' ]
        except:
            res = self.get_resolution()
           
        red = ( 250, 250, 0 )
        
        width, height = img.size
        
        # Resize factor for the minutiae
        fac = res / 2000
           
        pairingmark = Image.open( self.imgdir + "/pairing.png" )
        newsize = ( int( pairingmark.size[ 0 ] * fac ), int( pairingmark.size[ 1 ] * fac ) )
        pairingmark = pairingmark.resize( newsize, Image.BICUBIC )
           
        offsetx = pairingmark.size[ 0 ] / 2
        offsety = pairingmark.size[ 1 ] / 2
           
        pairingcolor = Image.new( 'RGBA', pairingmark.size, red )
          
        data = self.get_minutiae_paired( "xy", idc )
        if data != None:
            for cx, cy in data:
                cx = cx / 25.4 * res
                cy = cy / 25.4 * res
                cy = height - cy
                
                img.paste( pairingcolor, ( int( cx - offsetx ), int( cy - offsety ) ), mask = pairingmark )
        
        ########################################################################
        
        return img
