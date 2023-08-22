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
# #### SPGW-U Charm functions                                            ####
# ###########################################################################

class SPGWUCharm(CharmBase):

   # ###### Constructor #####################################################
   def __init__(self, framework, key):
      super().__init__(framework, key)

      # Listen to charm events
      self.framework.observe(self.on.config_changed, self.on_config_changed)
      self.framework.observe(self.on.install, self.on_install)
      self.framework.observe(self.on.start, self.on_start)

      # Listen to the action events
      self.framework.observe(self.on.prepare_spgwu_build_action, self.on_prepare_spgwu_build_action)
      self.framework.observe(self.on.configure_spgwu_action, self.on_configure_spgwu_action)
      self.framework.observe(self.on.restart_spgwu_action, self.on_restart_spgwu_action)


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


   # ###### prepare-spgwu-build action ######################################
   def on_prepare_spgwu_build_action(self, event):
      vduHelper.beginBlock('on_prepare_spgwu_build_action')
      try:

         # ====== Get SPGW-U parameters =====================================
         # For a documentation of the installation procedure, see:
         # https://github.com/simula/openairinterface-openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-u

         gitName       = event.params['git-name']
         gitEmail      = event.params['git-email']
         gitRepository = event.params['spgwu-git-repository']
         gitCommit     = event.params['spgwu-git-commit']
         gitDirectory  = 'openair-spgwu-tiny'

         spgwuS1U_IPv4Interface = IPv4Interface(event.params['spgwu-S1U-ipv4-interface'])
         if (event.params['spgwu-S1U-ipv4-gateway'] == None) or (event.params['spgwu-S1U-ipv4-gateway'] == ''):
            spgwuS1U_IPv4Gateway = None
         else:
            spgwuS1U_IPv4Gateway = IPv4Address(event.params['spgwu-S1U-ipv4-gateway'])

         spgwuSGi_IPv4Interface = IPv4Interface(event.params['spgwu-SGi-ipv4-interface'])
         spgwuSGi_IPv4Gateway   = IPv4Address(event.params['spgwu-SGi-ipv4-gateway'])
         if event.params['spgwu-SGi-ipv6-interface'] == '':
            spgwuSGi_IPv6Interface = None
         else:
            spgwuSGi_IPv6Interface = IPv6Interface(event.params['spgwu-SGi-ipv6-interface'])
         if (event.params['spgwu-SGi-ipv6-gateway'] == None) or (event.params['spgwu-SGi-ipv6-gateway'] == ''):
            spgwuSGi_IPv6Gateway = None
         else:
            spgwuSGi_IPv6Gateway = IPv6Address(event.params['spgwu-SGi-ipv6-gateway'])

         # Prepare network configurations:
         spgwuSXab_IfName       = 'ens4'
         spgwuS1U_IfName        = 'ens5'
         spgwuSGi_IfName        = 'ens6'

         configurationSXab = vduHelper.makeInterfaceConfiguration(spgwuSXab_IfName, None, metric=261)
         configurationS1U  = vduHelper.makeInterfaceConfiguration(spgwuS1U_IfName, spgwuS1U_IPv4Interface, spgwuS1U_IPv4Gateway, metric=262)
         configurationSGi  = vduHelper.makeInterfaceConfiguration(spgwuSGi_IfName, spgwuSGi_IPv4Interface, spgwuSGi_IPv4Gateway,
                                                                  spgwuSGi_IPv6Interface, spgwuSGi_IPv6Gateway,
                                                                  metric=200, pdnInterface = 'pdn')


         # ====== Prepare system ============================================
         vduHelper.beginBlock('Preparing system')

         vduHelper.configureInterface(spgwuSXab_IfName, configurationSXab, 61)
         vduHelper.configureInterface(spgwuS1U_IfName,  configurationS1U,  62)
         vduHelper.configureInterface(spgwuSGi_IfName,  configurationSGi,  63)
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


   # ###### configure-spgwu action ##########################################
   def on_configure_spgwu_action(self, event):
      vduHelper.beginBlock('on_configure_spgwu_action')
      try:

         # ====== Get SPGW-U parameters =====================================
         # For a documentation of the installation procedure, see:
         # https://github.com/simula/openairinterface-openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-u

         gitDirectory     = 'openair-spgwu-tiny'

         spgwuSXab_IfName = 'ens4'
         spgwuS1U_IfName  = 'ens5'
         spgwuSGi_IfName  = 'ens6'

         spgwcListString  = event.params['spgwu-spgwc-list'].split(',')
         spgwcList        = ''
         for spgwc in spgwcListString:
            spgwcAddress = IPv4Address(spgwc)
            if len(spgwcList) > 0:
               spgwcList = spgwcList + ', '
            spgwcList = spgwcList + '{{ IPV4_ADDRESS=\\\\\\"{spgwcAddress}\\\\\\"; }}'.format(spgwcAddress = str(spgwcAddress))


         # ====== Build SPGW-U dependencies =================================
         vduHelper.beginBlock('Building SPGW-U dependencies')
         vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \
