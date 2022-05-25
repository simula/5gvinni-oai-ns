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
# Copyright (C) 2019-2022 by Thomas Dreibholz
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
import charms.sshproxy

import subprocess
import sys
import traceback
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface

from . import VDUHelper

vduHelper = VDUHelper.VDUHelper()



# ###########################################################################
# #### HSS Charm functions                                               ####
# ###########################################################################

# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('hsscharm.installed')
def install_hsscharm_proxy_charm():
   set_flag('hsscharm.installed')
   vduHelper.setStatus('install_hsscharm_proxy_charm: SSH proxy charm is READY')


# ###### prepare-cassandra-hss-build function ###############################
@when('actions.prepare-cassandra-hss-build')
@when('hsscharm.installed')
@when_not('hsscharm.prepared-cassandra-hss-build')
def prepare_cassandra_hss_build():
   vduHelper.beginBlock('prepare_cassandra_hss_build')
   try:

      # ====== Get HSS parameters ===========================================
      # For a documentation of the installation procedure, see:
      # https://github.com/simula/openairinterface-openair-cn/wiki/OpenAirSoftwareSupport#install-hss

      gitRepository = function_get('hss-git-repository')
      gitCommit     = function_get('hss-git-commit')
      gitDirectory  = 'openair-hss'

      # Prepare network configuration:
      hssS6a_IfName    = 'ens4'
      configurationS6a = vduHelper.makeInterfaceConfiguration(hssS6a_IfName, IPv4Interface('0.0.0.0/0'))

      # ====== Prepare system ===============================================
      vduHelper.beginBlock('Preparing system')
      vduHelper.configureInterface(hssS6a_IfName, configurationS6a, 61)
      vduHelper.testNetworking()
      vduHelper.waitForPackageUpdatesToComplete()
      vduHelper.executeFromString("""if [ "`find /etc/apt/sources.list.d -name 'rmescandon-ubuntu-yq-*.list'`" == "" ] ; then sudo add-apt-repository -y ppa:rmescandon/yq ; fi""")
      vduHelper.aptInstallPackages([ 'yq' ])
      vduHelper.endBlock()

      # ====== Prepare sources ==============================================
      vduHelper.beginBlock('Preparing sources')
      vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
      vduHelper.endBlock()


      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('hsscharm.prepared-cassandra-hss-build')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.prepare-cassandra-hss-build')


# ###### configure-cassandra function #######################################
@when('actions.configure-cassandra')
@when('hsscharm.prepared-cassandra-hss-build')
def configure_cassandra():
   vduHelper.beginBlock('configure_cassandra')
   try:

      # ====== Get HSS parameters ===========================================
      # For a documentation of the installation procedure, see:
      # https://github.com/simula/openairinterface-openair-cn/wiki/OpenAirSoftwareSupport#install-hss

      gitDirectory      = 'openair-hss'
      cassandraServerIP = function_get('cassandra-server-ip')

      # ====== Build Cassandra ==============================================
      vduHelper.beginBlock('Building Cassandra')
      vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/nornetpp/src/{gitDirectory}/scripts && \\
mkdir -p logs && \\
sudo rm -f /etc/apt/sources.list.d/cassandra.sources.list && \\
./build_cassandra --cassandra-server-ip {cassandraServerIP} --check-installed-software --force >logs/build_cassandra.log 2>&1
""".format(
         gitDirectory      = gitDirectory,
         cassandraServerIP = cassandraServerIP
      ))
      vduHelper.endBlock()

      # ====== Configure Cassandra ==========================================
      vduHelper.beginBlock('Configuring Cassandra')
      vduHelper.executeFromString("""\
