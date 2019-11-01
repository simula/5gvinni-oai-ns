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


# ###### Execute command ####################################################
def execute(commands):
   err = ''
   try:
      result, err = charms.sshproxy._run(commands)
   except:
      action_fail('command failed:' + err)
      return False
   else:
      action_set({ 'outout': result})
      return True


# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('hsscharm.installed')
def install_hsscharm_proxy_charm():
   set_flag('hsscharm.installed')
   status_set('active', 'Ready!')


# ###### configure-hss function #############################################
@when('actions.configure-hss')
@when('hsscharm.installed')
def configure_hss():

   # ====== Install Cassandra and the HSS ===================================
   # For a documentation of the installation procedure, see:
   # https://github.com/OPENAIRINTERFACE/openair-cn/wiki/OpenAirSoftwareSupport#install-hss

   gitRepository      = 'https://github.com/OPENAIRINTERFACE/openair-cn.git'
   gitDirectory       = 'openair-cn'
   gitCommit          = 'develop'
   cassandraServerIP  = '172.16.6.129'
   networkRealm       = 'simula.nornet'
   networkLTE_K       = '449c4b91aeacd0ace182cf3a5a72bfa1'
   networkOP_K        = '1006020f0a478bf6b699f15c062e42b3'
   networkIMSIFirst   = '242881234500000'
   networkMSISDNFirst = '24288880000000'
   networkUsers       = 1024

   commands = """\
echo "###### Preparing system ###############################################" && \
sudo dhclient ens4 || true && \\
sudo add-apt-repository -y ppa:rmescandon/yq && \\
DEBIAN_FRONTEND=noninteractive sudo apt install -y -o Dpkg::Options::=--force-confold -o Dpkg::Options::=--force-confdef --no-install-recommends yq && \\
echo "###### Preparing sources ##############################################" && \
cd /home/nornetpp/src && \\
rm -rf {gitDirectory} && \\
git clone {gitRepository} {gitDirectory} && \\
cd {gitDirectory} && \\
git checkout {gitCommit} && \\
cd scripts && \\
mkdir logs && \\
echo "###### Building Cassandra #############################################" && \\
./build_cassandra --check-installed-software --force && \\
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
sleep 10 && \\
sudo service cassandra status | cat && \\
echo "###### Building HSS ###################################################" && \\
./build_hss_rel14 --check-installed-software --force && \\
./build_hss_rel14 --clean && \\
cqlsh --file ../src/hss_rel14/db/oai_db.cql {cassandraServerIP} && \\
./data_provisioning_users --apn default.{networkRealm} --apn2 internet.{networkRealm} --key {networkLTE_K} --imsi-first {networkIMSIFirst} --msisdn-first {networkMSISDNFirst} --mme-identity mme.{networkRealm} --no-of-users {networkUsers} --realm {networkRealm} --truncate True  --verbose True --cassandra-cluster {cassandraServerIP} && \\
./data_provisioning_mme --id 3 --mme-identity mme.{networkRealm} --realm {networkRealm} --ue-reachability 1 --truncate True  --verbose True -C {cassandraServerIP} && \\
echo "###### Creating HSS configuration files ###############################" && \\
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
HSS_CONF[@cassandra_Server_IP@]='{cassandraServerIP}' && \\
HSS_CONF[@cassandra_IP@]='{cassandraServerIP}' && \\
HSS_CONF[@OP_KEY@]='{networkOP_K}' && \\
HSS_CONF[@ROAMING_ALLOWED@]='true' && \\
for K in "${{!HSS_CONF[@]}}"; do sudo egrep -lRZ "$K" $PREFIX | xargs -0 -l sudo sed -i -e "s|$K|${{HSS_CONF[$K]}}|g" ; done && \\
../src/hss_rel14/bin/make_certs.sh hss {networkRealm} $PREFIX && \\
echo "====== Updating key ... ======" && \\
oai_hss -j $PREFIX/hss_rel14.json --onlyloadkey
   """.format(
      gitRepository      = gitRepository,
      gitDirectory       = gitDirectory,
      gitCommit          = gitCommit,
      cassandraServerIP  = cassandraServerIP,
      networkRealm       = networkRealm,
      networkLTE_K       = networkLTE_K,
      networkOP_K        = networkOP_K,
      networkIMSIFirst   = networkIMSIFirst,
      networkMSISDNFirst = networkMSISDNFirst,
      networkUsers       = networkUsers
   )

   if execute(commands) == True:
      clear_flag('actions.configure-hss')


# ###### restart-hss function ###############################################
@when('actions.restart-hss')
@when('hsscharm.installed')
def restart_hss():
   commands = 'touch /tmp/restart-hss'
   if execute(commands) == True:
      clear_flag('actions.restart-hss')
