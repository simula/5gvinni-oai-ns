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
# Copyright (C) 2019-2022 by Thomas Dreibholz
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
# #### MME Charm functions                                               ####
# ###########################################################################

# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('mmecharm.installed')
def install_mmecharm_proxy_charm():
   set_flag('mmecharm.installed')
   vduHelper.setStatus('install_mmecharm_proxy_charm: SSH proxy charm is READY')


# ###### prepare-mme-build function #########################################
@when('actions.prepare-mme-build')
@when('mmecharm.installed')
@when_not('mmecharm.prepared-mme-build')
def prepare_mme_build():
   vduHelper.beginBlock('prepare_mme_build')
   try:

      # ====== Get MME parameters ===========================================
      # For a documentation of the installation procedure, see:
      # https://github.com/OPENAIRINTERFACE/openair-cn/wiki/OpenAirSoftwareSupport#install-mme

      gitRepository        = function_get('mme-git-repository')
      gitCommit            = function_get('mme-git-commit')
      gitDirectory         = 'openair-mme'

      mmeS1C_IPv4Interface = IPv4Interface(function_get('mme-S1C-ipv4-interface'))
      mmeS1C_IPv4Gateway   = IPv4Address(function_get('mme-S1C-ipv4-gateway'))
      if function_get('mme-S1C-ipv6-interface') != '':
         mmeS1C_IPv6Interface = IPv6Interface(function_get('mme-S1C-ipv6-interface'))
      else:
         mmeS1C_IPv6Interface = None
      if function_get('mme-S1C-ipv6-gateway') != '':
         mmeS1C_IPv6Gateway   = IPv6Address(function_get('mme-S1C-ipv6-gateway'))
      else:
         mmeS1C_IPv6Gateway = None

      # Prepare network configurations:
      mmeS6a_IfName = 'ens4'
      mmeS11_IfName = 'ens5'
      mmeS1C_IfName = 'ens6'

      configurationS6a = vduHelper.makeInterfaceConfiguration(mmeS6a_IfName, IPv4Interface('0.0.0.0/0'))
      configurationS11 = vduHelper.makeInterfaceConfiguration(mmeS11_IfName, IPv4Interface('0.0.0.0/0'))
      configurationS1C = vduHelper.makeInterfaceConfiguration(mmeS1C_IfName, mmeS1C_IPv4Interface, mmeS1C_IPv4Gateway,
                                                              mmeS1C_IPv6Interface, mmeS1C_IPv6Gateway)

      # S10 dummy interface:
      mmeS10_IfName    = 'dummy0'
      configurationS10 = vduHelper.makeInterfaceConfiguration(mmeS10_IfName, IPv4Interface('192.168.10.110/24'), createDummy = True)

      # ====== Prepare system ===============================================
      vduHelper.beginBlock('Preparing system')
      vduHelper.configureInterface(mmeS6a_IfName, configurationS6a, 61)
      vduHelper.configureInterface(mmeS11_IfName, configurationS11, 62)
      vduHelper.configureInterface(mmeS1C_IfName, configurationS1C, 63)
      vduHelper.configureInterface(mmeS10_IfName, configurationS10, 64)
      vduHelper.testNetworking()
      vduHelper.waitForPackageUpdatesToComplete()
      vduHelper.endBlock()

      # ====== Prepare sources ==============================================
      vduHelper.beginBlock('Preparing sources')
      vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
      vduHelper.endBlock()


      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('mmecharm.prepared-mme-build')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.prepare-mme-build')


# ###### configure-mme function #############################################
@when('actions.configure-mme')
@when('mmecharm.prepared-mme-build')
def configure_mme():
   vduHelper.beginBlock('configure-mme')
   try:

      # ====== Get MME parameters ===========================================
      # For a documentation of the installation procedure, see:
      # https://github.com/OPENAIRINTERFACE/openair-cn/wiki/OpenAirSoftwareSupport#install-mme

      gitDirectory           = 'openair-mme'

      hssS6a_IPv4Address     = IPv4Address(function_get('hss-S6a-address'))
      mmeS1C_IPv4Interface   = IPv4Interface(function_get('mme-S1C-ipv4-interface'))
      mmeS11_IPv4Interface   = IPv4Interface(function_get('mme-S11-ipv4-interface'))
      mmeS10_IPv4Interface   = IPv4Interface('192.168.10.110/24')
      spwgcS11_IPv4Interface = IPv4Interface(function_get('spgwc-S11-ipv4-interface'))
      networkRealm           = function_get('network-realm')
      networkMCC             = int(function_get('network-mcc'))
      networkMNC             = int(function_get('network-mnc'))

      TAC_SGW_TEST = 7
      TAC_SGW_0    = 600
      TAC_MME_0    = 601
      TAC_MME_1    = 602

      tac_sgw_test = '{:04x}'.format(TAC_SGW_TEST)
      tac_sgw_0    = '{:04x}'.format(TAC_SGW_0)
      tac_mme_0    = '{:04x}'.format(TAC_MME_0)
      tac_mme_1    = '{:04x}'.format(TAC_MME_1)

      # Prepare network configurations:
      mmeS6a_IfName = 'ens4'
      mmeS11_IfName = 'ens5'
      mmeS1C_IfName = 'ens6'
      mmeS10_IfName = 'dummy0'

      # ====== Build MME dependencies =======================================
      vduHelper.beginBlock('Building MME dependencies')
      vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/nornetpp/src/{gitDirectory}/scripts && \\
