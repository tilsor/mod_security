%{!?_httpd_apxs: %{expand: %%global _httpd_apxs %%{_sbindir}/apxs}}
%{!?_httpd_mmn: %{expand: %%global _httpd_mmn %%(cat %{_includedir}/httpd/.mmn || echo 0-0)}}
# /etc/httpd/conf.d with httpd < 2.4 and defined as /etc/httpd/conf.modules.d with httpd >= 2.4
%{!?_httpd_modulesconfdir: %{expand: %%global _httpd_modulesconfdir %%{_sysconfdir}/httpd/conf.modules.d}}
%{!?_httpd_modconfdir: %{expand: %%global _httpd_modconfdir %%{_sysconfdir}/httpd/modsecurity.d}}
%{!?_httpd_confdir:    %{expand: %%global _httpd_confdir    %%{_sysconfdir}/httpd/conf.d}}
%{!?_httpd_moddir:    %{expand: %%global _httpd_moddir    %%{_libdir}/httpd/modules}}

# https://docs.fedoraproject.org/en-US/modularity/building-modules/local/building-modules-locally/#_spec_file_configuration_optional
%define _disable_source_fetch 0

# enable PIE
%global _hardened_build 1

%global with_mlogc 0%{?fedora} || 0%{?rhel} <= 6

# Conditionals
%bcond_with ssdeep

Summary: Security module for the Apache HTTP Server
Name: mod_security 
Version: 2.9.11
Release: 0 
License: ASL 2.0
URL: http://www.modsecurity.org/
Group: System Environment/Daemons
Source0: https://github.com/owasp-modsecurity/ModSecurity/releases/download/v%{version}/modsecurity-v%{version}.tar.gz
Source1: https://raw.githubusercontent.com/tilsor/mod_security/main/config/mod_security.conf
Source2: https://raw.githubusercontent.com/tilsor/mod_security/main/config/10-mod_security.conf
Source3: https://raw.githubusercontent.com/tilsor/mod_security/main/config/modsecurity_localrules.conf
Source4: https://raw.githubusercontent.com/tilsor/mod_security/main/config/00-modsecurity.base.conf
Requires: httpd httpd-mmn = %{_httpd_mmn}
# Required for force recent TLS  version
#BuildRequires: curl-devel yajl-devel
BuildRequires: httpd-devel
BuildRequires: perl-generators pcre2 pcre2-devel
#BuildRequires: pkgconfig(libxml-2.0) pkgconfig(lua) pkgconfig(libpcre) pkgconfig(libcurl) pcre2  
#BuildRequires: pkgconfig(libxml-2.0) pkgconfig(lua) pkgconfig(pcre2-devel) pkgconfig(libcurl) 
BuildRequires: pkgconfig(libxml-2.0) pkgconfig(lua) pkgconfig(libcurl) 

# Workarround for EL6
%if 0%{?el6}
BuildRequires: yajl-devel
%else
BuildRequires: pkgconfig(yajl)  
%endif

%if %{with ssdeep}
BuildRequires: ssdeep-devel
%endif

%description
ModSecurity is an open source intrusion detection and prevention engine
for web applications. It operates embedded into the web server, acting
as a powerful umbrella - shielding web applications from attacks.

%if %with_mlogc
%package -n     mlogc
Summary:        ModSecurity Audit Log Collector
Group:          System Environment/Daemons
Requires:       mod_security

%description -n mlogc
This package contains the ModSecurity Audit Log Collector.
%endif

%prep
%setup -q -n modsecurity-v%{version}

%build
%configure --enable-pcre-match-limit=1000000 \
           --enable-pcre-match-limit-recursion=1000000 \
           --with-apxs=%{_httpd_apxs} \
	       %{?_with_ssdeep} \
           --with-yajl
# remove rpath
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

make %{_smp_mflags}

%check
# Test suite does not start because of some issue in shipped httpd config (fix upstreamed in PR #669)
# After the fix, the test suite starts but still fails
#make test
#make test-regression

%install
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_httpd_moddir}
install -d %{buildroot}%{_sysconfdir}/httpd/modsecurity.d/
install -d %{buildroot}%{_sysconfdir}/httpd/modsecurity.d/activated_rules
install -d %{buildroot}%{_sysconfdir}/httpd/modsecurity.d/local_rules

install -m0755 apache2/.libs/mod_security2.so %{buildroot}%{_httpd_moddir}/mod_security2.so

