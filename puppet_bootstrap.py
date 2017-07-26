#!/usr/bin/python

import platform
from subprocess import call
import urllib
import os
import time
import shutil
import sys
import re
import getopt



def usage():
  help_string= '''
Usage: puppet_bootstrap.py [OPTIONS]
Installs dependencies needed to apply puppet manifests without a puppet-master.


With no options, apt/yum repos from puppetlabs are installed, and necessary
packages are installed.

 Options:
  -h, --help        print this screen
  -a, --apply=      apply the specified manifest file after installing packages
  -f, --factervar=  create the specified variable in facter. Should be in the
                   form <varname>:<varvalue>.
  -m, --modulepath= set modulepath parameter in /etc/puppetlabs/puppet/puppet.conf
  -p, --hierapath=  set hiera_config parameter in /etc/puppetlabs/puppet/puppet.conf
  -s, --server= set server parameter in /etc/puppetlabs/puppet/puppet.conf
  -e, --environment=  set environment parameter in /etc/puppetlabs/puppet/puppet.conf

 Examples:
  puppet_bootstrap.py -a /etc/puppetlabs/puppet/webserver.pp -f "fqdn:serv.example.com"
    # Will install packages, set the fqdn facter variable to
      myserver.example.com, then will apply /etc/puppetlabs/puppet/webserver.pp

  puppet_bootstrap.py -m /etc/puppetlabs/puppet/modules -p /etc/hiera.yaml
    # Installs packages and sets modulepath and hiera_config in puppet.conf
'''
  print help_string



'''
Processes command line options via getopt.

Exits with error (1) on failure.
'''
def process_opts():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "ha:f:m:p:s:e:", ["help", "apply=", "factervar=", "modulepath=", "hierapath=", "server=", "environment="])
  except getopt.GetoptError as err:
    print str(err)
    usage()
    exit(1)

  #Globals! Generally just the variables controlled by command line args
  global manifest_to_apply
  global factervar
  global should_puppet_config
  global hiera_path
  global module_path
  global environment
  global server

  #default values of variables
  manifest_to_apply = ""
  factervar = ""
  should_puppet_config = False
  module_path = ""
  hiera_path = ""
  server = ""
  environment = ""

  for o, a in opts:
    if o in ("-h", "--help"):
      usage()
      sys.exit(0)
    elif o in ("-a", "--apply"):
      manifest_to_apply = a
    elif o in ("-f", "--factervar"):
      factervar = a
    elif o in ("-m", "--modulepath"):
      should_puppet_config = True
      module_path = a
    elif o in ("-p", "--heirapath"):
      should_puppet_config = True
      hiera_path = a
    elif o in ("-s", "--server"):
      should_puppet_config = True
      server = a
    elif o in ("-e", "--environment"):
      should_puppet_config = True
      environment = a




'''
Downlaods the puppetlabs repo debian package and installs
'''
def deb_config(repo_url):
  print "configuring for ubuntu/debian..."

  #download the deb
  urllib.urlretrieve(repo_url, "/tmp/puppetlabs-release.deb")

  #wait a bit for file to download...
  #todo I should probably do something smarter (without a race condition) here...
  time.sleep(5)

  #install repo
  call(["dpkg", "-i", "/tmp/puppetlabs-release.deb"])

  #install puppet
  call(["apt-get", "update"])
  call(["apt-get", "-y", "install", "puppet-agent"])



'''
Installs puppetlabs yum repo via rpm url
'''
def rh_config(repo_url):
  print "configuring for redhat/centos..."
  call(["rpm", "-ivh", repo_url])
  call(["yum", "-y", "install", "puppet", "facter"])



'''
is_deb returns true if the passed distro is a debian based distro, otherwise it
returns false
'''
def is_deb(dist):
  if (re.match(r'Ubuntu', dist)) or (re.match(r'debian', dist)):
    return True
  else:
    return False



'''
is_rh returns true if the passed distro is a redhat based distro, otherwise it
returns false
'''
def is_rh(dist):
  if (re.match(r'redhat', dist)) or (re.match(r'centos', dist)):
    return True
  else:
    return False



'''
Returns the distribution in the form <distro><version>_<architecture>. Returns
minor version for ubuntu, but only major for redhat based distros (the level at
which we need to pay attention for setting the repo path).
'''
def get_distribution():
  distTuple = platform.dist()
  distver = distTuple[0] + distTuple[1]

  #strip minor version from redhat based distros
  if (re.match(r'centos', distver)) or (re.match(r'redhat', distver)):
    distver = re.sub(r'\.\d+', '', distver)

  #tack on architecture
  arch = platform.architecture()
  distver = distver + "_" + arch[0]

  return distver



