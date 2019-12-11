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


# ###########################################################################
# #### Helper functions                                                  ####
# ###########################################################################

# ###### Write debug output to file #########################################
def writeToFile(filename, content):
   cmd = [ 'echo "{content}" >{filename}'.format(
      filename = filename,
      content  = content
   ) ]
   result, err = charms.sshproxy._run(cmd)


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
       function_fail(message.encode('utf-8'))
       status_set('active', comment + ' COMMANDS FAILED!')
   except:
       exc_type, exc_value, exc_traceback = sys.exc_info()
       err = traceback.format_exception(exc_type, exc_value, exc_traceback)
       function_fail('Command execution failed: ' + str(err))
       status_set('active', comment + ' FAILED!')
   else:
      if successFlagToSet != None:
         set_flag(successFlagToSet)
      # function_set( { 'output': stdout.encode('utf-8') } )
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
@when_not('hsscharm.installed')
def install_hsscharm_proxy_charm():
   set_flag('hsscharm.installed')
   status_set('active', 'install_hsscharm_proxy_charm: SSH proxy charm is READY')


# ###### prepare-cassandra-hss-build function ###############################
@when('actions.prepare-cassandra-hss-build')
@when('hsscharm.installed')
@when_not('hsscharm.prepared-cassandra-hss-build')
def prepare_cassandra_hss_build():

   # ====== Install Cassandra and the HSS ===================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn/wiki/OpenAirSoftwareSupport#install-hss

   gitRepository = function_get('hss-git-repository')
   gitCommit     = function_get('hss-git-commit')
   gitDirectory  = 'openair-cn'

   # Prepare network configuration:
   hssS6a_IfName    = 'ens4'
   configurationS6a = configureInterface(hssS6a_IfName, IPv4Interface('0.0.0.0/0'))

   # NOTE:
   # Double escaping is required for \ and " in "command" string!
   # 1. Python
   # 2. bash -c "<command>"
   # That is: $ => \$ ; \ => \\ ; " => \\\"

   commands = """\
echo \\\"###### Preparing system ###############################################\\\" && \\
echo -e \\\"{configurationS6a}\\\" | sudo tee /etc/network/interfaces.d/61-{hssS6a_IfName} && sudo ifup {hssS6a_IfName} || true && \\
if [ \\\"`find /etc/apt/sources.list.d -name 'rmescandon-ubuntu-yq-*.list'`\\\" == \\\"\\\" ] ; then sudo add-apt-repository -y ppa:rmescandon/yq ; fi && \\
DEBIAN_FRONTEND=noninteractive sudo apt install -y -o Dpkg::Options::=--force-confold -o Dpkg::Options::=--force-confdef --no-install-recommends yq && \\
echo \\\"###### Preparing sources ##############################################\\\" && \\
cd /home/nornetpp/src && \\
if [ ! -d \\\"{gitDirectory}\\\" ] ; then git clone --quiet {gitRepository} {gitDirectory} && cd {gitDirectory} ; else cd {gitDirectory} && git pull ; fi && \\
git checkout {gitCommit} && \\
cd scripts && \\
echo \\\"###### Done! ##########################################################\\\"""".format(
      gitRepository    = gitRepository,
      gitDirectory     = gitDirectory,
      gitCommit        = gitCommit,
      hssS6a_IfName    = hssS6a_IfName,
      configurationS6a = configurationS6a
   )

   runShellCommands(commands, 'prepare_cassandra_hss_build: preparing Cassandra/HSS build',
                    'actions.prepare-cassandra-hss-build', 'hsscharm.prepared-cassandra-hss-build')


