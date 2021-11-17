%global forgeurl https://github.com/waydroid/waydroid
%global tag 1.2.0
%global debug_package %{nil}
%global _hardlink /usr/bin/hardlink
%global selinux_types %(%{__awk} '/^#[[:space:]]*SELINUXTYPE=/,/^[^#]/ { if ($3 == "-") printf "%s ", $2 }' /etc/selinux/config 2>/dev/null)
%global selinux_variants %([ -z "%{selinux_types}" ] && echo mls targeted || echo %{selinux_types})

%forgemeta
Name:           waydroid
Version:        %{tag}
Release:        3%{?dist}
Summary:        waydroid
License:        LGPLv2+
URL:            %{forgeurl}
Source:         %{forgesource}
Source1:        waydroid.te
Patch0:         setup-firealld.patch

BuildRequires:  checkpolicy, selinux-policy-devel, make

Requires:       selinux-policy >= %{selinux_policyver}
Requires:       python-gbinder-python 
Requires:       libgbinder
Requires:       lxc
Requires:       libglibutil
%if 0%{?fedora} || 0%{?rhel} >= 8
Recommends: %{name}-selinux = %{version}-%{release}
%endif

%description
waydroid


%package selinux
Summary:            SELinux policy module required tu run waydroid
BuildArch:          noarch
Requires:           %{name} = %{version}-%{release}
Requires:           selinux-policy >= %{_selinux_policy_version}
Requires(post):     /usr/sbin/semodule
Requires(postun):   /usr/sbin/semodule

%description selinux
This package contains SELinux policy module necessary to run waydroid.

%prep
%forgeautosetup -p1
sed -i "s|anbox-||g" gbinder/anbox.conf
mkdir SELinux
cp %{S:1} SELinux/

%build
cd SELinux
for selinuxvariant in %{selinux_variants}
do
  %{__make} NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
  %{__mv} %{name}.pp %{name}.pp.${selinuxvariant}
  %{__make} NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -

%install
mkdir -p %{buildroot}%{_prefix}/lib/waydroid
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_sysconfdir}/gbinder.d
mkdir -p %{buildroot}%{_prefix}/lib/systemd/system
cp -r tools data "%{buildroot}%{_prefix}/lib/waydroid"
mv "%{buildroot}%{_prefix}/lib/waydroid/data/Waydroid.desktop" "%{buildroot}%{_datadir}/applications"
cp waydroid.py "%{buildroot}%{_prefix}/lib/waydroid"
ln -s ../lib/waydroid/waydroid.py "%{buildroot}%{_bindir}/waydroid"
cp gbinder/anbox.conf  %{buildroot}%{_sysconfdir}/gbinder.d
cp debian/waydroid-container.service %{buildroot}%{_prefix}/lib/systemd/system
for selinuxvariant in %{selinux_variants}
do
  %{__install} -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
  %{__install} -p -m 644 SELinux/%{name}.pp.${selinuxvariant} \
               %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{name}.pp
done
%{_hardlink} -cv %{buildroot}%{_datadir}/selinux

%post selinux
for selinuxvariant in %{selinux_variants}
do
  /usr/sbin/semodule -s ${selinuxvariant} -i \
    %{_datadir}/selinux/${selinuxvariant}/%{name}.pp &> /dev/null || :
done

%postun selinux
if [ $1 -eq 0 ] ; then
  for selinuxvariant in %{selinux_variants}
  do
    /usr/sbin/semodule -s ${selinuxvariant} -r %{name} &> /dev/null || :
  done
fi

%files
%license LICENSE 
%doc README.md 
%{_prefix}/lib/waydroid
%{_datadir}/applications/Waydroid.desktop
%{_bindir}/waydroid
%{_sysconfdir}/gbinder.d/anbox.conf
%{_prefix}/lib/systemd/system/waydroid-container.service

%files selinux
%doc SELinux/%{name}.te
%{_datadir}/selinux/*/%{name}.pp

%changelog
* Wed Aug 12 2020 Qiyu Yan <yanqiyu@fedoraproject.org> - 0-0.1.20200811gitc87ea48
- initial package

