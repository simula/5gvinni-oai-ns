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
# SimulaMet OAI 5G Docker VNF and NS
# Copyright (C) 2019-2023 by Thomas Dreibholz
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
# #### OAI 5G Docker Charm functions                                     ####
# ###########################################################################

class OAI5GDockerCharm(CharmBase):

   # ###### Constructor #####################################################
   def __init__(self, framework, key):
      super().__init__(framework, key)

      # Listen to charm events
      self.framework.observe(self.on.config_changed, self.on_config_changed)
      self.framework.observe(self.on.install, self.on_install)
      self.framework.observe(self.on.start, self.on_start)

      # Listen to the action events
      self.framework.observe(self.on.prepare_oai5gdocker_build_action, self.on_prepare_oai5gdocker_build_action)
      self.framework.observe(self.on.configure_oai5gdocker_action, self.on_configure_oai5gdocker_action)
      self.framework.observe(self.on.restart_oai5gdocker_action, self.on_restart_oai5gdocker_action)


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


   # ###### prepare-oai5gdocker-build action ################################
   def on_prepare_oai5gdocker_build_action(self, event):
      vduHelper.beginBlock('on_prepare_oai5gdocker_build_action')
      try:

         # ====== Get OAI 5G Docker parameters ==============================
         gitName       = event.params['git-name']
         gitEmail      = event.params['git-email']
         gitRepository = event.params['oai5gdocker-git-repository']
         gitCommit     = event.params['oai5gdocker-git-commit']
         gitDirectory  = '5gvinni-oai-ns'

         # Prepare network configuration:
         # Cloud-Init configures both interfaces in Ubuntu 20.04+
         # => unwanted configuration on ens3 and ens4
         # Get rid of the Cloud-Init configuration, then configure the
         # interfaces manually with the correct configuration.
         vduHelper.runInShell('mv /etc/netplan/50-cloud-init.yaml ' + vduHelper.getHomeDirectory())
         interfaceConfiguration = vduHelper.makeInterfaceConfiguration('ens3')
         vduHelper.configureInterface('ens3', interfaceConfiguration, 50)
         interfaceConfiguration = vduHelper.makeInterfaceConfiguration('ens4', dhcpNoDNS = True)
         vduHelper.configureInterface('ens4', interfaceConfiguration, 51)

         # ====== Prepare system ============================================
         vduHelper.beginBlock('Preparing system')

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
         vduHelper.aptInstallPackages([ 'joe', 'mlocate', 'td-system-info',
                                        'docker.io', 'docker-compose', 'tshark'
                                      ])

         vduHelper.endBlock()

         # ====== Prepare sources ===========================================
         vduHelper.beginBlock('Preparing sources')
         vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
         vduHelper.executeFromString("""\
sudo usermod -a -G docker {user} && \
chown -R {user}:{group} {homeDirectory}/src/{gitDirectory} && \
cd {homeDirectory}/src/{gitDirectory} && \
sudo -u {user} -g {group} git submodule init && \
sudo -u {user} -g {group} git submodule update
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


   # ###### configure-oai5gdocker action ####################################
   def on_configure_oai5gdocker_action(self, event):
      vduHelper.beginBlock('on_configure_oai5gdocker_action')
      try:

         # ====== Get OAI 5G Docker parameters ==============================
         gitDirectory  = '5gvinni-oai-ns'

         # ====== Configure OAI 5G Docker ===================================
         vduHelper.beginBlock('Configuring OAI 5G Docker')

         vduHelper.executeFromString("""\
cd {homeDirectory}/src/{gitDirectory}
""".format(user          = vduHelper.getUser(),
           group         = vduHelper.getGroup(),
           homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))

         vduHelper.createFileFromString('/etc/rc.local',
"""\
#!/bin/sh

sysctl net.ipv4.conf.all.forwarding=1
iptables -P FORWARD ACCEPT
""", True)
         vduHelper.runInShell('sudo /etc/rc.local')

         vduHelper.endBlock()

         # ====== Set up OAI 5G Docker service ==============================
         vduHelper.beginBlock('Setting up OAI 5G Docker service')
         vduHelper.configureSystemInfo('OAI 5G Docker Controller', 'This is the OAI 5G Docker Controller of the SimulaMet OAI 5G Docker VNF!')

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


   # ###### restart-oai5gdocker action ##########################################
   def on_restart_oai5gdocker_action(self, event):
      vduHelper.beginBlock('on_restart_oai5gdocker_action')
      try:

         # vduHelper.runInShell('...')   # TBD!

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
   main(OAI5GDockerCharm)
