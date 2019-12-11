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
import subprocess
import sys
import traceback
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface


# ###########################################################################
# #### Helper functions                                                  ####
# ###########################################################################

# ###### Execute command ####################################################
def execute(commands):
   return charms.sshproxy._run(commands)


# ###### Run shell commands, handle exceptions, and upage status flags ######
def runShellCommands(commands, comment, actionFlagToClear, successFlagToSet = None):
   status_set('active', comment + ' ...')
   try:
       stdout, stderr = execute(commands)
   except subprocess.CalledProcessError as e:
       exc_type, exc_value, exc_traceback = sys.exc_info()
       err = traceback.format_exception(exc_type, exc_value, exc_traceback)
       message = 'Command execution failed: ' + str(err) + '\nOutput: ' + e.output.decode('utf-8')
       action_fail(message.encode('utf-8'))
       status_set('active', comment + ' COMMANDS FAILED!')
   except:
       exc_type, exc_value, exc_traceback = sys.exc_info()
       err = traceback.format_exception(exc_type, exc_value, exc_traceback)
       action_fail('Command execution failed: ' + str(err))
       status_set('active', comment + ' FAILED!')
   else:
      if successFlagToSet != None:
         set_flag(successFlagToSet)
      # action_set( { 'output': stdout.encode('utf-8') } )
      status_set('active', comment + ' COMPLETED')
   finally:
      clear_flag(actionFlagToClear)


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
@when_not('spgwucharm.installed')
def install_spgwucharm_proxy_charm():
   set_flag('spgwucharm.installed')
   status_set('active', 'install_spgwucharm_proxy_charm: SSH proxy charm is READY')


# ###### prepare-spgwu-build function #######################################
@when('actions.prepare-spgwu-build')
@when('spgwucharm.installed')
@when_not('spgwucharm.prepared-spgwu-build')
def prepare_spgwu_build():

   # ====== Install SPGW-U ==================================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-u

   gitRepository          = action_get('spgwu-git-repository')
   gitCommit              = action_get('spgwu-git-commit')
   gitDirectory           = 'openair-cn-cups'

   spgwuS1U_IPv4Interface = IPv4Interface(action_get('spgwu-S1U-ipv4-interface'))
   spgwuS1U_IPv4Gateway   = IPv4Address(action_get('spgwu-S1U-ipv4-gateway'))

   spgwuSGi_IPv4Interface = IPv4Interface(action_get('spgwu-SGi-ipv4-interface'))
   spgwuSGi_IPv4Gateway   = IPv4Address(action_get('spgwu-SGi-ipv4-gateway'))
   spgwuSGi_IPv6Interface = IPv6Interface(action_get('spgwu-SGi-ipv6-interface'))
   spgwuSGi_IPv6Gateway   = IPv6Address(action_get('spgwu-SGi-ipv6-gateway'))

   # Prepare network configurations:
   spgwuSXab_IfName       = 'ens4'
   spgwuS1U_IfName        = 'ens5'
   spgwuSGi_IfName        = 'ens6'

   configurationSXab = configureInterface(spgwuSXab_IfName, IPv4Interface('0.0.0.0/0'))
   configurationS1U  = configureInterface(spgwuS1U_IfName, spgwuS1U_IPv4Interface, spgwuS1U_IPv4Gateway)
   configurationSGi  = configureInterface(spgwuSGi_IfName, spgwuSGi_IPv4Interface, spgwuSGi_IPv4Gateway,
                                                           spgwuSGi_IPv6Interface, spgwuSGi_IPv6Gateway)

   # NOTE:
   # Double escaping is required for \ and " in "command" string!
   # 1. Python
   # 2. bash -c "<command>"
   # That is: $ => \$ ; \ => \\ ; " => \\\"

   commands = """\
echo \\\"###### Preparing system ###############################################\\\" && \\
echo -e \\\"{configurationSXab}\\\" | sudo tee /etc/network/interfaces.d/61-{spgwuSXab_IfName} && sudo ifup {spgwuSXab_IfName} || true && \\
echo -e \\\"{configurationS1U}\\\" | sudo tee /etc/network/interfaces.d/62-{spgwuS1U_IfName} && sudo ifup {spgwuS1U_IfName} || true && \\
echo -e \\\"{configurationSGi}\\\" | sudo tee /etc/network/interfaces.d/63-{spgwuSGi_IfName} && sudo ifup {spgwuSGi_IfName} || true && \\
echo \\\"###### Preparing sources ##############################################\\\" && \\
cd /home/nornetpp/src && \\
if [ ! -d \\\"{gitDirectory}\\\" ] ; then git clone --quiet {gitRepository} {gitDirectory} && cd {gitDirectory} ; else cd {gitDirectory} && git pull ; fi && \\
git checkout {gitCommit} && \\
cd build/scripts && \\
echo \\\"###### Done! ##########################################################\\\"""".format(
      gitRepository     = gitRepository,
      gitDirectory      = gitDirectory,
      gitCommit         = gitCommit,
      spgwuSXab_IfName  = spgwuSXab_IfName,
      spgwuS1U_IfName   = spgwuS1U_IfName,
      spgwuSGi_IfName   = spgwuSGi_IfName,
      configurationSXab = configurationSXab,
      configurationS1U  = configurationS1U,
      configurationSGi  = configurationSGi
   )

   runShellCommands(commands, 'prepare_spgwu_build: preparing SPGW-U build',
                    'actions.prepare-spgwu-build', 'spgwucharm.prepared-spgwu-build')


