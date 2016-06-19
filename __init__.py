#!/usr/bin/env python
#  *-* coding: utf-8 *-*

from _collections import defaultdict
from collections import OrderedDict
from lib.misc.binary import binstring_to_int, int_to_binstring
from lib.misc.boxer import boxer
from lib.misc.deprecated import deprecated
from lib.misc.logger import debug
from lib.misc.stringIterator import stringIterator
from string import join, upper
import inspect
import os

from PIL import Image

################################################################################
#
#    Abbreviation and full name of all Record type. 
#
################################################################################

LABEL = {
    1: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'VER', 'Version number' ),
        3:   ( 'CNT', 'File content' ),
        4:   ( 'TOT', 'Type of transaction' ),
        5:   ( 'DAT', 'Date' ),
        6:   ( 'PRY', 'Priority' ),
        7:   ( 'DAI', 'Destination agency identifier' ),
        8:   ( 'ORI', 'Originating agency identifier' ),
        9:   ( 'TCN', 'Transaction control number' ),
        10:  ( 'TCR', 'Transaction control reference' ),
        11:  ( 'NSR', 'Native scanning resolution' ),
        12:  ( 'NTR', 'Nominal resolution' ),
        13:  ( 'DOM', 'Domain name' ),
        14:  ( 'GMT', 'Greenwich Mean Time' ),
        15:  ( 'DCS', 'Character encoding' ),
        16:  ( 'APS', 'Application profile specifications' ),
        17:  ( 'ANM', 'Agency names' ),
        18:  ( 'GNS', 'Geographic name set' )
    },
    2: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' )
    },
    4: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'IMP', 'Impression type' ),
        4:   ( 'FGP', 'Friction ridge generalized position' ),
        5:   ( 'ISR', 'Image scanning resolution' ),
        6:   ( 'HLL', 'Horizontal line length' ),
        7:   ( 'VLL', 'Vertical line length' ),
        8:   ( 'CGA', 'Compression algorithm' ),
        9:   ( 'DATA', 'Image data' )
    },
    7: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' )
    },
    8: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'SIG', 'Signature type' ),
        4:   ( 'SRT', 'Signature representation type' ),
        5:   ( 'ISR', 'Image scanning resolution' ),
        6:   ( 'HLL', 'Horizontal line length' ),
        7:   ( 'VLL', 'Vertical line length' ),
        8:   ( 'DATA', 'Signature image data' )
    },
    9: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'IMP', 'Impression type' ),
        4:   ( 'FMT', 'Minutiae format' ),
        126: ( 'CBI', 'M1 CBEFF information' ),
        127: ( 'CEI', 'M1 capture equipment identification' ),
        128: ( 'HLL', 'M1 horizontal line length' ),
        129: ( 'VLL', 'M1 vertical line length' ),
        130: ( 'SLC', 'M1 scale units' ),
        131: ( 'THPS', 'M1 transmitted horizontal pixel scale' ),
        132: ( 'TVPS', 'M1 transmitted vertical pixel scale' ),
        133: ( 'FVW', 'M1 finger view' ),
        134: ( 'FGP', 'M1 friction ridge generalized position' ),
        135: ( 'FQD', 'M1 friction ridge quality data' ),
        136: ( 'NOM', 'M1 number of minutiae' ),
        137: ( 'FMD', 'M1 finger minutiae data' ),
        138: ( 'RCI', 'M1 ridge count information' ),
        139: ( 'CIN', 'M1 core information' ),
        140: ( 'DIN', 'M1 delta information' ),
        141: ( 'ADA', 'M1 additional delta angles' ),
        176: ( 'OOD', 'Other feature sets - owner or developer' ),
        177: ( 'PAG', 'Other feature sets - processing algorithm' ),
        178: ( 'SOD', 'Other feature sets - system or device' ),
        179: ( 'DTX', 'Other feature sets \x96contact information' ),
        300: ( 'ROI', 'EFS region of interest' ),
        301: ( 'ORT', 'EFS orientation' ),
        302: ( 'FPP', 'EFS finger - palm - plantar position' ),
        303: ( 'FSP', 'EFS feature set profile' ),
        307: ( 'PAT', 'EFS pattern classification' ),
        308: ( 'RQM', 'EFS ridge quality/confidence map' ),
        309: ( 'RQF', 'EFS ridge quality map format' ),
        310: ( 'RFM', 'EFS ridge flow map' ),
        311: ( 'RFF', 'EFS ridge flow map format' ),
        312: ( 'RWM', 'EFS ridge wavelength map' ),
        313: ( 'RWF', 'EFS ridge wavelength map format' ),
        314: ( 'TRV', 'EFS tonal reversal' ),
        315: ( 'PLR', 'EFS possible lateral reversal' ),
        316: ( 'FQM', 'EFS friction ridge quality metric' ),
        317: ( 'PGS', 'EFS possible growth or shrinkage' ),
        320: ( 'COR', 'EFS cores' ),
        321: ( 'DEL', 'EFS deltas' ),
        322: ( 'CDR', 'EFS core delta ridge counts' ),
        323: ( 'CPR', 'EFS center point of reference' ),
        324: ( 'DIS', 'EFS distinctive features' ),
        325: ( 'NCOR', 'EFS no cores present' ),
        326: ( 'NDEL', 'EFS no deltas present' ),
        327: ( 'NDIS', 'EFS no distinctive features present' ),
        331: ( 'MIN', 'EFS minutiae' ),
        332: ( 'MRA', 'EFS minutiae ridge count algorithm' ),
        333: ( 'MRC', 'EFS minutiae ridge counts' ),
        334: ( 'NMIN', 'EFS no minutiae present' ),
        335: ( 'RCC', 'EFS minutiae ridge count confidence' ),
        340: ( 'DOT', 'EFS dots' ),
        341: ( 'INR', 'EFS incipient ridges' ),
        342: ( 'CLD', 'EFS creases and linear discontinuities' ),
        343: ( 'REF', 'EFS ridge edge features' ),
        344: ( 'NPOR', 'EFS no pores present' ),
        345: ( 'POR', 'EFS pores' ),
        346: ( 'NDOT', 'EFS no dots present' ),
        347: ( 'NINR', 'EFS no incipient ridges present' ),
        348: ( 'NCLD', 'EFS no creases or linear discontinuities present' ),
        349: ( 'NREF', 'EFS no ridge edge features present' ),
        350: ( 'MFD', 'EFS method of feature detection' ),
        351: ( 'COM', 'EFS comments' ),
        352: ( 'LPM', 'EFS latent processing method' ),
        353: ( 'EAA', 'EFS examiner analysis assessment' ),
        354: ( 'EOF ', 'EFS evidence of fraud' ),
        355: ( 'LSB', 'EFS latent substrate' ),
        356: ( 'LMT', 'EFS latent matrix' ),
        357: ( 'LQI', 'EFS local quality issues' ),
        360: ( 'AOC', 'EFS area of correspondence' ),
        361: ( 'CPF', 'EFS corresponding points or features' ),
        362: ( 'ECD', 'EFS examiner comparison determination' ),
        363: ( 'RRC', 'EFS relative rotation of corresponding print' ),
        372: ( 'SIM', 'EFS skeletonized image' ),
        373: ( 'RPS', 'EFS ridge path segments' ),
        380: ( 'TPL', 'EFS temporary lines' ),
        381: ( 'FCC', 'EFS feature color - comment' ),
        901: ( 'ULA', 'Universal latent workstation annotation information' ),
        902: ( 'ANN', 'Annotation information' ),
        903: ( 'DUI', 'Device unique identifier' ),
        904: ( 'MMS', 'Make/model/serial number' )
    },
    10: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'IMT', 'Image type' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'PHD', 'Photo capture date' ),
        6:   ( 'HLL', 'Horizontal line length' ),
        7:   ( 'VLL', 'Vertical line length' ),
        8:   ( 'SLC', 'Scale units' ),
        9:   ( 'THPS', 'Transmitted horizontal pixel scale' ),
        10:  ( 'TVPS', 'Transmitted vertical pixel scale' ),
        11:  ( 'CGA', 'Compression algorithm' ),
        12:  ( 'CSP', 'Color space' ),
        13:  ( 'SAP', 'Subject acquisition profile' ),
        14:  ( 'FIP', 'Face image bounding box coordinates in full image' ),
        15:  ( 'FPFI', 'Face image path coordinates in full image' ),
        16:  ( 'SHPS', 'Scanned horizontal pixel scale' ),
        17:  ( 'SVPS', 'Scanned vertical pixel scale' ),
        18:  ( 'DIST', 'Distortion' ),
        19:  ( 'LAF', 'Lighting artifacts' ),
        20:  ( 'POS', 'Subject pose' ),
        21:  ( 'POA', 'Pose offset angle' ),
        23:  ( 'PAS', 'Photo acquisition source' ),
        24:  ( 'SQS', 'Subject quality score' ),
        25:  ( 'SPA', 'Subject pose angles' ),
        26:  ( 'SXS', 'Subject facial description' ),
        27:  ( 'SEC ', 'Subject eye color' ),
        28:  ( 'SHC', 'Subject hair color' ),
        29:  ( 'FFP', '2D facial feature points' ),
        30:  ( 'DMM', 'Device monitoring mode' ),
        31:  ( 'TMC', 'Tiered markup collection' ),
        32:  ( '3DF', '3D facial feature points' ),
        33:  ( 'FEC', 'Feature contours' ),
        34:  ( 'ICDR', 'Image capture date range estimate' ),
        38:  ( 'COM', 'Comment' ),
        39:  ( 'T10', 'Type-10 reference number' ),
        40:  ( 'SMT', 'NCIC SMT code' ),
        41:  ( 'SMS', 'SMT size or size of injury or identifying characteristic' ),
        42:  ( 'SMD', 'SMT descriptors' ),
        43:  ( 'COL', 'Tattoo color' ),
        44:  ( 'ITX', 'Image transform' ),
        45:  ( 'OCC', 'Occlusions' ),
        46:  ( 'SUB', 'Image subject condition' ),
        47:  ( 'CON', 'Capture organization name' ),
        48:  ( 'PID', 'Suspected patterned injury detail' ),
        49:  ( 'CID', 'Cheiloscopic image data' ),
        50:  ( 'VID', 'Dental visual image data information' ),
        51:  ( 'RSP', 'Ruler or scale presence' ),
        902: ( 'ANN', 'Annotation information' ),
        903: ( 'DUI', 'Device unique identifier' ),
        904: ( 'MMS', 'Make/model/serial number' ),
        992: ( 'T2C', 'Type-2 Record cross reference' ),
        993: ( 'SAN', 'Source agency name' ),
        995: ( 'ASC', 'Associated context' ),
        996: ( 'HAS', 'Hash' ),
        997: ( 'SOR', 'Source representation' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DATA', 'Body part image' )
    },
    11: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'AOD', 'Audio object descriptor code' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'VRSO', 'Voice recording source organization' ),
        6:   ( 'VRC', 'Voice recording content descriptor' ),
        7:   ( 'AREC', 'Audio recording device' ),
        8:   ( 'AQS', 'Acquisition source' ),
        9:   ( 'RCD', 'Record creation date' ),
        10:  ( 'VRD', 'Voice recording creation date' ),
        11:  ( 'TRD', 'Total recording duration' ),
        12:  ( 'PMO', 'Physical media object' ),
        13:  ( 'CONT', 'Container' ),
        14:  ( 'CDC', 'Codec' ),
        21:  ( 'RED', 'Redaction' ),
        22:  ( 'RDD', 'Redaction diary' ),
        23:  ( 'DIS', 'Discontinuities' ),
        24:  ( 'DCD', 'Discontinuities diary' ),
        25:  ( 'VOC', 'Vocal content' ),
        26:  ( 'VCD', 'Vocal content diary' ),
        27:  ( 'OCON', 'Other content' ),
        28:  ( 'OCD', 'Other content diary' ),
        32:  ( 'SGEO', 'Vocal segment geographical information' ),
        33:  ( 'SQV', 'Vocal segment quality values' ),
        34:  ( 'VCI', 'Vocal segment collision identifier' ),
        35:  ( 'PPY', 'Vocal segment processing priority' ),
        36:  ( 'VSCD', 'Vocal segment content description' ),
        37:  ( 'SCC', 'Vocal segment speaker characteristics' ),
        38:  ( 'SCH', 'Vocal segment channel' ),
        51:  ( 'COM', 'Comment' ),
        902: ( 'ANN', 'Annotation information' ),
        993: ( 'SAN', 'Source agency name' ),
        994: ( 'EFR', 'External file reference' ),
        995: ( 'ASC', 'Associated Context' ),
        996: ( 'HAS', 'Hash' ),
        997: ( 'SOR', 'Source representation' ),
        999: ( 'DATA', 'Voice record data' )
    },
    12: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'FDS', 'Forensic dental setting' ),
        4:   ( 'SRC', 'Source agency identification ID' ),
        6:   ( 'DSI', 'Dental subject information' ),
        7:   ( 'ODES', 'Original dental encoding system information' ),
        8:   ( 'TDES', 'Transmittal dental encoding system information' ),
        9:   ( 'HDD', 'Dental history data detail' ),
        10:  ( 'TDD', 'Tooth data detail' ),
        11:  ( 'MDD', 'Mouth data detail' ),
        12:  ( 'DSTI', 'Dental casts and impressions' ),
        20:  ( 'COM', 'Comment' ),
        47:  ( 'CON', 'Capture organization name' ),
        902: ( 'ANN', 'Annotation information' ),
        990: ( 'T10C', 'Type-10 Record cross reference' ),
        991: ( 'T22C', 'Type-22 Record cross reference' ),
        992: ( 'T2C', 'Type-2 Record cross reference' ),
        993: ( 'SAN', 'Source agency name' ),
        994: ( 'EFR', 'External file reference' ),
        995: ( 'ASC', 'Associated context' ),
        996: ( 'HAS', 'Hash' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DATA', 'Dental chart data' )
    },
    13: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'IMP', 'Impression type' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'LCD', 'Latent capture date' ),
        6:   ( 'HLL', 'Horizontal line length' ),
        7:   ( 'VLL', 'Vertical line length' ),
        8:   ( 'SLC', 'Scale units' ),
        9:   ( 'THPS', 'Transmitted horizontal pixel scale' ),
        10:  ( 'TVPS', 'Transmitted vertical pixel scale' ),
        11:  ( 'CGA', 'Compression algorithm' ),
        12:  ( 'BPX', 'Bits per pixel' ),
        13:  ( 'FGP', 'Friction ridge generalized position' ),
        14:  ( 'SPD', 'Search position descriptors' ),
        15:  ( 'PPC', 'Print position coordinates' ),
        16:  ( 'SHPS', 'Scanned horizontal pixel scale' ),
        17:  ( 'SVPS', 'Scanned vertical pixel scale' ),
        18:  ( 'RSP', 'Ruler or scale presence' ),
        19:  ( 'REM', 'Resolution method' ),
        20:  ( 'COM', 'Comment' ),
        24:  ( 'LQM', 'Latent quality metric' ),
        46:  ( 'SUB', 'Image subject condition' ),
        47:  ( 'CON', 'Capture organization name' ),
        902: ( 'ANN', 'Annotation information' ),
        903: ( 'DUI', 'Device unique identifier' ),
        904: ( 'MMS', 'Make/model/serial number' ),
        993: ( 'SAN', 'Source agency name' ),
        995: ( 'ASC', 'Associated context' ),
        996: ( 'HAS', 'Hash' ),
        997: ( 'SOR', 'Source representation' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DATA', 'Latent friction ridge image' )
    },
    14: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'IMP', 'Impression type' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'FCD', 'Fingerprint capture date' ),
        6:   ( 'HLL', 'Horizontal line length' ),
        7:   ( 'VLL', 'Vertical line length' ),
        8:   ( 'SLC', 'Scale units' ),
        9:   ( 'THPS', 'Transmitted horizontal pixel scale' ),
        10:  ( 'TVPS', 'Transmitted vertical pixel scale' ),
        11:  ( 'CGA', 'Compression algorithm' ),
        12:  ( 'BPX', 'Bits per pixel' ),
        13:  ( 'FGP', 'Friction ridge generalized position' ),
        14:  ( 'PPD', 'Print position descriptors' ),
        15:  ( 'PPC', 'Print position coordinates' ),
        16:  ( 'SHPS', 'Scanned horizontal pixel scale' ),
        17:  ( 'SVPS', 'Scanned vertical pixel scale' ),
        18:  ( 'AMP', 'Amputated or bandaged' ),
        20:  ( 'COM', 'Comment' ),
        21:  ( 'SEG', 'Finger segment position' ),
        22:  ( 'NQM', 'NIST quality metric' ),
        23:  ( 'SQM', 'Segmentation quality metric' ),
        24:  ( 'FQM', 'Fingerprint quality metric' ),
        25:  ( 'ASEG', 'Alternate finger segment position(s)' ),
        26:  ( 'SCF', 'Simultaneous capture' ),
        27:  ( 'SIF', 'Stitched image flag' ),
        30:  ( 'DMM', 'Device monitoring mode' ),
        31:  ( 'FAP', 'Subject acquisition profile \x96 fingerprint' ),
        46:  ( 'SUB', 'Image subject condition' ),
        47:  ( 'CON', 'Capture organization name' ),
        902: ( 'ANN', 'Annotation information' ),
        903: ( 'DUI', 'Device unique identifier' ),
        904: ( 'MMS', 'Make/model/serial number' ),
        993: ( 'SAN', 'Source agency name' ),
        995: ( 'ASC', 'Associated context' ),
        996: ( 'HAS', 'Hash' ),
        997: ( 'SOR', 'Source representation' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DATA', 'Fingerprint image' )
    },
    15: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'IMP', 'Impression type' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'PCD', 'Palm print capture date' ),
        6:   ( 'HLL', 'Horizontal line length' ),
        7:   ( 'VLL', 'Vertical line length' ),
        8:   ( 'SLC', 'Scale units' ),
        9:   ( 'THPS', 'Transmitted horizontal pixel scale' ),
        10:  ( 'TVPS', 'Transmitted vertical pixel scale' ),
        11:  ( 'CGA', 'Compression algorithm' ),
        12:  ( 'BPX', 'Bits per pixel' ),
        13:  ( 'FGP', 'Friction ridge generalized position' ),
        16:  ( 'SHPS', 'Scanned horizontal pixel scale' ),
        17:  ( 'SVPS', 'Scanned vertical pixel scale' ),
        18:  ( 'AMP', 'Amputated or bandaged' ),
        20:  ( 'COM', 'Comment' ),
        21:  ( 'SEG', 'Palm segment position' ),
        24:  ( 'PQM', 'Palm quality metric' ),
        30:  ( 'DMM', 'Device monitoring mode' ),
        46:  ( 'SUB', 'Subject condition' ),
        47:  ( 'CON', 'Capture organization name' ),
        902: ( 'ANN', 'Annotation information' ),
        903: ( 'DUI', 'Device unique identifier' ),
        904: ( 'MMS', 'Make/model/serial number' ),
        993: ( 'SAN', 'Source agency name' ),
        995: ( 'ASC', 'Associated context' ),
        996: ( 'HAS', 'Hash' ),
        997: ( 'SOR', 'Source representation' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DATA', 'Palm print image' )
    },
    16: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'UDI', 'User-defined image type' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'UTD', 'User-defined image test capture date' ),
        6:   ( 'HLL', 'Horizontal line length' ),
        7:   ( 'VLL', 'Vertical line length' ),
        8:   ( 'SLC', 'Scale units' ),
        9:   ( 'THPS', 'Transmitted horizontal pixel scale' ),
        10:  ( 'TVPS', 'Transmitted vertical pixel scale' ),
        11:  ( 'CGA', 'Compression algorithm' ),
        12:  ( 'BPX', 'Bits per pixel' ),
        13:  ( 'CSP', 'Color space' ),
        16:  ( 'SHPS', 'Scanned horizontal pixel scale' ),
        17:  ( 'SVPS', 'Scanned vertical pixel scale' ),
        20:  ( 'COM', 'Comment' ),
        24:  ( 'UQS', 'User-defined image quality metric' ),
        30:  ( 'DMM', 'Device monitoring mode' ),
        902: ( 'ANN', 'Annotation information' ),
        903: ( 'DUI', 'Device unique identifier' ),
        904: ( 'MMS', 'Make/model/serial number' ),
        993: ( 'SAN', 'Source agency name' ),
        995: ( 'ASC', 'Associated context' ),
        996: ( 'HAS', 'Hash' ),
        997: ( 'SOR', 'Source representation' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DAT A', 'Test data' )
    },
    17: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'ELR', 'Eye Label' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'ICD', 'Iris capture date' ),
        6:   ( 'HLL', 'Horizontal line length' ),
        7:   ( 'VLL', 'Vertical line length' ),
        8:   ( 'SLC', 'Scale units' ),
        9:   ( 'THPS', 'Transmitted horizontal pixel scale' ),
        10:  ( 'TVPS', 'Transmitted vertical pixel scale' ),
        11:  ( 'CGA', 'Compression algorithm' ),
        12:  ( 'BPX', 'Bits per pixel' ),
        13:  ( 'CSP', 'Color space' ),
        14:  ( 'RAE', 'Rotation angle of eye' ),
        15:  ( 'RAU', 'Rotation uncertainty' ),
        16:  ( 'IPC', 'Image property code' ),
        17:  ( 'DUI', 'Device unique identifier' ),
        19:  ( 'MMS', 'Make/model/serial number' ),
        20:  ( 'ECL', 'Eye color' ),
        21:  ( 'COM', 'Comment' ),
        22:  ( 'SHPS', 'Scanned horizontal pixel scale' ),
        23:  ( 'SVPS', 'Scanned vertical pixel scale' ),
        24:  ( 'IQS', 'Image quality score' ),
        25:  ( 'EAS', 'Effective acquisition spectrum' ),
        26:  ( 'IRD', 'Iris diameter' ),
        27:  ( 'SSV', 'Specified spectrum values' ),
        28:  ( 'DME', 'Damaged or missing eye' ),
        30:  ( 'DMM', 'Device monitoring mode' ),
        31:  ( 'IAP', 'Subject acquisition profile \x96 iris' ),
        32:  ( 'ISF', 'Iris storage format' ),
        33:  ( 'IPB', 'Iris pupil boundary' ),
        34:  ( 'ISB', 'Iris sclera boundary' ),
        35:  ( 'UEB', 'Upper eyelid boundary' ),
        36:  ( 'LEB', 'Lower eyelid boundary' ),
        37:  ( 'NEO', 'Non-eyelid occlusions' ),
        40:  ( 'RAN', 'Range' ),
        41:  ( 'GAZ', 'Frontal gaze' ),
        902: ( 'ANN', 'Annotation information' ),
        993: ( 'SAN', 'Source agency name' ),
        995: ( 'ASC', 'Associated context' ),
        996: ( 'HAS', 'Hash' ),
        997: ( 'SOR', 'Source representation' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DATA', 'Iris image data' )
    },
    18: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'DLS', 'DNA laboratory setting' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'NAL', 'Number of analyses flag' ),
        6:   ( 'SDI', 'Sample donor information' ),
        7:   ( 'COPR', 'Claimed or purported relationship' ),
        8:   ( 'VRS', 'Validated relationship' ),
        9:   ( 'PED', 'Pedigree information' ),
        10:  ( 'STY', 'Sample type' ),
        11:  ( 'STI', 'Sample typing information' ),
        12:  ( 'SCM', 'Sample collection method' ),
        13:  ( 'SCD', 'Sample collection date' ),
        14:  ( 'PSD', 'Profile storage date' ),
        15:  ( 'DPD', 'DNA profile data' ),
        16:  ( 'STR', 'Autosomal STR, X-STR and Y-STR' ),
        17:  ( 'DMD', 'Mitochondrial DNA data' ),
        18:  ( 'UDP', 'DNA user-defined profile data' ),
        19:  ( 'EPD', 'Electropherogram description' ),
        20:  ( 'DGD', 'DNA genotype distribution' ),
        21:  ( 'GAP', 'DNA genotype allele pair' ),
        22:  ( 'COM', 'Comment' ),
        23:  ( 'EPL', 'Electropherogram ladder' ),
        902: ( 'ANN', 'Annotation information' ),
        992: ( 'T2C', 'Type-2 Record cross reference' ),
        993: ( 'SAN', 'Source agency name' ),
        995: ( 'ASC', 'Associated context' ),
        998: ( 'GEO', 'Geographic sample acquisition location' )
    },
    19: {
        1: ( 'LEN', 'Logical record length' ),
        2: ( 'IDC', 'Information designation character' ),
        3: ( 'IMP', 'Impression type' ),
        4: ( 'SRC', 'Source agency' ),
        5: ( 'PCD', 'Plantar capture date' ),
        6: ( 'HLL', 'Horizontal line length' ),
        7: ( 'VLL', 'Vertical line length' ),
        8: ( 'SLC', 'Scale units' ),
        9: ( 'THPS', 'Transmitted horizontal pixel scale' ),
        10: ( 'TVPS', 'Transmitted vertical pixel scale' ),
        11: ( 'CGA', 'Compression algorithm' ),
        12: ( 'BPX', 'Bits per pixel' ),
        13: ( 'FGP', 'Friction ridge (plantar) generalized position' ),
        16: ( 'SHPS', 'Scanned horizontal pixel scale' ),
        17: ( 'SVPS', 'Scanned vertical pixel scale' ),
        18: ( 'AMP', 'Amputated or bandaged' ),
        19: ( 'FSP', 'Friction ridge - toe segment position(s)' ),
        20: ( 'COM', 'Comment' ),
        21: ( 'SEG', 'Plantar segment position' ),
        24: ( 'FQM', 'Friction ridge - plantar print quality metric' ),
        30: ( 'DMM', 'Device monitoring mode' ),
        46: ( 'SUB', 'Image subject condition' ),
        47: ( 'CON', 'Capture organization name' ),
        902: ( 'ANN', 'Annotation information' ),
        903: ( 'DUI', 'Device unique identifier' ),
        904: ( 'MMS', 'Make/model/serial number' ),
        993: ( 'SAN', 'Source agency name' ),
        995: ( 'ASC', 'Associated context' ),
        996: ( 'HAS', 'Hash' ),
        997: ( 'SOR', 'Source representation' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DATA', 'Plantar image' )
    },
    20: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'CAR', 'SRN cardinality' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'SRD', 'Source representation date' ),
        6:   ( 'HLL', 'Horizontal line length' ),
        7:   ( 'VLL', 'Vertical line length' ),
        8:   ( 'SLC', 'Scale units' ),
        9:   ( 'THPS', 'Transmitted horizontal pixel scale' ),
        10:  ( 'TVPS', 'Transmitted vertical pixel scale' ),
        11:  ( 'CGA', 'Compression algorithm' ),
        12:  ( 'BPX', 'Bits per pixel' ),
        13:  ( 'CSP', 'Color space' ),
        14:  ( 'AQS', 'Acquisition source' ),
        15:  ( 'SFT', 'Source representation format' ),
        16:  ( 'SEG', 'Segments' ),
        17:  ( 'SHPS', 'Scanned horizontal pixel scale' ),
        18:  ( 'SVPS', 'Scanned vertical pixel scale' ),
        19:  ( 'TIX', 'Time index' ),
        20:  ( 'COM', 'Comment' ),
        21:  ( 'SRN', 'Source representation number' ),
        22:  ( 'ICDR', 'Imagery capture date range estimate' ),
        902: ( 'ANN', 'Annotation information' ),
        903: ( 'DUI', 'Device unique identifier' ),
        904: ( 'MMS', 'Make/model/serial number' ),
        993: ( 'SAN', 'Source agency name' ),
        994: ( 'EFR', 'External file reference' ),
        995: ( 'ASC', 'Associated context' ),
        996: ( 'HAS', 'Hash' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DATA', 'Source representation data' )
        },
    21: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'ACD ', 'Associated context date' ),
        6:   ( 'MDI', 'Medical device information' ),
        15:  ( 'AFT', 'Associated context format' ),
        16:  ( 'SEG', 'Segments' ),
        19:  ( 'TIX', 'Time index' ),
        20:  ( 'COM', 'Comment' ),
        21:  ( 'ACN', 'Associated context number' ),
        22:  ( 'ICDR', 'Imagery capture date range estimate' ),
        46:  ( 'SUB', 'Image subject condition' ),
        47:  ( 'CON', 'Capture organization name' ),
        902: ( 'ANN', 'Annotation information' ),
        993: ( 'SAN', 'Source agency name' ),
        994: ( 'EFR', 'External file reference' ),
        996: ( 'HAS', 'Hash' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DATA', 'Associated context data' )
    },
    22: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information Designation Character' ),
        3:   ( 'ICD', 'Imagery capture date' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'ICDR', 'Imagery capture date range estimate' ),
        6:   ( 'BIC', 'Body image code' ),
        20:  ( 'COM', 'Comment' ),
        46:  ( 'SUB', 'Image subject condition' ),
        47:  ( 'CON', 'Capture organization name' ),
        101: ( 'ITYP', 'Non-photographic imagery type code' ),
        102: ( 'IFMT', 'Non-photographic imagery data format code' ),
        103: ( 'DRID', 'Dental radiograph image data' ),
        902: ( 'ANN', 'Annotation information' ),
        903: ( 'DUI', 'Device unique identifier' ),
        904: ( 'MMS', 'Make/model/serial number' ),
        992: ( 'T2C', 'Type-2 Record cross reference' ),
        993: ( 'SAN', 'Source agency name' ),
        994: ( 'EFR', 'External file reference' ),
        995: ( 'ASC', 'Associated context' ),
        996: ( 'HAS', 'Hash' ),
        997: ( 'SOR', 'Source representation' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DATA', 'Imagery data block' )
    },
    98: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        3:   ( 'DFO', 'IA data format owner' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'DFT', 'IA data format type' ),
        6:   ( 'DCD', 'IA data creation date' ),
        900: ( 'ALF', 'Audit log' ),
        901: ( 'ARN', 'Audit revision number' ),
        993: ( 'SAN', 'Source agency name' )
    },
    99: {
        1:   ( 'LEN', 'Logical record length' ),
        2:   ( 'IDC', 'Information designation character' ),
        4:   ( 'SRC', 'Source agency' ),
        5:   ( 'BCD', 'Biometric capture date' ),
        100: ( 'HDV', 'CBEFF header version' ),
        101: ( 'BTY', 'Biometric type' ),
        102: ( 'BDQ', 'Biometric data quality' ),
        103: ( 'BFO', 'BDB format owner' ),
        104: ( 'BFT', 'BDB format type' ),
        902: ( 'ANN', 'Annotation information' ),
        903: ( 'DUI', 'Device unique identifier' ),
        904: ( 'MMS', 'Make/model/serial number' ),
        993: ( 'SAN', 'Source agency name' ),
        995: ( 'ASC', 'Associated context' ),
        996: ( 'HAS', 'Hash' ),
        997: ( 'SOR', 'Source representation' ),
        998: ( 'GEO', 'Geographic sample acquisition location' ),
        999: ( 'DATA', 'Biometric data block' )
    }
}

