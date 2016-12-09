#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import division

from future.builtins import super

from PIL import Image

from MDmisc.eint import str_int_cmp
from MDmisc.elist import ifall
from MDmisc.string import split_r, join_r

from NIST.fingerprint.functions import Annotation

from .exceptions import pairingNameNotFound

from ..fingerprint import NISTf
from ..fingerprint.functions import AnnotationList as _AnnotationList
from ..traditional.config import RS
from ..traditional.config import US

################################################################################
# 
#    Overload of the AnnotationList to include the pairing information
# 
################################################################################

class AnnotationList( _AnnotationList ):
    def get_by_pairing_name( self, names, format = None ):
        self.set_format( format )
        
        try:
            d = dict( [ ( m.n, m ) for m in self._data if m.n != None ] )
            return [ d[ n ] for n in names ]
        
        except KeyError:
            raise pairingNameNotFound
    
################################################################################
# 
#    Wrapper around the NISTf object to work with the supplementaty information
#    added in the user-definded fields.
# 
################################################################################

class NIST_MDD( NISTf ):
    def get_minutiae( self, format = None, idc = -1 ):
        """
            Overload of the get_minutiae() function to add the pairing number.
        """
        lst = super().get_minutiae( format = format, idc = idc )
        
        try:
            pairing = dict( self.get_pairing( idc ) )
        
            for t, _ in enumerate( lst ):
                try:
                    lst[ t ].n = pairing[ lst[ t ].i ]
                except:
                    lst[ t ].n = None
        except:
            pass
        
        return lst
    
    def checkMinutiae( self, idc = -1 ):
        data = super().checkMinutiae( idc = idc )
        
        try:
            self.set_pairing( data.get( "in" ) )
        except:
            pass
    
    def get_pairing( self, idc = -1 ):
        """
            Return the pairing information ( minutia id, pairing id ). This
            information is stored in the field 9.255.
            
                >>> mark.get_pairing()
                [['1', '1'], ['2', '2'], ['3', '3']]
        """
        return split_r( [ RS, US ], self.get_field( "9.255", idc ) )
    
    def add_Type09( self, minutiae = None, idc = 0, **options ):
        super().add_Type09( minutiae = minutiae, idc = idc, **options )
        self.set_pairing( **options )
    
    def set_pairing( self, pairing = None, **options ):
        if pairing != None:
            self.set_field( "9.255", join_r( [ US, RS ], pairing.as_list() ) )
    
    def get_minutiae_paired( self, format = None, idc = -1 ):
        """
            Return all minutiae which are paired. The pairing information is not
            returned here.
            
                >>> mark.get_minutiae_paired() # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A' ),
                    Minutia( i='3', x='11.46', y='22.32', t='224', q='0', d='B' )
                ]
            
            It is also possible to filter out the interesting fields:
            
                >>> mark.get_minutiae_paired( 'xy' ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( x='7.85', y='7.05' ),
                    Minutia( x='13.8', y='15.3' ),
                    Minutia( x='11.46', y='22.32' )
                ]
        """
        if type( format ) == int:
            idc, format = format, self.minutiaeformat
        
        elif format == None:
            format = self.minutiaeformat
        
        try:
            lst = [ self.get_minutia_by_id( minutiaid, format, idc ) for minutiaid, minutiaename in self.get_pairing( idc ) if minutiaename != "None" ]
            return AnnotationList( [ m for m in lst if m is not None ] )
         
        except TypeError:
            return AnnotationList( [] )
    
    def get_minutiae_by_pairing_name( self, name, format = None, idc = -1 ):
        """
            Filter the minutiae list by pairing name
        """
        return AnnotationList( self.get_minutiae( idc ) ).get_by_pairing_name( name, format )
            
    def get_latent_annotated( self, idc = -1 ):
        """
            Overloading of the NISTf.get_latent_annotated() function to
            incorporate a special annotation for paired minutiae.
            
                >>> mark.get_latent_annotated() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        
        img = super().get_latent_annotated( idc )
        img = self.annotate( img, self.get_minutiae_paired( "xy", idc ), "pairing" )
        
        return img
    
    def get_print_annotated( self, idc = -1 ):
        """
            Overloading of the NISTf.get_print_annotated() function to
            incorporate a special annotation for paired minutiae.
            
                >>> mark.get_latent_annotated() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        img = super().get_print_annotated( idc )
        img = self.annotate( img, self.get_minutiae_paired( "xy", idc ), "pairing" )
        
        return img
    
    def annotate( self, img, data, type = "minutiae", res = None ):
        """
            Overloading of the NISTf.annotate() function to incorporate the
            annotation of the paired minutiae in yellow.
        """
        if type == "pairing":
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
            
            for d in data:
                cx, cy = d
                
                cx = cx / 25.4 * res
                cy = cy / 25.4 * res
                cy = height - cy
                
                img.paste( pairingcolor, ( int( cx - offsetx ), int( cy - offsety ) ), mask = pairingmark )
            
            return img
        
        else:
            return super().annotate( img, data, type, res )
        
        return img

################################################################################
# 
#    Pairing object, extending the Annotation class
# 
################################################################################

class Pairing( Annotation ):
    def set_format( self, **kwargs ):
        self._format = kwargs.get( 'format', "in" )
