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
@when_not('spgwccharm.installed')
def install_spgwccharm_proxy_charm():
   set_flag('spgwccharm.installed')
   status_set('active', 'install_spgwccharm_proxy_charm: SSH proxy charm is READY')


# ###### prepare-spgwc-build function #######################################
@when('actions.prepare-spgwc-build')
@when('spgwccharm.installed')
@when_not('spgwccharm.prepared-spgwc-build')
def prepare_spgwc_build():

   # ====== Install SPGW-C ==================================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-c

   gitRepository     = action_get('spgwc-git-repository')
   gitCommit         = action_get('spgwc-git-commit')
   gitDirectory      = 'openair-cn-cups'

   # Prepare network configurations:
   spgwcS11_IfName   = 'ens5'
   spgwcSXab_IfName  = 'ens4'
   configurationS11  = configureInterface(spgwcS11_IfName,  IPv4Interface('0.0.0.0/0'))
   configurationSXab = configureInterface(spgwcSXab_IfName, IPv4Interface('0.0.0.0/0'))

   # S5S8 dummy interfaces:
   spgwcS5S8_SGW_IfName  = 'dummy0:s5c'
   configurationS5S8_SGW = configureInterface(spgwcS5S8_SGW_IfName, IPv4Interface('172.58.58.102/24'))
   spgwcS5S8_PGW_IfName  = 'dummy0:p5c'
   configurationS5S8_PGW = configureInterface(spgwcS5S8_PGW_IfName, IPv4Interface('172.58.58.101/24'))

   # NOTE:
   # Double escaping is required for \ and " in "command" string!
   # 1. Python
   # 2. bash -c "<command>"
   # That is: $ => \$ ; \ => \\ ; " => \\\"

   commands = """\
echo \\\"###### Preparing system ###############################################\\\" && \\
echo -e \\\"{configurationS11}\\\" | sudo tee /etc/network/interfaces.d/61-{spgwcS11_IfName} && sudo ifup {spgwcS11_IfName} || true && \\
echo -e \\\"{configurationSXab}\\\" | sudo tee /etc/network/interfaces.d/62-{spgwcSXab_IfName} && sudo ifup {spgwcSXab_IfName} || true && \\
sudo ip link add dummy0 type dummy || true && \\
echo -e \\\"{configurationS5S8_SGW}\\\" | sudo tee /etc/network/interfaces.d/63-{spgwcS5S8_SGW_IfName} && sudo ifup {spgwcS5S8_SGW_IfName} || true && \\
echo -e \\\"{configurationS5S8_PGW}\\\" | sudo tee /etc/network/interfaces.d/64-{spgwcS5S8_PGW_IfName} && sudo ifup {spgwcS5S8_PGW_IfName} || true && \\
echo \\\"###### Preparing sources ##############################################\\\" && \\
cd /home/nornetpp/src && \\
if [ ! -d \\\"{gitDirectory}\\\" ] ; then git clone --quiet {gitRepository} {gitDirectory} && cd {gitDirectory} ; else cd {gitDirectory} && git pull ; fi && \\
git checkout {gitCommit} && \\
cd build/scripts && \\
echo \\\"###### Done! ##########################################################\\\"""".format(
      gitRepository          = gitRepository,
      gitDirectory           = gitDirectory,
      gitCommit              = gitCommit,
      spgwcS11_IfName        = spgwcS11_IfName,
      spgwcSXab_IfName       = spgwcSXab_IfName,
      spgwcS5S8_SGW_IfName   = spgwcS5S8_SGW_IfName,
      spgwcS5S8_PGW_IfName   = spgwcS5S8_PGW_IfName,
      configurationS11       = configurationS11,
      configurationSXab      = configurationSXab,
      configurationS5S8_SGW  = configurationS5S8_SGW,
      configurationS5S8_PGW  = configurationS5S8_PGW
   )

   runShellCommands(commands, 'prepare_spgwc_build: preparing SPGW-C build',
                    'actions.prepare-spgwc-build', 'spgwccharm.prepared-spgwc-build')


