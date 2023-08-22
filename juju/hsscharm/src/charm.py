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

import os
import subprocess
import sys
import traceback
from ipaddress import IPv4Address, IPv4Interface, IPv6Address, IPv6Interface

sys.path.append("lib")
sys.path.append("mod/operator")

from ops.charm import CharmBase
from ops.main  import main
from ops.model import ActiveStatus


import VDUHelper

vduHelper = VDUHelper.VDUHelper(1000)   # <<-- Default user ID for "ubuntu"!



# ###########################################################################
# #### HSS Charm functions                                               ####
# ###########################################################################

class HSSCharm(CharmBase):

   # ###### Constructor #####################################################
   def __init__(self, framework, key):
      super().__init__(framework, key)

      # Listen to charm events
      self.framework.observe(self.on.config_changed, self.on_config_changed)
      self.framework.observe(self.on.install, self.on_install)
      self.framework.observe(self.on.start, self.on_start)

      # Listen to the action events
      self.framework.observe(self.on.prepare_cassandra_hss_build_action, self.on_prepare_cassandra_hss_build_action)
      self.framework.observe(self.on.configure_cassandra_action, self.on_configure_cassandra_action)
      self.framework.observe(self.on.configure_hss_action, self.on_configure_hss_action)
      self.framework.observe(self.on.restart_hss_action, self.on_restart_hss_action)


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


   # ###### prepare-cassandra-hss-build action ##############################
   def on_prepare_cassandra_hss_build_action(self, event):
      vduHelper.beginBlock('on_prepare_cassandra_hss_build_action')
      try:

         # ====== Get HSS parameters ========================================
         # For a documentation of the installation procedure, see:
         # https://github.com/simula/openairinterface-openair-cn/wiki/OpenAirSoftwareSupport#install-hss

         gitName       = event.params['git-name']
         gitEmail      = event.params['git-email']
         gitRepository = event.params['hss-git-repository']
         gitCommit     = event.params['hss-git-commit']
         gitDirectory  = 'openair-hss'

         # Prepare network configuration:
         hssS6a_IfName    = 'ens4'
         configurationS6a = vduHelper.makeInterfaceConfiguration(hssS6a_IfName, None)

         # ====== Prepare system ============================================
         vduHelper.beginBlock('Preparing system')

         vduHelper.configureInterface(hssS6a_IfName, configurationS6a, 61)
         vduHelper.testNetworking()

         vduHelper.executeFromString("""\
sudo -u {user} -g {group} mkdir -p {homeDirectory}/src
""".format(user          = vduHelper.getUser(),
           group         = vduHelper.getGroup(),
           homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))
         vduHelper.configureGit(gitName, gitEmail)
         vduHelper.waitForPackageUpdatesToComplete()
         vduHelper.aptAddRepository('ppa:dreibh/ppa')
         vduHelper.aptAddRepository('ppa:rmescandon/yq')
         vduHelper.aptInstallPackages([ 'joe', 'mlocate', 'td-system-info',
                                        'yq'
                                      ])

         vduHelper.endBlock()

         # ====== Prepare sources ===========================================
         vduHelper.beginBlock('Preparing sources')
         vduHelper.fetchGitRepository(gitDirectory, gitRepository, gitCommit)
         vduHelper.executeFromString("""\
chown -R {user}:{group} {homeDirectory}/src/{gitDirectory}
""".format(user          = vduHelper.getUser(),
           group         = vduHelper.getGroup(),
           homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))
         vduHelper.endBlock()

         message = vduHelper.endBlock()
         event.set_results( { 'prepared': True, 'outout': message } )
      except:
         message = vduHelper.endBlockInException()
         event.fail(message)
      finally:
         self.model.unit.status = ActiveStatus()


   # ###### configure-cassandra action ######################################
   def on_configure_cassandra_action(self, event):
      vduHelper.beginBlock('on_configure_cassandra_action')
      try:

         # ====== Get HSS parameters ========================================
         # For a documentation of the installation procedure, see:
         # https://github.com/simula/openairinterface-openair-cn/wiki/OpenAirSoftwareSupport#install-hss

         gitDirectory      = 'openair-hss'
         cassandraServerIP = event.params['cassandra-server-ip']

         # ====== Build Cassandra ===========================================
         vduHelper.beginBlock('Building Cassandra')
         vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \
