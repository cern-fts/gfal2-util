#this file is only needed to automatically create a spec file and install it with distutils
#if using a spec file, it can be deleted

python setup.py install --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
# 'brp-compress' gzips the man pages without distutils knowing... fix this
sed -i -e 's@man/man\([[:digit:]]\)/\(.\+\.[[:digit:]]\)$@man/man\1/\2.gz@g' INSTALLED_FILES
cat INSTALLED_FILES | grep "\.py$" | grep "site-package" | sed "s/\.py$/\.pyo/" >> INSTALLED_FILES

