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
# SimulaMet FlexRAN VNF and NS
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

import sys
import subprocess

sys.path.append("lib")

from ops.charm import CharmBase
from ops.main  import main
from ops.model import ActiveStatus

import subprocess
import sys
import traceback
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface

from . import VDUHelper

vduHelper = VDUHelper.VDUHelper()


# ###########################################################################
# #### FlexRAN Charm functions                                           ####
# ###########################################################################

class FlexRANCharm(CharmBase):

   # ###### Constructor #####################################################
   def __init__(self, framework, key):
      super().__init__(framework, key)

      # Listen to charm events
      self.framework.observe(self.on.config_changed, self.on_config_changed)
      self.framework.observe(self.on.install, self.on_install)
      self.framework.observe(self.on.start, self.on_start)

      # Listen to the action events
      self.framework.observe(self.on.prepare_flexran_build_action, self.on_prepare_flexran_build_action)
      self.framework.observe(self.on.configure_flexran_action, self.on_configure_flexran_action)
      self.framework.observe(self.on.prepare_flexran_build_action, self.on_restart_flexran_action)


   # ###### Configuration ###################################################
   def on_config_changed(self, event):
      """Handle changes in configuration"""
      self.model.unit.status = ActiveStatus()


   # ###### Installation ####################################################
   def on_install(self, event):
      """Called when the charm is being installed"""
      self.model.unit.status = ActiveStatus()


   # ###### Start ###########################################################
   def on_start(self, event):
      """Called when the charm is being started"""
      self.model.unit.status = ActiveStatus()


   # ###### prepare-flexran-build Action ####################################
   def on_prepare_flexran_build_action():
      vduHelper.beginBlock('prepare_flexran_build')
      try:

         # ====== Get FlexRAN parameters ====================================
         # For a documentation of the installation procedure, see:
         # https://gitlab.eurecom.fr/mosaic5g/mosaic5g/-/wikis/tutorials/slicing

         gitName       = function_get('git-name')
         gitEmail      = function_get('git-email')
         gitRepository = function_get('flexran-git-repository')
         gitCommit     = function_get('flexran-git-commit')
         gitDirectory  = 'mosaic5g'

         flexranService_IPv4Interface = IPv4Interface(function_get('flexran-service-ipv4-interface'))
         if (function_get('flexran-service-ipv4-gateway') == None) or (function_get('flexran-service-ipv4-gateway') == ''):
            flexranService_IPv4Gateway = None
         else:
            flexranService_IPv4Gateway = IPv4Address(function_get('flexran-service-ipv4-gateway'))

         if function_get('flexran-service-ipv6-interface') != '':
            flexranService_IPv6Interface = IPv6Interface(function_get('flexran-service-ipv6-interface'))
         else:
            flexranService_IPv6Interface = None
         if (function_get('flexran-service-ipv6-gateway') == None) or (function_get('flexran-service-ipv6-gateway') == ''):
            flexranService_IPv6Gateway = None
         else:
            flexranService_IPv6Gateway = IPv6Address(function_get('flexran-service-ipv6-gateway'))

         # Prepare network configuration:
         # Cloud-Init configures all 3 interfaces in Ubuntu 20.04+
         # => unwanted configuration on ens3 and ens4
         # Get rid of the Cloud-Init configuration, then configure the
         # interfaces manually with the correct configuration.
         vduHelper.runInShell('sudo mv /etc/netplan/50-cloud-init.yaml /home/nornetpp')
         interfaceConfiguration = vduHelper.makeInterfaceConfiguration('ens3')
         vduHelper.configureInterface('ens3', interfaceConfiguration, 50)

         flexranService_IfName = 'ens4'
         configurationService = vduHelper.makeInterfaceConfiguration(flexranService_IfName,
                                                                     flexranService_IPv4Interface, flexranService_IPv4Gateway,
                                                                     flexranService_IPv6Interface, flexranService_IPv6Gateway)

         # ====== Prepare system ============================================
         vduHelper.beginBlock('Preparing system')
         vduHelper.configureGit(gitName, gitEmail)
         vduHelper.configureInterface(flexranService_IfName, configurationService, 61)
         vduHelper.testNetworking()
         vduHelper.waitForPackageUpdatesToComplete()
         vduHelper.endBlock()

         # ====== Prepare sources ===========================================
         vduHelper.beginBlock('Preparing sources')
         vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
         vduHelper.executeFromString("""\
cd /home/nornetpp/src/{gitDirectory} && \\
git submodule init && \\
git submodule update flexran
""".format(gitDirectory = gitDirectory))
         vduHelper.endBlock()


         message = vduHelper.endBlock()
         event.set_results( { 'prepared': True, 'outout': message } )
      except:
         message = vduHelper.endBlockInException()
         event.fail(message)
      finally:
         self.model.unit.status = ActiveStatus()


   # ###### configure-flexran function #########################################
   def on_configure_flexran_action():
      vduHelper.beginBlock('configure_flexran')
      try:

         # ====== Get FlexRAN parameters =======================================
         # For a documentation of the installation procedure, see:
         # https://gitlab.eurecom.fr/mosaic5g/mosaic5g/-/wikis/tutorials/slicing

         gitDirectory = 'mosaic5g'

         # ====== Build FlexRAN ================================================
         vduHelper.beginBlock('Building FlexRAN itself')
         # NOTE:
         # Use commit 9a65f40975fafca5bb5370ba6d0d00f42cbc4356 of Pistache as
         # work-around for issue:
         # https://gitlab.eurecom.fr/flexran/flexran-rtc/-/issues/7)
         vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/nornetpp/src/{gitDirectory} && \\
