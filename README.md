# mod_security RPM

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
