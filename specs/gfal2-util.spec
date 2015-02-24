
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}
%{!?python_version:  %global python_version  %(%{__python} -c "from sys import version_info; print('%d.%d'% (version_info[0],version_info[1]))")}


Name:				gfal2-util
Version:			1.0.0
Release:			1%{?dist}
Summary:			GFAL2 utility tools
Group:				Applications/Internet
License:			GPLv3
URL:				https://svnweb.cern.ch/trac/lcgutil/wiki/gfal2
# svn export http://svn.cern.ch/guest/lcgutil/gfal2-utils/trunk gfal2-utils
Source0:			http://grid-deployment.web.cern.ch/grid-deployment/dms/lcgutil/tar/%{name}/%{name}-%{version}.tar.gz
BuildRoot:			%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

#main lib dependencies
BuildRequires:		python2-devel
BuildArch:			noarch

# For the tests
BuildRequires:      gfal2-core
BuildRequires:      gfal2-python
BuildRequires:      python-argparse

Requires:			gfal2-python >= 1.5.0
%if "0%{?python_version}" <= "2.7"
Requires:			python-argparse
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
%{python_sitelib}/*
%{_bindir}/gfal-*
%{_mandir}/man1/*
%doc RELEASE-NOTES VERSION LICENSE


%changelog
* Mon Nov 04 2013 Duarte Meneses <duarte.meneses at cern.ch> - 1.0.0-1
 - Installation done with distutils
* Mon Nov 04 2013 Adrien Devresse <adevress at cern.ch> - 0.2.1-1
 - Initial EPEL compatible version