# ###### configure-spgwc function ###########################################
@when('actions.configure-spgwc')
@when('spgwccharm.prepared-spgwc-build')
def configure_spgwc():

   # ====== Install SPGW-C ==================================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn-cups/wiki/OpenAirSoftwareSupport#install-spgw-c

   gitDirectory         = 'openair-cn-cups'

   networkRealm         = action_get('network-realm')
   networkDNS1_IPv4     = IPv4Address(action_get('network-ipv4-dns1'))
   networkDNS2_IPv4     = IPv4Address(action_get('network-ipv4-dns2'))

   # Prepare network configurations:
   spgwcSXab_IfName     = 'ens4'
   spgwcS11_IfName      = 'ens5'
   spgwcS5S8_SGW_IfName = 'dummy0:s5c'
   spgwcS5S8_PGW_IfName = 'dummy0:p5c'

   # NOTE:
   # Double escaping is required for \ and " in "command" string!
   # 1. Python
   # 2. bash -c "<command>"
   # That is: $ => \$ ; \ => \\ ; " => \\\"

   commands = """\
echo \\\"###### Building SPGW-C ################################################\\\" && \\
export MAKEFLAGS=\\\"-j`nproc`\\\" && \\
cd /home/nornetpp/src && \\
cd {gitDirectory} && \\
cd build/scripts && \\
mkdir -p logs && \\
echo \\\"====== Building dependencies ... ======\\\" && \\
./build_spgwc -I -f >logs/build_spgwc-1.log 2>&1 && \\
echo \\\"====== Building service ... ======\\\" && \\
./build_spgwc -c -V -b Debug -j >logs/build_spgwc-2.log 2>&1 && \\
echo \\\"###### Creating SPGW-C configuration files ############################\\\" && \\
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
sudo sed -e \\\"s/APN_NI = \\\\\\"apn1\\\\\\"/APN_NI = \\\\\\"internet.{networkRealm}\\\\\\"/g\\\" -i /usr/local/etc/oai/spgw_c.conf && \\
echo \\\"====== Preparing SystemD Unit ... ======\\\" && \\
( echo \\\"[Unit]\\\" && \\
echo \\\"Description=Serving and Packet Data Network Gateway -- Control Plane (SPGW-C)\\\" && \\
echo \\\"After=ssh.target\\\" && \\
echo \\\"\\\" && \\
echo \\\"[Service]\\\" && \\
echo \\\"ExecStart=/usr/local/bin/spgwc -c /usr/local/etc/oai/spgw_c.conf -o\\\" && \\
echo \\\"KillMode=process\\\" && \\
echo \\\"Restart=on-failure\\\" && \\
echo \\\"RestartPreventExitStatus=255\\\" && \\
echo \\\"WorkingDirectory=/home/nornetpp/src/openair-cn-cups/build/scripts\\\" && \\
echo \\\"StandardOutput=file:/var/log/spgwc.log\\\" && \\
echo \\\"StandardError=inherit\\\" && \\
echo \\\"\\\" && \\
echo \\\"[Install]\\\" && \\
echo \\\"WantedBy=multi-user.target\\\" ) | sudo tee /lib/systemd/system/spgwc.service && \\
sudo systemctl daemon-reload && \\
echo \\\"###### Done! ##########################################################\\\"""".format(
      gitDirectory         = gitDirectory,
      networkRealm         = networkRealm,
      networkDNS1_IPv4     = networkDNS1_IPv4,
      networkDNS2_IPv4     = networkDNS2_IPv4,
      spgwcSXab_IfName     = spgwcSXab_IfName,
      spgwcS11_IfName      = spgwcS11_IfName,
      spgwcS5S8_SGW_IfName = spgwcS5S8_SGW_IfName,
      spgwcS5S8_PGW_IfName = spgwcS5S8_PGW_IfName
   )

   runShellCommands(commands, 'configure_spgwc: configuring SPGW-C',
                    'actions.configure-spgwc', 'spgwccharm.configured-spgwc')


# ###### restart-spgwc function #############################################
@when('actions.restart-spgwc')
@when('spgwccharm.installed')
def restart_spgwc():
   commands = 'sudo service spgwc restart'
   runShellCommands(commands, 'restart_spgwc: restarting SPGW-C', 'actions.restart-spgwc')