cd {homeDirectory}/src/{gitDirectory}/scripts && \
sudo -u {user} -g {group} mkdir -p logs && \
rm -f /etc/apt/sources.list.d/cassandra.sources.list && \\
sudo -u {user} -g {group} --preserve-env=MAKEFLAGS ./build_cassandra --cassandra-server-ip {cassandraServerIP} --check-installed-software --force >logs/build_cassandra.log 2>&1
""".format(user              = vduHelper.getUser(),
           group             = vduHelper.getGroup(),
           homeDirectory     = vduHelper.getHomeDirectory(),
           gitDirectory      = gitDirectory,
           cassandraServerIP = cassandraServerIP))
         vduHelper.endBlock()

         # ====== Configure Cassandra =======================================
         vduHelper.beginBlock('Configuring Cassandra')
         vduHelper.executeFromString("""\
cd {homeDirectory}/src/{gitDirectory}/scripts && \
update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java && \\
service cassandra stop && \\
rm -rf /var/lib/cassandra/data/system/* && \\
rm -rf /var/lib/cassandra/commitlog/* && \\
rm -rf /var/lib/cassandra/data/system_traces/* && \\
rm -rf /var/lib/cassandra/saved_caches/* && \\
yq w -i /etc/cassandra/cassandra.yaml "cluster_name" "HSS Cluster" && \\
yq w -i /etc/cassandra/cassandra.yaml "seed_provider[0].class_name" "org.apache.cassandra.locator.SimpleSeedProvider" && \\
yq w -i /etc/cassandra/cassandra.yaml "seed_provider[0].parameters[0].seeds" "{cassandraServerIP}" && \\
yq w -i /etc/cassandra/cassandra.yaml "listen_address" "{cassandraServerIP}" && \\
yq w -i /etc/cassandra/cassandra.yaml "rpc_address" "{cassandraServerIP}" && \\
yq w -i /etc/cassandra/cassandra.yaml "endpoint_snitch" "GossipingPropertyFileSnitch" && \\
service cassandra start && \\
t=1 ; while [ $t -le 180 ] ; do echo "Trying $t ..." ; if echo "SHOW VERSION;" | cqlsh 172.16.6.129 ; then break ; sleep 1 ; fi ; let t=$t+1 ; done && \\
service cassandra status | cat && \\
cqlsh --file ../src/hss_rel14/db/oai_db.cql {cassandraServerIP} >logs/oai_db.log 2>&1 && \\
cqlsh -e "SELECT COUNT(*) FROM vhss.users_imsi;" {cassandraServerIP} >logs/oai_db_check.log 2>&1 && echo "Cassandra is okay!" || echo "Cassandra seems to be unavailable!"
""".format(user              = vduHelper.getUser(),
           group             = vduHelper.getGroup(),
           homeDirectory     = vduHelper.getHomeDirectory(),
           gitDirectory      = gitDirectory,
           cassandraServerIP = cassandraServerIP))
         vduHelper.endBlock()

         message = vduHelper.endBlock()
         event.set_results( { 'prepared': True, 'outout': message } )
      except:
         message = vduHelper.endBlockInException()
         event.fail(message)
      finally:
         self.model.unit.status = ActiveStatus()


   # ###### configure-hss action ############################################
   def on_configure_hss_action(self, event):
      vduHelper.beginBlock('on_configure_hss_action')
      try:

         # ====== Get HSS parameters ========================================
         # For a documentation of the installation procedure, see:
         # https://github.com/simula/openairinterface-openair-cn/wiki/OpenAirSoftwareSupport#install-hss

         gitDirectory       = 'openair-hss'
         cassandraServerIP  = event.params['cassandra-server-ip']
         networkRealm       = event.params['network-realm']
         networkOP          = event.params['network-op']
         networkK           = event.params['network-k']
         networkIMSIFirst   = event.params['network-imsi-first']
         networkMSISDNFirst = event.params['network-msisdn-first']
         networkUsers       = int(event.params['network-users'])

         hssS6a_IPv4Address = IPv4Address(event.params['hss-S6a-address'])
         mmeS6a_IPv4Address = IPv4Address(event.params['mme-S6a-address'])

         # ====== Build HSS dependencies ====================================
         vduHelper.beginBlock('Building HSS dependencies')
         vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/{homeDirectory}/src/{gitDirectory}/scripts && \\
mkdir -p logs && \\
./build_hss_rel14 --check-installed-software --force >logs/build_hss_rel14-1.log 2>&1
""".format(homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory  = gitDirectory))
         vduHelper.endBlock()

         # ====== Build HSS itself ==========================================
         vduHelper.beginBlock('Building HSS itself')
         vduHelper.executeFromString("""\
export MAKEFLAGS="-j`nproc`" && \\
cd /home/{homeDirectory}/src/{gitDirectory}/scripts && \\
./build_hss_rel14 --clean >logs/build_hss_rel14-2.log 2>&1
service cassandra restart 2>&1 | tee logs/oai_db_check2.log && \\
t=1 ; while [ $t -le 180 ] ; do echo "Trying $t ..." | tee --append logs/oai_db_check2.log ; if echo "SHOW VERSION;" | cqlsh 172.16.6.129 >>logs/oai_db_check2.log 2>&1 ; then break ; sleep 1 ; fi ; let t=$t+1 ; done && \\
service cassandra status 2>&1 | tee --append logs/oai_db_check2.log
""".format(homeDirectory      = vduHelper.getHomeDirectory(),
           gitDirectory       = gitDirectory,
           cassandraServerIP  = cassandraServerIP
          ))
         vduHelper.endBlock()

         # ====== Provision users and MME ===================================
         vduHelper.beginBlock('Provisioning users and MME')
         vduHelper.executeFromString("""\
cd /home/{homeDirectory}/src/{gitDirectory}/scripts && \\
./data_provisioning_users --apn default.{networkRealm} --apn2 internet.{networkRealm} --key {networkK} --imsi-first {networkIMSIFirst} --msisdn-first {networkMSISDNFirst} --mme-identity mme.{networkRealm} --no-of-users {networkUsers} --realm {networkRealm} --truncate True  --verbose True --cassandra-cluster {cassandraServerIP} >logs/data_provisioning_users.log 2>&1 && \\
./data_provisioning_mme --id 3 --mme-identity mme.{networkRealm} --realm {networkRealm} --ue-reachability 1 --truncate True  --verbose True -C {cassandraServerIP} >logs/data_provisioning_mme.log 2>&1
""".format(homeDirectory      = vduHelper.getHomeDirectory(),
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

         # ====== Configure HSS =============================================
         vduHelper.beginBlock('Configuring HSS')
         vduHelper.executeFromString("""\
cd /home/{homeDirectory}/src/{gitDirectory}/scripts && \\
echo "{hssS6a_IPv4Address}   hss.{networkRealm} hss" | tee -a /etc/hosts && \\
echo "{mmeS6a_IPv4Address}   mme.{networkRealm} mme" | tee -a /etc/hosts && \\
openssl rand -out $HOME/.rnd 128 && \\
echo "====== Configuring Diameter ... ======" && \\
PREFIX='/usr/local/etc/oai' && \\
mkdir -m 0777 -p $PREFIX && \\
mkdir -m 0777 -p $PREFIX/freeDiameter && \\
cp ../etc/acl.conf ../etc/hss_rel14_fd.conf $PREFIX/freeDiameter && \\
cp ../etc/hss_rel14.conf ../etc/hss_rel14.json $PREFIX && \\
sed -i -e 's/#ListenOn/ListenOn/g' $PREFIX/freeDiameter/hss_rel14_fd.conf && \\
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
for K in "${{!HSS_CONF[@]}}"; do echo "K=$K ..." && egrep -lRZ "$K" $PREFIX | xargs -0 -l sed -i -e "s|$K|${{HSS_CONF[$K]}}|g" ; done && \\
../src/hss_rel14/bin/make_certs.sh hss {networkRealm} $PREFIX && \\
echo "====== Updating key ... ======" && \\
oai_hss -j $PREFIX/hss_rel14.json --onlyloadkey >logs/onlyloadkey.log 2>&1
""".format(homeDirectory      = vduHelper.getHomeDirectory(),
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

         # ====== Set up HSS service ========================================
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
WorkingDirectory=/home/{homeDirectory}/src/{gitDirectory}/scripts

[Install]
WantedBy=multi-user.target
""".format(homeDirectory = vduHelper.getHomeDirectory(),
           gitDirectory = gitDirectory))

         vduHelper.createFileFromString(os.path.join(vduHelper.getHomeDirectory(), 'log'),
"""\
#!/bin/sh
tail -f /var/log/hss.log
""", True)

         vduHelper.createFileFromString(os.path.join(vduHelper.getHomeDirectory(), 'restart'),
"""\
#!/bin/sh
DIRECTORY=`dirname $0`
service hss restart && $DIRECTORY/log
""", True)
         vduHelper.runInShell("""\
chown {user}:{group} {homeDirectory}/log {homeDirectory}/restart
""".format(user          = vduHelper.getUser(),
           group         = vduHelper.getGroup(),
           homeDirectory = vduHelper.getHomeDirectory()))
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


   # ###### restart-hss action ##############################################
   def on_restart_hss_action(self, event):
      vduHelper.beginBlock('on_restart_hss_action')
      try:

         vduHelper.runInShell('service hss restart')

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
   main(HSSCharm)
