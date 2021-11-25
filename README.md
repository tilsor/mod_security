# mod_security RPM

[![Copr build status](https://copr.fedorainfracloud.org/coprs/tilsor/mod_security/package/mod_security/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/tilsor/mod_security/package/mod_security/)

This repository has the config and spec files for building mod_security RPM for EL.

Build has `yajl` and `ssdeep` support, and the relevant config.  Packages are build using the excellent Fedora COPR system.

## Getting the RPM packages

For installing the packages in _CentOS/RHEL_ and derivatives, use this:

```
yum install yum-utils -y
yum-config-manager --add-repo https://copr.fedorainfracloud.org/coprs/tilsor/mod_security/repo/epel-7/tilsor-mod_security-epel-7.repo
yum-config-manager --enable tilsor-mod_security-epel-7
yum install mod_security -y
```

## Building locally

If you want to build locally the packages, you can do these steps:
```
yum install rpmdevtools rpm-build -y
spectool -g -R spec/mod_security.spec
rpmbuild -ba spec/mod_security.spec
```

Or you can do it in your local mock:

```
mock --buildsrpm -r epel-8-x86_64 --spec ~/rpmbuild/SPECS/mod_security.spec --sources ~/rpmbuild/SOURCES
cp /var/lib/mock/epel-8-x86_64/result/mod_security-2.9.5-1.el8.src.rpm ~/rpmbuild/SRPMS/
mock --rebuild -r epel-8-x86_64 mod_security-2.9.5-1.el8.src.rpm
```