################################################################################
#
#    Special delimiters
#
################################################################################

FS = chr( 28 )
GS = chr( 29 )
RS = chr( 30 )
US = chr( 31 )
CO = ':'
DO = '.'

################################################################################
# 
#    Exceptions
# 
################################################################################

class needIDC( BaseException ):
    pass

class intIDC( BaseException ):
    pass

class nonexistingIDC( BaseException ):
    pass

class minutiaeFormatNotSupported( BaseException ):
    pass

class notImplemented( BaseException ):
    pass

class ntypeNotFound( BaseException ):
    pass

class idcNotFound( BaseException ):
    pass

class tagNotFound( BaseException ):
    pass

################################################################################
# 
#    NIST object class
# 
################################################################################

class NIST( object ):
    def __init__( self, init = None ):
        """
            Initialization of the NIST Object.
            
            All biometric information are stored in the self.data recursive
            default dictionary object. The information is stored as following:
            
                self.data[ ntype ][ idc ][ tagid ]
            
            To get and set data, use the self.get_field() and self_set_field()
            functions.
        """
        debug.info( "Initialization of the NIST object" )
        
        self.filename = None
        self.data = defaultdict( dict )
        
        self.ntypeInOrder = []
        
        if init != None:
            self.load_auto( init )
        
    ############################################################################
    #
    #    Loading functions
    #
    ############################################################################
    
    @deprecated( "user the read() function instead" )
    def loadFromFile( self, infile ):
        return self.read( infile )
    
    def read( self, infile ):
        """
            Open the 'infile' file and transmit the data to the 'load' function.
        """
        debug.info( "Reading from file : %s" % infile )
        
        self.filename = infile
    
        with open( infile, "rb" ) as fp:
            data = fp.read()
        
        self.load( data )
    
    def load_auto( self, p ):
        """
            Function to detect and load automatically the 'p' value passed in
            parameter. The argument 'p' can be a string (URI to the file to
            load) or a NIST object (a copy will be done in the current object).
        """
        if type( p ) == str:
            self.read( p )
            
        elif isinstance( p, NIST ):
            # Get the list of all attributes stored in the NIST object.
            attributes = inspect.getmembers( p, lambda a: not( inspect.isroutine( a ) ) )
            
            # Copy all the values to the current NIST object. 
            for name, value in [ a for a in attributes if not( a[ 0 ].startswith( '__' ) and a[ 0 ].endswith( '__' ) ) ]:
                super( NIST, self ).__setattr__( name, value )
    
    def load( self, data ):
        """
            Load from the data passed in parameter, and populate all internal dictionaries.
        """
        debug.info( "Loading object" )
        
        records = data.split( FS )
        
        #    NIST Type01
        debug.debug( "Type-01 parsing", 1 )
        
        t01 = records[ 0 ].split( GS )
        record01 = {}
        
        for field in t01:
            tag, ntype, tagid, value = fieldSplitter( field )
            
            if tagid == 1:
                LEN = int( value )
            
            if tagid == 3:
                self.process_fileContent( value )
            
            debug.debug( "%d.%03d:\t%s" % ( ntype, tagid, value ), 2 )
            record01[ tagid ] = value
        
        self.data[ 1 ][ 0 ] = record01  # Store in IDC = 0 even if the standard implies no IDC for Type-01
        data = data[ LEN: ]
        
        #    NIST Type02 and after
        debug.debug( "Expected Types : %s" % ", ".join( map( str, self.ntypeInOrder ) ), 1 )
        
        for ntype in self.ntypeInOrder:
            debug.debug( "Type-%02d parsing" % ntype, 1 )
            LEN = 0
            
            if ntype in [ 2, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 98, 99 ]:
                current_type = data.split( FS )
                
                tx = current_type[ 0 ].split( GS )
                
                recordx = {}
                offset = 0
                idc = -1
                
                for t in tx:
                    try:
                        tag, ntype, tagid, value = fieldSplitter( t )
                    except:
                        tagid = 999
                    
                    if tagid == 1:
                        LEN = int( value )
                    elif tagid == 2:
                        idc = int( value )
                    elif tagid == 999:
                        if ntype == 9:
                            end = LEN
                        else:
                            end = LEN - 1
                        
                        offset += len( tag ) + 1
                        
                        value = data[ offset : end ]
                        debug.debug( "%d.%03d:\t%s" % ( ntype, tagid, bindump( value ) ), 2 )
                        recordx[ tagid ] = value
                        break
                        
                    debug.debug( "%d.%03d:\t%s" % ( ntype, tagid, value ), 2 )
                    recordx[ tagid ] = value
                    offset += len( t ) + 1
                    
                self.data[ ntype ][ idc ] = recordx
            
            elif ntype == 4:
                iter = stringIterator( data )
                
                LEN = binstring_to_int( iter.take( 4 ) )
                IDC = binstring_to_int( iter.take( 1 ) )
                IMP = binstring_to_int( iter.take( 1 ) )
                FGP = binstring_to_int( iter.take( 1 ) )
                iter.take( 5 )
                ISR = binstring_to_int( iter.take( 1 ) )
                HLL = binstring_to_int( iter.take( 2 ) )
                VLL = binstring_to_int( iter.take( 2 ) )
                GCA = binstring_to_int( iter.take( 1 ) )
                DAT = iter.take( LEN - 18 )
                
                LEN = str( LEN )
                IDC = str( IDC )
                IMP = str( IMP )
                FGP = str( FGP )
                ISR = str( ISR )
                HLL = str( HLL )
                VLL = str( VLL )
                GCA = str( GCA )
                
                debug.debug( "Parsing Type-04 IDC %s" % IDC, 2 )
                debug.debug( "LEN: %s" % LEN, 3 )
                debug.debug( "IDC: %s" % IDC, 3 )
                debug.debug( "IMP: %s" % IMP, 3 )
                debug.debug( "FGP: %s" % FGP, 3 )
                debug.debug( "ISR: %s" % ISR, 3 )
                debug.debug( "HLL: %s" % HLL, 3 )
                debug.debug( "VLL: %s" % VLL, 3 )
                debug.debug( "GCA: %s (%s)" % ( GCA, decode_gca( GCA ) ), 3 )
                debug.debug( "DAT: %s" % bindump( DAT ), 3 )
                
                nist04 = {
                    1:   LEN,
                    2:   IDC,
                    3:   IMP,
                    4:   FGP,
                    5:   ISR,
                    6:   HLL,
                    7:   VLL,
                    8:   GCA,
                    999: DAT
                }
                
                IDC = int( IDC )
                self.data[ ntype ][ IDC ] = nist04
                
                LEN = int( LEN )
            
            else:
                debug.critical( boxer( "Unknown Type-%02d" % ntype, "The Type-%02d is not supported. It will be skipped in the pasing process. Contact the developer for more information." % ntype ) )
                
                if data.startswith( str( ntype ) ):
                    _, _, _, LEN = fieldSplitter( data[ 0 : data.find( GS ) ] )
                    LEN = int( LEN )
                else:
                    LEN = binstring_to_int( data[ 0 : 4 ] )
            
            data = data[ LEN: ]
            
    def process_fileContent( self, data ):
        """
            Function to process the 1.003 field passed in parameter.
        """
        data = map( lambda x: map( int, x.split( US ) ), data.split( RS ) )
        
        self.nbLogicalRecords = data[ 0 ][ 1 ]
        
        for ntype, idc in data[ 1: ]:
            self.ntypeInOrder.append( ntype )
    
    ############################################################################
    # 
    #    Content delete
    # 
    ############################################################################
    
    def delete( self, ntype = None, idc = -1 ):
        """
            Function to delete a specific Type-'ntype', IDC or field.
            
            To delete the Type-09 record:
                n.delete( 9 )
            
            To delete the Type-09 IDC 0:
                n.delete( 9, 0 )
            
            To delete the field "9.012":
                n.delete( "9.012" )
            
            To delete the field "9.012" IDC 0:
                n.delete( "9.012", 0 )
            
        """
        if type( ntype ) == str:
            tag = ntype
            self.delete_tag( tag, idc )
        else:
            if idc < 0:
                self.delete_ntype( ntype )
            else:
                self.delete_idc( ntype, idc )
        
    def delete_ntype( self, ntype ):
        """
            Delete the 'ntype' record.
        """
        if self.data.has_key( ntype ):
            del( self.data[ ntype ] )
        else:
            raise ntypeNotFound
    
    def delete_idc( self, ntype, idc ):
        """
            Delete the specific IDC passed in parameter from 'ntype' record.
        """
        if self.data.has_key( ntype ) and self.data[ ntype ].has_key( idc ):
            del( self.data[ ntype ][ idc ] )
        else:
            raise idcNotFound
    
    def delete_tag( self, tag, idc = -1 ):
        """
            Delete the field 'tag' from the specific IDC.
        """
        ntype, tagid = tagSplitter( tag )
        
        idc = self.checkIDC( ntype, idc )
        
        if self.data.has_key( ntype ) and self.data[ ntype ].has_key( idc ):
            del( self.data[ ntype ][ idc ][ tagid ] )
        else:
            raise tagNotFound
    
    ############################################################################
    # 
    #    Dumping
    # 
    ############################################################################
    
    def dump_record( self, ntype, idc = 0, fullname = False ):
        """
            Dump a specific ntype - IDC record.
        """
        d = self.data[ ntype ][ idc ]
        
        s = ""
        for t in sorted( d.keys() ):
            lab = get_label( ntype, t, fullname )
            header = "%02d.%03d %s" % ( ntype, t, lab )
            
            if t == 999:
                field = bindump( d[ t ] )
            else:
                if ntype == 18 and t == 19:
                    field = bindump( d[ t ] )
                else:
                    field = d[ t ]
            
            debug.debug( "%s: %s" % ( header, field ), 2 )
            s = s + leveler( "%s: %s\n" % ( header, field ), 1 )
        
        return s
    
    def dump( self, fullname = False ):
        """
            Return a readable version of the NIST object. Printable on screen.
        """
        debug.info( "Dumping NIST" )
        
        s = ""
        
        for ntype in self.get_ntype():
            debug.debug( "NIST Type-%02d" % ntype, 1 )
            
            if ntype == 1:
                s += "NIST Type-%02d\n" % ntype
                s += self.dump_record( ntype, 0, fullname ) 
            else:
                for idc in self.get_idc( ntype ):
                    s += "NIST Type-%02d (IDC %d)\n" % ( ntype, idc )
                    s += self.dump_record( ntype, idc, fullname )
        
        return s
    
    def dumpbin( self ):
        """
            Return a binary dump of the NIST object. Writable in a file ("wb" mode).
        """
        debug.info( "Dumping NIST in binary" )
        
        self.clean()
        self.patch_to_standard()
        
        outnist = ""
        
        for ntype in self.get_ntype():
            for idc in self.get_idc( ntype ):
                if ntype == 4:
                    self.reset_binary_length( ntype, idc )
                    
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 1 ] ), 4 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 2 ] ), 1 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 3 ] ), 1 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 4 ] ), 1 * 8 )
                    outnist += ( chr( 0xFF ) * 5 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 5 ] ), 1 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 6 ] ), 2 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 7 ] ), 2 * 8 )
                    outnist += int_to_binstring( int( self.data[ ntype ][ idc ][ 8 ] ), 1 * 8 )
                    outnist += self.data[ ntype ][ idc ][ 999 ]
                else:
                    self.reset_alpha_length( ntype, idc )
                    
                    od = OrderedDict( sorted( self.data[ ntype ][ idc ].items() ) )
                    outnist += join( [ tagger( ntype, tagid ) + value for tagid, value in od.iteritems() ], GS ) + FS
        
        return outnist
    
    @deprecated( "use the write() function instead" )
    def saveToFile( self, outfile ):
        return self.write( outfile )
    
    def write( self, outfile ):
        """
            Write the NIST object to a specific file.
        """
        debug.info( "Write the NIST object to '%s'" % outfile )
        
        if not os.path.isdir( os.path.dirname( os.path.realpath( outfile ) ) ):
            os.makedirs( os.path.dirname( os.path.realpath( outfile ) ) )
        
        with open( outfile, "wb+" ) as fp:
            fp.write( self.dumpbin() )
    
    ############################################################################
    # 
    #    Cleaning and resetting functions
    # 
    ############################################################################
    
    def clean( self ):
        """
            Function to clean all unused fields in the self.data variable.
        """
        debug.info( "Cleaning the NIST object" )
        
        #     Delete all empty fields.
        for ntype in self.get_ntype():
            for idc in self.data[ ntype ].keys():
                for tagid in self.data[ ntype ][ idc ].keys():
                    value = self.get_field( "%d.%03d" % ( ntype, tagid ), idc )
                    if value == "" or value == None:
                        debug.debug( "Field %02d.%03d IDC %d deleted" % ( ntype, tagid, idc ), 1 )
                        del( self.data[ ntype ][ idc ][ tagid ] )
        
        #    Recheck the content of the NIST object and udpate the 1.003 field
        content = []
        for ntype in self.get_ntype()[ 1: ]:
            for idc in self.get_idc( ntype ):
                debug.debug( "Type-%02d, IDC %d present" % ( ntype, idc ), 1 )
                content.append( "%s%s%s" % ( ntype, US, idc ) )
                
        content.insert( 0, "%s%s%s" % ( 1, US, len( content ) ) )
        self.set_field( "1.003", join( content, RS ) )
        
    def patch_to_standard( self ):
        """
            Check some requirements for the NIST file. Fields checked:
                1.002
                1.011
                1.012
                4.005
                9.004
        """
        debug.info( "Patch some fields regaring the ANSI/NIST-ITL standard" )
        
        #    1.002 : Standard version:
        #        0300 : ANSI/NIST-ITL 1-2000
        #        0400 : ANSI/NIST-ITL 1-2007
        #        0500 : ANSI/NIST-ITL 1-2011
        #        0501 : ANSI/NIST-ITL 1-2011 Update: 2013 Traditional Encoding
        #        0502 : ANSI/NIST-ITL 1-2011 Update: 2015 Traditional Encoding
        debug.debug( "set version to 0501 (ANSI/NIST-ITL 1-2011 Update: 2013 Traditional Encoding)", 1 )
        self.set_field( "1.002", "0501" )
        
        #    1.011 and 1.012
        #        For transactions that do not contain Type-3 through Type-7
        #        fingerprint image records, this field shall be set to "00.00")
        if not 4 in self.get_ntype():
            debug.debug( "Fields 1.011 and 1.012 patched: no Type04 in this NIST file", 1 )
            self.set_field( "1.011", "00.00" )
            self.set_field( "1.012", "00.00" )
        
        #    Type-04
        for idc in self.get_idc( 4 ):
            #    4.005
            #        The minimum scanning resolution was defined in ANSI/NIST-
            #        ITL 1-2007 as "19.69 ppmm plus or minus 0.20 ppmm (500 ppi
            #        plus or minus 5 ppi)." Therefore, if the image scanning
            #        resolution corresponds to the Appendix F certification
            #        level (See Table 14 Class resolution with defined
            #        tolerance), a 0 shall be entered in this field.
            #        
            #        If the resolution of the Type-04 is in 500DPI +- 1%, then
            #        the 4.005 then field is set to 0, otherwise 1.
            debug.debug( "Set the conformity with the Appendix F certification level for Type-04 image", 1 )
            if 19.49 < float( self.get_field( "1.011" ) ) < 19.89:
                self.set_field( "4.005", "0", idc )
            else:
                self.set_field( "4.005", "1", idc )
        
        #    Type-09
        for idc in self.get_idc( 9 ):
            #    9.004
            #        This field shall contain an "S" to indicate that the
            #        minutiae are formatted as specified by the standard Type-9
            #        logical record field descriptions. This field shall contain
            #        a "U" to indicate that the minutiae are formatted in
            #        vendor-specific or M1- 378 terms
            if any( x in [ 5, 6, 7, 8, 9, 10, 11, 12 ] for x in self.data[ 9 ][ idc ].keys() ):
                debug.debug( "minutiae are formatted as specified by the standard Type-9 logical record field descriptions", 1 )
                self.set_field( "9.004", "S", idc )
            else:
                debug.debug( "minutiae are formatted in vendor-specific or M1-378 terms", 1 )
                self.set_field( "9.004", "U", idc )
        
    def reset_alpha_length( self, ntype, idc = 0 ):
        """
            Recalculate the LEN field of the ntype passed in parameter.
            Only for ASCII ntype.
        """
        debug.debug( "Resetting the length of Type-%02d" % ntype )
        
        self.set_field( "%d.001" % ntype, "%08d" % 0, idc )
        
        # %d.%03d:<data><GS>
        lentag = len( "%d" % ntype ) + 6
        
        recordsize = 0
        for t in self.data[ ntype ][ idc ].keys():
            recordsize += len( self.data[ ntype ][ idc ][ t ] ) + lentag
        
        diff = 8 - len( str( recordsize ) )
        recordsize -= diff
        
        self.set_field( "%d.001" % ntype, "%d" % recordsize, idc )
        
    def reset_binary_length( self, ntype, idc = 0 ):
        """
            Recalculate the LEN field of the ntype passed in parameter.
            Only for binary ntype.
        """
        debug.debug( "Resetting the length of Type-%02d" % ntype )
        
        if ntype == 4:
            recordsize = 18
            
            if self.data[ ntype ][ idc ].has_key( 999 ):
                recordsize += len( self.data[ ntype ][ idc ][ 999 ] )
                
        self.set_field( "%d.001" % ntype, "%d" % recordsize, idc )
    
    ############################################################################
    # 
    #    Minutiae functions
    # 
    ############################################################################
    
    def get_minutiae( self, format = "ixytdq", idc = -1 ):
        """
            Get the minutiae information from the field 9.012 for the IDC passed
            in argument.
            
            The parameter 'format' allow to select the data to extract:
            
                i: Index number
                x: X coordinate
                y: Y coordinate
                t: Angle theta
                d: Type designation
                q: Quality
            
            The 'format' parameter is optional. The IDC value can be passed in
            parameter even without format. The default format ('ixytdq') will be
            used.
        """
        # If the 'format' value is an int, then the function is called without
        # the 'format' argument, but the IDC is passed instead.
        if type( format ) == int:
            idc = format
            format = "ixytdq"
        
        # Get the minutiae string, without the final <FS> character.                
        minutiae = self.get_field( "9.012", idc )[ :-1 ]
        
        if minutiae == None:
            return []
        else:
            ret = []

            for m in minutiae.split( RS ):
                try:
                    id, xyt, d, q = m.split( US )
                    
                    tmp = []
                    
                    for c in format:
                        if c == "i":
                            tmp.append( id )
                        
                        if c == "x":
                            tmp.append( int( xyt[ 0:4 ] ) / 100.0 )
                        
                        if c == "y":
                            tmp.append( int( xyt[ 4:8 ] ) / 100.0 )
                        
                        if c == "t":
                            tmp.append( int( xyt[ 8:11 ] ) )
                        
                        if c == "d":
                            tmp.append( d )
                        
                        if c == "q":
                            tmp.append( q )
        
                    ret.append( tmp )
                except:
                    raise minutiaeFormatNotSupported
                
            return ret
    
    @deprecated( "use the get_minutiae( 'xy' ) instead" )
    def get_minutiaeXY( self, idc = -1 ):
        return self.get_minutiae( "xy", idc )
    
    @deprecated( "use the get_minutiae( 'xyt' ) instead" )
    def get_minutiaeXYT( self, idc = -1 ):
        return self.get_minutiae( "xyt", idc )
    
    @deprecated( "use the get_minutiae( 'xytq' ) instead" )
    def get_minutiaeXYTQ( self, idc = -1 ):
        return self.get_minutiae( "xytq", idc )
    
    def get_center( self, idc = -1 ):
        """
            Process and return the center coordinate.
        """
        c = self.get_field( "9.008", idc )

        if c == None:
            return None
        else:
            x = int( c[ 0:4 ] ) / 100.0
            y = int( c[ 4:8 ] ) / 100.0

            return ( x, y )
    
    def set_minutiae( self, data ):
        """
            Set the minutiae in the field 9.012.
            The 'data' parameter can be a minutiae-table (id, x, y, theta, quality, type) or
            the final string.
        """
        if type( data ) == list:
            data = lstTo012( data )
            
        self.set_field( "9.012", data )
        
        minnum = len( data.split( RS ) ) - 1
        self.set_field( "9.010", minnum )
        
        return minnum
    
    ############################################################################
    # 
    #    Image processing
    # 
    ############################################################################
    
    #    Size
    def get_size( self, idc = -1 ):
        """
            Get a python-tuple representing the size of the image.
        """
        return ( self.get_width( idc ), self.get_height( idc ) )
    
    def get_width( self, idc = -1 ):
        """
            Return the width of the Type-13 image.
        """
        return int( self.get_field( "13.006", idc ) )
        
    def get_height( self, idc = -1 ):
        """
            Return the height of the Type-13 image.
        """
        return int( self.get_field( "13.007", idc ) )
    
    #    Resolution
    def get_resolution( self, idc = -1 ):
        """
            Return the (horizontal) resolution of the Type-13 image in dpi.
        """
        return self.get_horizontalResolution( idc )

    def get_horizontalResolution( self, idc = -1 ):
        """
            Return the horizontal resolution of the Type-13 image.
            If the resolution is stored in px/cm, the conversion to dpi is done.
        """
        if self.get_field( "13.008", idc ) == '1':
            return int( self.get_field( "13.009" ) )
        elif self.get_field( "13.008", idc ) == '2':
            return int( self.get_field( "13.009" ) / 10.0 * 25.4 )

    def get_verticalResolution( self, idc = -1 ):
        """
            Return the vertical resolution of the Type-13 image.
            If the resolution is stored in px/cm, the conversion to dpi is done.
        """
        if self.get_field( "13.008", idc ) == '1':
            return int( self.get_field( "13.010" ) )
        elif self.get_field( "13.008", idc ) == '2':
            return int( self.get_field( "13.010" ) / 10.0 * 25.4 )
    
    def set_resolution( self, res, idc = -1 ):
        """
            Set the resolution in dpi.
        """
        res = int( res )
        
        self.set_horizontalResolution( res, idc )
        self.set_verticalResolution( res, idc )
        
        self.set_field( "13.008", "1", idc )

    def set_horizontalResolution( self, value, idc = -1 ):
        """
            Set the horizontal resolution.
        """
        self.set_field( "13.009", value, idc )
        
    def set_verticalResolution( self, value, idc = -1 ):
        """
            Set the vertical resolution.
        """
        self.set_field( "13.010", value, idc )
        
    #    Compression
    def get_compression( self, idc = -1 ):
        """
            Get the compression used in the latent image.
        """
        gca = self.get_field( "13.011", idc )
        return decode_gca( gca )
    
    #    Image
    @deprecated( "use the get_image( 'RAW', idc ) function instead" )
    def get_RAW( self, idc = -1 ):
        return self.get_image( "RAW", idc )
    
    @deprecated( "use the get_image( 'PIL', idc ) function instead" )
    def get_PIL( self, idc = -1 ):
        return self.get_image( "PIL", idc )
    
    def get_image( self, format = 'RAW', idc = -1 ):
        """
            Return the image in the format passed in parameter (RAW or PIL)
        """
        format = upper( format )
        
        raw = self.get_field( "13.999", idc )
        
        if format == "RAW":
            return raw
        elif format == "PIL":
            return Image.frombytes( "L", self.get_size( idc ), raw )
        else:
            raise NotImplemented
    
    def set_image( self, data, idc = -1 ):
        """
            Detect the type of image passed in parameter and store it in the
            13.999 field.
        """
        if type( data ) == str:
            self.set_field( "13.999", data, idc )
            
        elif isinstance( data, Image.Image ):
            self.set_RAW( PILToRAW( data ) )
            self.set_size( data.size )
            
            try:
                self.set_resolution( data.info[ 'dpi' ][ 0 ] )
            except:
                self.set_resolution( 500 )
    
    ############################################################################
    # 
    #    Access to the fields value
    # 
    ############################################################################
    
    def get_field( self, tag, idc = -1 ):
        """
            Get the content of a specific tag in the NIST object.
        """
        ntype, tagid = tagSplitter( tag )
        
        idc = self.checkIDC( ntype, idc )
    
        try:
            return self.data[ ntype ][ idc ][ tagid ]
        except:
            return None
    
    def set_field( self, tag, value, idc = -1 ):
        """
            Set the value of a specific tag in the NIST object.
        """
        ntype, tagid = tagSplitter( tag )
        
        idc = self.checkIDC( ntype, idc )
        
        if type( value ) != str:
            value = str( value )
        
        self.data[ ntype ][ idc ][ tagid ] = value
    
    ############################################################################
    # 
    #    Get specific information
    # 
    ############################################################################
    
    def get_caseName( self ):
        """
            Return the case name.
        """
        return self.get_field( "2.007" )
    
    ############################################################################
    # 
    #    Generic functions
    # 
    ############################################################################
    
    def get_ntype( self ):
        """
            Return all ntype presents in the NIST object.
        """
        return sorted( self.data.keys() )
    
    def get_idc( self, ntype ):
        """
            Return all IDC for a specific ntype.
        """
        return sorted( self.data[ ntype ].keys() )
    
    def checkIDC( self, ntype, idc ):
        """
            Check if the IDC passed in parameter exists for the specific ntype,
            and if the value is numeric. If the IDC is negative, then the value
            is searched in the ntype field and returned only if the value is
            unique; if multiple IDC are stored for the specific ntype, an
            exception is raised.
        """
        if idc < 0:
            idc = self.get_idc( ntype )
            
            if len( idc ) > 1:
                raise needIDC
            else:
                idc = idc[ 0 ]
            
        if type( idc ) != int:
            raise intIDC
        
        if not idc in self.get_idc( ntype ):
            raise nonexistingIDC
        
        return idc
    
    def __str__( self ):
        """
            Return the printable version of the NIST object.
        """
        return self.dump()
    
    def __repr__( self ):
        """
            Return unambiguous description.
        """
        return "NIST object, " + ", ".join( [ "Type-%02d" % x for x in self.get_ntype() if x > 2 ] )
    
