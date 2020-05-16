Installation
============

The installation process is done as follows.

1. Create a folder on your system to store all the mendatory libraries
2. Clone all mendatory libraries:

.. code-block:: bash

   cd libraries
   git clone https://github.com/mdedonno1337/NIST.git
   git clone https://github.com/mdedonno1337/MDmisc.git
   git clone https://github.com/mdedonno1337/PMlib.git
   git clone https://github.com/mdedonno1337/WSQ.git

The structure of the files should be as follows:

.. code-block:: bash

   .
   ├── library
   │   ├── MDmisc
   │   │   ├── doctester.py
   │   │   ├── __init__.py
   │   │   ├── LICENSE
   │   │   ├── MDmisc
   │   │   └── requirements.txt
   │   ├── NIST
   │   │   ├── CHANGELOG.txt
   │   │   ├── doc
   │   │   ├── doctester2.py
   │   │   ├── doctester.py
   │   │   ├── __init__.py
   │   │   ├── LICENSE
   │   │   ├── NIST
   │   │   ├── readme.rst
   │   │   ├── requirements.txt
   │   │   ├── TODO.txt
   │   │   └── update.py
   │   ├── PMlib
   │   │   ├── LICENSE
   │   │   ├── PMlib
   │   │   └── requirements.txt
   │   └── WSQ
   │       ├── __init__.py
   │       ├── LICENSE
   │       ├── requirements.txt
   │       └── WSQ
   .
   .
   .

3. Create a ``mdedonno.pth`` in the site-packages python directory pointing to the libraries folders:

.. code-block:: bash

   $ cat /usr/local/lib/python2.7/dist-packages/mdedonno.pth
   /library/NIST
   /library/WSQ
   /library/PMlib
   /library/MDmisc

4. Check the installation by running python and typing ``import NIST``

