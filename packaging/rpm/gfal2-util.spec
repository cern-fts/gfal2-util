#-------------------------------------------------------------------------------
# Configure python2/3 according to platform and passed-in parameter
#-------------------------------------------------------------------------------

# Require --without=python3 in order to disable python3 build package
%bcond_without python3

# Require --without=python2 in order to disable python2 build package on RHEL7
%if 0%{?rhel} == 7
%bcond_without python2
%endif

%if 0%{with python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from sysconfig import get_path; print get_path('purelib')")}
%endif

%if 0%{with python3}
%{!?python3_sitelib: %global python3_sitelib %(%{__python3} -c "from sysconfig import get_path; print(get_path('purelib'))")}
%endif

Name:           gfal2-util
Version:        1.8.0
Release:        1%{?dist}
Summary:        GFAL2 utility tools
Group:          Applications/Internet
License:        ASL 2.0
URL:            http://dmc.web.cern.ch/
# git clone https://gitlab.cern.ch/dmc/gfal2-util.git gfal2-util-1.8.0 --depth=1
# pushd gfal2-util-1.8.0
# git checkout v1.8.0
# popd
# tar czf gfal2-util-1.8.0.tar.gz --exclude-vcs gfal2-util-1.8.0
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildArch:      noarch

BuildRequires:  gfal2-core
BuildRequires:  gfal2-plugin-file

%global _description \
gfal2-util is a set of basic utility tools for file \
interactions and file copy based on the GFAL 2.0 toolkit. \
gfal2-util supports the protocols of GFAL 2.0 : WebDav(s), \
gridFTP, http(s), SRM, xrootd, etc...

%description %_description

%prep
%if 0%{?without python2} && 0%{?without python3}
  echo "Must either remove --without=python2 or provide --with=python3 switch"
  exit 1
%endif

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

%if 0%{with python2}
  python2 setup.py build
%endif
%if 0%{with python3}
  python3 setup.py build
%endif

%install
rm -rf %{buildroot}
%if 0%{with python2}
  python2 setup.py install --root=%{buildroot}
%endif
%if 0%{with python3}
  python3 setup.py install --root=%{buildroot}
%endif

%clean
rm -rf %{buildroot}

#-------------------------------------------------------------------------------
# Gfal2-util-scripts package
#-------------------------------------------------------------------------------
%package scripts
Summary:        gfal2 command line scripts

%description scripts
Provides a set of command line scripts to call gfal2-util python functions.

%files scripts
%defattr (-,root,root)
%{_bindir}/gfal-*
%{_mandir}/man1/*

#-------------------------------------------------------------------------------
# Gfal2-util package for Python2
#-------------------------------------------------------------------------------
%if 0%{with python2}
%package -n python2-gfal2-util
Summary:        gfal2 clients for python2

BuildRequires:  python2-gfal2 >= 1.12.0
BuildRequires:  python2
BuildRequires:  python2-rpm-macros
BuildRequires:  python2-setuptools
BuildRequires:  python2-future
Requires:       python2-gfal2 >= 1.12.0
Requires:       gfal2-util-scripts = %{version}-%{release}
Requires:       gfal2-plugin-file
Requires:       python2
Requires:       python2-future

# Introduced in v1.6.0 / Remove around FC36
Provides:       gfal2-util = %{version}-%{release}
Obsoletes:      gfal2-util < %{version}-%{release}

%description -n python2-gfal2-util %_description

%files -n python2-gfal2-util
%defattr (-,root,root)
%{python2_sitelib}/gfal2_util*
%doc RELEASE-NOTES VERSION LICENSE readme.html
%endif

#-------------------------------------------------------------------------------
# Gfal2-util package for Python3
#-------------------------------------------------------------------------------
%if 0%{with python3}
%package -n python3-gfal2-util
Summary:        gfal2 clients for python3

BuildRequires:  python3-gfal2 >= 1.12.0
BuildRequires:  python3
BuildRequires:  python3-rpm-macros
BuildRequires:  python3-setuptools
Requires:       python3-gfal2 >= 1.12.0
Requires:       gfal2-util-scripts = %{version}-%{release}
Requires:       gfal2-plugin-file
Requires:       python3

# EL7 upgrade path is for python2-gfal2-util
%if 0%{?rhel} != 7
Provides:       gfal2-util = %{version}-%{release}
%endif

# Introduced in v1.6.0 / Remove around FC36
Obsoletes:      gfal2-util < %{version}-%{release}

%description -n python3-gfal2-util %_description

%files -n python3-gfal2-util
%defattr (-,root,root)
%{python3_sitelib}/gfal2_util*
%doc RELEASE-NOTES VERSION LICENSE readme.html
%endif

%changelog
* Fri Sep 02 2022 Joao Lopes <batistal@cern.ch> - 1.8.0-1
- New upstream release
- Renew gfal-legacy-bringonline command
- Introduces gfal-evict and gfal-archivepoll commands

* Mon Mar 07 2022 Mihai Patrascoiu <mipatras@cern.ch> - 1.7.1-1
- New upstream release

* Thu Oct 07 2021 Mihai Patrascoiu <mipatras@cern.ch> - 1.7.0-2
- New upstream release
- Python3 package with Provides and Obsoletes capabilities

* Thu Sep 23 2021 Joao Lopes <batistal@cern.ch> - 1.7.0-1
- New upstream release
- Introduces SE-Token retrieval

* Thu Nov 19 2020 Petr Vokac <petr.vokac at cern.ch> - 1.6.0-1
- New upstream release
- Provide distinct packages for Python2 and Python3

* Mon Sep 14 2020 Mihai Patrascoiu <mipatras at cern.ch> - 1.5.4-1
- New upstream release

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