mkdir -p logs && \\
./build_mme --check-installed-software --force >logs/build_mme-1.log 2>&1
""".format(gitDirectory = gitDirectory))
      vduHelper.endBlock()

      # ====== Build MME itself =============================================
      vduHelper.beginBlock('Building MME itself')
      vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/nornetpp/src/{gitDirectory}/scripts && \\
./build_mme --clean >logs/build_mme-2.log 2>&1
""".format(gitDirectory = gitDirectory))
      vduHelper.endBlock()

      # ====== Configure MME ================================================
      vduHelper.beginBlock('Configuring MME')
      vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/nornetpp/src/{gitDirectory}/scripts && \\
echo "127.0.1.1        mme.{networkRealm} mme" | sudo tee -a /etc/hosts && \\
echo "{hssS6a_IPv4Address}     hss.{networkRealm} hss" | sudo tee -a /etc/hosts && \\
openssl rand -out $HOME/.rnd 128 && \\
INSTANCE=1 && \\
PREFIX='/usr/local/etc/oai' && \\
sudo mkdir -m 0777 -p $PREFIX && \\
sudo mkdir -m 0777 -p $PREFIX/freeDiameter && \\
sudo cp ../etc/mme_fd.sprint.conf  $PREFIX/freeDiameter/mme_fd.conf && \\
sudo cp ../etc/mme.conf  $PREFIX && \\
declare -A MME_CONF && \\
MME_CONF[@MME_S6A_IP_ADDR@]="127.0.0.11" && \\
MME_CONF[@INSTANCE@]=$INSTANCE && \\
MME_CONF[@PREFIX@]=$PREFIX && \\
MME_CONF[@REALM@]='{networkRealm}' && \\
MME_CONF[@PID_DIRECTORY@]='/var/run' && \\
MME_CONF[@MME_FQDN@]="mme.{networkRealm}" && \\
MME_CONF[@HSS_HOSTNAME@]='hss' && \\
MME_CONF[@HSS_FQDN@]="hss.{networkRealm}" && \\
MME_CONF[@HSS_IP_ADDR@]='{hssS6a_IPv4Address}' && \\
MME_CONF[@MCC@]='{networkMCC}' && \\
MME_CONF[@MNC@]='{networkMNC}' && \\
MME_CONF[@MME_GID@]='32768' && \\
MME_CONF[@MME_CODE@]='3' && \\
MME_CONF[@TAC_0@]='600' && \\
MME_CONF[@TAC_1@]='601' && \\
MME_CONF[@TAC_2@]='602' && \\
MME_CONF[@MME_INTERFACE_NAME_FOR_S1_MME@]='{mmeS1C_IfName}' && \\
MME_CONF[@MME_IPV4_ADDRESS_FOR_S1_MME@]='{mmeS1C_IPv4Interface}' && \\
MME_CONF[@MME_INTERFACE_NAME_FOR_S11@]='{mmeS11_IfName}' && \\
MME_CONF[@MME_IPV4_ADDRESS_FOR_S11@]='{mmeS11_IPv4Interface}' && \\
MME_CONF[@MME_INTERFACE_NAME_FOR_S10@]='{mmeS10_IfName}' && \\
MME_CONF[@MME_IPV4_ADDRESS_FOR_S10@]='{mmeS10_IPv4Interface}' && \\
MME_CONF[@OUTPUT@]='CONSOLE' && \\
MME_CONF[@SGW_IPV4_ADDRESS_FOR_S11_TEST_0@]='{spwgcS11_IPv4Address}' && \\
MME_CONF[@SGW_IPV4_ADDRESS_FOR_S11_0@]='{spwgcS11_IPv4Address}' && \\
MME_CONF[@PEER_MME_IPV4_ADDRESS_FOR_S10_0@]='0.0.0.0/24' && \\
MME_CONF[@PEER_MME_IPV4_ADDRESS_FOR_S10_1@]='0.0.0.0/24' && \\
MME_CONF[@TAC-LB_SGW_TEST_0@]={tac_sgw_test_lo} && \\
MME_CONF[@TAC-HB_SGW_TEST_0@]={tac_sgw_test_hi} && \\
MME_CONF[@MCC_SGW_0@]={networkMCC} && \\
MME_CONF[@MNC3_SGW_0@]={networkMNC:03d} && \\
MME_CONF[@TAC-LB_SGW_0@]={tac_sgw_0_lo} && \\
MME_CONF[@TAC-HB_SGW_0@]={tac_sgw_0_hi} && \\
MME_CONF[@MCC_MME_0@]={networkMCC} && \\
MME_CONF[@MNC3_MME_0@]={networkMNC:03d} && \\
MME_CONF[@TAC-LB_MME_0@]={tac_mme_0_lo} && \\
MME_CONF[@TAC-HB_MME_0@]={tac_mme_0_hi} && \\
MME_CONF[@MCC_MME_1@]={networkMCC} && \\
MME_CONF[@MNC3_MME_1@]={networkMNC:03d} && \\
MME_CONF[@TAC-LB_MME_1@]={tac_mme_1_lo} && \\
MME_CONF[@TAC-HB_MME_1@]={tac_mme_1_hi} && \\
for K in "${{!MME_CONF[@]}}"; do sudo egrep -lRZ "$K" $PREFIX | xargs -0 -l sudo sed -i -e "s|$K|${{MME_CONF[$K]}}|g" ; ret=$?;[[ ret -ne 0 ]] && echo "Tried to replace $K with ${{MME_CONF[$K]}}" || true ; done && \\
sudo ./check_mme_s6a_certificate $PREFIX/freeDiameter mme.{networkRealm} >logs/check_mme_s6a_certificate.log 2>&1
""".format(
         gitDirectory           = gitDirectory,
         hssS6a_IPv4Address     = hssS6a_IPv4Address,
         mmeS1C_IfName          = mmeS1C_IfName,
         mmeS1C_IPv4Interface   = mmeS1C_IPv4Interface,
         mmeS11_IfName          = mmeS11_IfName,
         mmeS11_IPv4Interface   = mmeS11_IPv4Interface,
         mmeS10_IfName          = mmeS10_IfName,
         mmeS10_IPv4Interface   = mmeS10_IPv4Interface,

         spwgcS11_IPv4Address   = spwgcS11_IPv4Interface.ip,
         networkRealm           = networkRealm,
         networkMCC             = networkMCC,
         networkMNC             = networkMNC,

         tac_sgw_test_hi        = tac_sgw_test[0:2],
         tac_sgw_test_lo        = tac_sgw_test[2:4],
         tac_sgw_0_hi           = tac_sgw_0[0:2],
         tac_sgw_0_lo           = tac_sgw_0[2:4],
         tac_mme_0_hi           = tac_mme_0[0:2],
         tac_mme_0_lo           = tac_mme_0[2:4],
         tac_mme_1_hi           = tac_mme_1[0:2],
         tac_mme_1_lo           = tac_mme_1[2:4]
      ))
      vduHelper.endBlock()

      # ====== Set up MME service ===========================================
      vduHelper.beginBlock('Setting up MME service')
      vduHelper.configureSystemInfo('MME', 'This is the MME of the SimulaMet OAI VNF!')
      vduHelper.createFileFromString('/lib/systemd/system/mme.service', """\
