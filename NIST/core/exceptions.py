#!/usr/bin/python
# -*- coding: UTF-8 -*-

class needIDC( BaseException ):
    pass

class needNtype( BaseException ):
    pass

class intIDC( BaseException ):
    pass

class notImplemented( BaseException ):
    pass

class ntypeNotFound( BaseException ):
    pass

class recordNotFound( BaseException ):
    pass

class idcNotFound( BaseException ):
    pass

class tagNotFound( BaseException ):
    pass

class ntypeAlreadyExisting( BaseException ):
    pass

class idcAlreadyExisting( BaseException ):
    pass

class formatNotSupported( BaseException ):
    pass
