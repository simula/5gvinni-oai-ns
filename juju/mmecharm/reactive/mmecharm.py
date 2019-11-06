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
# Copyright (C) 2019 by Thomas Dreibholz
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
    action_get,
    action_fail,
    action_set,
    status_set
)
from charms.reactive import (
    clear_flag,
    set_flag,
    when,
    when_not
)
import charms.sshproxy
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface


# ###########################################################################
# #### Helper functions                                                  ####
# ###########################################################################

# ###### Execute command ####################################################
def execute(commands):
   err = ''
   try:
      result, err = charms.sshproxy._run(commands)
   except:
      action_fail('command failed:' + err)
      return False
   else:
      # action_set( { 'outout': str(result).encode('utf-8') } )
      return True


# ######  Get /etc/network/interfaces setup for interface ###################
def configureInterface(name,
                       ipv4Interface = IPv4Interface('0.0.0.0/0'), ipv4Gateway = None,
                       ipv6Interface = None,                       ipv6Gateway = None,
                       metric = 1):

   # NOTE:
   # Double escaping is required for \ and " in "configuration" string!
   # 1. Python
   # 2. bash -c "<command>"

   configuration = 'auto ' + name + '\\\\n'

   # ====== IPv4 ============================================================
   if ipv4Interface == IPv4Interface('0.0.0.0/0'):
      configuration = configuration + 'iface ' + name + ' inet dhcp'
   else:
      configuration = configuration + \
         'iface ' + name + ' inet static\\\\n' + \
         '\\\\taddress ' + str(ipv4Interface.ip)      + '\\\\n' + \
         '\\\\tnetmask ' + str(ipv4Interface.netmask) + '\\\\n'
      if ((ipv4Gateway != None) and (ipv4Gateway != IPv4Address('0.0.0.0'))):
         configuration = configuration + \
            '\\\\tgateway ' + str(ipv4Gateway) + '\\\\n' + \
            '\\\\tmetric '  + str(metric)      + '\\\\n'
      configuration = configuration + '\\\\n'

   # ====== IPv6 ============================================================
   if ipv6Interface == None:
      configuration = configuration + \
         '\\\\niface ' + name + ' inet6 manual\\\\n' + \
         '\\\\tautoconf 0\\\\n'
   elif ipv6Interface == IPv6Interface('::/0'):
      configuration = configuration + \
         '\\\\niface ' + name + ' inet6 dhcp\\\\n' + \
         '\\\\tautoconf 0\\\\n'
   else:
      configuration = configuration + \
         '\\\\niface ' + name + ' inet6 static\\\\n' + \
         '\\\\tautoconf 0\\\\n' + \
         '\\\\taddress ' + str(ipv6Interface.ip)                + '\\\\n' + \
         '\\\\tnetmask ' + str(ipv6Interface.network.prefixlen) + '\\\\n'
      if ((ipv6Gateway != None) and (ipv6Gateway != IPv6Address('::'))):
         configuration = configuration + \
            '\\\\tgateway ' + str(ipv6Gateway) + '\\\\n' + \
            '\\\\tmetric '  + str(metric)      + '\\\\n'

   return configuration



# ###########################################################################
# #### Charm functions                                                   ####
# ###########################################################################

# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('mmecharm.installed')
def install_mmecharm_proxy_charm():
   set_flag('mmecharm.installed')
   status_set('active', 'Ready!')


