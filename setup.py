#!/usr/bin/env python
from distutils.core import setup
from glob import glob

doc_files = ['RELEASE-NOTES', 'VERSION', 'LICENSE', 'readme.html']
bin_files = glob('src/gfal-*')
module_name = 'gfal2_util'
data_files = []

man_root = 'share/man/man1'
man_files = glob('doc/man/gfal*.1')
data_files.append((man_root, man_files))

setup(name=module_name,
      version='1.7.0',
      license='GPLv3',
      description='GFAL2 utility tools',
      long_description='''gfal2-util is a set of basic utility tools for file
interactions and file copy based on the GFAL 2.0 toolkit.
gfal2-util supports the protocols of GFAL 2.0 : WebDav(s),
gridFTP, http(s), SRM, xrootd, etc...''',
      author='Duarte Meneses, Adrien Devresse, Andrea Manzi, Mihai Patrascoiu',
      author_email='dmc-devel@cern.ch',
      url='http://dmc.web.cern.ch/projects/gfal2-utils',
      packages=[module_name],
      package_dir={module_name: 'src/' + module_name},
      scripts=bin_files,
      data_files=data_files,
      )