# ###### configure-cassandra function #######################################
@when('actions.configure-cassandra')
@when('hsscharm.prepared-cassandra-hss-build')
def configure_cassandra():

   # ====== Install Cassandra and the HSS ===================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn/wiki/OpenAirSoftwareSupport#install-hss

   gitDirectory      = 'openair-cn'
   cassandraServerIP = function_get('cassandra-server-ip')

   # NOTE:
   # Double escaping is required for \ and " in "command" string!
   # 1. Python
   # 2. bash -c "<command>"
   # That is: $ => \$ ; \ => \\ ; " => \\\"

   commands = """\
echo \\\"###### Building Cassandra #############################################\\\" && \\
export MAKEFLAGS=\\\"-j`nproc`\\\" && \\
cd /home/nornetpp/src && \\
cd {gitDirectory} && \\
cd scripts && \\
mkdir -p logs && \\
sudo rm -f /etc/apt/sources.list.d/cassandra.sources.list && \\
./build_cassandra --check-installed-software --force >logs/build_cassandra.log 2>&1 && \\
sudo update-alternatives --set java /usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java && \\
sudo service cassandra stop && \\
sudo rm -rf /var/lib/cassandra/data/system/* && \\
sudo rm -rf /var/lib/cassandra/commitlog/* && \\
sudo rm -rf /var/lib/cassandra/data/system_traces/* && \\
sudo rm -rf /var/lib/cassandra/saved_caches/* && \\
sudo yq w -i /etc/cassandra/cassandra.yaml \\\"cluster_name\\\" \\\"HSS Cluster\\\" && \\
sudo yq w -i /etc/cassandra/cassandra.yaml \\\"seed_provider[0].class_name\\\" \\\"org.apache.cassandra.locator.SimpleSeedProvider\\\" && \\
sudo yq w -i /etc/cassandra/cassandra.yaml \\\"seed_provider[0].parameters[0].seeds\\\" \\\"{cassandraServerIP}\\\" && \\
sudo yq w -i /etc/cassandra/cassandra.yaml \\\"listen_address\\\" \\\"{cassandraServerIP}\\\" && \\
sudo yq w -i /etc/cassandra/cassandra.yaml \\\"rpc_address\\\" \\\"{cassandraServerIP}\\\" && \\
sudo yq w -i /etc/cassandra/cassandra.yaml \\\"endpoint_snitch\\\" \\\"GossipingPropertyFileSnitch\\\" && \\
sudo service cassandra start && \\
sleep 10 && \\
sudo service cassandra status | cat && \\
echo \\\"###### Done! ##########################################################\\\"""".format(
      gitDirectory      = gitDirectory,
      cassandraServerIP = cassandraServerIP
   )

   runShellCommands(commands, 'configure_cassandra: configuring Cassandra',
                    'actions.configure-cassandra', 'hsscharm.configured-cassandra')


