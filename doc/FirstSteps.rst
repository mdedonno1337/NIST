First steps and examples
========================

Traditional NIST objects
------------------------

Fingerprint NIST objects
------------------------

The main purpose of this module is to implement some functions needed to work with fingerprint NIST files. The main class is named **`NISTf`**, for NIST-fingerprints. 

Examples
~~~~~~~~

Imports:

>>> from NIST import NISTf
>>> from NIST.fingerprint.functions import AnnotationList

Construction of list of minutiae:

>>> lst = [
    [  1, 7.85, 7.05, 290, 0, 'A' ],
    [  2, 13.80, 15.30, 155, 0, 'A' ],
    [  3, 11.46, 22.32, 224, 0, 'B' ],
    [  4, 22.61, 25.17, 194, 0, 'A' ],
    [  5, 6.97, 8.48, 153, 0, 'B' ],
    [  6, 12.58, 19.88, 346, 0, 'A' ],
    [  7, 19.69, 19.80, 111, 0, 'C' ],
    [  8, 12.31, 3.87, 147, 0, 'A' ],
    [  9, 13.88, 14.29, 330, 0, 'D' ],
    [ 10, 15.47, 22.49, 271, 0, 'D' ]
]
>>> minutiae = AnnotationList()
>>> minutiae.from_list( lst, "ixytqd" )

Latent fingermark
~~~~~~~~~~~~~~~~~

Construction of the NIST object:

>>> mark = NISTf()
>>> mark.add_Type01()
>>> mark.add_Type02()

Add the minutiae to the NIST object:

>>> mark.add_Type09( 1 )
>>> mark.set_minutiae( minutiae, 1 )

Set the core of the latent fingermark:

>>> mark.set_cores( [ [ 12.5, 18.7 ] ], 1 )

Add a empty image to the NIST object:

>>> mark.add_Type13( ( 500, 500 ), 500, 1 )

The same result can be obtained by using the following code:

>>> params = {
    'minutiae': minutiae,
    'cores': [ [ 12.5, 18.7 ] ]
}
>>> mark = NISTf()
>>> mark.init_latent( **params )

The resulting latent fingermark NIST object should be something like:

>>> print mark
Information about the NIST object:
    Records: Type-01, Type-02, Type-09, Type-13
    Class:   NISTf
<BLANKLINE>
NIST Type-01
    01.001 LEN: 00000145
    01.002 VER: 0501
    01.003 CNT: 1<US>3<RS>2<US>0<RS>9<US>0<RS>13<US>0
    01.004 TOT: USA
    01.005 DAT: 20161217
    01.006 PRY: 1
    01.007 DAI: FILE
    01.008 ORI: UNIL
    01.009 TCN: 1481995137
    01.011 NSR: 00.00
    01.012 NTR: 00.00
NIST Type-02 (IDC 0)
    02.001 LEN: 00000062
    02.002 IDC: 0
    02.003    : 0300
    02.004    : 20161217
    02.054    : 0300<US><US>
NIST Type-09 (IDC 0)
    09.001 LEN: 00000266
    09.002 IDC: 0
    09.003 IMP: 4
    09.004 FMT: S
    09.007    : U
    09.008    : 12501870
    09.010    : 10
    09.011    : 0
    09.012    : 1<US>07850705290<US>0<US>A<RS>2<US>13801530155<US>0<US>A<RS>3<US>11462232224<US>0<US>B<RS>4<US>22612517194<US>0<US>A<RS>5<US>06970848153<US>0<US>B<RS>6<US>12581988346<US>0<US>A<RS>7<US>19691980111<US>0<US>C<RS>8<US>12310387147<US>0<US>A<RS>9<US>13881429330<US>0<US>D<RS>10<US>15472249271<US>0<US>D
NIST Type-13 (IDC 0)
    13.001 LEN: 00250150
    13.002 IDC: 0
    13.003 IMP: 4
    13.004 SRC: UNIL
    13.005 LCD: 20161217
    13.006 HLL: 500
    13.007 VLL: 500
    13.008 SLC: 1
    13.009 THPS: 500
    13.010 TVPS: 500
    13.011 CGA: 0
    13.012 BPX: 8
    13.013 FGP: 0
    13.999 DATA: FFFFFFFF ... FFFFFFFF (250000 bytes)

.. note:: All dynamic fields (such as the creation date) are calculated by the `NISTf` class, and will (obviously) be different in your case.

.. note:: All binary fields, such as the field 13.999, are converted to HEX value, and cropped to show the first and last 4 bytes.

.. warning:: This representation is not usable as input to construct a new NIST file. 

