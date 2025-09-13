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
# SimulaMet P4-SS VNF and NS
# Copyright (C) 2021-2023 by Thomas Dreibholz
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

import os
import subprocess
import sys
import traceback
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface

sys.path.append("lib")
sys.path.append("mod/operator")

from ops.charm import CharmBase
from ops.main  import main
from ops.model import ActiveStatus


import VDUHelper

vduHelper = VDUHelper.VDUHelper(1000)   # <<-- Default user ID for "ubuntu"!



# ###########################################################################
# #### P4-SS Charm functions                                             ####
# ###########################################################################

class P4SSCharm(CharmBase):

   # ###### Constructor #####################################################
   def __init__(self, framework, key):
      super().__init__(framework, key)

      # Listen to charm events
      self.framework.observe(self.on.config_changed, self.on_config_changed)
      self.framework.observe(self.on.install, self.on_install)
      self.framework.observe(self.on.start, self.on_start)

      # Listen to the action events
      self.framework.observe(self.on.prepare_p4ss_build_action, self.on_prepare_p4ss_build_action)
      self.framework.observe(self.on.configure_p4ss_action, self.on_configure_p4ss_action)
      self.framework.observe(self.on.restart_p4ss_action, self.on_restart_p4ss_action)


   # ###### Configuration ###################################################
   def on_config_changed(self, event):
      """Handle changes in configuration"""
      self.model.unit.status = ActiveStatus()


   # ###### Installation ####################################################
   def on_install(self, event):
      """Called when the charm is being installed"""
      self.model.unit.status = ActiveStatus()


   # ###### Start ###########################################################
   def on_start(self, event):
      """Called when the charm is being started"""
      self.model.unit.status = ActiveStatus()


   # ###### prepare-p4ss-build action #######################################
   def on_prepare_p4ss_build_action(self, event):
      vduHelper.beginBlock('on_prepare_p4ss_build_action')
      try:

         # ====== Get P4-SS parameters ======================================
         gitName       = event.params['git-name']
         gitEmail      = event.params['git-email']
         gitRepository = event.params['p4ss-git-repository']
         gitCommit     = event.params['p4ss-git-commit']
         gitDirectory  = 'bmv2'

         # ====== Prepare system ============================================
         vduHelper.beginBlock('Preparing system')

         # Prepare network configuration:
         # Cloud-Init configures all 3 interfaces in Ubuntu 20.04+
         # => unwanted configuration on ens3 and ens4
         # Get rid of the Cloud-Init configuration, then configure the
         # interfaces manually with the correct configuration.
         vduHelper.runInShell('mv /etc/netplan/50-cloud-init.yaml ' + vduHelper.getHomeDirectory())
         interfaceConfiguration = vduHelper.makeInterfaceConfiguration('ens3')
         vduHelper.configureInterface('ens3', interfaceConfiguration, 50)
         n = 0
         for interfaceName in [ 'ens4', 'ens5' ]:
            interfaceConfiguration = vduHelper.makeInterfaceConfiguration(interfaceName, None)
            vduHelper.configureInterface(interfaceName, interfaceConfiguration, 61 + n)
            n = n + 1
         vduHelper.testNetworking()

         vduHelper.executeFromString("""\
sudo -u {user} -g {group} mkdir -p {homeDirectory}/src
""".format(user          = vduHelper.getUser(),
           group         = vduHelper.getGroup(),
           homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))
         vduHelper.configureGit(gitName, gitEmail)
         vduHelper.waitForPackageUpdatesToComplete()
         vduHelper.aptAddRepository('ppa:dreibh/ppa')
         vduHelper.aptInstallPackages([
            'autoconf',
            'automake',
            'g++',
            'joe',
            'make',
            'mlocate',
            'libboost-dev',
            'libboost-filesystem-dev',
            'libboost-program-options-dev',
            'libboost-system-dev',
            'libboost-thread-dev',
            'libgmp-dev',
            'libgrpc++-dev',
            'libgrpc-dev',
            'libjudy-dev',
            'libnanomsg-dev',
            'libpcap-dev',
            'libprotobuf-dev',
            'libprotoc-dev',
            'libssl-dev',
            'libthrift-dev',
            'libtool',
            'protobuf-compiler',
            'protobuf-compiler-grpc',
            'python3-six',
            'python3-thrift',
            'td-system-info',
            'thrift-compiler'
         ])
         vduHelper.endBlock()

         # ====== Prepare sources ===========================================
         vduHelper.beginBlock('Preparing sources')
         vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
         vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \
