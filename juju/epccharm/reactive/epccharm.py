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
@when_not('epccharm.installed')
def install_epccharm_proxy_charm():
   set_flag('epccharm.installed')
   status_set('active', 'Ready!')


# ###### configure-epc function #############################################
@when('actions.configure-epc')
@when('epccharm.installed')
def configure_epc():
   err = ''
   try:
      # filename = action_get('filename')
      cmd = [ 'touch /tmp/configure-epc' ]
      result, err = charms.sshproxy._run(cmd)
   except:
      action_fail('command failed:' + err)
   else:
      action_set({'outout': result})

   clear_flag('actions.configure-epc')


# ###### restart-epc function ###############################################
@when('actions.restart-epc')
@when('epccharm.installed')
def restart_epc():
   err = ''
   try:
      # filename = action_get('filename')
      cmd = [ 'touch /tmp/restart-epc' ]
      result, err = charms.sshproxy._run(cmd)
   except:
      action_fail('command failed:' + err)
   else:
      action_set({'outout': result})

   clear_flag('actions.restart-epc')
