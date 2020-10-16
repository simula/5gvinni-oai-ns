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
# Copyright (C) 2019-2020 by Thomas Dreibholz
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


# ***************************************************************************
# NOTE:
# Double escaping is required for \ and " in command string!
# 1. Python
# 2. bash -c "<command>"
# That is: $ => \$ ; \ => \\ ; " => \\\"
# ***************************************************************************



# ###########################################################################
# #### SPGW-U Charm functions                                            ####
# ###########################################################################

# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('spgwucharm.installed')
def install_spgwucharm_proxy_charm():
   set_flag('spgwucharm.installed')
   vduHelper.setStatus('install_spgwucharm_proxy_charm: SSH proxy charm is READY')


# ###### prepare-spgwu-build function #######################################
@when('actions.prepare-spgwu-build')
@when('spgwucharm.installed')
@when_not('spgwucharm.prepared-spgwu-build')
def prepare_spgwu_build():
   vduHelper.beginBlock('prepare_spgwu_build')
   try:

      # ====== Get SPGW-U parameters ========================================
      # For a documentation of the installation procedure, see:
      # https://github.com/OPENAIRINTERFACE/openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-u

      gitRepository          = function_get('spgwu-git-repository')
      gitCommit              = function_get('spgwu-git-commit')
      gitDirectory           = 'openair-spgwu-tiny'

      spgwuS1U_IPv4Interface = IPv4Interface(function_get('spgwu-S1U-ipv4-interface'))
      spgwuS1U_IPv4Gateway   = IPv4Address(function_get('spgwu-S1U-ipv4-gateway'))

      spgwuSGi_IPv4Interface = IPv4Interface(function_get('spgwu-SGi-ipv4-interface'))
      spgwuSGi_IPv4Gateway   = IPv4Address(function_get('spgwu-SGi-ipv4-gateway'))
      if function_get('spgwu-SGi-ipv6-interface') == '':
         spgwuSGi_IPv6Interface = None
      else:
         spgwuSGi_IPv6Interface = IPv6Interface(function_get('spgwu-SGi-ipv6-interface'))
      if function_get('spgwu-SGi-ipv6-gateway') == '':
         spgwuSGi_IPv6Gateway = None
      else:
         spgwuSGi_IPv6Gateway = IPv6Address(function_get('spgwu-SGi-ipv6-gateway'))

      # Prepare network configurations:
      spgwuSXab_IfName       = 'ens4'
      spgwuS1U_IfName        = 'ens5'
      spgwuSGi_IfName        = 'ens6'

      configurationSXab = vduHelper.makeInterfaceConfiguration(spgwuSXab_IfName, IPv4Interface('0.0.0.0/0'), metric=61)
      configurationS1U  = vduHelper.makeInterfaceConfiguration(spgwuS1U_IfName, spgwuS1U_IPv4Interface, spgwuS1U_IPv4Gateway, metric=62)
      configurationSGi  = vduHelper.makeInterfaceConfiguration(spgwuSGi_IfName, spgwuSGi_IPv4Interface, spgwuSGi_IPv4Gateway,
                                                               spgwuSGi_IPv6Interface, spgwuSGi_IPv6Gateway,
                                                               metric=1, pdnInterface = 'pdn')


      # ====== Prepare system ===============================================
      vduHelper.beginBlock('Preparing system')
      vduHelper.configureInterface(spgwuSXab_IfName, configurationSXab, 61)
      vduHelper.configureInterface(spgwuS1U_IfName,  configurationS1U,  62)
      vduHelper.configureInterface(spgwuSGi_IfName,  configurationSGi,  63)
      vduHelper.testNetworking()
      vduHelper.waitForPackageUpdatesToComplete()
      vduHelper.endBlock()

      # ====== Prepare sources ==============================================
      vduHelper.beginBlock('Preparing sources')
      vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
      vduHelper.endBlock()


      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('spgwucharm.prepared-spgwu-build')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.prepare-spgwu-build')


# ###### configure-spgwu function ###########################################
@when('actions.configure-spgwu')
@when('spgwucharm.prepared-spgwu-build')
def configure_spgwu():
   vduHelper.beginBlock('configure_spgwu')
   try:

      # ====== Get SPGW-U parameters ========================================
      # For a documentation of the installation procedure, see:
      # https://github.com/OPENAIRINTERFACE/openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-u

      gitDirectory     = 'openair-spgwu-tiny'

      spgwuSXab_IfName = 'ens4'
      spgwuS1U_IfName  = 'ens5'
      spgwuSGi_IfName  = 'ens6'

      spgwcListString  = function_get('spgwu-spgwc-list').split(',')
      spgwcList        = ''
      for spgwc in spgwcListString:
         spgwcAddress = IPv4Address(spgwc)
         if len(spgwcList) > 0:
            spgwcList = spgwcList + ', '
         spgwcList = spgwcList + '{{ IPV4_ADDRESS=\\\\\\"{spgwcAddress}\\\\\\"; }}'.format(spgwcAddress = str(spgwcAddress))


      # ====== Build SPGW-U dependencies ====================================
      vduHelper.beginBlock('Building SPGW-U dependencies')
      vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/nornetpp/src/{gitDirectory}/build/scripts && \\