# ###### configure-hss function #############################################
@when('actions.configure-hss')
@when('hsscharm.configured-cassandra')
def configure_hss():

   # ====== Install Cassandra and the HSS ===================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn/wiki/OpenAirSoftwareSupport#install-hss

   gitDirectory       = 'openair-cn'
   cassandraServerIP  = function_get('cassandra-server-ip')
   networkRealm       = function_get('network-realm')
   networkLTE_K       = function_get('network-lte-k')
   networkOP_K        = function_get('network-op-k')
   networkIMSIFirst   = function_get('network-imsi-first')
   networkMSISDNFirst = function_get('network-msisdn-first')
   networkUsers       = int(function_get('network-users'))

   # NOTE:
   # Double escaping is required for \ and " in "command" string!
   # 1. Python
   # 2. bash -c "<command>"
   # That is: $ => \$ ; \ => \\ ; " => \\\"

   commands = """\
echo \\\"###### Building HSS ###################################################\\\" && \\
export MAKEFLAGS=\\\"-j`nproc`\\\" && \\
cd /home/nornetpp/src && \\
cd {gitDirectory} && \\
cd scripts && \\
mkdir -p logs && \\
echo \\\"====== Building dependencies ... ======\\\" && \\
./build_hss_rel14 --check-installed-software --force >logs/build_hss_rel14-1.log 2>&1 && \\
echo \\\"====== Building service ... ======\\\" && \\
./build_hss_rel14 --clean >logs/build_hss_rel14-2.log 2>&1 && \\
cqlsh --file ../src/hss_rel14/db/oai_db.cql {cassandraServerIP} >logs/oai_db.log 2>&1 && \\
echo \\\"====== Provisioning users ... ======\\\" && \\
./data_provisioning_users --apn default.{networkRealm} --apn2 internet.{networkRealm} --key {networkLTE_K} --imsi-first {networkIMSIFirst} --msisdn-first {networkMSISDNFirst} --mme-identity mme.{networkRealm} --no-of-users {networkUsers} --realm {networkRealm} --truncate True  --verbose True --cassandra-cluster {cassandraServerIP} >logs/data_provisioning_users.log 2>&1 && \\
echo \\\"====== Provisioning MME ... ======\\\" && \\
./data_provisioning_mme --id 3 --mme-identity mme.{networkRealm} --realm {networkRealm} --ue-reachability 1 --truncate True  --verbose True -C {cassandraServerIP} >logs/data_provisioning_mme.log 2>&1 && \\
echo \\\"###### Creating HSS configuration files ###############################\\\" && \\
echo "127.0.1.1        hss.{networkRealm} hss" | sudo tee -a /etc/hosts && \\
openssl rand -out \$HOME/.rnd 128 && \\
echo \\\"====== Configuring Diameter ... ======\\\" && \\
PREFIX='/usr/local/etc/oai' && \\
sudo mkdir -m 0777 -p \$PREFIX && \\
sudo mkdir -m 0777 -p \$PREFIX/freeDiameter && \\
sudo cp ../etc/acl.conf ../etc/hss_rel14_fd.conf \$PREFIX/freeDiameter && \\
sudo cp ../etc/hss_rel14.conf ../etc/hss_rel14.json \$PREFIX && \\
sudo sed -i -e 's/#ListenOn/ListenOn/g' \$PREFIX/freeDiameter/hss_rel14_fd.conf && \\
echo \\\"====== Updating configuration files ... ======\\\" && \\
declare -A HSS_CONF && \\
HSS_CONF[@PREFIX@]=\$PREFIX && \\
HSS_CONF[@REALM@]='{networkRealm}' && \\
HSS_CONF[@HSS_FQDN@]='hss.{networkRealm}' && \\
HSS_CONF[@cassandra_Server_IP@]='{cassandraServerIP}' && \\
HSS_CONF[@cassandra_IP@]='{cassandraServerIP}' && \\
HSS_CONF[@OP_KEY@]='{networkOP_K}' && \\
HSS_CONF[@ROAMING_ALLOWED@]='true' && \\
for K in \\\"\${{!HSS_CONF[@]}}\\\"; do echo \\\"K=\$K ...\\\" && sudo egrep -lRZ \\\"\$K\\\" \$PREFIX | xargs -0 -l sudo sed -i -e \\\"s|\$K|\${{HSS_CONF[\$K]}}|g\\\" ; done && \\
../src/hss_rel14/bin/make_certs.sh hss {networkRealm} \$PREFIX && \\
echo \\\"====== Updating key ... ======\\\" && \\
oai_hss -j \$PREFIX/hss_rel14.json --onlyloadkey >logs/onlyloadkey.log 2>&1 && \\
echo \\\"====== Preparing SystemD Unit ... ======\\\" && \\
echo \\\"A\\\" >/tmp/A.txt && \\
echo \\\"B\\\" | tee /tmp/B.txt && \\
echo \\\"C\\\" | sudo tee /tmp/C.txt && \\
( echo \\\"[Unit]\\\" && \\
echo \\\"Description=Home Subscriber Server (HSS)\\\" && \\
echo \\\"After=ssh.target\\\" && \\
echo \\\"\\\" && \\
echo \\\"[Service]\\\" && \\
echo \\\"ExecStart=/usr/local/bin/oai_hss -j /usr/local/etc/oai/hss_rel14.json\\\" && \\
echo \\\"KillMode=process\\\" && \\
echo \\\"Restart=on-failure\\\" && \\
echo \\\"RestartPreventExitStatus=255\\\" && \\
echo \\\"WorkingDirectory=/home/nornetpp/src/openair-cn/scripts\\\" && \\
echo \\\"StandardOutput=file:/var/log/hss.log\\\" && \\
echo \\\"StandardError=inherit\\\" && \\
echo \\\"\\\" && \\
echo \\\"[Install]\\\" && \\
echo \\\"WantedBy=multi-user.target\\\" ) | sudo tee /lib/systemd/system/hss.service && \\
sudo systemctl daemon-reload \\
echo \\\"###### Done! ##########################################################\\\"""".format(
      gitDirectory       = gitDirectory,
      cassandraServerIP  = cassandraServerIP,
      networkRealm       = networkRealm,
      networkLTE_K       = networkLTE_K,
      networkOP_K        = networkOP_K,
      networkIMSIFirst   = networkIMSIFirst,
      networkMSISDNFirst = networkMSISDNFirst,
      networkUsers       = networkUsers
   )

   runShellCommands(commands, 'configure_hss: configuring HSS',
                    'actions.configure-hss', 'hsscharm.configured-hss')


# ###### restart-hss function ###############################################
@when('actions.restart-hss')
@when('hsscharm.configured-hss')
def restart_hss():
   commands = 'sudo service hss restart'
   runShellCommands(commands, 'restart_hss: restarting HSS', 'actions.restart-hss')


# FIXME!
@when('actions.touch')
def touch():
   gitDirectory      = 'openair-cn'
   cassandraServerIP = function_get('cassandra-server-ip')

   status_set('active', 'configure-cassandra: configuring Cassandra ...')

   err = ''
   try:
       filename = '/tmp/x0'
       cmd = [ 'echo "{cassandraServerIP}" >{filename}'.format(
          filename          = filename,
          cassandraServerIP = cassandraServerIP
       ) ]
       result, err = charms.sshproxy._run(cmd)
   except:
       function_fail('command failed:' + err)
   else:
       function_set({'outout': result})
   finally:
       clear_flag('actions.touch')
# FIXME!