mkdir -p logs && \\
sed -e 's#^    cd pistache .. exit$#    cd pistache \&\& git checkout 9a65f40975fafca5bb5370ba6d0d00f42cbc4356 || exit 1#' -i flexran/tools/install_dependencies && \\
./build_m5g -f >logs/build_flexran.log 2>&1
""".format(gitDirectory = gitDirectory))
         vduHelper.endBlock()

         # ====== Configure FlexRAN ================================================
         vduHelper.beginBlock('Configuring FlexRAN')
         vduHelper.executeFromString("""\
cd /home/nornetpp/src/{gitDirectory}/flexran
""".format(gitDirectory = gitDirectory))
         vduHelper.endBlock()

         # ====== Set up FlexRAN service ===========================================
         vduHelper.beginBlock('Setting up FlexRAN service')
         vduHelper.configureSystemInfo('FlexRAN Controller', 'This is the FlexRAN Controller of the SimulaMet FlexRAN VNF!')
         vduHelper.createFileFromString('/lib/systemd/system/flexran.service', """\
[Unit]
Description=FlexRAN Controller
After=ssh.target

[Service]
ExecStart=/bin/sh -c 'exec /usr/bin/env FLEXRAN_RTC_HOME=/home/nornetpp/src/{gitDirectory}/flexran FLEXRAN_RTC_EXEC=/home/nornetpp/src/{gitDirectory}/flexran/build ./build/rt_controller -c log_config/basic_log >>/var/log/flexran.log 2>&1'
KillMode=process
Restart=on-failure
RestartPreventExitStatus=255
WorkingDirectory=/home/nornetpp/src/{gitDirectory}/flexran

[Install]
WantedBy=multi-user.target
""".format(gitDirectory = gitDirectory))

         vduHelper.createFileFromString('/home/nornetpp/log',
"""\
#!/bin/sh
tail -f /var/log/flexran.log
""", True)

         vduHelper.createFileFromString('/home/nornetpp/restart',
"""\
#!/bin/sh
DIRECTORY=`dirname $0`
sudo service flexran restart && $DIRECTORY/log
""", True)
         vduHelper.runInShell('sudo chown nornetpp:nornetpp /home/nornetpp/log /home/nornetpp/restart')
         vduHelper.endBlock()

         # ====== Set up sysstat service ====================================
         vduHelper.installSysStat()

         # ====== Clean up ==================================================
         vduHelper.cleanUp()

         message = vduHelper.endBlock()
         event.set_results( { 'configured': True, 'outout': message } )
      except:
         message = vduHelper.endBlockInException()
         event.fail(message)
      finally:
         self.model.unit.status = ActiveStatus()


   # ###### restart-flexran function ########################################
   def on_restart_flexran_action():
      vduHelper.beginBlock('restart_flexran')
      try:

         vduHelper.runInShell('sudo service flexran restart')

         message = vduHelper.endBlock()
         event.set_results( { 'restarted': True, 'outout': message } )
      except:
         message = vduHelper.endBlockInException()
         event.fail(message)
      finally:
         self.model.unit.status = ActiveStatus()



# ###########################################################################
# #### Main program                                                      ####
# ###########################################################################

if __name__ == "__main__":
   main(FlexRANCharm)