mkdir -p logs && \\
./build_spgwu -I -f >logs/build_spgwu-1.log 2>&1""".format(gitDirectory = gitDirectory))
      vduHelper.endBlock()

      # ====== Build SPGW-U itself ==========================================
      vduHelper.beginBlock('Building SPGW-U itself')
      vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/nornetpp/src/{gitDirectory}/build/scripts && \\
./build_spgwu -c -V -b Debug -j >logs/build_spgwu-2.log 2>&1""".format(gitDirectory = gitDirectory))
      vduHelper.endBlock()

      # ====== Configure SPGW-U =============================================
      vduHelper.beginBlock('Configuring SPGW-U')
      vduHelper.executeFromString("""\
cd /home/nornetpp/src/{gitDirectory}/build/scripts && \\
INSTANCE=1 && \\
PREFIX='/usr/local/etc/oai' && \\
sudo mkdir -m 0777 -p $PREFIX && \\
sudo cp ../../etc/spgw_u.conf  $PREFIX && \\
declare -A SPGWU_CONF && \\
SPGWU_CONF[@INSTANCE@]=$INSTANCE && \\
SPGWU_CONF[@PREFIX@]=$PREFIX && \\
SPGWU_CONF[@PID_DIRECTORY@]='/var/run' && \\
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_S1U_S12_S4_UP@]='{spgwuS1U_IfName}' && \\
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_SX@]='{spgwuSXab_IfName}' && \\
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_SGI@]='{spgwuSGi_IfName}' && \\
for K in "${{!SPGWU_CONF[@]}}"; do sudo egrep -lRZ "$K" $PREFIX | xargs -0 -l sudo sed -i -e "s|$K|${{SPGWU_CONF[$K]}}|g" ; ret=$?;[[ ret -ne 0 ]] && echo "Tried to replace $K with ${{SPGWU_CONF[$K]}}" || true ; done && \\
sudo sed -e "s/{{.*IPV4_ADDRESS=\\"192.168.160.100|\\".*;.*}}\|{{.*IPV4_ADDRESS=\\"@SPGWC0_IP_ADDRESS@\\".*;.*}}/{spgwcList}/g" -i /usr/local/etc/oai/spgw_u.conf""".format(
         gitDirectory      = gitDirectory,
         spgwuSXab_IfName  = spgwuSXab_IfName,
         spgwuS1U_IfName   = spgwuS1U_IfName,
         spgwuSGi_IfName   = spgwuSGi_IfName,
         spgwcList         = spgwcList
      ))
      vduHelper.endBlock()


      # ====== Configure HENCSAT QoS Setup ==================================
      vduHelper.beginBlock('Configuring QoS Setup')
      vduHelper.runInShell('sudo mkdir -p /etc/hencsat')
      vduHelper.createFileFromString('/etc/hencsat/hencsat-router.conf',
"""# HENCSAT Router Configuration

ROUTER_INTERFACE_LEFT=ens6
ROUTER_INTERFACE_RIGHT=pdn
""")
      vduHelper.aptInstallPackages([ 'hencsat-router' ], False)
      vduHelper.endBlock()


      # ====== Set up SPGW-U service ========================================
      vduHelper.beginBlock('Setting up SPGW-U service')
      vduHelper.configureSystemInfo('SPGW-U', 'This is the SPGW-U of the SimulaMet OAI VNF!')
      vduHelper.createFileFromString('/lib/systemd/system/spgwu.service',
"""[Unit]
Description=Serving and Packet Data Network Gateway -- User Plane (SPGW-U)
After=ssh.target

[Service]
ExecStart=/bin/sh -c 'exec /usr/local/bin/spgwu -c /usr/local/etc/oai/spgw_u.conf -o >>/var/log/spgwu.log 2>&1'
KillMode=process
Restart=on-failure
RestartPreventExitStatus=255
WorkingDirectory=/home/nornetpp/src/{gitDirectory}/build/scripts

[Install]
WantedBy=multi-user.target""".format(gitDirectory = gitDirectory))

      vduHelper.createFileFromString('/home/nornetpp/log',
"""#!/bin/sh
tail -f /var/log/spgwu.log""", True)

      vduHelper.createFileFromString('/home/nornetpp/restart',
"""#!/bin/sh
DIRECTORY=`dirname $0`
sudo service spgwu restart && $DIRECTORY/log""", True)
      vduHelper.endBlock()

      # ====== Set up sysstat service =======================================
      vduHelper.installSysStat()

      # ====== Clean up =====================================================
      vduHelper.cleanUp()

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('spgwucharm.configured-spgwu')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.configure-spgwu')


# ###### restart-spgwu function #############################################
@when('actions.restart-spgwu')
@when('spgwucharm.configured-spgwu')
def restart_spgwu():
   vduHelper.beginBlock('restart_spgwu')
   try:

      vduHelper.runInShell('sudo service spgwu restart')

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.restart-spgwu')
