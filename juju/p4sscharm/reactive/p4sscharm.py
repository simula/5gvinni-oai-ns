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
# #### P4-SS Charm functions                                            ####
# ###########################################################################

# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('p4sscharm.installed')
def install_p4sscharm_proxy_charm():
   set_flag('p4sscharm.installed')
   vduHelper.setStatus('install_p4sscharm_proxy_charm: SSH proxy charm is READY')


# ###### configure-p4ss function ###########################################
@when('actions.configure-p4ss')
@when('p4sscharm.installed')
def configure_p4ss():
   vduHelper.beginBlock('configure_p4ss')
   try:

      # ====== Prepare system ===============================================
      vduHelper.beginBlock('Preparing system')

      # Cloud-Init configures all 3 interfaces in Ubuntu 20.04+
      # => unwanted configuration on ens3 and ens4
      # Get rid of the Cloud-Init configuration, then configure the
      # interfaces manually with the correct configuration.
      vduHelper.runInShell('sudo mv /etc/netplan/50-cloud-init.yaml /home/nornetpp')
      interfaceConfiguration = vduHelper.makeInterfaceConfiguration('ens3')
      vduHelper.configureInterface('ens3', interfaceConfiguration, 50)
      n = 0
      for interfaceName in [ 'ens4', 'ens5' ]:
         interfaceConfiguration = vduHelper.makeInterfaceConfiguration(interfaceName, None)
         vduHelper.configureInterface(interfaceName, interfaceConfiguration, 61 + n)
         n = n + 1
      vduHelper.testNetworking()
      vduHelper.waitForPackageUpdatesToComplete()
      vduHelper.aptInstallPackages([
         'p4lang-p4c'
      ])
      vduHelper.endBlock()

      # ====== Configure P4-SS =============================================
      vduHelper.beginBlock('Configuring P4-SS')
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
      vduHelper.endBlock()

      # ====== Set up P4-SS service ========================================
      vduHelper.beginBlock('Setting up P4-SS service')
      vduHelper.configureSystemInfo('P4-SS', 'This is the SimulaMet P4-SimpleSwitch VNF!')
      vduHelper.createFileFromString('/lib/systemd/system/p4ss.service', """\
[Unit]
Description=FlexRAN Controller
After=ssh.target

[Service]
ExecStart=/bin/sh -c 'exec simple_switch --log-console --interface 0@ens4 --interface 1@ens5 PROVIDE_PROGRAM_HERE >>/var/log/p4ss.log 2>&1'
KillMode=process
Restart=on-failure
RestartPreventExitStatus=255
WorkingDirectory=/home/nornetpp

[Install]
WantedBy=multi-user.target
""")

      vduHelper.createFileFromString('/home/nornetpp/log',
"""\
#!/bin/sh
tail -f /var/log/p4ss.log
""", True)

      vduHelper.createFileFromString('/home/nornetpp/restart',
"""\
#!/bin/sh
DIRECTORY=`dirname $0`
sudo service p4ss restart && $DIRECTORY/log
""", True)
      vduHelper.runInShell('sudo chown nornetpp:nornetpp /home/nornetpp/log /home/nornetpp/restart')
      vduHelper.endBlock()

      # ====== Set up sysstat service =======================================
      vduHelper.installSysStat()

      # ====== Clean up =====================================================
      vduHelper.cleanUp()

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('p4sscharm.configured-p4ss')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.configure-p4ss')


# ###### restart-p4ss function #############################################
@when('actions.restart-p4ss')
@when('p4sscharm.configured-p4ss')
def restart_p4ss():
   vduHelper.beginBlock('restart_p4ss')
   try:

      # !!! FIXME! !!!
      # vduHelper.runInShell('sudo service p4ss restart')

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.restart-p4ss')
