#!/usr/bin/env python
import sys
from distutils.core import setup
from glob import glob

man_files=glob('doc/gfal*.1')
doc_files=['RELEASE-NOTES', 'VERSION', 'LICENSE', 'readme.html']
bin_files=glob('src/gfal-*')
module_name='gfal2_util'

#f = open('setup.cfg', 'w')
#f.write('[bdist_rpm]\n')
#f.write('install_script = install-rpm.sh\n')
#f.write('release = 1\n')
#f.write('packager = Duarte Meneses <duarte.meneses@cern.ch>\n')
#f.write('doc_files = RELEASE-NOTES VERSION LICENSE\n')
#f.write('requires = gfal2-python >= 1.2.1')
#if sys.hexversion < 0x02070000:
#        f.write(', python-argparse\n')
#else:
#        f.write('\n')
#f.close()

setup(name=module_name,
      version='1.0.0',
      license='GPLv3',
      description='GFAL2 utility tools',
      long_description='''gfal2-util is a set of basic utility tools for file
interactions and file copy based on the GFAL 2.0 toolkit.
gfal2-util supports the protocols of GFAL 2.0 : WebDav(s),
gridFTP, http(s), SRM, xrootd, etc...''',
      author='Duarte Meneses, Adrien Devresse',
      author_email='duarte.meneses@cern.ch, adrien.devresse@cern.ch',
      url='http://dmc.web.cern.ch/projects/gfal2-utils',
      packages=[module_name],
      package_dir={ module_name : 'src/' + module_name},
      scripts=bin_files,
      data_files=[('/usr/share/man/man1', man_files)],
                 # ('/usr/share/doc/' + module_name, doc_files)],
     )