%if "%{_httpd_modconfdir}" != "%{_httpd_confdir}"
# 2.4-style
install -Dp -m0644 %{SOURCE2} %{buildroot}%{_httpd_modulesconfdir}/10-mod_security.conf
install -Dp -m0644 %{SOURCE1} %{buildroot}%{_httpd_confdir}/mod_security.conf
install -Dp -m0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/httpd/modsecurity.d/00-modsecurity.base.conf
%else
# 2.2-style
install -d -m0755 %{buildroot}%{_httpd_confdir}
cat %{SOURCE2} %{SOURCE1} > %{buildroot}%{_httpd_confdir}/mod_security.conf
%endif
install -m 700 -d $RPM_BUILD_ROOT%{_localstatedir}/lib/%{name}

# Local rules example
install -Dp -m0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/httpd/modsecurity.d/local_rules/

# mlogc
%if %with_mlogc
install -d %{buildroot}%{_localstatedir}/log/mlogc
install -d %{buildroot}%{_localstatedir}/log/mlogc/data
install -m0755 mlogc/mlogc %{buildroot}%{_bindir}/mlogc
install -m0755 mlogc/mlogc-batch-load.pl %{buildroot}%{_bindir}/mlogc-batch-load
install -m0644 mlogc/mlogc-default.conf %{buildroot}%{_sysconfdir}/mlogc.conf
%endif


