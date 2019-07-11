%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}
%{!?python_version:  %global python_version  %(%{__python} -c "from sys import version_info; print('%d.%d'% (version_info[0],version_info[1]))")}

Name:           gfal2-util
Version:        1.5.3
Release:        1%{?dist}
Summary:        GFAL2 utility tools
Group:          Applications/Internet
License:        GPLv3
URL:            http://dmc.web.cern.ch/
# git clone https://gitlab.cern.ch/dmc/gfal2-util.git gfal2-util-1.5.1 --depth=1
# pushd gfal2-util-1.5.1
# git checkout v1.5.1
# popd
# tar czf gfal2-util-1.5.1.tar.gz --exclude-vcs gfal2-util-1.5.1
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildArch:      noarch

BuildRequires:  gfal2-core
BuildRequires:  gfal2-python >= 1.9.0
BuildRequires:  gfal2-plugin-file
BuildRequires:  python2

Requires:       gfal2-python >= 1.9.0
Requires:       python2

%if %{?fedora}%{!?fedora:0} < 26
BuildRequires:      python-argparse
Requires:       python-argparse
%endif

%description
gfal2-util is a set of basic utility tools for file 
interactions and file copy based on the GFAL 2.0 toolkit.
gfal2-util supports the protocols of GFAL 2.0 : WebDav(s),
gridFTP, http(s), SRM, xrootd, etc...

%clean
rm -rf %{buildroot}
python setup.py clean

%prep
%setup -q

%build
# Validate the version
gfal2_util_ver=`sed -n "s/VERSION = '\(.*\)'/\1/p" src/gfal2_util/base.py`
gfal2_util_spec_ver=`expr "%{version}" : '\([0-9]*\\.[0-9]*\\.[0-9]*\)'`
if [ "$gfal2_util_ver" != "$gfal2_util_spec_ver" ]; then
    echo "The version in the spec file does not match the base.py version!"
    echo "%{version} != $gfal2_util_ver"
    exit 1
fi

python setup.py build

%install
rm -rf %{buildroot}
python setup.py install --root=%{buildroot}

%check
python test/functional/test_all.py

%files
%defattr (-,root,root)
%{python_sitelib}/gfal2_util*
%{_bindir}/gfal-*
%{_mandir}/man1/*
%doc RELEASE-NOTES VERSION LICENSE readme.html


%changelog
* Fri Mar 29 2019 Andrea Manzi <amanzi at cern.ch> - 1.5.3-1
- New upstream release

* Mon Feb 20 2017 Alejandro Alvarez <aalvarez at cern.ch> - 1.5.0-1
- New upstream release

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.4.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Sep 27 2016  Alejandro Alvarez <aalvarez at cern.ch> - 1.4.0-1
- New upstream release
- python-argparse is part of python's stdlib

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.2-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Tue Mar 08 2016 Alejandro Alvarez <aalvarez at cern.ch> - 1.3.2-1
- Update for new upstream 1.3.2 release

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Mon Nov 09 2015 Alejandro Alvarez <aalvarez at cern.ch> - 1.3.1-1
- Update for new upstream 1.3.1 release

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Fri Apr 17 2015 Alejandro Alvarez <aalvarez at cern.ch> - 1.2.1-1
- Update for new upstream 1.2.1 release

* Fri Nov 07 2014 Alejandro Alvarez <aalvarez at cern.ch> - 1.1.0-1
- Update for new upstream 1.1.0 release

* Wed Jul 02 2014 Alejandro Alvarez <aalvarez at cern.ch> - 1.0.0-1
- Update for new upstream 1.0.0 release
- Installation done with distutils
- Run tests on check stage 

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Mon Nov 04 2013 Adrien Devresse <adevress at cern.ch> - 0.2.1-1
 - Initial EPEL compatible version
