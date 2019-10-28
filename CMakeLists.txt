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


#############################################################################
# INITIALISE
#############################################################################

CMAKE_MINIMUM_REQUIRED(VERSION 3.0.2)
PROJECT(SimulaMet-OAI-EPC C)


#############################################################################
# OPTIONS
#############################################################################

SET(VALIDATE_DESCRIPTOR "../devops/descriptor-packages/tools/validate_descriptor.py")
SET(GENERATE_DESCRIPTOR "../devops/descriptor-packages/tools/generate_descriptor_pkg.sh")

SET(VNFD_LIST SimulaMet-OAI-EPC_vnfd)
SET(NSD_LIST  SimulaMet-OAI-EPC_nsd)

# Automatically obtain list of charms:
EXECUTE_PROCESS(COMMAND git ls-tree --name-only HEAD juju/
                COMMAND tr " \n" ";;"
                OUTPUT_VARIABLE CHARM_LIST OUTPUT_STRIP_TRAILING_WHITESPACE)


#############################################################################
# Build VNFDs
#############################################################################

# ###### Create unique target name from file name ###########################
FUNCTION(makeUniqueTarget target fileName)
   # STRING(MAKE_C_IDENTIFIER ${fileName} result)
   SET(result ${fileName})
   STRING(REGEX REPLACE "[/\\ ]" "-"  result ${result})
   STRING(REPLACE "ä" "ae" result ${result})
   STRING(REPLACE "ö" "oe" result ${result})
   STRING(REPLACE "ü" "ue" result ${result})
   STRING(REPLACE "ß" "ss" result ${result})
   STRING(REPLACE "Ä" "AE" result ${result})
   STRING(REPLACE "Ö" "OE" result ${result})
   STRING(REPLACE "Ü" "UE" result ${result})
   STRING(REPLACE "æ" "ae" result ${result})
   STRING(REPLACE "ø" "oe" result ${result})
   STRING(REPLACE "å" "aa" result ${result})
   STRING(REPLACE "Æ" "AE" result ${result})
   STRING(REPLACE "Ø" "OE" result ${result})
   STRING(REPLACE "Å" "AA" result ${result})
   STRING(REGEX REPLACE "[áàǎã]" "a" result ${result})
   STRING(REGEX REPLACE "[ÁÀǍÃ]" "A" result ${result})
   STRING(REGEX REPLACE "[éèê]"  "e" result ${result})
   STRING(REGEX REPLACE "[ÉÈÊ]"  "E" result ${result})
   STRING(REGEX REPLACE "[^a-zA-Z0-9\\.@_+-]" "_X_" result ${result})
   SET(${target} ${result} PARENT_SCOPE)
ENDFUNCTION()


SET(allCharms "")
FOREACH(charm IN LISTS CHARM_LIST)
   MESSAGE("Charm: ${charm}")


ENDFOREACH()


FOREACH(vnfd IN LISTS VNFD_LIST)
   EXECUTE_PROCESS(COMMAND git ls-tree -r --name-only HEAD ${vnfd}
                   COMMAND tr " \n" ";;"
                   OUTPUT_VARIABLE vnfdFiles OUTPUT_STRIP_TRAILING_WHITESPACE)

   SET(vnfdDefinition "${vnfd}/${vnfd}.yaml")
   SET(vnfdPackage    "${vnfd}.tar.gz")
   makeUniqueTarget(generate_vnfdPackage "generate_${vnfdPackage}")

   ADD_CUSTOM_COMMAND(OUTPUT  ${vnfdPackage}
                      COMMAND ${VALIDATE_DESCRIPTOR} ${vnfdDefinition}
                      COMMAND ${GENERATE_DESCRIPTOR} -t vnfd -N ${vnfd}/
                      COMMAND du -k ${vnfdPackage}
                      DEPENDS ${vnfdFiles})
   ADD_CUSTOM_TARGET(${generate_vnfdPackage} ALL DEPENDS ${vnfdPackage})
ENDFOREACH()


FOREACH(nsd IN LISTS NSD_LIST)
   EXECUTE_PROCESS(COMMAND git ls-tree -r --name-only HEAD ${nsd}
                   COMMAND tr " \n" ";;"
                   OUTPUT_VARIABLE nsdFiles OUTPUT_STRIP_TRAILING_WHITESPACE)

   SET(nsdDefinition "${nsd}/${nsd}.yaml")
   SET(nsdPackage    "${nsd}.tar.gz")
   makeUniqueTarget(generate_nsdPackage "generate_${nsdPackage}")

   ADD_CUSTOM_COMMAND(OUTPUT  ${nsdPackage}
                      COMMAND ${VALIDATE_DESCRIPTOR} ${nsdDefinition}
                      COMMAND ${GENERATE_DESCRIPTOR} -t nsd -N ${nsd}/
                      COMMAND du -k ${nsdPackage}
                      DEPENDS ${nsdFiles})
   ADD_CUSTOM_TARGET(${generate_nsdPackage} ALL DEPENDS ${nsdPackage})
ENDFOREACH()
