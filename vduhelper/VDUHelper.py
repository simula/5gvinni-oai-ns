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
      self.endBlock(False)
      self.logger.error(str(''.join(map(str, exceptionTraceback))))


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
         sys.stdout.write('-----------------------------------------------------------------------------\n')
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


   # ######  Get /etc/network/interfaces setup for interface ###################
   def makeInterfaceConfiguration(self,
                                  interfaceName,
                                  ipv4Interface = ipaddress.IPv4Interface('0.0.0.0/0'),
                                  ipv4Gateway   = None,
                                  ipv6Interface = None,
                                  ipv6Gateway   = None,
                                  metric        = 1,
                                  pdnInterface  = None,
                                  createDummy   = False):

      # NOTE:
      # Double escaping is required for \ and " in "interfaceConfiguration" string!
      # 1. Python
      # 2. bash -c "<command>"
      # That is: $ => \$ ; \ => \\ ; " => \\\"


      # ====== Dummy interface configuration ================================
      dummyInterfaceConfiguration = ''
      if createDummy == True:
         dummyInterfaceName = interfaceName.split(':')
         if len(dummyInterfaceName) > 0:
            dummyInterfaceName = dummyInterfaceName[0]
            dummyInterfaceConfiguration = \
               '\\\\tpre-up ip link add ' + dummyInterfaceName + ' type dummy || true\\\\n'


      interfaceConfiguration = 'auto ' + interfaceName + '\\\\n'

      # ====== Helper function =================================================
      def makePDNRules(pdnInterface, interface, gateway):
         rules = \
            '\\\\tpost-up /bin/ip rule add from ' + str(interface.network) + ' lookup 1000 pref 100\\\\n' + \
            '\\\\tpost-up /bin/ip rule add iif pdn lookup 1000 pref 100\\\\n' + \
            '\\\\tpost-up /bin/ip route add ' + str(interface.network) + ' scope link dev ' + interfaceName + ' table 1000\\\\n' + \
            '\\\\tpost-up /bin/ip route add default via ' + str(gateway) + ' dev ' + interfaceName + ' table 1000\\\\n' + \
            '\\\\tpre-down /bin/ip route del default via ' + str(gateway) + ' dev ' + interfaceName + ' table 1000 || true\\\\n' + \
            '\\\\tpre-down /bin/ip route del ' + str(interface.network) + ' scope link dev ' + interfaceName + ' table 1000 || true\\\\n' + \
            '\\\\tpre-down /bin/ip rule del iif pdn lookup 1000 pref 100 || true\\\\n' + \
            '\\\\tpre-down /bin/ip rule del from ' + str(interface.network) + ' lookup 1000 pref 100 || true\\\\n'
         return rules

      # ====== IPv4 ============================================================
      if ipv4Interface == ipaddress.IPv4Interface('0.0.0.0/0'):
         interfaceConfiguration = interfaceConfiguration + 'iface ' + interfaceName + ' inet dhcp'
      else:
         interfaceConfiguration = interfaceConfiguration + \
            'iface ' + interfaceName + ' inet static\\\\n' + \
            '\\\\taddress ' + str(ipv4Interface.ip)      + '\\\\n' + \
            '\\\\tnetmask ' + str(ipv4Interface.netmask) + '\\\\n'
         if ((ipv4Gateway != None) and (ipv4Gateway != ipaddress.IPv4Address('0.0.0.0'))):
            interfaceConfiguration = interfaceConfiguration + \
               '\\\\tgateway ' + str(ipv4Gateway) + '\\\\n' + \
               '\\\\tmetric '  + str(metric)      + '\\\\n'
         if pdnInterface != None:
            interfaceConfiguration = interfaceConfiguration + makePDNRules(pdnInterface, ipv4Interface, ipv4Gateway)
      interfaceConfiguration = interfaceConfiguration + dummyInterfaceConfiguration + '\\\\n'

      # ====== IPv6 ============================================================
      if ipv6Interface == None:
         interfaceConfiguration = interfaceConfiguration + \
            '\\\\niface ' + interfaceName + ' inet6 manual\\\\n' + \
            '\\\\tautoconf 0\\\\n'
      elif ipv6Interface == IPv6Interface('::/0'):
         interfaceConfiguration = interfaceConfiguration + \
            '\\\\niface ' + interfaceName + ' inet6 dhcp\\\\n' + \
            '\\\\tautoconf 0\\\\n'
      else:
         interfaceConfiguration = interfaceConfiguration + \
            '\\\\niface ' + interfaceName + ' inet6 static\\\\n' + \
            '\\\\tautoconf 0\\\\n' + \
            '\\\\taddress ' + str(ipv6Interface.ip)                + '\\\\n' + \
            '\\\\tnetmask ' + str(ipv6Interface.network.prefixlen) + '\\\\n'
         if ((ipv6Gateway != None) and (ipv6Gateway != ipaddress.IPv6Address('::'))):
            interfaceConfiguration = interfaceConfiguration + \
               '\\\\tgateway ' + str(ipv6Gateway) + '\\\\n' + \
               '\\\\tmetric '  + str(metric)      + '\\\\n'
         if pdnInterface != None:
            interfaceConfiguration = interfaceConfiguration + makePDNRules(pdnInterface, ipv6Interface, ipv6Gateway)
      interfaceConfiguration = interfaceConfiguration + dummyInterfaceConfiguration

      return interfaceConfiguration


   # ###### Configuration and activate network interface ####################
   def configureInterface(self, interfaceName, interfaceConfiguration, priority = 61):
      self.beginBlock('Configuring and activating ' + interfaceName)

      try:
         commands = """\
echo -e \\\"{interfaceConfiguration}\\\" | sudo tee /etc/network/interfaces.d/{priority}-{interfaceName} && sudo ifup {interfaceName} || true""".format(
            interfaceName          = interfaceName,
            interfaceConfiguration = interfaceConfiguration,
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
