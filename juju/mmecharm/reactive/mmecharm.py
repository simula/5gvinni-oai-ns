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
      action_set({ 'outout': 'DONE!'})
      return True


# ######  Get /etc/network/interfaces setup for interface ###################
def configureInterface(name,
                       ipv4Interface = IPv4Interface('0.0.0.0/0'), ipv4Gateway = None,
                       ipv6Interface = None,                       ipv6Gateway = None,
                       metric = 1):
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


# ###### configure-mme function #############################################
@when('actions.configure-mme')
@when('mmecharm.installed')
def configure_mme():

   # ====== Install MME =====================================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn/wiki/OpenAirSoftwareSupport#install-mme

   gitRepository            = 'https://github.com/OPENAIRINTERFACE/openair-cn.git'
   gitDirectory             = 'openair-cn'
   gitCommit                = 'develop'
   cassandraServerIP        = '172.16.6.129'
   networkRealm             = 'simula.nornet'
   networkLTE_K             = '449c4b91aeacd0ace182cf3a5a72bfa1'
   networkOP_K              = '1006020f0a478bf6b699f15c062e42b3'
   networkIMSIFirst         = '242881234500000'
   networkMSISDNFirst       = '24288880000000'
   networkUsers             = 1024
   networkS1C_IPv4Interface = IPv4Interface('192.168.247.102/24')
   networkS1C_IPv4Gateway   = IPv4Address('0.0.0.0')
   networkS1C_IPv6Interface = None
   networkS1C_IPv6Gateway   = None

   # Prepare network configurations:
   configurationS6a = configureInterface('ens4', IPv4Interface('0.0.0.0/0'))
   configurationS11 = configureInterface('ens5', IPv4Interface('0.0.0.0/0'))
   configurationS1C = configureInterface('ens6', networkS1C_IPv4Interface, networkS1C_IPv4Gateway)

   commands = """\
echo "###### Preparing system ###############################################" && \\
echo -e "{configurationS6a}" | sudo tee /etc/network/interfaces.d/61-ens4 && sudo ifup ens4 || true && \\
echo -e "{configurationS11}" | sudo tee /etc/network/interfaces.d/62-ens5 && sudo ifup ens5 || true && \\
echo -e "{configurationS1C}" | sudo tee /etc/network/interfaces.d/63-ens6 && sudo ifup ens6 || true && \\
echo "###### Preparing sources ##############################################" && \\
cd /home/nornetpp/src && \\
rm -rf {gitDirectory} && \\
git clone {gitRepository} {gitDirectory} && \\
cd {gitDirectory} && \\
git checkout {gitCommit} && \\
cd scripts && \\
mkdir logs && \\
echo "###### Building MME ####################################################" && \\
./build_mme --check-installed-software --force && \\
./build_mme --clean
""".format(
      gitRepository      = gitRepository,
      gitDirectory       = gitDirectory,
      gitCommit          = gitCommit,
      cassandraServerIP  = cassandraServerIP,
      networkRealm       = networkRealm,
      networkLTE_K       = networkLTE_K,
      networkOP_K        = networkOP_K,
      networkIMSIFirst   = networkIMSIFirst,
      networkMSISDNFirst = networkMSISDNFirst,
      networkUsers       = networkUsers,
      configurationS6a   = configurationS6a,
      configurationS11   = configurationS11,
      configurationS1C   = configurationS1C
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