################################################################################
#
#    Generic functions
#
################################################################################

#    Grayscale Compression Algorithm
GCA = {
    'NONE': "RAW",
    '0': "RAW",
    '1': "WSQ",
    '2': "JPEGB",
    '3': "JPEGL",
    '4': "JP2",
    '5': "JP2L",
    '6': "PNG"
}

def decode_gca( code ):
    """
        Function to decode the 'Grayscale Compression Algorithm' value passed in
        parameter.
        
        >>> decode_gca( 'NONE' )
        'RAW'
    """
    return GCA[ str( code ) ]

#    Binary print
def bindump( data ):
    """
        Return the first and last 4 bytes of a binary data.
        
        >>> bindump( chr(255) * 250000 )
        'ffffffff ... ffffffff (250000 bytes)'
    """
    return "%02x%02x%02x%02x ... %02x%02x%02x%02x (%d bytes)" % ( 
        ord( data[ 0 ] ), ord( data[ 1 ] ), ord( data[ 2 ] ), ord( data[ 3 ] ),
        ord( data[ -4 ] ), ord( data[ -3 ] ), ord( data[ -2 ] ), ord( data[ -1 ] ), len( data )
    )

#    Field split
def fieldSplitter( data ):
    """
        Split the input data in a ( tag, ntype, tagid, value ) tuple.
        
        >>> fieldSplitter( "1.002:0501" )
        ('1.002', 1, 2, '0501')
    """
    tag, value = data.split( CO )
    ntype, tagid = tag.split( DO )
    ntype = int( ntype )
    tagid = int( tagid )
    
    return tag, ntype, tagid, value

