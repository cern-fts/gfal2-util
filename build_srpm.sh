#!/bin/bash
set -x

this_script=`readlink -f "$0"`
this_dir=`dirname "$this_script"`

version=`sed -nre 's/^Version:\s+((([0-9]+)\.)*[0-9]+)/\1/p' "${this_dir}/specs/gfal2-util.spec"`

echo "Packaging version $version"
mkdir -p /tmp/gfal2-util/SOURCES/
cd "$this_dir" > /dev/null
tar czf /tmp/gfal2-util/SOURCES/gfal2-util-$version.tar.gz . --exclude=.git --exclude="*.pyc" --transform "s,^,gfal2-util-$version/,"
cd - > /dev/null

rpmbuild -bs "${this_dir}/specs/gfal2-util.spec" \
    --define='_topdir /tmp/gfal2-util/' \
    --define='_sourcedir %{_topdir}/SOURCES' \
    --define='_builddir %{_topdir}/BUILD' \
    --define='_srcrpmdir %{_topdir}/SRPMS' \
    --define='_rpmdir %{_topdir}/RPMS' > /dev/null

cp /tmp/gfal2-util/SRPMS/*.rpm .
rm -rf /tmp/gfal2-util/
