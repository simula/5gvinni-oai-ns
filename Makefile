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
# SimulaMet OpenAirInterface Evolved Packet Core VNF and NS
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


# ====== Requirements  ======================================================
# curl "https://osm-download.etsi.org/repository/osm/debian/ReleaseSIX/OSM%20ETSI%20Release%20Key.gpg" | sudo apt-key add -
# sudo apt-get update
# sudo add-apt-repository -y "deb [arch=amd64] https://osm-download.etsi.org/repository/osm/debian/ReleaseSIX stable IM osmclient devops"
# sudo apt-get update
# sudo apt-get install python-osm-im
# sudo -H pip install pyangbind
# ===========================================================================

# NOTE: Clone https://osm.etsi.org/gerrit/osm/devops.git to .., or update the following definitions:
VALIDATE_DESCRIPTOR = ../devops/descriptor-packages/tools/validate_descriptor.py
GENERATE_DESCRIPTOR = ../devops/descriptor-packages/tools/generate_descriptor_pkg.sh


all:	SimulaMet-OAI-EPC_vnfd.tar.gz SimulaMet-OAI-EPC_nsd.tar.gz


SimulaMet-OAI-EPC_vnfd.tar.gz:
	$(VALIDATE_DESCRIPTOR) SimulaMet-OAI-EPC_vnfd/SimulaMet-OAI-EPC_vnfd.yaml
	$(GENERATE_DESCRIPTOR) -t vnfd -N SimulaMet-OAI-EPC_vnfd/

SimulaMet-OAI-EPC_nsd.tar.gz:
	$(VALIDATE_DESCRIPTOR) SimulaMet-OAI-EPC_nsd/SimulaMet-OAI-EPC_nsd.yaml
	$(GENERATE_DESCRIPTOR) -t nsd -N SimulaMet-OAI-EPC_nsd/


clean:
	rm -f *.tar.gz
