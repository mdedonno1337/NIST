#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import division

from _collections import defaultdict
from PIL import Image

from MDmisc.eint import str_int_cmp
from MDmisc.elist import ifall, ifany
from MDmisc.string import split_r, join_r

from .exceptions import pairingNameNotFound
from .functions import add_pairing

from ...core.config import RS, US
from ...core.exceptions import idcNotFound
from ...fingerprint import NISTf
from ...fingerprint.functions import AnnotationList as _AnnotationList
from ...fingerprint.functions import Annotation, AnnotationTypes

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
    
    def unpair( self, lst ):
        """
            Delete the pairing for all Annotations if the pairing name is
            present in the 'lst' parameter.
            
            :param lst: List of pairing name to delete
            :type lst: Python list
        """
        lst = [ int( e ) for e in lst if not e == None ]
        
        deleted = []
        for m in self:
            try:
                if int( m.n ) in lst:
                    deleted.append( m.n )
                    m.n = None
            except:
                pass
        
        return deleted
    
    def unpair_fist( self, n ):
        todelete = [ m.n for m in self[ :n ] ]
        return self.unpair( todelete )
        
    def unpair_last( self, n ):
        todelete = [ m.n for m in self[ n: ] ]
        return self.unpair( todelete )
    
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
        9.225), to the function to annotate the pairing on the images.
    """
    
    ############################################################################
    # 
    #    Function to migrate a latent fingermark to a fingerprint
    # 
    ############################################################################
    
    def migrate_Type13_to_type14( self, idc = -1 ):
        """
            Function to migrate an latent fingermark to a fingerprint (Type13 to Type14).
            
            :param idc: IDC value.
            :type idc: idc
        """
        idc = self.checkIDC( 13, idc )
        size = self.get_size( idc )
        res = self.get_resolution( idc )
        image = self.get_latent( "RAW", idc )
        
        self.add_Type14( size, res, idc )
        self.set_field( "14.999", image, idc )
        
        self.delete_idc( 13, idc )
    
    ############################################################################
    # 
    #    Minutiae related functions
    # 
    ############################################################################
    
    def get_minutiae( self, format = None, idc = -1, **options ):
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
        if isinstance( format, int ):
            format, idc = None, format
        
        lst = NISTf.get_minutiae( self, format = format, idc = idc, **options )
        lst.__class__ = AnnotationList
        
        try:
            lst = self.add_pairing( lst, idc )
            lst.set_format( format )
            lst.__class__ = AnnotationList
        except:
            pass
        
        return lst
    
    def add_pairing( self, lst, idc = -1 ):
        """
            Add the pairing information into the AnnotationList passed in
            argument.
            
            :param lst: List of Annotations to process
            :type lst: AnnotationList
            
            :param idc: IDC value
            :type idc: int
            
            :return: Updated AnnotationList
            :rtype: AnnotationList
        """
        pairing = dict( self.get_pairing( idc ) )
        ret = add_pairing(lst, pairing)
        ret.__class__ = AnnotationList
        
        return ret
    
    def checkMinutiae( self, idc = -1 ):
        """
            Overload of the :func:`NIST.fingerprint.NISTf.checkMinutiae`
            function, to set the pairing information.
            
            :param idc: IDC value.
            :type idc: int
            
            .. seealso::
                :func:`NIST.fingerprint.NISTf.checkMinutiae`
        """
        data = NISTf.checkMinutiae( self, idc = idc )
        
        try:
            self.set_pairing( data.get( "in" ) )
        except:
            pass
        
        return data
    
    def get_pairing( self, idc = -1, clean = False ):
        """
            Return the pairing information ( minutia id, pairing id ). This
            information is stored in the field 9.225.
            
            :param idc: IDC value.
            :type idc: int
            
            :param clean: Remove the minutiae without pairing information ('None' value as pairing name otherwise).
            :type clean: boolean
            
            Usage:
                
                >>> mark.get_pairing() # doctest: +NORMALIZE_WHITESPACE
                [
                    Pairing( i='1', n='1' ),
                    Pairing( i='2', n='2' ),
                    Pairing( i='3', n='3' ),
                    Pairing( i='4', n='None' ),
                    Pairing( i='5', n='None' ),
                    Pairing( i='6', n='None' ),
                    Pairing( i='7', n='None' ),
                    Pairing( i='8', n='None' ),
                    Pairing( i='9', n='None' ),
                    Pairing( i='10', n='None' )
                ]
                
                >>> mark.get_pairing( clean = True ) # doctest: +NORMALIZE_WHITESPACE
                [
                    Pairing( i='1', n='1' ),
                    Pairing( i='2', n='2' ),
                    Pairing( i='3', n='3' )
                ]
        """
        lst = AnnotationList()
        
        pairing = split_r( [ RS, US ], self.get_field( "9.225", idc ) )
        
        if clean:
            pairing = [ [ minid, pairingid ] for minid, pairingid in pairing if pairingid != 'None' ]
        
        lst.from_list( pairing, 'in', 'Pairing' )
        return lst
    
    def add_Type09( self, minutiae = None, idc = 0, **options ):
        """
            Overload of the :func:`NIST.fingerprint.NISTf.add_Type09` function
            to initialize the AnnotationList with pairing information if
            provided.
            
            .. seealso::
                :func:`NIST.fingerprint.NISTf.add_Type09`
        """
        NISTf.add_Type09( self, minutiae = minutiae, idc = idc, **options )
        self.set_pairing( **options )
    
    def set_minutiae( self, data, idc = -1 ):
        """
            Overload of the set_minutaie() function, to set the pairing
            information at the same time.
            
            .. seealso::
                :func:`NIST.fingerprint.NISTf.set_minutiae`
                :func:`NIST.fingerprint.NISTf.set_pairing`
        """
        lst = super( NIST_MDD, self ).set_minutiae( data, idc = idc )
        self.set_pairing( data, idc )
        return lst
    
    def set_pairing( self, pairing = None, idc = -1, **options ):
        """
            Function to set the pairing information in the User-defined field
            9.225. The pairing information is stored as following:
            
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
                
            The pairing is set as follow:
            
                >>> mark2 = mark.get()
                >>> mark2.set_pairing( data )
            
            The pairing can also be set with an AnnotationList object:
            
                >>> pairing = AnnotationList()
                >>> pairing.from_list( data, format = "in", type = "Pairing" )
                >>> pairing # doctest: +NORMALIZE_WHITESPACE
                [
                    Pairing( i='1', n='1' ),
                    Pairing( i='2', n='2' ),
                    Pairing( i='3', n='3' )
                ]
            
            The pairing is set as follow:
                
                >>> mark2.set_pairing( pairing )
        """
        if pairing != None:
            def n():
                return None
            
            pai = defaultdict( n )
            for p in pairing:
                try:
                    if isinstance( p, Annotation ):
                        i, n = p.i, p.n
                    else:
                        i, n = p
                        
                    pai[ int( i ) ] = int( n )
                    
                except:
                    continue
            
            lst = []
            for m in self.get_minutiae():
                lst.append( ( m.i, pai[ int( m.i ) ] ) )
            
            self.set_field( "9.225", join_r( [ US, RS ], lst ), idc )
    
    def get_minutiae_paired( self, format = None, idc = -1, **options ):
        """
            Return all minutiae which are paired.
        """
        if isinstance( format, int ):
            idc, format = format, self.minutiaeformat
        
        elif format == None:
            format = self.minutiaeformat
        
        lst = AnnotationList()
        for m in self.get_minutiae( format, idc, **options ):
            try:
                if m.n not in [ "None", None ]:
                    lst.append( m )
            except:
                continue
        
        lst.set_format( format )
        
        return lst
    
    def get_minutiae_paired_all( self, format = None, **options ):
        """
            Return only the paired minutiae for all fingers, similair to the get_minutiae_all() function
        """
        if ifany( [ 4, 14 ], self.get_ntype() ):
            if format == None:
                format = self.minutiaeformat
                
            ret = []
            
            for idc in xrange( 1, 11 ):
                try:
                    ret.append( self.get_minutiae_paired( format = format, idc = idc ) )
                except idcNotFound:
                    ret.append( [] )
            
            return ret
        
        elif 13 in self.get_ntype():
            ret = [ [] ] * 10
            ret[ 0 ] = self.get_minutiae( format = format )
            return ret
        
        else:
            raise notImplemented
    
    def get_minutiae_paired_count( self, idc = -1 ):
        """
            Get the number of minutiae pairing.
            
            :param idc: IDC value.
            :type idc: int
            
            :return: Number of minutiae paired
            :rtype: int
            
            >>> mark.get_minutiae_paired_count()
            3
        """
        return len( self.get_pairing( idc, True ) )
    
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
                    Minutia( i='1', x='7.85', y='7.05', t='290', q='0', d='A', n='1' ),
                    Minutia( i='2', x='13.8', y='15.3', t='155', q='0', d='A', n='2' )
                ]
        """
        return AnnotationList( self.get_minutiae( idc = idc ) ).get_by_pairing_name( name, format )
            
    def get_latent_annotated( self, idc = -1, **options ):
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
        
        img = super( NIST_MDD, self ).get_latent_annotated( idc, **options )
        img = self.annotate( img, self.get_minutiae_paired( idc, **options ), "pairing" )
        
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
            
                >>> pr.get_print_annotated( 1 ) # doctest: +ELLIPSIS
                <PIL.Image.Image image mode=RGB size=500x500 at ...>
        """
        img = super( NIST_MDD, self ).get_print_annotated( idc )
        img = self.annotate( img, self.get_minutiae_paired( idc ), "pairing" )
        
        return img
    
    def annotate( self, image, data, type = "minutiae", res = None, idc = -1, **options ):
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
               
            yellow = ( 250, 250, 0 )
            
            width, height = image.size
            
            # Resize factor for the minutiae
            fac = res / 2000
            
            pairingmark = Image.open( self.imgdir + "/pairing.png" )
            newsize = ( int( pairingmark.size[ 0 ] * fac ), int( pairingmark.size[ 1 ] * fac ) )
            pairingmark = pairingmark.resize( newsize, Image.BICUBIC ).convert( "L" )
               
            offsetx = pairingmark.size[ 0 ] / 2
            offsety = pairingmark.size[ 1 ] / 2
               
            pairingcolor = Image.new( 'RGBA', pairingmark.size, yellow )
            
            for d in data:
                if d.n in [ "None", None ]:
                    continue
                 
                cx, cy = d.x, d.y
                
                cx = cx / 25.4 * res
                cy = cy / 25.4 * res
                cy = height - cy
                
                image.paste( pairingcolor, ( int( cx - offsetx ), int( cy - offsety ) ), mask = pairingmark )
            
            return image
        
        else:
            return super( NIST_MDD, self ).annotate( image, data, type, res, **options )
        
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
    defaultformat = "in"

AnnotationTypes[ 'Pairing' ] = Pairing