# ###### prepare-mme-build function #########################################
@when('actions.prepare-mme-build')
@when('mmecharm.installed')
@when_not('mmecharm.prepared-mme-build')
def prepare_mme_build():

   # ====== Install MME =====================================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn/wiki/OpenAirSoftwareSupport#install-mme

   gitRepository            = 'https://github.com/OPENAIRINTERFACE/openair-cn.git'
   gitDirectory             = 'openair-cn'
   gitCommit                = 'develop'
   networkS1C_IPv4Interface = IPv4Interface('192.168.247.102/24')
   networkS1C_IPv4Gateway   = IPv4Address('0.0.0.0')
   networkS1C_IPv6Interface = None
   networkS1C_IPv6Gateway   = None

   # Prepare network configurations:
   mmeS6a_IfName = 'ens4'
   mmeS11_IfName = 'ens5'
   mmeS1C_IfName = 'ens6'

   configurationS6a = configureInterface(mmeS6a_IfName, IPv4Interface('0.0.0.0/0'))
   configurationS11 = configureInterface(mmeS11_IfName, IPv4Interface('0.0.0.0/0'))
   configurationS1C = configureInterface(mmeS1C_IfName, networkS1C_IPv4Interface, networkS1C_IPv4Gateway)

   # NOTE:
   # Double escaping is required for \ and " in "command" string!
   # 1. Python
   # 2. bash -c "<command>"
   # That is: $ => \$ ; \ => \\ ; " => \\\"

   commands = """\
echo \\\"###### Preparing system ###############################################\\\" && \\
echo -e \\\"{configurationS6a}\\\" | sudo tee /etc/network/interfaces.d/61-{mmeS6a_IfName} && sudo ifup {mmeS6a_IfName} || true && \\
echo -e \\\"{configurationS11}\\\" | sudo tee /etc/network/interfaces.d/62-{mmeS11_IfName} && sudo ifup {mmeS11_IfName} || true && \\
echo -e \\\"{configurationS1C}\\\" | sudo tee /etc/network/interfaces.d/63-{mmeS1C_IfName} && sudo ifup {mmeS1C_IfName} || true && \\
echo \\\"###### Preparing sources ##############################################\\\" && \\
cd /home/nornetpp/src && \\
if [ ! -d \\\"{gitDirectory}\\\" ] ; then git clone --quiet {gitRepository} {gitDirectory} && cd {gitDirectory} ; else cd {gitDirectory} && git pull ; fi && \\
git checkout {gitCommit} && \\
cd scripts && \\
echo \\\"###### Done! ##########################################################\\\"""".format(
      gitRepository    = gitRepository,
      gitDirectory     = gitDirectory,
      gitCommit        = gitCommit,
      mmeS6a_IfName    = mmeS6a_IfName,
      mmeS11_IfName    = mmeS11_IfName,
      mmeS1C_IfName    = mmeS1C_IfName,
      configurationS6a = configurationS6a,
      configurationS11 = configurationS11,
      configurationS1C = configurationS1C
   )

   if execute(commands) == True:
      set_flag('mmecharm.prepared-mme-build')
      clear_flag('actions.prepare-mme-build')