#    Get label name
def get_label( ntype, tagid, fullname = False ):
    """
        Return the name of a specific field.
        
        >>> get_label( 1, 2 )
        'VER'
        
        >>> get_label( 1, 2, True )
        'Version number'
    """
    index = int( fullname )
    
    try:
        return LABEL[ ntype ][ tagid ][ index ]
    except:
        if not fullname:
            return "   "
        else:
            return ""

#    Alignment function
def leveler( msg, level = 1 ):
    """
        Return an indented string.
        
        >>> leveler( "1.002", 1 )
        '    1.002'
    """
    return "    " * level + msg

#    Tag function
def tagger( ntype, tagid ):
    """
        Return the tag value from a ntype and tag value in parameter.
        
        >>> tagger( 1, 2 )
        '1.002:'
    """
    return "%d.%03d:" % ( ntype, tagid )

def tagSplitter( tag ):
    """
        Split a tag in a list of [ ntype, tagid ].
        
        >>> tagSplitter( "1.002" )
        [1, 2]
    """
    return map( int, tag.split( DO ) )

#    Field 9.012 to list (and reverse)
def lstTo012( lst ):
    """
        Convert the entire minutiae-table to the 9.012 field format.
        
        >>> lstTo012(
        ...    [['000',  7.85,  7.05, 290, '00', 'A'], 
        ...     ['001', 13.80, 15.30, 155, '00', 'A'], 
        ...     ['002', 11.46, 22.32, 224, '00', 'A'], 
        ...     ['003', 22.61, 25.17, 194, '00', 'A'], 
        ...     ['004',  6.97,  8.48, 153, '00', 'A'], 
        ...     ['005', 12.58, 19.88, 346, '00', 'A'], 
        ...     ['006', 19.69, 19.80, 111, '00', 'A'], 
        ...     ['007', 12.31,  3.87, 147, '00', 'A'], 
        ...     ['008', 13.88, 14.29, 330, '00', 'A'], 
        ...     ['009', 15.47, 22.49, 271, '00', 'A']] 
        ... )
        '000\\x1f07850705290\\x1f00\\x1fA\\x1e001\\x1f13801530155\\x1f00\\x1fA\\x1e002\\x1f11462232224\\x1f00\\x1fA\\x1e003\\x1f22612517194\\x1f00\\x1fA\\x1e004\\x1f06970848153\\x1f00\\x1fA\\x1e005\\x1f12581988346\\x1f00\\x1fA\\x1e006\\x1f19691980111\\x1f00\\x1fA\\x1e007\\x1f12310387147\\x1f00\\x1fA\\x1e008\\x1f13881429330\\x1f00\\x1fA\\x1e009\\x1f15472249271\\x1f00\\x1fA'
    """
    lst = map( lstTo012field, lst )
    lst = join( lst, RS )
     
    return lst

