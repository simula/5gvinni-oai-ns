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
# #### SPGW-C Charm functions                                            ####
# ###########################################################################

# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('spgwccharm.installed')
def install_spgwccharm_proxy_charm():
   set_flag('spgwccharm.installed')
   vduHelper.setStatus('install_spgwccharm_proxy_charm: SSH proxy charm is READY')


# ###### prepare-spgwc-build function #######################################
@when('actions.prepare-spgwc-build')
@when('spgwccharm.installed')
@when_not('spgwccharm.prepared-spgwc-build')
def prepare_spgwc_build():
   vduHelper.beginBlock('prepare_spgwc_build')
   try:

      # ====== Get SPGW-C parameters ========================================
      # For a documentation of the installation procedure, see:
      # https://github.com/OPENAIRINTERFACE/openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-c

      gitRepository     = function_get('spgwc-git-repository')
      gitCommit         = function_get('spgwc-git-commit')
      gitDirectory      = 'openair-cn-cups'

      # Prepare network configurations:
      spgwcS11_IfName   = 'ens5'
      spgwcSXab_IfName  = 'ens4'
      configurationS11  = vduHelper.makeInterfaceConfiguration(spgwcS11_IfName,  IPv4Interface('0.0.0.0/0'))
      configurationSXab = vduHelper.makeInterfaceConfiguration(spgwcSXab_IfName, IPv4Interface('0.0.0.0/0'))

      # S5S8 dummy interfaces:
      spgwcS5S8_SGW_IfName  = 'dummy0:s5c'
      configurationS5S8_SGW = vduHelper.makeInterfaceConfiguration(spgwcS5S8_SGW_IfName, IPv4Interface('172.58.58.102/24'))
      spgwcS5S8_PGW_IfName  = 'dummy0:p5c'
      configurationS5S8_PGW = vduHelper.makeInterfaceConfiguration(spgwcS5S8_PGW_IfName, IPv4Interface('172.58.58.101/24'))

      # ====== Prepare system ===============================================
      vduHelper.beginBlock('Preparing system')
      vduHelper.configureInterface(spgwcS11_IfName,       configurationS11,       61)
      vduHelper.configureInterface(spgwcSXab_IfName,      configurationSXab,      62)
      vduHelper.configureInterface(spgwcS5S8_SGW_IfName,  configurationS5S8_SGW,  63)
      vduHelper.configureInterface(spgwcS5S8_PGW_IfName,  configurationS5S8_PGW,  64)
      vduHelper.testNetworking('8.8.8.8')
      vduHelper.endBlock()

      # ====== Prepare sources ==============================================
      vduHelper.beginBlock('Preparing sources')
      vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
      vduHelper.endBlock()


      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('spgwccharm.prepared-spgwc-build')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.prepare-spgwc-build')


