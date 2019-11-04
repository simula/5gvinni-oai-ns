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
      action_set({ 'outout': result})
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
@when_not('spgwucharm.installed')
def install_spgwucharm_proxy_charm():
   set_flag('spgwucharm.installed')
   status_set('active', 'Ready!')


# ###### configure-spgwu function ###########################################
@when('actions.configure-spgwu')
@when('spgwucharm.installed')
def configure_spgwu():

   # ====== Install SPGW-U ==================================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-u

   gitRepository            = 'https://github.com/OPENAIRINTERFACE/openair-cn-cups.git'
   gitDirectory             = 'openair-cn-cups'
   gitCommit                = 'develop'
   networkRealm             = 'simula.nornet'
   networkS1U_IPv4Interface = IPv4Interface('192.168.248.159/24')
   networkSGi_IPv4Interface = IPv4Interface('10.254.1.203/24')
   networkSGi_IPv4Gateway   = IPv4Address('10.254.1.1')
   networkSGi_IPv6Interface = IPv6Interface('3ffe::2/64')
   networkSGi_IPv6Gateway   = IPv6Address('3ffe::1')

   # Prepare network configurations:
   configurationSXab = configureInterface('ens4', IPv4Interface('0.0.0.0/0'))
   configurationS1U  = configureInterface('ens5', networkS1U_IPv4Interface, IPv4Address('0.0.0.0'))
   configurationSGI  = configureInterface('ens6', networkSGi_IPv4Interface, networkSGi_IPv4Gateway,
                                                  networkSGi_IPv6Interface, networkSGi_IPv6Gateway)

   commands = """\
echo "###### Preparing system ###############################################" && \\
echo -e "{configurationSXab}" | sudo tee /etc/network/interfaces.d/61-ens4 && sudo ifup ens4 || true && \\
echo -e "{configurationS1U}" | sudo tee /etc/network/interfaces.d/62-ens5 && sudo ifup ens5 || true && \\
echo -e "{configurationSGI}" | sudo tee /etc/network/interfaces.d/63-ens6 && sudo ifup ens6 || true && \\
echo "###### Preparing sources ##############################################" && \\
cd /home/nornetpp/src && \\
rm -rf {gitDirectory} && \\
git clone {gitRepository} {gitDirectory} && \\
cd {gitDirectory} && \\
git checkout {gitCommit} && \\
cd build/scripts && \\
echo "###### Building SPGW-U ################################################" && \\
./build_spgwu -I -f && \
./build_spgwu -c -V -b Debug -j
""".format(
      gitRepository     = gitRepository,
      gitDirectory      = gitDirectory,
      gitCommit         = gitCommit,
      networkRealm      = networkRealm,
      configurationSXab = configurationSXab,
      configurationS1U  = configurationS1U,
      configurationSGI  = configurationSGI
   )

   if execute(commands) == True:
      clear_flag('actions.configure-spgwu')


# ###### restart-spgwu function #############################################
@when('actions.restart-spgwu')
@when('spgwucharm.installed')
def restart_spgwu():
   commands = 'touch /tmp/restart-spgwu'
   if execute(commands) == True:
      clear_flag('actions.restart-spgwu')