# ###### configure-spgwu function ###########################################
@when('actions.configure-spgwu')
@when('spgwucharm.prepared-spgwu-build')
def configure_spgwu():

   # ====== Install SPGW-U ==================================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-u

   gitDirectory     = 'openair-cn-cups'

   # Prepare network configurations:
   spgwuSXab_IfName = 'ens4'
   spgwuS1U_IfName  = 'ens5'
   spgwuSGi_IfName  = 'ens6'

   # NOTE:
   # Double escaping is required for \ and " in "command" string!
   # 1. Python
   # 2. bash -c "<command>"
   # That is: $ => \$ ; \ => \\ ; " => \\\"

   commands = """\
echo \\\"###### Building SPGW-U ################################################\\\" && \\
export MAKEFLAGS=\\\"-j`nproc`\\\" && \\
cd /home/nornetpp/src && \\
cd {gitDirectory} && \\
cd build/scripts && \\
mkdir -p logs && \\
echo \\\"====== Building dependencies ... ======\\\" && \\
./build_spgwu -I -f >logs/build_spgwu-1.log 2>&1 && \\
echo \\\"====== Building service ... ======\\\" && \\
./build_spgwu -c -V -b Debug -j >logs/build_spgwu-2.log 2>&1 && \\
INSTANCE=1 && \\
PREFIX='/usr/local/etc/oai' && \\
sudo mkdir -m 0777 -p \$PREFIX && \\
sudo cp ../../etc/spgw_u.conf  \$PREFIX && \\
declare -A SPGWU_CONF && \\
SPGWU_CONF[@INSTANCE@]=\$INSTANCE && \\
SPGWU_CONF[@PREFIX@]=\$PREFIX && \\
SPGWU_CONF[@PID_DIRECTORY@]='/var/run' && \\
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_S1U_S12_S4_UP@]='{spgwuS1U_IfName}' && \\
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_SX@]='{spgwuSXab_IfName}' && \\
SPGWU_CONF[@SGW_INTERFACE_NAME_FOR_SGI@]='{spgwuSGi_IfName}' && \\
for K in \\\"\${{!SPGWU_CONF[@]}}\\\"; do sudo egrep -lRZ \\\"\$K\\\" \$PREFIX | xargs -0 -l sudo sed -i -e \\\"s|\$K|\${{SPGWU_CONF[\$K]}}|g\\\" ; ret=\$?;[[ ret -ne 0 ]] && echo \\\"Tried to replace \$K with \${{SPGWU_CONF[\$K]}}\\\" || true ; done && \\
echo \\\"###### Done! ##########################################################\\\"""".format(
      gitDirectory     = gitDirectory,
      spgwuSXab_IfName = spgwuSXab_IfName,
      spgwuS1U_IfName  = spgwuS1U_IfName,
      spgwuSGi_IfName  = spgwuSGi_IfName
   )

   runShellCommands(commands, 'configure_spgwu: configuring SPGW-U',
                    'actions.configure-spgwu', 'spgwucharm.configured-spgwu')


# ###### restart-spgwu function #############################################
@when('actions.restart-spgwu')
@when('spgwucharm.installed')
def restart_spgwu():
   commands = 'touch /tmp/restart-spgwu'
   if execute(commands) == True:
      clear_flag('actions.restart-spgwu')