# ###### configure-spgwc function ###########################################
@when('actions.configure-spgwc')
@when('spgwccharm.prepared-spgwc-build')
def configure_spgwc():
   vduHelper.beginBlock('configure_spgwc')
   try:

      # ====== Get SPGW-C parameters ========================================
      # For a documentation of the installation procedure, see:
      # https://github.com/OPENAIRINTERFACE/openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-c

      gitDirectory         = 'openair-cn-cups'

      networkRealm         = function_get('network-realm')
      networkDNS1_IPv4     = IPv4Address(function_get('network-ipv4-dns1'))
      networkDNS2_IPv4     = IPv4Address(function_get('network-ipv4-dns2'))

      # Prepare network configurations:
      spgwcSXab_IfName     = 'ens4'
      spgwcS11_IfName      = 'ens5'
      spgwcS5S8_SGW_IfName = 'dummy0:s5c'
      spgwcS5S8_PGW_IfName = 'dummy0:p5c'

      # ====== Build SPGW-C dependencies ====================================
      vduHelper.beginBlock('Building SPGW-C dependencies')
      commands = """\
export MAKEFLAGS=\\\"-j`nproc`\\\" && \\
cd /home/nornetpp/src/{gitDirectory}/build/scripts && \\
mkdir -p logs && \\
./build_spgwc -I -f >logs/build_spgwc-1.log 2>&1""".format(gitDirectory = gitDirectory)
      vduHelper.runInShell(commands)
      vduHelper.endBlock()

      # ====== Build SPGW-C itself ==========================================
      vduHelper.beginBlock('Building SPGW-C itself')
      commands = """\
export MAKEFLAGS=\\\"-j`nproc`\\\" && \\
cd /home/nornetpp/src/{gitDirectory}/build/scripts && \\
./build_spgwc -c -V -b Debug -j >logs/build_spgwc-2.log 2>&1""".format(gitDirectory = gitDirectory)
      vduHelper.runInShell(commands)
      vduHelper.endBlock()

      # ====== Configure SPGW-C =============================================
      vduHelper.beginBlock('Configuring SPGW-C')
      commands = """\
cd /home/nornetpp/src/{gitDirectory}/build/scripts && \\
INSTANCE=1 && \\
PREFIX='/usr/local/etc/oai' && \\
sudo mkdir -m 0777 -p \$PREFIX && \\
sudo cp ../../etc/spgw_c.conf  \$PREFIX && \\
declare -A SPGWC_CONF && \\
SPGWC_CONF[@INSTANCE@]=\$INSTANCE && \\
SPGWC_CONF[@PREFIX@]=\$PREFIX && \\
SPGWC_CONF[@PID_DIRECTORY@]='/var/run' && \\
SPGWC_CONF[@SGW_INTERFACE_NAME_FOR_S11@]='{spgwcS11_IfName}' && \\
SPGWC_CONF[@SGW_INTERFACE_NAME_FOR_S5_S8_CP@]='{spgwcS5S8_SGW_IfName}' && \\
SPGWC_CONF[@PGW_INTERFACE_NAME_FOR_S5_S8_CP@]='{spgwcS5S8_PGW_IfName}' && \\
SPGWC_CONF[@PGW_INTERFACE_NAME_FOR_SX@]='{spgwcSXab_IfName}' && \\
SPGWC_CONF[@DEFAULT_DNS_IPV4_ADDRESS@]='{networkDNS1_IPv4}' && \\
SPGWC_CONF[@DEFAULT_DNS_SEC_IPV4_ADDRESS@]='{networkDNS2_IPv4}' && \\
for K in \\\"\${{!SPGWC_CONF[@]}}\\\"; do sudo egrep -lRZ \\\"\$K\\\" \$PREFIX | xargs -0 -l sudo sed -i -e \\\"s|\$K|\${{SPGWC_CONF[\$K]}}|g\\\" ; ret=\$?;[[ ret -ne 0 ]] && echo \\\"Tried to replace \$K with \${{SPGWC_CONF[\$K]}}\\\" || true ; done && \\
sudo sed -e \\\"s/APN_NI = \\\\\\"default\\\\\\"/APN_NI = \\\\\\"default.{networkRealm}\\\\\\"/g\\\" -i /usr/local/etc/oai/spgw_c.conf && \\
sudo sed -e \\\"s/APN_NI = \\\\\\"apn1\\\\\\"/APN_NI = \\\\\\"internet.{networkRealm}\\\\\\"/g\\\" -i /usr/local/etc/oai/spgw_c.conf""".format(
         gitDirectory         = gitDirectory,
         networkRealm         = networkRealm,
         networkDNS1_IPv4     = networkDNS1_IPv4,
         networkDNS2_IPv4     = networkDNS2_IPv4,
         spgwcSXab_IfName     = spgwcSXab_IfName,
         spgwcS11_IfName      = spgwcS11_IfName,
         spgwcS5S8_SGW_IfName = spgwcS5S8_SGW_IfName,
         spgwcS5S8_PGW_IfName = spgwcS5S8_PGW_IfName
      )
      vduHelper.runInShell(commands)
      vduHelper.endBlock()


      # ====== Set up SPGW-C service ========================================
      vduHelper.beginBlock('Setting up SPGW-C service')
      commands = """\
( echo \\\"[Unit]\\\" && \\
echo \\\"Description=Serving and Packet Data Network Gateway -- Control Plane (SPGW-C)\\\" && \\
echo \\\"After=ssh.target\\\" && \\
echo \\\"\\\" && \\
echo \\\"[Service]\\\" && \\
echo \\\"ExecStart=/bin/sh -c \\\'exec /usr/local/bin/spgwc -c /usr/local/etc/oai/spgw_c.conf -o >>/var/log/spgwc.log 2>&1\\\'\\\" && \\
echo \\\"KillMode=process\\\" && \\
echo \\\"Restart=on-failure\\\" && \\
echo \\\"RestartPreventExitStatus=255\\\" && \\
echo \\\"WorkingDirectory=/home/nornetpp/src/openair-cn-cups/build/scripts\\\" && \\
echo \\\"\\\" && \\
echo \\\"[Install]\\\" && \\
echo \\\"WantedBy=multi-user.target\\\" ) | sudo tee /lib/systemd/system/spgwc.service && \\
sudo systemctl daemon-reload && \\
( echo -e \\\"#\\x21/bin/sh\\\" && echo \\\"tail -f /var/log/spgwc.log\\\" ) | tee /home/nornetpp/log && \\
chmod +x /home/nornetpp/log && \\
( echo -e \\\"#\\x21/bin/sh\\\" && echo \\\"sudo service spgwc restart && ./log\\\" ) | tee /home/nornetpp/restart && \\
chmod +x /home/nornetpp/restart"""

      vduHelper.runInShell(commands)
      vduHelper.endBlock()

      # ====== Set up sysstat service =======================================
      vduHelper.installSysStat()


      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('spgwccharm.configured-spgwc')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.configure-spgwc')


# ###### restart-spgwc function #############################################
@when('actions.restart-spgwc')
@when('spgwccharm.configured-spgwc')
def restart_spgwc():
   vduHelper.beginBlock('restart_spgwc')
   try:

      commands = 'sudo service spgwc restart'
      vduHelper.runInShell(commands)

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.restart-spgwc')
