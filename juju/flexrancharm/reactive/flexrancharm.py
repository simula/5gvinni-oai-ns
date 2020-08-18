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


from charmhelpers.core.hookenv import (
    function_get,
    function_fail,
    function_set,
    status_set
)
from charms.reactive import (
    clear_flag,
    set_flag,
    when,
    when_not
)
import subprocess
import sys
import traceback
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface

from . import VDUHelper

vduHelper = VDUHelper.VDUHelper()


# ***************************************************************************
# NOTE:
# Double escaping is required for \ and " in command string!
# 1. Python
# 2. bash -c "<command>"
# That is: $ => \$ ; \ => \\ ; " => \\\"
# ***************************************************************************



# ###########################################################################
# #### FlexRAN Charm functions                                           ####
# ###########################################################################

# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('flexrancharm.installed')
def install_flexrancharm_proxy_charm():
   set_flag('flexrancharm.installed')
   vduHelper.setStatus('install_flexrancharm_proxy_charm: SSH proxy charm is READY')


# ###### prepare-flexran-build function #####################################
@when('actions.prepare-flexran-build')
@when('flexrancharm.installed')
@when_not('flexrancharm.prepared-flexran-build')
def prepare_cassandra_flexran_build():
   vduHelper.beginBlock('prepare_cassandra_flexran_build')
   try:

      # ====== Get FlexRAN parameters ===========================================
      # For a documentation of the installation procedure, see:
      # https://gitlab.eurecom.fr/mosaic5g/mosaic5g/-/wikis/tutorials/slicing

      gitRepository = function_get('flexran-git-repository')
      gitCommit     = function_get('flexran-git-commit')
      gitDirectory  = 'mosaic5g'

      # Prepare network configuration:
      flexranService_IfName = 'ens4'
      configurationS6a = vduHelper.makeInterfaceConfiguration(flexranService_IfName, IPv4Interface('0.0.0.0/0'))

      # ====== Prepare system ===============================================
      vduHelper.beginBlock('Preparing system')
      vduHelper.configureInterface(flexranService_IfName, configurationService, 61)
      vduHelper.testNetworking('8.8.8.8')
      vduHelper.endBlock()

      # ====== Prepare sources ==============================================
      vduHelper.beginBlock('Preparing sources')
      vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
      vduHelper.endBlock()


      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('flexrancharm.prepared-flexran-build')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.prepare-flexran-build')


# ###### configure-flexran function #########################################
@when('actions.configure-flexran')
@when('flexrancharm.configured-cassandra')
def configure_flexran():
   vduHelper.beginBlock('configure_flexran')
   try:

      # ====== Get FlexRAN parameters =======================================
      # For a documentation of the installation procedure, see:
      # https://gitlab.eurecom.fr/mosaic5g/mosaic5g/-/wikis/tutorials/slicing

      gitDirectory = 'mosaic5g'
      #networkUsers       = int(function_get('network-users'))

      # ====== Build FlexRAN ================================================
      vduHelper.beginBlock('Building FlexRAN itself')
      commands = """\
export MAKEFLAGS=\\\"-j`nproc`\\\" && \\
cd /home/nornetpp/src/{gitDirectory} && \\
mkdir -p logs && \\
./build_m5g -f >logs/build_flexran.log 2>&1""".format(gitDirectory = gitDirectory)
         gitDirectory       = gitDirectory
      )
      vduHelper.runInShell(commands)
      vduHelper.endBlock()

      # ====== Configure FlexRAN ================================================
      vduHelper.beginBlock('Configuring FlexRAN')
      commands = """\
cd /home/nornetpp/src/{gitDirectory}/scripts""".format(
         gitDirectory = gitDirectory
      )
      vduHelper.runInShell(commands)
      vduHelper.endBlock()

      # ====== Set up FlexRAN service ===========================================
      vduHelper.beginBlock('Setting up FlexRAN service')
      commands = """\
( echo \\\"[Unit]\\\" && \\
echo \\\"Description=Home Subscriber Server (FlexRAN)\\\" && \\
echo \\\"After=ssh.target\\\" && \\
echo \\\"\\\" && \\
echo \\\"[Service]\\\" && \\
echo \\\"ExecStart=/bin/sh -c \\\'exec /home/nornetpp/src/mosaic5g/flexran/run_flexran_rtc.sh >>/var/log/flexran.log 2>&1\\\'\\\" && \\
echo \\\"KillMode=process\\\" && \\
echo \\\"Restart=on-failure\\\" && \\
echo \\\"RestartPreventExitStatus=255\\\" && \\
echo \\\"WorkingDirectory=/home/nornetpp/src/mosaic5g/flexran\\\" && \\
echo \\\"\\\" && \\
echo \\\"[Install]\\\" && \\
echo \\\"WantedBy=multi-user.target\\\" ) | sudo tee /lib/systemd/system/flexran.service && \\
sudo systemctl daemon-reload && \\
( echo -e \\\"#\\x21/bin/sh\\\" && echo \\\"tail -f /var/log/flexran.log\\\" ) | tee /home/nornetpp/log && \\
chmod +x /home/nornetpp/log && \\
( echo -e \\\"#\\x21/bin/sh\\\" && echo \\\"sudo service flexran restart && ./log\\\" ) | tee /home/nornetpp/restart && \\
chmod +x /home/nornetpp/restart"""
      vduHelper.runInShell(commands)
      vduHelper.endBlock()

      # ====== Set up sysstat service =======================================
      vduHelper.installSysStat()


      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('flexrancharm.configured-flexran')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.configure-flexran')


# ###### restart-flexran function ###############################################
@when('actions.restart-flexran')
@when('flexrancharm.configured-flexran')
def restart_flexran():
   vduHelper.beginBlock('restart_flexran')
   try:

      commands = 'sudo service flexran restart'
      vduHelper.runInShell(commands)

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.restart-flexran')
