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

import base64
import ipaddress
import logging
import logging.config
import os
import subprocess
import sys
import traceback


# ###########################################################################
# #### VDUHelper class                                                   ####
# ###########################################################################

class VDUHelper:
   # ###### Constructor #####################################################
   def __init__(self, testMode = False):
      # ====== Initialise object ============================================
      self.testMode   = testMode
      self.blockStack = []
      self.lastError  = None

      if self.testMode == False:
         import charmhelpers.core.hookenv
         self.hookenv_module = charmhelpers.core.hookenv
         import charms.sshproxy
         self.sshproxy_module = charms.sshproxy

      # ====== Initialise logger ============================================
      self.logger = logging.getLogger(__name__)
      if self.testMode == False:
         self.logger.error('Starting')
      else:
         self.logger.error('Starting in Test Mode!')


   # ###### Begin block #####################################################
   def setStatus(self, message, isError = False):
      # print('Status: ' + message)
      if isError:
         self.logger.error(message)
      else:
         self.logger.debug(message)
      if self.testMode == False:
         self.hookenv_module.status_set('active', message)


   # ###### Begin block #####################################################
   def beginBlock(self, label):
      self.blockStack.append(label)
      self.lastError = None

      message = label + ' ...'
      self.setStatus(message)
      return message


   # ###### End block #######################################################
   def endBlock(self, success = True):
      assert len(self.blockStack) > 0
      label = self.blockStack.pop()

      if success == True:
         message = label + ' completed!'
         self.setStatus(message)
      else:
         message = label + ' FAILED!'
         self.setStatus(message, True)
         if self.lastError == None:
            self.lastError = message
         else:
            return message + ' <= ' + self.lastError

      return message


   # ###### End block as part of exception handling #########################
   def endBlockInException(self):
      exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
      exceptionTraceback = traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback)
      self.logger.error('Ending block with exception: ' + str(''.join(map(str, exceptionTraceback))))
      return self.endBlock(False)


   # ###### Touch file ######################################################
   def touchFile(self, fileName):
      self.beginBlock('Touch ' + fileName)

      try:
         commands = """touch {}""".format(fileName)
         self.runInShell(commands)
      except:
         self.endBlock(False)
         raise

      self.endBlock()


   # ###### Execute command #################################################
   def execute(self, commands):
      if self.testMode == False:
         print('Shell: ' + commands)
         self.logger.debug('Shell: ' + commands)
         self.sshproxy_module._run(commands)

      else:
         sys.stdout.write('# ---------------------------------------------------------------------------\n')
         sys.stdout.write('time bash -c "' + commands + '"\n')

         # commands = 'echo "' + commands + '"'
         # subprocess.check_call(commands, shell=True)


   # ###### Run shell commands and handle exceptions ########################
   def runInShell(self, commands, raiseExceptionOnError = True):
      try:
         self.execute(commands)
      except:
         message = 'Command execution failed: ' + commands
         self.logger.error(message)
         if raiseExceptionOnError:
            raise
         return False
      else:
         return True


   # ###### Encode string to base64 ##########################################
   def makeBase64(self, string):
      # NOTE: Handling multiple levels of string encapsulation with Python, bash,
      # etc. is just a total mess! Therefore, using a straightforward approach here:
      # Create the command string as is, apply base64 encoding, and decode it at the
      # VDU's shell by using "base64 -d".

      if string != None:
         return base64.b64encode(string.encode('utf-8')).decode('ascii')
      return None


   # ######  Get /etc/network/interfaces setup for interface #################
   def makeInterfaceConfiguration(self,
                                  interfaceName,
                                  ipv4Interface = ipaddress.IPv4Interface('0.0.0.0/0'),
                                  ipv4Gateway   = None,
                                  ipv6Interface = None,
                                  ipv6Gateway   = None,
                                  metric        = 1,
                                  pdnInterface  = None,
                                  createDummy   = False):

      # ====== Create header ================================================
      interfaceConfiguration = \
         'network:\n' + \
         '  version: 2\n' + \
         '  renderer: networkd\n'
      if createDummy == False:
        interfaceConfiguration = interfaceConfiguration + \
           '  ethernets:\n' + \
           '    ' + interfaceName + ':\n'
      else:
        interfaceConfiguration = interfaceConfiguration + \
           '  bridges:\n' + \
           '    ' + interfaceName + ':\n' + \
           '      interfaces: [ ]\n'


      # ====== Addressing ===================================================
      networks = []
      if ipv4Interface == ipaddress.IPv4Interface('0.0.0.0/0'):
         interfaceConfiguration = interfaceConfiguration + '      dhcp4: true\n'
      else:
         interfaceConfiguration = interfaceConfiguration + '      dhcp4: false\n'

      if ((ipv6Interface == None) and (ipv6Interface == ipaddress.IPv6Interface('::/0'))):
         interfaceConfiguration = interfaceConfiguration + '      dhcp6: true\n'
      else:
         interfaceConfiguration = interfaceConfiguration + '      dhcp6: false\n'
         interfaceConfiguration = interfaceConfiguration + '      accept-ra: no\n'

      if ( (ipv4Interface != ipaddress.IPv4Interface('0.0.0.0/0')) or
           ((ipv6Interface == None) and (ipv6Interface == ipaddress.IPv6Interface('::/0'))) ):

         interfaceConfiguration = interfaceConfiguration + '      addresses:\n'

         if ipv4Interface != ipaddress.IPv4Interface('0.0.0.0/0'):
            interfaceConfiguration = interfaceConfiguration + '        - ' + \
               str(ipv4Interface.ip) + '/' + \
               str(ipv4Interface.network.prefixlen) + \
               '\n'
            networks.append(ipv4Interface.network)

         if ((ipv6Interface == None) and (ipv6Interface == ipaddress.IPv6Interface('::/0'))):
            interfaceConfiguration = interfaceConfiguration + '        - ' + \
               str(ipv6Interface.ip) + '/' + \
               str(ipv6Interface.network.prefixlen) + \
               '\n'
            networks.append(ipv6Interface,network)

      # ====== Routing ======================================================
      postUpRules, preDownRules = None, None
      if ( ((ipv4Gateway != None) and (ipv4Gateway != ipaddress.IPv4Address('0.0.0.0'))) or
           ((ipv6Gateway != None) and (ipv6Gateway != ipaddress.IPv6Address('::'))) ):

         interfaceConfiguration = interfaceConfiguration + '      routes:\n'

         gateways = []
         if ((ipv4Gateway != None) and (ipv4Gateway != ipaddress.IPv4Address('0.0.0.0'))):
            interfaceConfiguration = interfaceConfiguration + \
                '       - to: 0.0.0.0/0\n' + \
                '         via: ' + str(ipv4Gateway) + '\n' + \
                '         metric: ' + str(metric) + '\n'
            gateways.append(ipv4Gateway)

         if ((ipv6Gateway != None) and (ipv6Gateway != ipaddress.IPv6Address('::'))):
            interfaceConfiguration = interfaceConfiguration + \
                '       - to: ::/0\n' + \
                '         via: ' + str(ipv6Gateway) + '\n' + \
                '         metric: ' + str(metric) + '\n'
            gateways.append(ipv6Gateway)

         if ((pdnInterface != None) and (len(networks) > 0) and (len(gateways) > 0)):
            postUpRules, preDownRules = self.makeRoutingRules(pdnInterface, interfaceName, networks, gateways)

      print(interfaceConfiguration)

      return [ self.makeBase64(interfaceConfiguration),
               self.makeBase64(postUpRules),
               self.makeBase64(preDownRules) ]


   # ###### Get IP routing rules for PDN interface ##########################
   def makeRoutingRules(self, pdnInterface, interfaceName, networks, gateways):
      # ------ Create post-up rules -----------------------------------------
      postUp = \
         '#!/bin/sh\n' + \
         'if [ "$IFACE" = "' + interfaceName + '" ] ; then\n'
      for network in networks:
         postUp = postUp + \
            '   /bin/ip rule add from ' + str(network) + ' lookup 1000 pref 100\n'
      postUp = postUp + \
         '   /bin/ip rule add iif ' + pdnInterface + ' lookup 1000 pref 100\n'
      for network in networks:
         postUp = postUp + \
            '   /bin/ip route add ' + str(network) + ' scope link dev ' + interfaceName + ' table 1000\n'
      for gateway in gateways:
         postUp = postUp + \
         '   /bin/ip route add default via ' + str(gateway) + ' dev ' + interfaceName + ' table 1000\n'
      postUp = postUp + \
         'fi\n'

      # ------ Create pre-down rules ----------------------------------------
      preDown = \
         '#\\x21/bin/sh\n' + \
         'if [ "$IFACE" = "' + interfaceName + '" ] ; then\n'
      for gateway in gateways:
         preDown = preDown + \
         '   /bin/ip route del default via ' + str(gateway) + ' dev ' + interfaceName + ' table 1000\n'
      for network in networks:
         preDown = preDown + \
            '   /bin/ip route del ' + str(network) + ' scope link dev ' + interfaceName + ' table 1000\n'
      preDown = preDown + \
         '   /bin/ip rule del iif ' + pdnInterface + ' lookup 1000 pref 100\n'
      for network in networks:
         preDown = preDown + \
            '   /bin/ip rule del from ' + str(network) + ' lookup 1000 pref 100\n'
      preDown = preDown + \
         'fi\n'

      return postUp, preDown


   # ###### Configuration and activate network interface ####################
   def configureInterface(self, interfaceName, interfaceConfiguration, priority = 60):
      self.beginBlock('Configuring and activating ' + interfaceName)

      try:
         commands = ''
         if interfaceConfiguration[1] != None:
            commands = commands + """\
echo \\\"{postUpRules}\\\" | base64 -d | sudo tee /etc/networkd-dispatcher/routable.d/{priority}-{interfaceName} && sudo chmod +x /etc/networkd-dispatcher/routable.d/{priority}-{interfaceName} ; """ .format(
               interfaceName = interfaceName,
               postUpRules   = interfaceConfiguration[1],
               priority      = priority
            )

         if interfaceConfiguration[2] != None:
            commands = commands + """\
echo \\\"{preDownRules}\\\" | base64 -d | sudo tee /etc/networkd-dispatcher/off.d/{priority}-{interfaceName} && sudo chmod +x /etc/networkd-dispatcher/off.d/{priority}-{interfaceName} ; """ .format(
               interfaceName = interfaceName,
               preDownRules  = interfaceConfiguration[2],
               priority      = priority
            )

         commands = commands + """\
echo \\\"{interfaceConfiguration}\\\" | base64 -d | sudo tee /etc/netplan/{interfaceName}.yaml && sudo netplan apply || true""".format(
            interfaceName          = interfaceName,
            interfaceConfiguration = interfaceConfiguration[0],
            priority               = priority
         )
         self.runInShell(commands)
      except:
         self.endBlock(False)
         raise

      self.endBlock()


   # ###### Test networking #################################################
   def testNetworking(self, destination = ipaddress.IPv4Address('8.8.8.8'), timeout = 60, interval = 0.333):
      self.beginBlock('Testing networking')

      try:
         commands = """ping -W{timeout}  -i{interval} -c3 {destination}""".format(
            destination = str(destination),
            timeout     = timeout,
            interval    = interval
         )
         self.runInShell(commands)
      except:
         self.endBlock(False)
         raise

      self.endBlock()


   # ###### Wait for all package updates to complete ########################
   def waitForPackageUpdatesToComplete(self):
      self.beginBlock('Waiting for package management to complete all running tasks ...')

      # Based on https://gist.github.com/tedivm/e11ebfdc25dc1d7935a3d5640a1f1c90
      commands = """\
while sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1 ; do sleep 1 ; done ; \\
while sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 ; do sleep 1 ; done ; \\
if [ -f /var/log/unattended-upgrades/unattended-upgrades.log ]; then \\
   while sudo fuser /var/log/unattended-upgrades/unattended-upgrades.log >/dev/null 2>&1 ; do sleep 1 ; done ; \\
fi"""
      try:
         self.runInShell(commands)
      except:
         self.endBlock(False)
         raise

      self.endBlock()


   # ###### Test networking #################################################
   def aptInstallPackages(self, packages, update = True):
      if len(packages) > 0:
         if update == True:
            commands = 'sudo apt update && \\\n'
         else:
            commands = ''
         commands = commands + 'DEBIAN_FRONTEND=noninteractive sudo apt install -y -o Dpkg::Options::=--force-confold -o Dpkg::Options::=--force-confdef --no-install-recommends '
         for package in packages:
            commands = commands + package
         self.runInShell(commands)


   # ###### Install SysStat #################################################
   def installSysStat(self):
      self.beginBlock('Setting up sysstat service')
      commands = """\
DEBIAN_FRONTEND=noninteractive sudo apt install -y -o Dpkg::Options::=--force-confold -o Dpkg::Options::=--force-confdef --no-install-recommends sysstat && \\
sudo sed -e \\\"s/^ENABLED=.*$/ENABLED=\\\\\\"true\\\\\\"/g\\\" -i /etc/default/sysstat && \\
sudo sed -e \\\"s/^SADC_OPTIONS=.*$/SADC_OPTIONS=\\\\\\"-S ALL\\\\\\"/g\\\" -i /etc/sysstat/sysstat && \\
sudo service sysstat restart"""
      self.runInShell(commands)
      self.endBlock()


   # ###### Fetch Git repository ############################################
   def fetchGitRepository(self, gitDirectory, gitRepository, gitCommit):
      self.beginBlock('Fetching Git repository ' + gitDirectory)

      try:
         commands = """\
cd /home/nornetpp/src && \\
if [ ! -d \\\"{gitDirectory}\\\" ] ; then git clone --quiet {gitRepository} {gitDirectory} && cd {gitDirectory} ; else cd {gitDirectory} && git pull ; fi && \\
git checkout {gitCommit}""".format(
            gitRepository    = gitRepository,
            gitDirectory     = gitDirectory,
            gitCommit        = gitCommit
         )
         self.runInShell(commands)
      except:
         self.endBlock(False)
         raise

      self.endBlock()


   # ###### Clean up ########################################################
   def cleanUp(self):
      self.beginBlock('Cleaning up')
      commands = """\
sudo updatedb"""
      self.runInShell(commands)
      self.endBlock()
