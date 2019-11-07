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
import sys
import traceback
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
@when_not('epccharm.installed')
def install_epccharm_proxy_charm():
   set_flag('epccharm.installed')
   status_set('active', 'Ready!')


# ###### configure-epc function #############################################
@when('actions.configure-epc')
@when('epccharm.installed')
def configure_epc():
   err = ''
   try:
      # filename = action_get('filename')
      cmd = [ 'touch /tmp/configure-epc' ]
      result, err = charms.sshproxy._run(cmd)
   except:
      action_fail('command failed:' + err)
   else:
      action_set({'outout': result})

   clear_flag('actions.configure-epc')


# ###### restart-epc function ###############################################
@when('actions.restart-epc')
@when('epccharm.installed')
def restart_epc():
   err = ''
   try:
      # filename = action_get('filename')
      cmd = [ 'touch /tmp/restart-epc' ]
      result, err = charms.sshproxy._run(cmd)
   except:
      action_fail('command failed:' + err)
   else:
      action_set({'outout': result})

   clear_flag('actions.restart-epc')