chown -R {user}:{group} {homeDirectory}/src/{gitDirectory} && \
cd {homeDirectory}/src/{gitDirectory} && \
sudo -u {user} -g {group} --preserve-env=MAKEFLAGS ./autogen.sh && \
sudo -u {user} -g {group} --preserve-env=MAKEFLAGS ./configure --with-pdfixed --enable-debugger --with-thrift --with-nanomsggit
""".format(user          = vduHelper.getUser(),
           group         = vduHelper.getGroup(),
           homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))
         vduHelper.endBlock()


         message = vduHelper.endBlock()
         event.set_results( { 'prepared': True, 'outout': message } )
      except:
         message = vduHelper.endBlockInException()
         event.fail(message)
      finally:
         self.model.unit.status = ActiveStatus()


   # ###### configure-p4ss action ########################################
   def on_configure_p4ss_action(self, event):
      vduHelper.beginBlock('on_configure_p4ss_action')
      try:

         # ====== Get P4-SS parameters ======================================
         gitDirectory  = 'bmv2'

         # ====== Configure P4-SS ===========================================
         #vduHelper.beginBlock('Configuring P4-SS')
         #vduHelper.configureSwitch('ss0', [ 'ens4', 'ens5' ])
         #vduHelper.createFileFromString('/etc/rc.local',
#"""\
##!/bin/sh

## IMPORTANT: Ignore VXLAN traffic, to prevent that the switch generates a
##            packet flooding with VXLAN packets when it is attached to the
##            network also transporting traffic of the VLs!
#ovs-ofctl -O OpenFlow15 add-flow ss0 "priority=8000 udp,nw_dst=224.0.0.1,tp_dst=8472 actions=drop"
#""", True)
         #vduHelper.runInShell('sudo /etc/rc.local')
         #vduHelper.endBlock()

         # ====== Set up P4-SS service ======================================
         vduHelper.beginBlock('Setting up P4-SS service')
         vduHelper.configureSystemInfo('P4-SS', 'This is the SimulaMet P4-SimpleSwitch VNF!')
         vduHelper.createFileFromString('/lib/systemd/system/p4ss.service', """\
[Unit]
Description=P4SS Controller
After=ssh.target

[Service]
ExecStart=/bin/sh -c 'exec simple_switch --log-console --interface 0@ens4 --interface 1@ens5 PROVIDE_PROGRAM_HERE >>/var/log/p4ss.log 2>&1'
KillMode=process
Restart=on-failure
RestartPreventExitStatus=255
WorkingDirectory={homeDirectory}

[Install]
WantedBy=multi-user.target
""".format(homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))

         vduHelper.createFileFromString(os.path.join(vduHelper.getHomeDirectory(), 'log'),
"""\
#!/bin/sh
tail -f /var/log/p4ss.log
""", True)

         vduHelper.createFileFromString(os.path.join(vduHelper.getHomeDirectory(), 'restart'),
"""\
#!/bin/sh
DIRECTORY=`dirname $0`
service p4ss restart && $DIRECTORY/log
""", True)
         vduHelper.runInShell("""\
chown {user}:{group} {homeDirectory}/log {homeDirectory}/restart
""".format(user          = vduHelper.getUser(),
           group         = vduHelper.getGroup(),
           homeDirectory = vduHelper.getHomeDirectory()))
         vduHelper.endBlock()

         # ====== Set up sysstat service ====================================
         vduHelper.installSysStat()

         # ====== Clean up ==================================================
         vduHelper.cleanUp()

         message = vduHelper.endBlock()
         event.set_results( { 'configured': True, 'outout': message } )
      except:
         message = vduHelper.endBlockInException()
         event.fail(message)
      finally:
         self.model.unit.status = ActiveStatus()


   # ###### restart-p4ss action #############################################
   def on_restart_p4ss_action(self, event):
      vduHelper.beginBlock('on_restart_p4ss_action')
      try:

         # vduHelper.runInShell('service p4ss restart')

         message = vduHelper.endBlock()
         event.set_results( { 'restarted': True, 'outout': message } )
      except:
         message = vduHelper.endBlockInException()
         event.fail(message)
      finally:
         self.model.unit.status = ActiveStatus()



# ###########################################################################
# #### Main program                                                      ####
# ###########################################################################

if __name__ == "__main__":
   main(P4SSCharm)