cd /home/{homeDirectory}/src/{gitDirectory}/build/scripts && \
mkdir -p logs && \
sudo -u {user} -g {group} --preserve-env=MAKEFLAGS ./build_spgwu -I -f >logs/build_spgwu-1.log 2>&1
""".format(user          = vduHelper.getUser(),
           group         = vduHelper.getGroup(),
           homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))
         vduHelper.endBlock()

         # ====== Build SPGW-U itself =======================================
         vduHelper.beginBlock('Building SPGW-U itself')
         vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \
cd {homeDirectory}/src/{gitDirectory}/scripts && \
sudo -u {user} -g {group} mkdir -p logs && \
sudo -u {user} -g {group} --preserve-env=MAKEFLAGS ./build_spgwu -c -V -b Debug -j >logs/build_spgwu-2.log 2>&1
""".format(user          = vduHelper.getUser(),
           group         = vduHelper.getGroup(),
           homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))
         vduHelper.endBlock()

         # ====== Configure SPGW-U ==========================================
         vduHelper.beginBlock('Configuring SPGW-U')
         vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \
cd {homeDirectory}/src/{gitDirectory}/scripts && \
INSTANCE=1 && \\
PREFIX='/usr/local/etc/oai' && \\
sudo mkdir -m 0777 -p $PREFIX && \\
sudo cp ../../etc/spgw_u.conf $PREFIX && \\
declare -A SPGWU_CONF && \\
SPGWU_CONF[@INSTANCE@]=$INSTANCE && \\
SPGWU_CONF[@PREFIX@]=$PREFIX && \\
SPGWU_CONF[@PID_DIRECTORY@]='/var/run' && \\
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_S1U_S12_S4_UP@]='{spgwuS1U_IfName}' && \\
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_SX@]='{spgwuSXab_IfName}' && \\
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_SGI@]='{spgwuSGi_IfName}' && \\
for K in "${{!SPGWU_CONF[@]}}"; do sudo egrep -lRZ "$K" $PREFIX | xargs -0 -l sudo sed -i -e "s|$K|${{SPGWU_CONF[$K]}}|g" ; ret=$?;[[ ret -ne 0 ]] && echo "Tried to replace $K with ${{SPGWU_CONF[$K]}}" || true ; done && \\
sudo sed -e "s/{{.*IPV4_ADDRESS=\\"192.168.160.100|\\".*;.*}}\|{{.*IPV4_ADDRESS=\\"@SPGWC0_IP_ADDRESS@\\".*;.*}}/{spgwcList}/g" -i /usr/local/etc/oai/spgw_u.conf
""".format(user              = vduHelper.getUser(),
           group             = vduHelper.getGroup(),
           homeDirectory     = vduHelper.getHomeDirectory(),
           gitDirectory      = gitDirectory,
           spgwuSXab_IfName  = spgwuSXab_IfName,
           spgwuS1U_IfName   = spgwuS1U_IfName,
           spgwuSGi_IfName   = spgwuSGi_IfName,
           spgwcList         = spgwcList
         ))
         vduHelper.endBlock()


         # ====== Configure HENCSAT QoS Setup ===============================
         vduHelper.beginBlock('Configuring QoS Setup')
         vduHelper.runInShell('sudo mkdir -p /etc/hencsat')
         vduHelper.createFileFromString('/etc/hencsat/hencsat-router.conf',
"""# HENCSAT Router Configuration

ROUTER_INTERFACE_LEFT=ens6
ROUTER_INTERFACE_RIGHT=pdn
""")
         vduHelper.aptInstallPackages([ 'hencsat-router' ], False)
         vduHelper.endBlock()


         # ====== Set up SPGW-U service =====================================
         vduHelper.beginBlock('Setting up SPGW-U service')
         vduHelper.configureSystemInfo('SPGW-U', 'This is the SPGW-U of the SimulaMet OAI VNF!')
         vduHelper.createFileFromString('/lib/systemd/system/spgwu.service', """\
[Unit]
Description=Serving and Packet Data Network Gateway -- User Plane (SPGW-U)
After=ssh.target

[Service]
ExecStart=/bin/sh -c 'exec /usr/local/bin/spgwu -c /usr/local/etc/oai/spgw_u.conf -o >>/var/log/spgwu.log 2>&1'
KillMode=process
Restart=on-failure
RestartPreventExitStatus=255
WorkingDirectory=/home/{homeDirectory}/src/{gitDirectory}/build/scripts

[Install]
WantedBy=multi-user.target
""".format(homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))

         vduHelper.createFileFromString(os.path.join(vduHelper.getHomeDirectory(), 'log'),
"""\
#!/bin/sh
tail -f /var/log/spgwu.log
""", True)

         vduHelper.createFileFromString(os.path.join(vduHelper.getHomeDirectory(), 'restart'),
"""\
#!/bin/sh
DIRECTORY=`dirname $0`
service spgwu restart && $DIRECTORY/log
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


   # ###### restart-spgwu action ##########################################
   def on_restart_spgwu_action(self, event):
      vduHelper.beginBlock('on_restart_spgwu_action')
      try:

         vduHelper.runInShell('service spgwu restart')

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
   main(SPGWUCharm)
