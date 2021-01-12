#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =====================================================================
#     #######  #####          #     #   ###   #     # #     #   ###
#     #       #     #         #     #    #    ##    # ##    #    #
#     #       #               #     #    #    # #   # # #   #    #
#      #####  #  ####  #####  #     #    #    #  #  # #  #  #    #
#           # #     #          #   #     #    #   # # #   # #    #
#     #     # #     #           # #      #    #    ## #    ##    #
#      #####   #####             #      ###   #     # #     #   ###
# =====================================================================
#
# SimulaMet P4-OvS VNF and NS
# Copyright (C) 2021 by Thomas Dreibholz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact: dreibh@simula.no


from charmhelpers.core.hookenv import (
    function_get,
    function_fail,
    function_set,
    status_set
)
from charms.reactive import (
    clear_flag,
    set_flag,
    when,
    when_not
)
import charms.sshproxy

import subprocess
import sys
import traceback
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface

from . import VDUHelper

vduHelper = VDUHelper.VDUHelper()



# ###########################################################################
# #### FlexRAN Charm functions                                           ####
# ###########################################################################

# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('flexrancharm.installed')
def install_flexrancharm_proxy_charm():
   set_flag('flexrancharm.installed')
   vduHelper.setStatus('install_flexrancharm_proxy_charm: SSH proxy charm is READY')


# ###### prepare-flexran-build function #####################################
@when('actions.prepare-flexran-build')
@when('flexrancharm.installed')
@when_not('flexrancharm.prepared-flexran-build')
def prepare_flexran_build():
   vduHelper.beginBlock('prepare_flexran_build')
   try:

      # ====== Get FlexRAN parameters ===========================================
      # For a documentation of the installation procedure, see:
      # https://gitlab.eurecom.fr/mosaic5g/mosaic5g/-/wikis/tutorials/slicing

      gitName       = function_get('git-name')
      gitEmail      = function_get('git-email')
      gitRepository = function_get('flexran-git-repository')
      gitCommit     = function_get('flexran-git-commit')
      gitDirectory  = 'mosaic5g'

      flexranService_IPv4Interface = IPv4Interface(function_get('flexran-service-ipv4-interface'))
      flexranService_IPv4Gateway   = IPv4Address(function_get('flexran-service-ipv4-gateway'))
      if function_get('flexran-service-ipv6-interface') != '':
         flexranService_IPv6Interface = IPv6Interface(function_get('flexran-service-ipv6-interface'))
      else:
         flexranService_IPv6Interface = None
      if function_get('flexran-service-ipv6-gateway') != '':
         flexranService_IPv6Gateway   = IPv6Address(function_get('flexran-service-ipv6-gateway'))
      else:
         flexranService_IPv6Gateway = None

      # Prepare network configuration:
      flexranService_IfName = 'ens4'
      configurationService = vduHelper.makeInterfaceConfiguration(flexranService_IfName,
                                                                  flexranService_IPv4Interface, flexranService_IPv4Gateway,
                                                                  flexranService_IPv6Interface, flexranService_IPv6Gateway)

      # ====== Prepare system ===============================================
      vduHelper.beginBlock('Preparing system')
      vduHelper.configureGit(gitName, gitEmail)
      vduHelper.configureInterface(flexranService_IfName, configurationService, 61)
      vduHelper.testNetworking()
      vduHelper.waitForPackageUpdatesToComplete()
      vduHelper.endBlock()

      # ====== Prepare sources ==============================================
      vduHelper.beginBlock('Preparing sources')
      vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
      vduHelper.executeFromString("""\
cd /home/nornetpp/src/{gitDirectory} && \\
git submodule init && \\
git submodule update flexran
""".format(gitDirectory = gitDirectory))
      vduHelper.endBlock()


      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('flexrancharm.prepared-flexran-build')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.prepare-flexran-build')


# ###### configure-flexran function #########################################
@when('actions.configure-flexran')
@when('flexrancharm.prepared-flexran-build')
def configure_flexran():
   vduHelper.beginBlock('configure_flexran')
   try:

      # ====== Get FlexRAN parameters =======================================
      # For a documentation of the installation procedure, see:
      # https://gitlab.eurecom.fr/mosaic5g/mosaic5g/-/wikis/tutorials/slicing

      gitDirectory = 'mosaic5g'

      # ====== Build FlexRAN ================================================
      vduHelper.beginBlock('Building FlexRAN itself')
      vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/nornetpp/src/{gitDirectory} && \\
mkdir -p logs && \\
./build_m5g -f >logs/build_flexran.log 2>&1
""".format(gitDirectory = gitDirectory))
      vduHelper.endBlock()

      # ====== Configure FlexRAN ================================================
      vduHelper.beginBlock('Configuring FlexRAN')
      vduHelper.executeFromString("""\