%files
%license LICENSE
%doc CHANGES README.md NOTICE
%{_httpd_moddir}/mod_security2.so
%config(noreplace) %{_httpd_confdir}/*.conf
%if "%{_httpd_modconfdir}" != "%{_httpd_confdir}"
%config(noreplace) %{_httpd_modconfdir}/*.conf
%endif
%dir %{_sysconfdir}/httpd/modsecurity.d
%dir %{_sysconfdir}/httpd/modsecurity.d/activated_rules
%dir %{_sysconfdir}/httpd/modsecurity.d/local_rules
%config(noreplace) %{_sysconfdir}/httpd/modsecurity.d/local_rules/*.conf
%config(noreplace) %{_sysconfdir}/httpd/modsecurity.d/*.conf
%attr(770,apache,root) %dir %{_localstatedir}/lib/%{name}

%if %with_mlogc
%files -n mlogc
%doc mlogc/INSTALL
%attr(0640,root,apache) %config(noreplace) %{_sysconfdir}/mlogc.conf
%attr(0755,root,root) %dir %{_localstatedir}/log/mlogc
%attr(0770,root,apache) %dir %{_localstatedir}/log/mlogc/data
%attr(0755,root,root) %{_bindir}/mlogc
%attr(0755,root,root) %{_bindir}/mlogc-batch-load
%endif

%changelog
* Wed Jul 02 2025 Germán González <ggonzalez@tilsor.com.uy> - 2.9.11
- Update ModSecurity to last version. Fix CVE-2025-52891 - 2.9.11

* Mon Jun 16 2025 Germán González <ggonzalez@tilsor.com.uy> - 2.9.10
- Update ModSecurity to last version. - 2.9.10

* Wed Sep 11 2024 Germán González <ggonzalez@tilsor.com.uy> - 2.9.8-1
- Fix compilation error. - 2.9.8-1
- Update ModSecurity to last version. - 2.9.8

* Mon Dec 11 2023 Germán González <ggonzalez@tilsor.com.uy> - 2.9.7-2
- Fix path to ModSeurity base config. - 2.9.7-2

* Fri Dec 08 2023 Germán González <ggonzalez@tilsor.com.uy> - 2.9.7-1
- Changes on mod_security configuration files. Separate includes from base config. - 2.9.7-1

* Mon Jan 09 2023 Germán González <ggonzalez@tilsor.com.uy> - 2.9.7-0
- Update to the last version - 2.9.7

* Mon Sep 19 2022 Germán González <ggonzalez@tilsor.com.uy> - 2.9.6-0
- Update to 2.9.6

* Wed Nov 24 2021 Felipe Zipitría <fzipitria@tilsor.com.uy> - 2.9.5-1
- Update to 2.9.5

* Fri Aug 18 2017 Felipe Zipitría <fzipi@fing.edu.uy> - 2.9.2-1
- Update to 2.9.2

* Wed Mar 09 2016 Athmane Madjoudj <athmane@fedoraproject.org> 2.9.1-1
- Update to final 2.9.1
- Minor spec fix.

* Tue Mar 08 2016 Athmane Madjoudj <athmane@fedoraproject.org> 2.9.1-0.1.rc1
- Add workaround for el6

* Tue Mar 08 2016 Athmane Madjoudj <athmane@fedoraproject.org> 2.9.1-0.rc1
- Update to 2.9.1-rc1
- Remove upstreamed patch

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.9.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Oct 02 2015 Athmane Madjoudj <athmane@fedoraproject.org> 2.9.0-5
- Update BuildRequires using pkgconfig name schema

* Tue Sep 01 2015 Athmane Madjoudj <athmane@fedoraproject.org>  2.9.0-4
- Add yajl support

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Fri Feb 13 2015 Athmane Madjoudj <athmane@fedoraproject.org> 2.9.0-2
- Remove curl version dep. since it no longer required

* Fri Feb 13 2015 Athmane Madjoudj <athmane@fedoraproject.org>  2.9.0-1
- Update to 2.9.0
- Remove backported patch
- Add patch to fix lua 5.3 build issue (PR #837)

* Tue Nov 04 2014 Athmane Madjoudj <athmane@fedoraproject.org> 2.8.0-7
- Make sure mod_security is built with correct curl version

* Mon Nov 03 2014 Athmane Madjoudj <athmane@fedoraproject.org> 2.8.0-6
- Changes the default SSL version to TLS 1.2 since SSLv3 is vulnerable to poodle

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.8.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Aug 15 2014 Athmane Madjoudj <athmane@fedoraproject.org> 2.8.0-4
- Add support for user-provided configurations and rules (rhbz #1129843)

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.8.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed Apr 16 2014  Athmane Madjoudj <athmane@fedoraproject.org> 2.8.0-1
- Update to 2.8.0 Final

* Thu Apr 03 2014 Athmane Madjoudj <athmane@fedoraproject.org> 2.8.0-0.rc1
- Update to 2.8.0-RC1

* Tue Mar 04 2014 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.7-6
- Fix status code in the configuration file (upstream PR #666)

* Sat Mar 01 2014 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.7-5
- Fix rpmlint warnings

* Thu Feb 27 2014 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.7-4
- Add check section

* Sat Feb 22 2014 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.7-3
- Fix bogus date in chanelog

* Thu Jan 23 2014 Joe Orton <jorton@redhat.com> - 2.7.7-2
- fix _httpd_mmn expansion in absence of httpd-devel

* Thu Dec 19 2013 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.7-1
- Update to 2.7.7
- Fix the spec file since upstream fixed the bugs reported.

* Tue Dec 17 2013 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.6-2
- Add autotools deps

* Tue Dec 17 2013 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.6-1
- Update to 2.7.6
- Fix spec since upstream will only provide tarball via Github

* Sat Aug 03 2013 Petr Pisar <ppisar@redhat.com> - 2.7.5-2
- Perl 5.18 rebuild

* Tue Jul 30 2013 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.5-1
- Update to 2.7.5

* Thu Jul 18 2013 Petr Pisar <ppisar@redhat.com> - 2.7.4-2
- Perl 5.18 rebuild

* Tue May 28 2013 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.4-1
- Update to 2.7.4
- Drop non required patch

* Tue May 28 2013 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.3-2
- Fix NULL pointer dereference (DoS, crash) (CVE-2013-2765) (RHBZ #967615)
- Fix a possible memory leak.

* Sat Mar 30 2013 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.3-1
- Update to 2.7.3

* Fri Jan 25 2013 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.2-1
- Update to 2.7.2
- Update source url in the spec.

* Thu Nov 22 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.1-5
- Use conditional for loading mod_unique_id (rhbz #879264)
- Fix syntax errors on httpd 2.4.x by using IncludeOptional (rhbz #879264, comment #2)

* Mon Nov 19 2012 Peter Vrabec <pvrabec@redhat.com> 2.7.1-4
- mlogc subpackage is not provided on RHEL7

* Thu Nov 15 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.1-3
- Add some missing directives RHBZ #569360
- Fix multipart/invalid part ruleset bypass issue (CVE-2012-4528)
  (RHBZ #867424, #867773, #867774)

* Thu Nov 15 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.1-2
- Fix mod_security.conf

* Thu Nov 15 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.1-1
- Update to 2.7.1
- Remove libxml2 build patch (upstreamed)
- Update spec since upstream moved to github

* Thu Oct 18 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.0-2
- Add a patch to fix failed build against libxml2 >= 2.9.0

* Wed Oct 17 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.7.0-1
- Update to 2.7.0

* Fri Sep 28 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.6.8-1
- Update to 2.6.8

* Wed Sep 12 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.6.7-2
- Re-add mlogc sub-package for epel (#856525)
 
* Sat Aug 25 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.6.7-1
- Update to 2.6.7

* Sat Aug 25 2012 Athmane Madjoudj <athmane@fedoraproject.org> 2.6.7-1
- Update to 2.6.7

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.6.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Fri Jun 22 2012 Peter Vrabec <pvrabec@redhat.com> - 2.6.6-2
- mlogc subpackage is not provided on RHEL
 
* Thu Jun 21 2012 Peter Vrabec <pvrabec@redhat.com> - 2.6.6-1
- upgrade

* Mon May  7 2012 Joe Orton <jorton@redhat.com> - 2.6.5-3
- packaging fixes

* Fri Apr 27 2012 Peter Vrabec <pvrabec@redhat.com> 2.6.5-2
- fix license tag

* Thu Apr 05 2012 Peter Vrabec <pvrabec@redhat.com> 2.6.5-1
- upgrade & move rules into new package mod_security_crs

* Fri Feb 10 2012 Petr Pisar <ppisar@redhat.com> - 2.5.13-3
- Rebuild against PCRE 8.30
- Do not install non-existing files

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.13-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue  May 3 2011 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.13-1
- Newer upstream version

* Wed Jun 30 2010 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.12-3
- Fix log dirs and files ordering per bz#569360

* Thu Apr 29 2010 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.12-2
- Fix SecDatadir and minimal config per bz #569360

* Sat Feb 13 2010 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.12-1
- Update to latest upstream release
- SECURITY: Fix potential rules bypass and denial of service (bz#563576)

* Fri Nov 6 2009 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.10-2
- Fix rules and Apache configuration (bz#533124)

* Thu Oct 8 2009 Michael Fleming <mfleming+rpm@thatfleminggent.com> - 2.5.10-1
- Upgrade to 2.5.10 (with Core Rules v2)

* Sat Jul 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Mar 12 2009 Michael Fleming <mfleming+rpm@thatfleminggent.com> 2.5.9-1
- Update to upstream release 2.5.9
- Fixes potential DoS' in multipart request and PDF XSS handling

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Dec 29 2008 Michael Fleming <mfleming+rpm@enlartenment.com> 2.5.7-1
- Update to upstream 2.5.7
- Reinstate mlogc

* Sat Aug 2 2008 Michael Fleming <mfleming+rpm@enlartenment.com> 2.5.6-1
- Update to upstream 2.5.6
- Remove references to mlogc, it no longer ships in the main tarball.
- Link correctly vs. libxml2 and lua (bz# 445839)
- Remove bogus LoadFile directives as they're no longer needed.

* Sun Apr 13 2008 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.7-1
- Update to upstream 2.1.7

* Sat Feb 23 2008 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.6-1
- Update to upstream 2.1.6 (Extra features including SecUploadFileMode)

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 2.1.5-3
- Autorebuild for GCC 4.3

* Sun Jan 27 2008 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.5-2
- Update to 2.1.5 (bz#425986)
- "blocking" -> "optional_rules" per tarball ;-)


* Thu Sep  13 2007 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.3-1
- Update to 2.1.3
- Update License tag per guidelines.

* Mon Sep  3 2007 Joe Orton <jorton@redhat.com> 2.1.1-3
- rebuild for fixed 32-bit APR (#254241)

* Wed Aug 29 2007 Fedora Release Engineering <rel-eng at fedoraproject dot org> - 2.1.1-2
- Rebuild for selinux ppc32 issue.

* Tue Jun 19 2007 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.1-1
- New upstream release
- Drop ASCIIZ rule (fixed upstream)
- Re-enable protocol violation/anomalies rules now that REQUEST_FILENAME
  is fixed upstream.

* Sun Apr 1 2007 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.0-3
- Automagically configure correct library path for libxml2 library.
- Add LoadModule for mod_unique_id as the logging wants this at runtime

* Mon Mar 26 2007 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.0-2
- Fix DSO permissions (bz#233733)

* Tue Mar 13 2007 Michael Fleming <mfleming+rpm@enlartenment.com> 2.1.0-1
- New major release - 2.1.0
- Fix CVE-2007-1359 with a local rule courtesy of Ivan Ristic
- Addition of core ruleset
- (Build)Requires libxml2 and pcre added.

* Sun Sep 3 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.4-2
- Rebuild
- Fix minor longstanding braino in included sample configuration (bz #203972)

* Mon May 15 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.4-1
- New upstream release

* Tue Apr 11 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.3-1
- New upstream release
- Trivial spec tweaks

* Wed Mar 1 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.2-3
- Bump for FC5

* Fri Feb 10 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.2-2
- Bump for newer gcc/glibc

* Wed Jan 18 2006 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.2-1
- New upstream release

* Fri Dec 16 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.1-2
- Bump for new httpd

* Thu Dec 1 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9.1-1
- New release 1.9.1 

* Wed Nov 9 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.9-1
- New stable upstream release 1.9

* Sat Jul 9 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.8.7-4
- Add Requires: httpd-mmn to get the appropriate "module magic" version
  (thanks Ville Skytta)
- Disabled an overly-agressive rule or two..

* Sat Jul 9 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.8.7-3
- Correct Buildroot
- Some sensible and safe rules for common apps in mod_security.conf

* Thu May 19 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.8.7-2
- Don't strip the module (so we can get a useful debuginfo package)

* Thu May 19 2005 Michael Fleming <mfleming+rpm@enlartenment.com> 1.8.7-1
- Initial spin for Extras

