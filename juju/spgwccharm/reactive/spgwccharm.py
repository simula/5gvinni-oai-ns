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
      return -1
   else:
      action_set({ 'outout': result} )
      return result

# ###### Installation #######################################################
@when('sshproxy.configured')
@when_not('spgwccharm.installed')
def install_spgwccharm_proxy_charm():
   set_flag('spgwccharm.installed')
   status_set('active', 'Ready!')


# ###### configure-spgwc function ###########################################
@when('actions.configure-spgwc')
@when('spgwccharm.installed')
def configure_spgwc():
   commands = """\
sudo dhclient ens4 || true && \\
sudo dhclient ens5 || true
"""
   if execute(commands) == 0:
      clear_flag('actions.configure-spgwc')


# ###### restart-spgwc function #############################################
@when('actions.restart-spgwc')
@when('spgwccharm.installed')
def restart_spgwc():
   commands = 'touch /tmp/restart-spgwc'
   if execute(commands) == 0:
      clear_flag('actions.restart-spgwc')
