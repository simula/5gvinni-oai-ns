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
# Copyright (C) 2019-2023 by Thomas Dreibholz
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
import os
import subprocess
import shutil
import sys
import traceback


# ###########################################################################
# #### Colored Log Formatter class                                       ####
# ###########################################################################

class ColouredLogFormatter(logging.Formatter):
   formatString = '%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s'   # (%(filename)s:%(lineno)d)
   FORMATS = {
      logging.CRITICAL: '\x1b[37;41;1m' + formatString + '\x1b[0m',
      logging.ERROR:    '\x1b[31m' + formatString + '\x1b[0m',
      logging.WARNING:  '\x1b[33m' + formatString + '\x1b[0m',
      logging.INFO:     '\x1b[34m' + formatString + '\x1b[0m',
      logging.DEBUG:    '\x1b[37m' + formatString + '\x1b[0m'
    }

   def format(self, record):
      logFormatter = self.FORMATS.get(record.levelno)
      formatter = logging.Formatter(logFormatter)
      return formatter.format(record)



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

      # ====== Initialise logger ============================================
      self.logger = logging.getLogger(__name__)
      streamHandler = logging.StreamHandler()
      streamHandler.setFormatter(ColouredLogFormatter())
      self.logger.addHandler(streamHandler)
      self.logger.setLevel(logging.DEBUG)   # <<-- Enabling verbose output!

      # ------ TEST ONLY! ---------------------------------
      self.logger.critical('critical message')
      self.logger.error('error message')
      self.logger.warning('warning message')
      self.logger.info('info message')
      self.logger.debug('debug message')
      # ---------------------------------------------------

      if self.testMode == False:
         self.logger.info('Starting')
      else:
         self.logger.info('Starting in Test Mode!')


   # ###### Begin block #####################################################
   def setStatus(self, message, isError = False):
      if isError:
         self.logger.error(message)
      else:
         self.logger.info(message)


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
         commands = 'touch {}'.format(fileName)
         self.runInShell(commands)
      except:
         self.endBlock(False)
         raise

      self.endBlock()


   # ###### Execute command #################################################
   def execute(self, commands):
      # ====== Run via SSH ==================================================
      if self.testMode == False:
         self.logger.debug('Shell: ' + commands)
         subprocess.run(commands, shell = True, check = True)

      # ====== Test Mode ====================================================
      else:
         label = ''
         if len(self.blockStack) > 0:
            label = ' ' + self.blockStack[-1] + ' '
         width = shutil.get_terminal_size(fallback=(80, 25)).columns
         n = width - 8 - len(label)
         if n < 0:
            n = 0
         sys.stdout.write('\x1b[34m# ------' + label + ('-' * n) + '\x1b[0m\n')
         sys.stdout.write('time bash -c "' + commands + '"\n')


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


   # ###### Store string into file ##########################################
   def createFileFromString(self, fileName, contentString, makeExecutable = False, setOwnerTo = None):
      self.beginBlock('Creating file ' + fileName)

      contentBase64 = self.makeBase64(contentString)
      try:
         commands = 'echo "{contentBase64}" | base64 -d | sudo tee {fileName}'.format(
                       fileName = fileName, contentBase64 = contentBase64)
         if makeExecutable == False:
            commands = commands + ' && \\\nsudo chmod +x {fileName}'.format(fileName = fileName)
         if setOwnerTo != None:
            commands = commands + ' && \\\nsudo chown {setOwnerTo} {fileName}'.format(fileName = fileName, setOwnerTo = setOwnerTo)
         self.runInShell(commands)
      except:
         self.endBlock(False)
         raise

      self.endBlock()


   # ###### Execute command-line from string ################################
   def executeFromString(self, commandLineString):
      commandLineBase64 = self.makeBase64(commandLineString)
      try:
         commands = 'echo "{commandLineBase64}" | base64 -d | /bin/bash -x'.format(
                       commandLineBase64 = commandLineBase64)
         self.runInShell(commands)
      except:
         self.endBlock(False)
         raise


   # ###### Encode string to base64 ##########################################
   def makeBase64(self, string):
      # NOTE: Handling multiple levels of string encapsulation with Python, bash,
      # etc. is just a total mess! Therefore, using a straightforward approach here:
      # Create the command string as is, apply base64 encoding, and decode it at the
      # VDU's shell by using "base64 -d".

      if string != None:
         b64 = base64.b64encode(string.encode('utf-8')).decode('ascii')
         self.logger.debug('makeBase64("' + string + '")="' + b64 + '"')
         return b64
      return None


   # ######  Get /etc/network/interfaces setup for interface #################
   def makeInterfaceConfiguration(self,
                                  interfaceName,
                                  ipv4Interface = None,
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
      if ipv4Interface == None:
         interfaceConfiguration = interfaceConfiguration + '      dhcp4: true\n'
      else:
         interfaceConfiguration = interfaceConfiguration + '      dhcp4: false\n'

      if ((ipv6Interface == None) and (ipv6Interface == ipaddress.IPv6Interface('::/0'))):
         interfaceConfiguration = interfaceConfiguration + '      dhcp6: true\n'
      else:
         interfaceConfiguration = interfaceConfiguration + '      dhcp6: false\n'
         interfaceConfiguration = interfaceConfiguration + '      accept-ra: no\n'

      if ( (ipv4Interface != None) or
           ((ipv6Interface == None) and (ipv6Interface == ipaddress.IPv6Interface('::/0'))) ):

         if ( ((ipv4Interface != None) and (ipv4Interface != None)) or
              ((ipv6Interface != None) and (ipv6Interface == ipaddress.IPv6Interface('::/0'))) ):
            interfaceConfiguration = interfaceConfiguration + '      addresses:\n'

         if ((ipv4Interface != None) and (ipv4Interface != ipaddress.IPv4Interface('0.0.0.0/0'))):
            interfaceConfiguration = interfaceConfiguration + '        - ' + \
               str(ipv4Interface.ip) + '/' + \
               str(ipv4Interface.network.prefixlen) + \
               '\n'
            networks.append(ipv4Interface.network)

         if ((ipv6Interface != None) and (ipv6Interface == ipaddress.IPv6Interface('::/0'))):
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

      return [ interfaceConfiguration, postUpRules, preDownRules ]


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
         '#\x21/bin/sh\n' + \
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
         if interfaceConfiguration[1] != None:
            self.createFileFromString('/etc/networkd-dispatcher/routable.d/{priority}-{interfaceName}'.format(
                                         interfaceName = interfaceName, priority = priority),
                                      interfaceConfiguration[1], True)

         if interfaceConfiguration[2] != None:
            self.createFileFromString('/etc/networkd-dispatcher/off.d/{priority}-{interfaceName}'.format(
                                         interfaceName = interfaceName, priority = priority),
                                      interfaceConfiguration[2], True)

         self.createFileFromString('/etc/netplan/{interfaceName}.yaml'.format(interfaceName = interfaceName),
                                   interfaceConfiguration[0])
         self.runInShell('sudo netplan apply')
      except:
         self.endBlock(False)
         raise

      self.endBlock()


   # ###### Configuration OpenVSwitch #######################################
   def configureSwitch(self, switchName, interfaceNames):
      self.beginBlock('Configuring and activating ' + switchName)

      switchConfiguration = """\
network:
  version: 2
  renderer: networkd
  ethernets:
"""

      for interfaceName in interfaceNames:
         switchConfiguration = switchConfiguration + """\
    {interfaceName}:
       dhcp4: no
       accept-ra: no
""".format(interfaceName = interfaceName)

      switchConfiguration = switchConfiguration + """\
  openvswitch:
    protocols: [OpenFlow13, OpenFlow14, OpenFlow15]
  bridges:
    {switchName}:
      dhcp4: no
      accept-ra: no
      interfaces:
""".format(switchName = switchName)

      for interfaceName in interfaceNames:
         switchConfiguration = switchConfiguration + """\
        - {interfaceName}
""".format(interfaceName = interfaceName)

      switchConfiguration = switchConfiguration + """\
      openvswitch:
        protocols: [OpenFlow13, OpenFlow14, OpenFlow15]
"""

      try:
         self.createFileFromString('/etc/netplan/{switchName}.yaml'.format(switchName = switchName),
                                   switchConfiguration)
         self.runInShell('sudo netplan apply')
      except:
         self.endBlock(False)
         raise

      self.endBlock()


   # ###### Store string into file ##########################################
   def createFileFromString(self, fileName, contentString, makeExecutable = False):
      self.beginBlock('Creating file ' + fileName)

      contentBase64 = self.makeBase64(contentString)
      try:
         commands = 'echo "{contentBase64}" | base64 -d | sudo tee {fileName}'.format(
                       fileName = fileName, contentBase64 = contentBase64)
         if makeExecutable == True:
            commands = commands + ' && \\\nsudo chmod +x {fileName}'.format(fileName = fileName)
         self.runInShell(commands)
      except:
         self.endBlock(False)
         raise

      self.endBlock()


   # ###### Execute command-line from string ################################
   def executeFromString(self, commandLineString):
      commandLineBase64 = self.makeBase64(commandLineString)
      try:
         commands = 'echo "{commandLineBase64}" | base64 -d | /bin/bash -x'.format(
                       commandLineBase64 = commandLineBase64)
         self.runInShell(commands)
      except:
         self.endBlock(False)
         raise


   # ###### Test networking #################################################
   def testNetworking(self, destination = ipaddress.IPv4Address('8.8.8.8'), timeout = 60, interval = 0.333):
      self.beginBlock('Testing networking')

      try:
         commands = 'ping -W{timeout}  -i{interval} -c3 {destination}'.format(
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

      try:
         # Trying the most straightforward solution: explicitly calling the
         # updater script, to make sure it finishes!
         self.runInShell('sudo /usr/lib/apt/apt.systemd.daily')
      except:
         self.endBlock(False)
         raise

      self.endBlock()


   # ###### Install packages with APT #######################################
   def aptInstallPackages(self, packages, update = True):
      if len(packages) > 0:
         if update == True:
            commands = 'sudo apt update && \\\n'
         else:
            commands = ''
         commands = commands + 'sudo env DEBIAN_FRONTEND=noninteractive apt install -y -o Dpkg::Options::=--force-confold -o Dpkg::Options::=--force-confdef --no-install-recommends'
         for package in packages:
            commands = commands + ' ' + package
         self.runInShell(commands)


   # ###### Install packages with PIP #######################################
   def pipInstallPackages(self, packages, pipVersion = 3):
      commands = 'sudo '
      if pipVersion == None:
         commands = commands + 'pip '
      else:
         commands = commands + 'pip' + str(pipVersion) + ' '
      commands = commands + 'install'
      for package in packages:
         commands = commands + ' ' + package
      self.runInShell(commands)


   # ###### Write .gitconfig ################################################
   def configureGit(self, name, email):
      self.beginBlock('Configuring Git')
      self.createFileFromString('/home/nornetpp/.gitconfig', """\
[user]
        name = {name}
        email = {email}
[push]
        default = simple
[color]
        ui = auto
[credential]
        helper = store
""".format(name = name, email = email))
      self.runInShell('sudo chown nornetpp:nornetpp /home/nornetpp/.gitconfig')
      self.endBlock()


   # ###### Configure System-Info banner ####################################
   def configureSystemInfo(self, banner, information):
      self.beginBlock('Configuring System-Info')
      self.aptInstallPackages([ 'td-system-info', 'figlet' ], False)
      self.createFileFromString('/etc/system-info.d/90-vduhelper',
"""
#!/bin/bash -e

# ###### Center text in console #############################################
center ()
{{
   local text="$1"
   local length=${{#text}}
   local width=`tput cols`   # Console width

   let indent=(${{width}} - ${{length}})/2
   if [ ${{indent}} -lt 0 ] ; then
      indent=0
   fi
   printf "%${{indent}}s%s\n" "" "${{text}}"
}}


# ###### Print centered separator in console ################################
separator ()
{{
   local separatorCharacter="="
   local separator=""
   local width=`tput cols`   # Console width
   local separatorWidth

   let separatorWidth=${{width}}-4
   local i=0
   while [ $i -lt ${{separatorWidth}} ] ; do
      separator="${{separator}}${{separatorCharacter}}"
      let i=$i+1
   done
   center "<${{separator}}>"
}}


# ====== Print banner =======================================================

# NOTE:
# You can produce ASCII text banners with "sysvbanner".
# More advanced, UTF-8-capable tools are e.g. figlet and toilet.

echo -en "\x1b[1;34m"
separator
echo -en "\x1b[1;31m"
figlet -w`tput cols` -c "{banner}"
echo -en "\x1b[1;34m"
# echo ""
center "{information}"
separator
echo -e "\x1b[0m"

exit 1   # With exit code 1, no further files in /etc/system-info.d are processed!

# Use exit code 0 to process further files!
""".format(banner = banner, information = information), True)
      self.endBlock()


   # ###### Install SysStat #################################################
   def installSysStat(self):
      self.beginBlock('Setting up sysstat service')
      self.aptInstallPackages([ 'sysstat' ], False)
      self.executeFromString("""\
sudo sed -e "s/^ENABLED=.*$/ENABLED=\"true\"/g" -i /etc/default/sysstat && \
sudo sed -e "s/^SADC_OPTIONS=.*$/SADC_OPTIONS=\"-S ALL\"/g" -i /etc/sysstat/sysstat && \
sudo service sysstat restart""")
      self.endBlock()


   # ###### Fetch Git repository ############################################
   def fetchGitRepository(self, gitDirectory, gitRepository, gitCommit):
      self.beginBlock('Fetching Git repository ' + gitDirectory)

      try:
         commands = """\
cd /home/nornetpp/src && \
if [ ! -d "{gitDirectory}" ] ; then git clone --quiet {gitRepository} {gitDirectory} && cd {gitDirectory} ; else cd {gitDirectory} && git pull ; fi && \
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
      commands = """sudo updatedb"""
      self.runInShell(commands)
      self.endBlock()