cd /home/nornetpp/src/{gitDirectory}/flexran
""".format(gitDirectory = gitDirectory))
      vduHelper.endBlock()

      # ====== Set up FlexRAN service ===========================================
      vduHelper.beginBlock('Setting up FlexRAN service')
      vduHelper.configureSystemInfo('FlexRAN Controller', 'This is the FlexRAN Controller of the SimulaMet FlexRAN VNF!')
      vduHelper.createFileFromString('/lib/systemd/system/flexran.service', """\
[Unit]
Description=FlexRAN Controller
After=ssh.target

[Service]
ExecStart=/bin/sh -c 'exec /usr/bin/env FLEXRAN_RTC_HOME=/home/nornetpp/src/{gitDirectory}/flexran FLEXRAN_RTC_EXEC=/home/nornetpp/src/{gitDirectory}/flexran/build ./build/rt_controller -c log_config/basic_log >>/var/log/flexran.log 2>&1'
KillMode=process
Restart=on-failure
RestartPreventExitStatus=255
WorkingDirectory=/home/nornetpp/src/{gitDirectory}/flexran

[Install]
WantedBy=multi-user.target
""".format(gitDirectory = gitDirectory))

      vduHelper.createFileFromString('/home/nornetpp/log',
"""\
#!/bin/sh
tail -f /var/log/flexran.log
""", True)

      vduHelper.createFileFromString('/home/nornetpp/restart',
"""\
#!/bin/sh
DIRECTORY=`dirname $0`
sudo service flexran restart && $DIRECTORY/log
""", True)
      vduHelper.runInShell('sudo chown nornetpp:nornetpp /home/nornetpp/log /home/nornetpp/restart')
      vduHelper.endBlock()

      # ====== Set up sysstat service =======================================
      vduHelper.installSysStat()

      # ====== Clean up =====================================================
      vduHelper.cleanUp()

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('flexrancharm.configured-flexran')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.configure-flexran')


# ###### restart-flexran function ###############################################
@when('actions.restart-flexran')
@when('flexrancharm.configured-flexran')
def restart_flexran():
   vduHelper.beginBlock('restart_flexran')
   try:

      vduHelper.runInShell('sudo service flexran restart')

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.restart-flexran')



# ###########################################################################
# #### P4-OvS Charm functions                                           ####
# ###########################################################################

# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('p4ovscharm.installed')
def install_p4ovscharm_proxy_charm():
   set_flag('p4ovscharm.installed')
   vduHelper.setStatus('install_p4ovscharm_proxy_charm: SSH proxy charm is READY')


# ###### prepare-p4ovs-build function #####################################
@when('actions.prepare-p4ovs-build')
@when('p4ovscharm.installed')
@when_not('p4ovscharm.prepared-p4ovs-build')
def prepare_p4ovs_build():
   vduHelper.beginBlock('prepare_p4ovs_build')
   try:

      # ====== Get P4-OvS parameters ===========================================
      # For a documentation of the installation procedure, see:
      # https://gitlab.eurecom.fr/mosaic5g/mosaic5g/-/wikis/tutorials/slicing

      gitRepository = function_get('p4ovs-git-repository')
      gitCommit     = function_get('p4ovs-git-commit')
      gitDirectory  = 'P4-OvS'

      # ====== Prepare system ===============================================
      vduHelper.beginBlock('Preparing system')
      vduHelper.testNetworking()
      vduHelper.waitForPackageUpdatesToComplete()
      vduHelper.aptInstallPackages([
         'automake',
         'bison',
         'cmake',
         'flex',
         'g++',
         'libboost-all-dev',
         'libevent-dev',
         'libgc-dev',
         'libgmp-dev',
         'libgrpc++-dev',
         'libgrpc-dev',
         'libjudy-dev',
         'libnanomsg-dev',
         'libpcap-dev',
         'libprotobuf-dev',
         'libssl-dev',
         'libtool',
         'pkg-config',
         'protobuf-compiler',
         'protobuf-compiler-grpc',
         'python3-dev',
         'python3-pip'
      ])
      vduHelper.pipInstallPackages([ 'nnpy' ])
      vduHelper.endBlock()

      # ====== Prepare sources ==============================================
      vduHelper.beginBlock('Preparing sources')
      vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
      vduHelper.executeFromString("""\
cd /home/nornetpp/src/{gitDirectory} && \\
git remote add upstream https://github.com/osinstom/P4-OvS.git""".format(gitDirectory = gitDirectory))
      vduHelper.endBlock()


      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('p4ovscharm.prepared-p4ovs-build')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.prepare-p4ovs-build')


