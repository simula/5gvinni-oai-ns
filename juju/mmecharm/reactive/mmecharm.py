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


# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('mmecharm.installed')
def install_mmecharm_proxy_charm():
   set_flag('mmecharm.installed')
   status_set('active', 'Ready!')


# ###### configure-mme function #############################################
@when('actions.configure-mme')
@when('mmecharm.installed')
def configure_mme():

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
echo "###### Preparing system ###############################################" && \\
sudo dhclient ens4 || true && \\
sudo dhclient ens5 || true && \\
sudo dhclient ens6 || true && \\
echo "###### Preparing sources ##############################################" && \\
cd /home/nornetpp/src && \\
rm -rf {gitDirectory} && \\
git clone {gitRepository} {gitDirectory} && \\
cd {gitDirectory} && \\
git checkout {gitCommit} && \\
cd scripts && \\
mkdir logs && \\
echo "###### Building MME ####################################################" && \\
./build_mme --check-installed-software --force && \\
./build_mme --clean
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
      clear_flag('actions.configure-mme')


# ###### restart-mme function ###############################################
@when('actions.restart-mme')
@when('mmecharm.installed')
def restart_mme():
   err = ''
   try:
      # filename = action_get('filename')
      cmd = [ 'touch /tmp/restart-mme' ]
      result, err = charms.sshproxy._run(cmd)
   except:
      action_fail('command failed:' + err)
   else:
      action_set({'outout': result})

   clear_flag('actions.restart-mme')