cd /home/nornetpp/src/{gitDirectory}/scripts && \\
sudo update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java && \\
sudo service cassandra stop && \\
sudo rm -rf /var/lib/cassandra/data/system/* && \\
sudo rm -rf /var/lib/cassandra/commitlog/* && \\
sudo rm -rf /var/lib/cassandra/data/system_traces/* && \\
sudo rm -rf /var/lib/cassandra/saved_caches/* && \\
sudo yq w -i /etc/cassandra/cassandra.yaml "cluster_name" "HSS Cluster" && \\
sudo yq w -i /etc/cassandra/cassandra.yaml "seed_provider[0].class_name" "org.apache.cassandra.locator.SimpleSeedProvider" && \\
sudo yq w -i /etc/cassandra/cassandra.yaml "seed_provider[0].parameters[0].seeds" "{cassandraServerIP}" && \\
sudo yq w -i /etc/cassandra/cassandra.yaml "listen_address" "{cassandraServerIP}" && \\
sudo yq w -i /etc/cassandra/cassandra.yaml "rpc_address" "{cassandraServerIP}" && \\
sudo yq w -i /etc/cassandra/cassandra.yaml "endpoint_snitch" "GossipingPropertyFileSnitch" && \\
sudo service cassandra start && \\
t=1 ; while [ $t -le 180 ] ; do echo "Trying $t ..." ; if echo "SHOW VERSION;" | cqlsh 172.16.6.129 ; then break ; sleep 1 ; fi ; let t=$t+1 ; done && \\
sudo service cassandra status | cat && \\
cqlsh --file ../src/hss_rel14/db/oai_db.cql {cassandraServerIP} >logs/oai_db.log 2>&1 && \\
cqlsh -e "SELECT COUNT(*) FROM vhss.users_imsi;" {cassandraServerIP} >logs/oai_db_check.log 2>&1 && echo "Cassandra is okay!" || echo "Cassandra seems to be unavailable!"
""".format(
         gitDirectory      = gitDirectory,
         cassandraServerIP = cassandraServerIP
      ))
      vduHelper.endBlock()


      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('hsscharm.configured-cassandra')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.configure-cassandra')


# ###### configure-hss function #############################################
@when('actions.configure-hss')
@when('hsscharm.configured-cassandra')
def configure_hss():
   vduHelper.beginBlock('configure_hss')
   try:

      # ====== Get HSS parameters ===========================================
      # For a documentation of the installation procedure, see:
      # https://github.com/simula/openairinterface-openair-cn/wiki/OpenAirSoftwareSupport#install-hss

      gitDirectory       = 'openair-hss'
      cassandraServerIP  = function_get('cassandra-server-ip')
      networkRealm       = function_get('network-realm')
      networkOP          = function_get('network-op')
      networkK           = function_get('network-k')
      networkIMSIFirst   = function_get('network-imsi-first')
      networkMSISDNFirst = function_get('network-msisdn-first')
      networkUsers       = int(function_get('network-users'))

      hssS6a_IPv4Address = IPv4Address(function_get('hss-S6a-address'))
      mmeS6a_IPv4Address = IPv4Address(function_get('mme-S6a-address'))

      # ====== Build HSS dependencies =======================================
      vduHelper.beginBlock('Building HSS dependencies')
      vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/nornetpp/src/{gitDirectory}/scripts && \\
mkdir -p logs && \\
./build_hss_rel14 --check-installed-software --force >logs/build_hss_rel14-1.log 2>&1
""".format(gitDirectory = gitDirectory))
      vduHelper.endBlock()

      # ====== Build HSS itself =============================================
      vduHelper.beginBlock('Building HSS itself')
      vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/nornetpp/src/{gitDirectory}/scripts && \\
./build_hss_rel14 --clean >logs/build_hss_rel14-2.log 2>&1
sudo service cassandra restart 2>&1 | tee logs/oai_db_check2.log && \\
t=1 ; while [ $t -le 180 ] ; do echo "Trying $t ..." | tee --append logs/oai_db_check2.log ; if echo "SHOW VERSION;" | cqlsh 172.16.6.129 >>logs/oai_db_check2.log 2>&1 ; then break ; sleep 1 ; fi ; let t=$t+1 ; done && \\
sudo service cassandra status 2>&1 | tee --append logs/oai_db_check2.log
""".format(
         gitDirectory       = gitDirectory,
         cassandraServerIP  = cassandraServerIP
      ))
      vduHelper.endBlock()

      # ====== Provision users and MME ======================================
      vduHelper.beginBlock('Provisioning users and MME')
      vduHelper.executeFromString("""\
cd /home/nornetpp/src/{gitDirectory}/scripts && \\
./data_provisioning_users --apn default.{networkRealm} --apn2 internet.{networkRealm} --key {networkK} --imsi-first {networkIMSIFirst} --msisdn-first {networkMSISDNFirst} --mme-identity mme.{networkRealm} --no-of-users {networkUsers} --realm {networkRealm} --truncate True  --verbose True --cassandra-cluster {cassandraServerIP} >logs/data_provisioning_users.log 2>&1 && \\
./data_provisioning_mme --id 3 --mme-identity mme.{networkRealm} --realm {networkRealm} --ue-reachability 1 --truncate True  --verbose True -C {cassandraServerIP} >logs/data_provisioning_mme.log 2>&1
""".format(
         gitDirectory       = gitDirectory,
         cassandraServerIP  = cassandraServerIP,
         networkRealm       = networkRealm,
         networkOP          = networkOP,
         networkK           = networkK,
         networkIMSIFirst   = networkIMSIFirst,
         networkMSISDNFirst = networkMSISDNFirst,
         networkUsers       = networkUsers
      ))
      vduHelper.endBlock()

      # ====== Configure HSS ================================================
      vduHelper.beginBlock('Configuring HSS')
      vduHelper.executeFromString("""\
cd /home/nornetpp/src/{gitDirectory}/scripts && \\
echo "{hssS6a_IPv4Address}   hss.{networkRealm} hss" | sudo tee -a /etc/hosts && \\
echo "{mmeS6a_IPv4Address}   mme.{networkRealm} mme" | sudo tee -a /etc/hosts && \\
openssl rand -out $HOME/.rnd 128 && \\
echo "====== Configuring Diameter ... ======" && \\
PREFIX='/usr/local/etc/oai' && \\
sudo mkdir -m 0777 -p $PREFIX && \\
sudo mkdir -m 0777 -p $PREFIX/freeDiameter && \\
sudo cp ../etc/acl.conf ../etc/hss_rel14_fd.conf $PREFIX/freeDiameter && \\
sudo cp ../etc/hss_rel14.conf ../etc/hss_rel14.json $PREFIX && \\
sudo sed -i -e 's/#ListenOn/ListenOn/g' $PREFIX/freeDiameter/hss_rel14_fd.conf && \\
echo "====== Updating configuration files ... ======" && \\
declare -A HSS_CONF && \\
HSS_CONF[@PREFIX@]=$PREFIX && \\
HSS_CONF[@REALM@]='{networkRealm}' && \\
HSS_CONF[@HSS_FQDN@]='hss.{networkRealm}' && \\
HSS_CONF[@HSS_HOSTNAME@]='hss' && \\
HSS_CONF[@cassandra_Server_IP@]='{cassandraServerIP}' && \\
HSS_CONF[@cassandra_IP@]='{cassandraServerIP}' && \\
HSS_CONF[@OP_KEY@]='{networkOP}' && \\
HSS_CONF[@ROAMING_ALLOWED@]='true' && \\
for K in "${{!HSS_CONF[@]}}"; do echo "K=$K ..." && sudo egrep -lRZ "$K" $PREFIX | xargs -0 -l sudo sed -i -e "s|$K|${{HSS_CONF[$K]}}|g" ; done && \\
../src/hss_rel14/bin/make_certs.sh hss {networkRealm} $PREFIX && \\
echo "====== Updating key ... ======" && \\
oai_hss -j $PREFIX/hss_rel14.json --onlyloadkey >logs/onlyloadkey.log 2>&1
""".format(
         gitDirectory       = gitDirectory,
         cassandraServerIP  = cassandraServerIP,
         hssS6a_IPv4Address = hssS6a_IPv4Address,
         mmeS6a_IPv4Address = mmeS6a_IPv4Address,
         networkRealm       = networkRealm,
         networkOP          = networkOP,
         networkK           = networkK,
         networkIMSIFirst   = networkIMSIFirst,
         networkMSISDNFirst = networkMSISDNFirst,
         networkUsers       = networkUsers
      ))
      vduHelper.endBlock()

      # ====== Set up HSS service ===========================================
      vduHelper.beginBlock('Setting up HSS service')
      vduHelper.configureSystemInfo('HSS', 'This is the HSS of the SimulaMet OAI VNF!')
      vduHelper.createFileFromString('/lib/systemd/system/hss.service', """\
[Unit]
Description=Home Subscriber Server (HSS)
After=ssh.target

[Service]
ExecStart=/bin/sh -c 'exec /usr/local/bin/oai_hss -j /usr/local/etc/oai/hss_rel14.json >>/var/log/hss.log 2>&1'
KillMode=process
Restart=on-failure
RestartPreventExitStatus=255
WorkingDirectory=/home/nornetpp/src/{gitDirectory}/scripts

[Install]
WantedBy=multi-user.target
""".format(gitDirectory = gitDirectory))

      vduHelper.createFileFromString('/home/nornetpp/log',
"""\
#!/bin/sh
tail -f /var/log/hss.log
""", True)

      vduHelper.createFileFromString('/home/nornetpp/restart',
"""\
#!/bin/sh
DIRECTORY=`dirname $0`
sudo service hss restart && $DIRECTORY/log
""", True)
      vduHelper.runInShell('sudo chown nornetpp:nornetpp /home/nornetpp/log /home/nornetpp/restart')
      vduHelper.endBlock()

      # ====== Set up sysstat service =======================================
      vduHelper.installSysStat()

      # ====== Clean up =====================================================
      vduHelper.cleanUp()

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
      set_flag('hsscharm.configured-hss')
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.configure-hss')


# ###### restart-hss function ###############################################
@when('actions.restart-hss')
@when('hsscharm.configured-hss')
def restart_hss():
   vduHelper.beginBlock('restart_hss')
   try:

      vduHelper.runInShell('sudo service hss restart')

      message = vduHelper.endBlock()
      function_set( { 'outout': message } )
   except:
      message = vduHelper.endBlockInException()
      function_fail(message)
   finally:
      clear_flag('actions.restart-hss')
