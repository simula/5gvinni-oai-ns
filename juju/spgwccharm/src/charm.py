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
# SimulaMet OpenAirInterface Evolved Packet Core NS
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
# #### SPGW-C Charm functions                                            ####
# ###########################################################################

class SPGWCCharm(CharmBase):

   # ###### Constructor #####################################################
   def __init__(self, framework, key):
      super().__init__(framework, key)

      # Listen to charm events
      self.framework.observe(self.on.config_changed, self.on_config_changed)
      self.framework.observe(self.on.install, self.on_install)
      self.framework.observe(self.on.start, self.on_start)

      # Listen to the action events
      self.framework.observe(self.on.prepare_spgwc_build_action, self.on_prepare_spgwc_build_action)
      self.framework.observe(self.on.configure_spgwc_action, self.on_configure_spgwc_action)
      self.framework.observe(self.on.restart_spgwc_action, self.on_restart_spgwc_action)


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


   # ###### prepare-spgwc-build action ######################################
   def on_prepare_spgwc_build_action(self, event):
      vduHelper.beginBlock('on_prepare_spgwc_build_action')
      try:

         # ====== Get SPGW-C parameters =====================================
         # For a documentation of the installation procedure, see:
         # https://github.com/OPENAIRINTERFACE/openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-c

         gitName       = event.params['git-name']
         gitEmail      = event.params['git-email']
         gitRepository = event.params['spgwc-git-repository']
         gitCommit     = event.params['spgwc-git-commit']
         gitDirectory  = 'openair-spgwc'

         # Prepare network configurations:
         spgwcS11_IfName   = 'ens5'
         spgwcSXab_IfName  = 'ens4'
         configurationS11  = vduHelper.makeInterfaceConfiguration(spgwcS11_IfName,  None)
         configurationSXab = vduHelper.makeInterfaceConfiguration(spgwcSXab_IfName, None)

         # S5S8 dummy interfaces:
         spgwcS5S8_SGW_IfName  = 'dummy0'
         configurationS5S8_SGW = vduHelper.makeInterfaceConfiguration(spgwcS5S8_SGW_IfName, IPv4Interface('172.58.58.102/24'), createDummy = True)
         spgwcS5S8_PGW_IfName  = 'dummy1'
         configurationS5S8_PGW = vduHelper.makeInterfaceConfiguration(spgwcS5S8_PGW_IfName, IPv4Interface('172.58.58.101/24'), createDummy = True)

         # ====== Prepare system ============================================
         vduHelper.beginBlock('Preparing system')

         vduHelper.configureInterface(spgwcS11_IfName,       configurationS11,      61)
         vduHelper.configureInterface(spgwcSXab_IfName,      configurationSXab,     62)
         vduHelper.configureInterface(spgwcS5S8_SGW_IfName,  configurationS5S8_SGW, 63)
         vduHelper.configureInterface(spgwcS5S8_PGW_IfName,  configurationS5S8_PGW, 64)
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
         vduHelper.aptInstallPackages([ 'joe', 'mlocate', 'td-system-info' ])

         vduHelper.endBlock()

         # ====== Prepare sources ===========================================
         vduHelper.beginBlock('Preparing sources')
         vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
         vduHelper.executeFromString("""\
chown -R {user}:{group} {homeDirectory}/src/{gitDirectory}
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


   # ###### configure-spgwc action ##########################################
   def on_configure_spgwc_action(self, event):
      vduHelper.beginBlock('on_configure_spgwc_action')
      try:

         # ====== Get SPGW-C parameters =====================================
         # For a documentation of the installation procedure, see:
         # https://github.com/OPENAIRINTERFACE/openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-c

         gitDirectory         = 'openair-spgwc'

         networkRealm         = event.params['network-realm']
         networkDNS1_IPv4     = IPv4Address(event.params['network-ipv4-dns1'])
         networkDNS2_IPv4     = IPv4Address(event.params['network-ipv4-dns2'])

         # Prepare network configurations:
         spgwcSXab_IfName     = 'ens4'
         spgwcS11_IfName      = 'ens5'
         spgwcS5S8_SGW_IfName = 'dummy0'
         spgwcS5S8_PGW_IfName = 'dummy1'

         # ====== Build SPGW-C dependencies =================================
         vduHelper.beginBlock('Building SPGW-C dependencies')
         vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \
cd {homeDirectory}/src/{gitDirectory}/build/scripts && \
mkdir -p logs && \
sudo -u {user} -g {group} --preserve-env=MAKEFLAGS ./build_spgwc -I -f >logs/build_spgwc-1.log 2>&1
""".format(user          = vduHelper.getUser(),
           group         = vduHelper.getGroup(),
           homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))
         vduHelper.endBlock()

         # ====== Build SPGW-C itself =======================================
         vduHelper.beginBlock('Building SPGW-C itself')
         vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \
cd {homeDirectory}/src/{gitDirectory}/build/scripts && \
mkdir -p logs && \
sudo -u {user} -g {group} --preserve-env=MAKEFLAGS ./build_spgwc -c -V -b Debug -j >logs/build_spgwc-2.log 2>&1
""".format(user          = vduHelper.getUser(),
           group         = vduHelper.getGroup(),
           homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))
         vduHelper.endBlock()

         # ====== Configure SPGW-C ==========================================
         vduHelper.beginBlock('Configuring SPGW-C')
         vduHelper.executeFromString("""\
cd {homeDirectory}/src/{gitDirectory}/build/scripts && \\
INSTANCE=1 && \\
PREFIX='/usr/local/etc/oai' && \\
sudo mkdir -m 0777 -p $PREFIX && \\
sudo cp ../../etc/spgw_c.conf  $PREFIX && \\
declare -A SPGWC_CONF && \\
SPGWC_CONF[@INSTANCE@]=$INSTANCE && \\
SPGWC_CONF[@PREFIX@]=$PREFIX && \\
SPGWC_CONF[@PID_DIRECTORY@]='/var/run' && \\
SPGWC_CONF[@SGW_INTERFACE_NAME_FOR_S11@]='{spgwcS11_IfName}' && \\
SPGWC_CONF[@SGW_INTERFACE_NAME_FOR_S5_S8_CP@]='{spgwcS5S8_SGW_IfName}' && \\
SPGWC_CONF[@PGW_INTERFACE_NAME_FOR_S5_S8_CP@]='{spgwcS5S8_PGW_IfName}' && \\
SPGWC_CONF[@PGW_INTERFACE_NAME_FOR_SX@]='{spgwcSXab_IfName}' && \\
SPGWC_CONF[@DEFAULT_DNS_IPV4_ADDRESS@]='{networkDNS1_IPv4}' && \\
SPGWC_CONF[@DEFAULT_DNS_SEC_IPV4_ADDRESS@]='{networkDNS2_IPv4}' && \\
SPGWC_CONF[@DEFAULT_APN@]='default.{networkRealm}' && \\
for K in "${{!SPGWC_CONF[@]}}"; do sudo egrep -lRZ "$K" $PREFIX | xargs -0 -l sudo sed -i -e "s|$K|${{SPGWC_CONF[$K]}}|g" ; ret=$?;[[ ret -ne 0 ]] && echo "Tried to replace $K with ${{SPGWC_CONF[$K]}}" || true ; done && \\
sudo sed -e "s/APN_NI = \\"default\\"/APN_NI = \\"default.{networkRealm}\\"/g" -i /usr/local/etc/oai/spgw_c.conf && \\
sudo sed -e "s/APN_NI = \\"apn1\\"/APN_NI = \\"internet.{networkRealm}\\"/g" -i /usr/local/etc/oai/spgw_c.conf
""".format(user                 = vduHelper.getUser(),
           group                = vduHelper.getGroup(),
           homeDirectory        = vduHelper.getHomeDirectory(),
           gitDirectory         = gitDirectory,
           networkRealm         = networkRealm,
           networkDNS1_IPv4     = networkDNS1_IPv4,
           networkDNS2_IPv4     = networkDNS2_IPv4,
           spgwcSXab_IfName     = spgwcSXab_IfName,
           spgwcS11_IfName      = spgwcS11_IfName,
           spgwcS5S8_SGW_IfName = spgwcS5S8_SGW_IfName,
           spgwcS5S8_PGW_IfName = spgwcS5S8_PGW_IfName
          ))
         vduHelper.endBlock()


         # ====== Set up SPGW-C service ========================================
         vduHelper.beginBlock('Setting up SPGW-C service')
         vduHelper.configureSystemInfo('SPGW-C', 'This is the SPGW-C of the SimulaMet OAI VNF!')
         vduHelper.createFileFromString('/lib/systemd/system/spgwc.service', """\
[Unit]
Description=Serving and Packet Data Network Gateway -- Control Plane (SPGW-C)
After=ssh.target

[Service]
ExecStart=/bin/sh -c 'exec /usr/local/bin/spgwc -c /usr/local/etc/oai/spgw_c.conf -o >>/var/log/spgwc.log 2>&1'
KillMode=process
Restart=on-failure
RestartPreventExitStatus=255
WorkingDirectory={homeDirectory}/src/{gitDirectory}/build/scripts

[Install]
WantedBy=multi-user.target
""".format(homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))

         vduHelper.createFileFromString(os.path.join(vduHelper.getHomeDirectory(), 'log'),
"""\
#!/bin/sh
tail -f /var/log/spgwc.log
""", True)

         vduHelper.createFileFromString(os.path.join(vduHelper.getHomeDirectory(), 'restart'),
"""\
#!/bin/sh
DIRECTORY=`dirname $0`
service spgwc restart && $DIRECTORY/log
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


   # ###### restart-spgwc action ############################################
   def on_restart_spgwc_action(self, event):
      vduHelper.beginBlock('on_restart_spgwc_action')
      try:

         vduHelper.runInShell('service spgwc restart')

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
   main(SPGWCCharm)