'''
get_dist_url iterates through all possible distros and returns the url to the
repo installation package.
'''
def get_dist_url(dist):
  print "setting the repository..."
  return{
         'Ubuntu10.04_32bit': 'http://apt.puppetlabs.com/puppetlabs-release-lucid.deb',
         'Ubuntu10.04_64bit': 'http://apt.puppetlabs.com/puppetlabs-release-lucid.deb',
         'Ubuntu12.04_32bit': 'http://apt.puppetlabs.com/puppetlabs-release-precise.deb',
         'Ubuntu12.04_64bit': 'http://apt.puppetlabs.com/puppetlabs-release-precise.deb',
         'Ubuntu12.10_32bit': 'http://apt.puppetlabs.com/puppetlabs-release-quantal.deb',
         'Ubuntu12.10_64bit': 'http://apt.puppetlabs.com/puppetlabs-release-quantal.deb',
         'Ubuntu13.04_32bit': 'http://apt.puppetlabs.com/puppetlabs-release-raring.deb',
         'Ubuntu13.04_64bit': 'http://apt.puppetlabs.com/puppetlabs-release-raring.deb',
         'Ubuntu13.10_32bit': 'http://apt.puppetlabs.com/puppetlabs-release-saucy.deb',
         'Ubuntu13.10_64bit': 'http://apt.puppetlabs.com/puppetlabs-release-saucy.deb',
         'Ubuntu14.04_32bit': 'http://apt.puppetlabs.com/puppetlabs-release-pc1-trusty.deb',
         'Ubuntu14.04_64bit': 'http://apt.puppetlabs.com/puppetlabs-release-pc1-trusty.deb',
         'Ubuntu16.04_64bit': 'http://apt.puppetlabs.com/puppetlabs-release-pc1-xenial.deb',
         'redhat5_32bit': 'https://yum.puppetlabs.com/el/5/products/i386/puppetlabs-release-5-7.noarch.rpm',
         'redhat5_64bit': 'https://yum.puppetlabs.com/el/5/products/x86_64/puppetlabs-release-5-7.noarch.rpm',
         'redhat6_32bit': 'https://yum.puppetlabs.com/el/6/products/i386/puppetlabs-release-6-7.noarch.rpm',
         'redhat6_64bit': 'https://yum.puppetlabs.com/el/6/products/x86_64/puppetlabs-release-6-7.noarch.rpm',
         'centos5_32bit': 'https://yum.puppetlabs.com/el/5/products/i386/puppetlabs-release-5-7.noarch.rpm',
         'centos5_64bit': 'https://yum.puppetlabs.com/el/5/products/x86_64/puppetlabs-release-5-7.noarch.rpm',
         'centos6_32bit': 'https://yum.puppetlabs.com/el/6/products/i386/puppetlabs-release-6-7.noarch.rpm',
         'centos6_64bit': 'https://yum.puppetlabs.com/el/6/products/x86_64/puppetlabs-release-6-7.noarch.rpm',
         'centos7_64bit': 'https://yum.puppetlabs.com/puppetlabs-release-pc1-el-7.noarch.rpm',
         }[dist]




'''
util function to prepend a string with "FACTER_" and remove anything after ':'
'''
def get_facter_varname(var):
  varname = re.sub(r'\:.+', '', var)
  varname = "FACTER_" + varname
  return varname



'''
util function to remove anything before ':' in a string
'''
def get_facter_varvalue(var):
  varvalue = re.sub(r'\w+\:', '', var)
  return varvalue



'''
function to edit puppet.conf config
'''
def edit_puppet_conf():

  import ConfigParser

  puppet_conf_loc = "/etc/puppetlabs/puppet/puppet.conf"

  puppet_config = ConfigParser.ConfigParser()
  puppet_config.readfp(open(puppet_conf_loc))
  puppet_config.add_section("main")

  if module_path:
    puppet_config.set("main", "basemodulepath", module_path)

  if hiera_path:
    puppet_config.set("main", "hiera_config", hiera_path)

  if server:
    puppet_config.set("main", "server", server)

  if environment:
    puppet_config.set("main", "environment", environment)

  puppet_config.remove_option("main", "templatedir")

  puppet_config.write(open(puppet_conf_loc, "wb"))



'''
ConfigParser doesn't appear to handle whitespace very well. This function will
remove leading and trailing whitespace from /etc/puppetlabs/puppet/puppet.conf, allowing
edits to the file via ConfigParser
'''
def sanitize_puppet_conf():
  #attempt to open puppet.conf for reading, then open new file for writing
  puppet_conf_loc = "/etc/puppetlabs/puppet/puppet.conf"
  try:
    orig_conf = open(puppet_conf_loc, "r")
  except IOError:
    print "Couldn't open " + puppet_conf_loc
    return 1

  new_conf_loc = puppet_conf_loc + ".tmp"
  new_conf = open(new_conf_loc, "w")


  #iterate through lines of puppet.conf stripping whitespace (but re-append \n)
  for line in orig_conf.readlines():
    new_conf.write(line.strip() + "\n")

  #close, then move over the new conf we craeted
  orig_conf.close()
  new_conf.close()
  os.rename(new_conf_loc, puppet_conf_loc)




'''
main function!
'''
def main():
  process_opts();

  #get dist and the url for the dist repo install package
  dist = get_distribution();
  repo_url = get_dist_url(dist);

  # Branch off to appropriate config function for dist
  if is_deb(dist):
    deb_config(repo_url)
  elif is_rh(dist):
    rh_config(repo_url)


  if should_puppet_config:
    sanitize_puppet_conf()
    edit_puppet_conf()


  if factervar:
    varname = get_facter_varname(factervar)
    varvalue = get_facter_varvalue(factervar)
    os.environ[varname] = varvalue


  if manifest_to_apply:
    call(["/opt/puppetlabs/bin/puppet", "apply", "-v", manifest_to_apply, "--modulepath", module_path, "--hiera_config", hiera_path])


if __name__ == '__main__':
  main()
