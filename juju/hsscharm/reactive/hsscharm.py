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

from charms.reactive import when, when_not, set_flag

from charmhelpers.core.hookenv import (
    action_get,
    action_fail,
    action_set,
    config,
    status_set,
)

from charms.reactive import (
    remove_state as remove_flag,
    set_state as set_flag,
    when, when_not
)

import charms.sshproxy

@when('actions.configure-hss')
def configure_hss():
    spgw_ip = action_get('spgw-ip')
    hss_ip = action_get('hss-ip')
    cmd1 = "sudo ip link set ens4 up && sudo dhclient ens4"
    charms.sshproxy._run(cmd1)
    cmd2= 'sudo sed -i "\'s/$hss_ip/{}/g\'" /etc/nextepc/freeDiameter/hss.conf'.format(hss_ip)
    charms.sshproxy._run(cmd2)
    cmd3= 'sudo sed -i "\'s/$spgw_ip/{}/g\'" /etc/nextepc/freeDiameter/hss.conf'.format(spgw_ip)
    charms.sshproxy._run(cmd3)
    remove_flag('actions.configure-hss')

@when('actions.restart-hss')
def restart_hss():
    cmd = "sudo systemctl restart nextepc-hssd"
    charms.sshproxy._run(cmd)
    remove_flag('actions.restart-hss')
