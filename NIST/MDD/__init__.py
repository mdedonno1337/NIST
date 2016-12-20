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
    """
        Overload of the :func:`NIST.fingerprint.functions.AnnotationList` class
        to implement the pairing information.
    """
    def get_by_pairing_name( self, names, format = None ):
        """
            Get the Annotation based on the pairing name.
            
            :param names: Names of the Annotations to retrieve.
            :type names: str or list
            
            :param format: Format of the Annotations to return.
            :type format: str or list
            
            :return: List of Annotations filtered by pairing name
            :rtype: AnnotationList
            
            :raise pairingNameNotFound: if the pairing name is not found in the AnnotationList
        """
        self.set_format( format )
        
        try:
            d = dict( [ ( m.n, m ) for m in self._data if m.n != None ] )
            return AnnotationList( [ d[ str( n ) ] for n in names ] )
        
        except KeyError:
            raise pairingNameNotFound
    
################################################################################
# 
#    Wrapper around the NISTf object to work with the supplementaty information
#    added in the user-definded fields.
# 
################################################################################

class NIST_MDD( NISTf ):
    """
        Overload of the :func:`NIST.fingerprint.NISTf` class, to implement all
        functions related to the pairing information, from the function to store
        the pairingn information in the NIST file (in the user-defined field
        9.255), to the function to annotate the pairing on the images.
    """
    def get_minutiae( self, format = None, idc = -1 ):
        """
            Overload of the :func:`NIST.fingerprint.NISTf.get_minutiae` function
            to add the pairing number.
            
            :param format: Format to return the minutiae.
            :type format: str or list
            
            :param idc: IDC value.
            :type idc: int
            
            :return: List of minutiae.
            :rtype: AnnotationList
            
            .. seealso::
                :func:`NIST.fingerprint.NISTf.get_minutiae`
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
        """
            Overload of the :func:`NIST.fingerprint.NISTf.checkMinutiae`
            function, to set the pairing information.
            
            :param idc: IDC value.
            :type idc: int
            
            .. seealso::
                :func:`NIST.fingerprint.NISTf.checkMinutiae`
        """
        data = super().checkMinutiae( idc = idc )
        
        try:
            self.set_pairing( data.get( "in" ) )
        except:
            pass
    
    def get_pairing( self, idc = -1, clean = False ):
        """
            Return the pairing information ( minutia id, pairing id ). This
            information is stored in the field 9.255.
            
            :param idc: IDC value.
            :type idc: int
            
            :param clean: Remove the minutiae without pairing information ('None' value as pairing name otherwise).
            :type clean: boolean
            
            Usage:
            
                >>> mark.get_pairing()
                [['1', '1'], ['2', '2'], ['3', '3'], ['4', 'None'], ['5', 'None'], ['6', 'None'], ['7', 'None'], ['8', 'None'], ['9', 'None'], ['10', 'None']]
                
                >>> mark.get_pairing( clean = True )
                [['1', '1'], ['2', '2'], ['3', '3']]
        """
        pairing = split_r( [ RS, US ], self.get_field( "9.255", idc ) )
        
        if clean:
            return [ [ minid, pairingid ] for minid, pairingid in pairing if pairingid != 'None' ]
        
        else:
            return pairing
    
    def add_Type09( self, minutiae = None, idc = 0, **options ):
        """
            Overload of the :func:`NIST.fingerprint.NISTf.add_Type09` function
            to initialize the AnnotationList with pairing information if
            provided.
            
            .. seealso::
                :func:`NIST.fingerprint.NISTf.add_Type09`
        """
        super().add_Type09( minutiae = minutiae, idc = idc, **options )
        self.set_pairing( **options )
    
    def set_pairing( self, pairing = None, **options ):
        """
            Function to set the pairing information in the User-defined field
            9.255. The pairing information is stored as following:
            
                minutia id <US> minutia name <RS> ...
                
            :param pairing: Pairing information.
            :type pairing: AnnotationList
            
            Let the pairing information be defined as follow:
                
                >>> from NIST.fingerprint.functions import AnnotationList
                >>> data = [
                ...     ( '1', '1' ), # Minutiae '1' nammed '1'
                ...     ( '2', '2' ), # Minutiae '2' nammed '2'
                ...     ( '3', '3' )  # Minutiae '3' nammed '3'
                ... ]
                >>> pairing = AnnotationList()
                >>> pairing.from_list( data, format = "in" )
                >>> pairing  # doctest: +NORMALIZE_WHITESPACE
                [
                    Annotation( i='1', n='1' ),
                    Annotation( i='2', n='2' ),
                    Annotation( i='3', n='3' )
                ]
            
            The pairing is set as follow:
                
                >>> mark.set_pairing( pairing )
        """
        if pairing != None:
            if isinstance( pairing, list ):
                pairing = AnnotationList( pairing )
                
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
            Filter the minutiae list by pairing name.
            
            :param name: Name of the Annotations to retrieve.
            :type name: list
            
            :param format: Format of the Annotations to retrive.
            :type format: str or list
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Filtered AnnotationList
            :rtype: AnnotationList
            
            Usage:
            
                >>> mark.get_minutiae_by_pairing_name( [ 1, 2 ] ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A' ),
                    Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A' )
                ]
        """
        return AnnotationList( self.get_minutiae( idc ) ).get_by_pairing_name( name, format )
            
    def get_latent_annotated( self, idc = -1 ):
        """
            Overloading of the NISTf.get_latent_annotated() function to
            incorporate a special annotation for paired minutiae.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Annotated latent fingermark
            :rtype: PIL.Image
            
            Usage:
            
                >>> mark.get_latent_annotated() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        
        img = super().get_latent_annotated( idc )
        img = self.annotate( img, self.get_minutiae_paired( idc ), "pairing" )
        
        return img
    
    def get_print_annotated( self, idc = -1 ):
        """
            Overloading of the NISTf.get_print_annotated() function to
            incorporate a special annotation for paired minutiae.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Annotated fingerprint
            :rtype: PIL.Image
            
            Usage:
            
                >>> pr.get_print_annotated() # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        img = super().get_print_annotated( idc )
        img = self.annotate( img, self.get_minutiae_paired( idc ), "pairing" )
        
        return img
    
    def annotate( self, image, data, type = "minutiae", res = None ):
        """
            Overloading of the NISTf.annotate() function to incorporate the
            annotation of the paired minutiae in yellow.
            
            :param image: Image to annotate.
            :type image: PIL.Image
            
            :param data: Data used to annotate the image.
            :type data: AnnotationList
            
            :param type: Type of annotation (minutiae or center).
            :type type: str
            
            :param res: Resolution of the image in DPI.
            :type res: int
            
            :return: Annotated image.
            :rtype: PIL.Image
        """
        if type == "pairing":
            try:
                res, _ = image.info[ 'dpi' ]
            except:
                res = self.get_resolution()
               
            red = ( 250, 250, 0 )
            
            width, height = image.size
            
            # Resize factor for the minutiae
            fac = res / 2000
            
            pairingmark = Image.open( self.imgdir + "/pairing.png" )
            newsize = ( int( pairingmark.size[ 0 ] * fac ), int( pairingmark.size[ 1 ] * fac ) )
            pairingmark = pairingmark.resize( newsize, Image.BICUBIC )
               
            offsetx = pairingmark.size[ 0 ] / 2
            offsety = pairingmark.size[ 1 ] / 2
               
            pairingcolor = Image.new( 'RGBA', pairingmark.size, red )
            
            for d in data:
                cx, cy = d.x, d.y
                
                cx = cx / 25.4 * res
                cy = cy / 25.4 * res
                cy = height - cy
                
                image.paste( pairingcolor, ( int( cx - offsetx ), int( cy - offsety ) ), mask = pairingmark )
            
            return image
        
        else:
            return super().annotate( image, data, type, res )
        
        return image

################################################################################
# 
#    Pairing object, extending the Annotation class
# 
################################################################################

class Pairing( Annotation ):
    """
        Pairing annotation.
    """
    def set_format( self, **kwargs ):
        self._format = kwargs.get( 'format', "in" )