[Unit]
Description=Mobility Management Entity (MME)
After=ssh.target

[Service]
ExecStart=/bin/sh -c 'exec /usr/local/bin/mme -c /usr/local/etc/oai/mme.conf >>/var/log/mme.log 2>&1'
KillMode=process
Restart=on-failure
RestartPreventExitStatus=255
WorkingDirectory=/home/nornetpp/src/{gitDirectory}/scripts

[Install]
WantedBy=multi-user.target
""".format(gitDirectory = gitDirectory))

      vduHelper.createFileFromString('/home/nornetpp/log',
"""\
#!/bin/sh
tail -f /var/log/mme.log
""", True)

      vduHelper.createFileFromString('/home/nornetpp/restart',
"""\
#!/bin/sh
DIRECTORY=`dirname $0`
sudo service mme restart && $DIRECTORY/log
""", True)
      vduHelper.runInShell('sudo chown nornetpp:nornetpp /home/nornetpp/log /home/nornetpp/restart')
      vduHelper.endBlock()

      # ====== Set up sysstat service =======================================
      vduHelper.installSysStat()

      # ====== Clean up =====================================================
      vduHelper.cleanUp()

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('mmecharm.configured-mme')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.configure-mme')


# ###### restart-mme function ###############################################
@when('actions.restart-mme')
@when('mmecharm.configured-mme')
def restart_mme():
   vduHelper.beginBlock('restart_mme')
   try:

      vduHelper.runInShell('sudo service mme restart')

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.restart-mme')
