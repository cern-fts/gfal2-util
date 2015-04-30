%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}
%{!?python_version:  %global python_version  %(%{__python} -c "from sys import version_info; print('%d.%d'% (version_info[0],version_info[1]))")}

Name:			gfal2-util
Version:		1.3.0
Release:		1%{?dist}
Summary:		GFAL2 utility tools
Group:			Applications/Internet
License:		GPLv3
URL:			https://svnweb.cern.ch/trac/lcgutil/wiki/gfal2
# git clone https://gitlab.cern.ch/dmc/gfal2-util.git gfal2-util-1.3.0
# pushd gfal2-util-1.3.0
# git checkout v1.3.0
# git submodule init && git submodule update
# popd
# tar czf gfal2-util-1.3.0.tar.gz gfal2-util-1.3.0
Source0:		%{name}-%{version}.tar.gz
BuildRoot:		%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildArch:		noarch

BuildRequires:		gfal2-core
BuildRequires:		gfal2-python >= 1.8.0
BuildRequires:		gfal2-plugin-file

Requires:		gfal2-python >= 1.8.0

%if "0%{?python_version}" <= "2.7"
BuildRequires:		python-argparse
Requires:		python-argparse
%endif # python < 2.7

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
%doc RELEASE-NOTES VERSION LICENSE


%changelog
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
