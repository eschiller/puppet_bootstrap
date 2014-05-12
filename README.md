# Puppet_bootstrap.py

Gets Puppet up and running for provisioning stand-alone systems (environments without a puppet-master). 

Can Install puppet client, point to the correct location for modules and hiera config, and kick-off an initial run.

This script should work for most recent versions of RHEL/Centos and Ubuntu.

# Usage

With no options, apt/yum repos from puppetlabs are installed, and necessary
packages are installed.

<pre>
 Options:
  -h, --help        print this screen
  -a, --apply=      apply the specified manifest file after installing packages
  -f, --factervar=  create the specified variable in facter. Should be in the
                   form <varname>:<varvalue>.
  -m, --modulepath= set modulepath parameter in /etc/puppet/puppet.conf
  -p, --hierapath=  set hiera_config parameter in /etc/puppet/puppet.conf
</pre>

 Examples:
  puppet_bootstrap.py -a /etc/puppet/webserver.pp -f "fqdn:serv.example.com"
    # Will install packages, set the fqdn facter variable to
      myserver.example.com, then will apply /etc/puppet/webserver.pp
      
  puppet_bootstrap.py -m /etc/puppet/modules -p /etc/hiera.yaml
    # Installs packages and sets modulepath and hiera_config in puppet.conf