def lstTo012field( lst ):
    """
        Function to convert a minutiae from the minutiae-table to a 9.012 sub-field.
        
        >>> lstTo012field( ['000',  7.85,  7.05, 290, '00', 'A'] )
        '000\\x1f07850705290\\x1f00\\x1fA'
    """
    id, x, y, theta, quality, t = lst
    
    return join( 
        [
            id,
            "%04d%04d%03d" % ( round( float( x ) * 100 ), round( float( y ) * 100 ), theta ),
            quality,
            t
        ],
        US
    )

################################################################################
# 
#    Image processing functions
# 
################################################################################

def RAWToPIL( raw, size = ( 500, 500 ) ):
    """
        Convert a RAW string to PIL object.
        
        >>> p = RAWToPIL( chr( 255 ) * 250000, ( 500, 500 ) )
        >>> isinstance( p, Image.Image )
        True
        >>> p.size
        (500, 500)
    """
    return Image.frombytes( 'L', size, raw )

def PILToRAW( pil ):
    """
        Convert a PIL object to RAW string.
        
        >>> p = Image.new( '1', ( 5, 5 ) )
        >>> r = PILToRAW( p )
        >>> r
        '\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'
        >>> len( r )
        25
    """
    return pil.convert( 'L' ).tobytes()

################################################################################
#
#    Main
#
################################################################################

if __name__ == "__main__":
    import doctest
    doctest.testmod( extraglobs = { 'n': NIST() }, verbose = True )