# ###### configure-thrift function ##########################################
@when('actions.configure-thrift')
@when('p4ovscharm.prepared-p4ovs-build')
def configure_thrift():
   vduHelper.beginBlock('configure_thrift')
   try:

      # ====== Build Thrift =================================================
      vduHelper.beginBlock('Building Thrift')
      vduHelper.executeFromString("""\
cd /home/nornetpp/src && \\
git clone https://github.com/apache/thrift && \\
cd thrift && \\
git checkout v0.13.0 && \\
./bootstrap.sh && \\
./configure --prefix=/usr && \\
make && \\
sudo make install""")
      vduHelper.endBlock()

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('p4ovscharm.configured-thrift')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.configure-thrift')


# ###### configure-pi function ##############################################
@when('actions.configure-pi')
@when('p4ovscharm.configured-thrift')
def configure_pi():
   vduHelper.beginBlock('configure_pi')
   try:

      # ====== Build PI =====================================================
      vduHelper.beginBlock('Building PI')
      vduHelper.executeFromString("""\
cd /home/nornetpp/src && \\
git clone https://github.com/osinstom/PI && \\
cd PI && \\
git checkout p4-ovs && \\
git submodule update --init && \\
./autogen.sh && \\
./configure --prefix=/usr --with-proto --with-fe-cpp --with-cli --with-internal-rpc --with-gnu-ld && \\
make && \\
sudo make install""")
      vduHelper.endBlock()

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('p4ovscharm.configured-pi')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.configure-pi')


# ###### configure-p4ovs function #########################################
@when('actions.configure-p4ovs')
@when('p4ovscharm.configured-pi')
def configure_p4ovs():
   vduHelper.beginBlock('configure_p4ovs')
   try:

      # ====== Get P4-OvS parameters =======================================
      # For a documentation of the installation procedure, see:
      # https://gitlab.eurecom.fr/mosaic5g/mosaic5g/-/wikis/tutorials/slicing

      gitDirectory = 'P4-OvS'

      # ====== Build P4-OvS ================================================
      vduHelper.beginBlock('Building P4-OvS itself')
      vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/nornetpp/src/{gitDirectory} && \\
./boot.sh && \\
./configure && \\
make""".format(gitDirectory = gitDirectory))
      vduHelper.endBlock()

      # ====== Configure P4-OvS ================================================
      vduHelper.beginBlock('Configuring P4-OvS')
      vduHelper.executeFromString("""\
cd /home/nornetpp/src/{gitDirectory}""".format(gitDirectory = gitDirectory))
      vduHelper.endBlock()

      # ====== Set up P4-OvS service ===========================================
      vduHelper.beginBlock('Setting up P4-OvS service')
      vduHelper.configureSystemInfo('P4-OvS', 'This is the SimulaMet P4-OvS VNF!')
      #vduHelper.createFileFromString('/lib/systemd/system/p4ovs.service', """\
#[Unit]
#Description=P4-OvS
#After=ssh.target

#[Service]
#ExecStart=/bin/sh -c 'exec /usr/bin/env FLEXRAN_RTC_HOME=/home/nornetpp/src/{gitDirectory}/p4ovs FLEXRAN_RTC_EXEC=/home/nornetpp/src/{gitDirectory}/p4ovs/build ./build/rt_controller -c log_config/basic_log >>/var/log/p4ovs.log 2>&1'
#KillMode=process
#Restart=on-failure
#RestartPreventExitStatus=255
#WorkingDirectory=/home/nornetpp/src/{gitDirectory}/p4ovs

#[Install]
#WantedBy=multi-user.target
#""".format(gitDirectory = gitDirectory))

      vduHelper.createFileFromString('/home/nornetpp/log',
"""\
#!/bin/sh
tail -f /var/log/p4ovs.log
""", True)

      vduHelper.createFileFromString('/home/nornetpp/restart',
"""\
#!/bin/sh
DIRECTORY=`dirname $0`
sudo service p4ovs restart && $DIRECTORY/log
""", True)
      vduHelper.runInShell('sudo chown nornetpp:nornetpp /home/nornetpp/log /home/nornetpp/restart')
      vduHelper.endBlock()

      # ====== Set up sysstat service =======================================
      vduHelper.installSysStat()

      # ====== Clean up =====================================================
      vduHelper.cleanUp()

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('p4ovscharm.configured-p4ovs')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.configure-p4ovs')


# ###### restart-p4ovs function ###############################################
@when('actions.restart-p4ovs')
@when('p4ovscharm.configured-p4ovs')
def restart_p4ovs():
   vduHelper.beginBlock('restart_p4ovs')
   try:

      # !!! FIXME! !!!
      # vduHelper.runInShell('sudo service p4ovs restart')

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.restart-p4ovs')