# ###### configure-mme function #############################################
@when('actions.configure-mme')
@when('mmecharm.prepared-mme-build')
def configure_mme():

   # ====== Install MME =====================================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn/wiki/OpenAirSoftwareSupport#install-mme

   gitRepository          = 'https://github.com/OPENAIRINTERFACE/openair-cn.git'
   gitDirectory           = 'openair-cn'
   gitCommit              = 'develop'
   hssS6a_IPv4Address     = '172.16.6.129'
   mmeS1C_IPv4IfName      = 'ens6'
   mmeS1C_IPv4Interface   = IPv4Interface('192.168.247.102/24')
   mmeS11_IPv4IfName      = 'ens5'
   mmeS11_IPv4Interface   = IPv4Interface('172.16.1.102/24')
   spwgcS11_IPv4Interface = IPv4Interface('172.16.1.104/24')
   networkRealm           = 'simula.nornet'
   networkMCC             = 242
   networkMNC             = 88
   networkLTE_K           = '449c4b91aeacd0ace182cf3a5a72bfa1'
   networkOP_K            = '1006020f0a478bf6b699f15c062e42b3'
   networkIMSIFirst       = '242881234500000'
   networkMSISDNFirst     = '24288880000000'
   networkUsers           = 1024

   TAC_SGW_TEST = 7
   TAC_SGW_0    = 600
   TAC_MME_0    = 601
   TAC_MME_1    = 602

   tac_sgw_test = '{:04x}'.format(TAC_SGW_TEST)
   tac_sgw_0    = '{:04x}'.format(TAC_SGW_0)
   tac_mme_0    = '{:04x}'.format(TAC_MME_0)
   tac_mme_1    = '{:04x}'.format(TAC_MME_1)

   # NOTE:
   # Double escaping is required for \ and " in "command" string!
   # 1. Python
   # 2. bash -c "<command>"
   # That is: $ => \$ ; \ => \\ ; " => \\\"

   commands = """\
echo \\\"###### Building MME ####################################################\\\" && \\
export MAKEFLAGS=\\\"-j`nproc`\\\" && \\
cd /home/nornetpp/src && \\
cd {gitDirectory} && \\
cd scripts && \\
mkdir -p logs && \\
echo \\\"====== Building dependencies ... ======\\\" && \\
./build_mme --check-installed-software --force >logs/build_mme-1.log 2>&1 && \\
echo \\\"====== Building service ... ======\\\" && \\
./build_mme --clean >logs/build_mme-2.log 2>&1 && \\
echo \\\"###### Creating MME configuration files ###############################\\\" && \\
openssl rand -out \$HOME/.rnd 128 && \\
INSTANCE=1 && \\
PREFIX='/usr/local/etc/oai' && \\
sudo mkdir -m 0777 -p \$PREFIX && \\
sudo mkdir -m 0777 -p \$PREFIX/freeDiameter && \\
sudo cp ../etc/mme_fd.sprint.conf  \$PREFIX/freeDiameter/mme_fd.conf && \\
sudo cp ../etc/mme.conf  \$PREFIX && \\
declare -A MME_CONF && \\
MME_CONF[@MME_S6A_IP_ADDR@]=\\\"127.0.0.11\\\" && \\
MME_CONF[@INSTANCE@]=\$INSTANCE && \\
MME_CONF[@PREFIX@]=\$PREFIX && \\
MME_CONF[@REALM@]='{networkRealm}' && \\
MME_CONF[@PID_DIRECTORY@]='/var/run' && \\
MME_CONF[@MME_FQDN@]=\\\"mme.{networkRealm}\\\" && \\
MME_CONF[@HSS_HOSTNAME@]='hss' && \\
MME_CONF[@HSS_FQDN@]=\\\"hss.{networkRealm}\\\" && \\
MME_CONF[@HSS_IP_ADDR@]='{hssS6a_IPv4Address}' && \\
MME_CONF[@MCC@]='{networkMCC}' && \\
MME_CONF[@MNC@]='{networkMNC}' && \\
MME_CONF[@MME_GID@]='32768' && \\
MME_CONF[@MME_CODE@]='3' && \\
MME_CONF[@TAC_0@]='600' && \\
MME_CONF[@TAC_1@]='601' && \\
MME_CONF[@TAC_2@]='602' && \\
MME_CONF[@MME_INTERFACE_NAME_FOR_S1_MME@]='{mmeS1C_IPv4IfName}' && \\
MME_CONF[@MME_IPV4_ADDRESS_FOR_S1_MME@]='{mmeS1C_IPv4Interface}' && \\
MME_CONF[@MME_INTERFACE_NAME_FOR_S11@]='{mmeS11_IPv4IfName}' && \\
MME_CONF[@MME_IPV4_ADDRESS_FOR_S11@]='{mmeS11_IPv4Interface}' && \\
MME_CONF[@MME_INTERFACE_NAME_FOR_S10@]='eth0:m10' && \\
MME_CONF[@MME_IPV4_ADDRESS_FOR_S10@]='192.168.10.110/24' && \\
MME_CONF[@OUTPUT@]='CONSOLE' && \\
MME_CONF[@SGW_IPV4_ADDRESS_FOR_S11_TEST_0@]='{spwgcS11_IPv4Interface}' && \\
MME_CONF[@SGW_IPV4_ADDRESS_FOR_S11_0@]='{spwgcS11_IPv4Interface}' && \\
MME_CONF[@PEER_MME_IPV4_ADDRESS_FOR_S10_0@]='0.0.0.0/24' && \\
MME_CONF[@PEER_MME_IPV4_ADDRESS_FOR_S10_1@]='0.0.0.0/24' && \\
MME_CONF[@TAC-LB_SGW_TEST_0@]={tac_sgw_test_hi} && \\
MME_CONF[@TAC-HB_SGW_TEST_0@]={tac_sgw_test_lo} && \\
MME_CONF[@MCC_SGW_0@]={networkMCC} && \\
MME_CONF[@MNC3_SGW_0@]={networkMNC:03d} && \\
MME_CONF[@TAC-LB_SGW_0@]={tac_sgw_0_hi} && \\
MME_CONF[@TAC-HB_SGW_0@]={tac_sgw_0_lo} && \\
MME_CONF[@MCC_MME_0@]={networkMCC} && \\
MME_CONF[@MNC3_MME_0@]={networkMNC:03d} && \\
MME_CONF[@TAC-LB_MME_0@]={tac_mme_0_hi} && \\
MME_CONF[@TAC-HB_MME_0@]={tac_mme_0_lo} && \\
MME_CONF[@MCC_MME_1@]={networkMCC} && \\
MME_CONF[@MNC3_MME_1@]={networkMNC:03d} && \\
MME_CONF[@TAC-LB_MME_1@]={tac_mme_1_hi} && \\
MME_CONF[@TAC-HB_MME_1@]={tac_mme_1_lo} && \\
for K in \\\"\${{!MME_CONF[@]}}\\\"; do sudo egrep -lRZ \\\"\$K\\\" \$PREFIX | xargs -0 -l sudo sed -i -e \\\"s|\$K|\${{MME_CONF[\$K]}}|g\\\" ; ret=\$?;[[ ret -ne 0 ]] && echo \\\"Tried to replace \$K with \${{MME_CONF[\$K]}}\\\" || true ; done && \\
sudo ./check_mme_s6a_certificate \$PREFIX/freeDiameter mme.{networkRealm} >logs/check_mme_s6a_certificate.log 2>&1 && \\
echo \\\"###### Done! ##########################################################\\\"""".format(
      gitRepository          = gitRepository,
      gitDirectory           = gitDirectory,
      gitCommit              = gitCommit,
      hssS6a_IPv4Address     = hssS6a_IPv4Address,
      mmeS1C_IPv4IfName      = mmeS1C_IPv4IfName,
      mmeS1C_IPv4Interface   = mmeS1C_IPv4Interface,
      mmeS11_IPv4IfName      = mmeS11_IPv4IfName,
      mmeS11_IPv4Interface   = mmeS11_IPv4Interface,
      spwgcS11_IPv4Interface = spwgcS11_IPv4Interface,
      networkRealm           = networkRealm,
      networkMCC             = networkMCC,
      networkMNC             = networkMNC,
      networkLTE_K           = networkLTE_K,
      networkOP_K            = networkOP_K,
      networkIMSIFirst       = networkIMSIFirst,
      networkMSISDNFirst     = networkMSISDNFirst,
      networkUsers           = networkUsers,

      tac_sgw_test_hi        = tac_sgw_test[0:2],
      tac_sgw_test_lo        = tac_sgw_test[2:4],
      tac_sgw_0_hi           = tac_sgw_0[0:2],
      tac_sgw_0_lo           = tac_sgw_0[2:4],
      tac_mme_0_hi           = tac_mme_0[0:2],
      tac_mme_0_lo           = tac_mme_0[2:4],
      tac_mme_1_hi           = tac_mme_1[0:2],
      tac_mme_1_lo           = tac_mme_1[2:4]
   )

   if execute(commands) == True:
      clear_flag('actions.configure-mme')


# ###### restart-mme function ###############################################
@when('actions.restart-mme')
@when('mmecharm.installed')
def restart_mme():
   err = ''
   try:
      # filename = action_get('filename')
      cmd = [ 'touch /tmp/restart-mme' ]
      result, err = charms.sshproxy._run(cmd)
   except:
      action_fail('command failed:' + err)
   else:
      action_set({'outout': result})

   clear_flag('actions.restart-mme')
