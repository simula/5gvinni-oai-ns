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

# Installed scripts:
SET(VALIDATE_DESCRIPTOR_SCRIPT "/usr/share/osm-devops/descriptor-packages/tools/validate_descriptor.py")
SET(GENERATE_DESCRIPTOR_SCRIPT "/usr/share/osm-devops/descriptor-packages/tools/generate_descriptor_pkg.sh")
# Local scripts (NOTE: make sure to use scripts compatible with the current OSM setup!):
# SET(VALIDATE_DESCRIPTOR_SCRIPT "devops/descriptor-packages/tools/validate_descriptor.py")
# SET(GENERATE_DESCRIPTOR_SCRIPT "devops/descriptor-packages/tools/generate_descriptor_pkg.sh")

# Automatically obtain list of VNFDs:
EXECUTE_PROCESS(COMMAND git ls-files
                COMMAND cut -d/ -f1
                COMMAND sort -u
                COMMAND grep "vnfd$"
                COMMAND tr "\n" ";"
                COMMAND sed -e "s/;$//g"
                OUTPUT_VARIABLE VNFD_LIST OUTPUT_STRIP_TRAILING_WHITESPACE)
MESSAGE("VNFDs: ${VNFD_LIST}")

# Automatically obtain list of NSDs:
EXECUTE_PROCESS(COMMAND git ls-files
                COMMAND cut -d/ -f1
                COMMAND sort -u
                COMMAND grep "nsd$"
                COMMAND tr "\n" ";"
                COMMAND sed -e "s/;$//g"
                OUTPUT_VARIABLE NSD_LIST OUTPUT_STRIP_TRAILING_WHITESPACE)
MESSAGE("NSDs: ${NSD_LIST}")

# Automatically obtain list of charms:
SET(CHARMS_SOURCE_DIRECTORY "juju/")
SET(CHARMS_BUILD_DIRECTORY  ".build/")
EXECUTE_PROCESS(COMMAND git ls-files
                COMMAND cut -d/ -f1
                COMMAND sort -u
                COMMAND tr "\n" ";"
                COMMAND sed -e "s/;$//g"
                WORKING_DIRECTORY ${CHARMS_SOURCE_DIRECTORY}
                OUTPUT_VARIABLE CHARM_SOURCE_LIST OUTPUT_STRIP_TRAILING_WHITESPACE)
MESSAGE("Charms: ${CHARM_SOURCE_LIST}")


#############################################################################
# REQUIREMENTS
#############################################################################

FIND_PROGRAM(CHARM charm)
IF(NOT CHARM)
   MESSAGE(FATAL_ERROR "charm (Ubuntu/Debian: sudo snap install charm --classic) not found!")
ENDIF()

FIND_PROGRAM(YAMLLINT yamllint)
IF(NOT YAMLLINT)
   MESSAGE(FATAL_ERROR "yamllint (Ubuntu/Debian: yamllint) not found!")
ENDIF()

FIND_PROGRAM(VALIDATE_DESCRIPTOR ${VALIDATE_DESCRIPTOR_SCRIPT})
IF(NOT VALIDATE_DESCRIPTOR)
   MESSAGE(FATAL_ERROR "validate_descriptor.py (Ubuntu: osm-devops python-osm-im) not found!")
ENDIF()

FIND_PROGRAM(GENERATE_DESCRIPTOR ${GENERATE_DESCRIPTOR_SCRIPT})
IF(NOT GENERATE_DESCRIPTOR)
   MESSAGE(FATAL_ERROR "validate_descriptor.py (Ubuntu: osm-devops python-osm-im) not found!")
ENDIF()


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


# ###### Validate YAML ######################################################
EXECUTE_PROCESS(COMMAND git ls-files ${vnfd}
                COMMAND grep -E ".yaml$"
                COMMAND tr "\n" ";"
                COMMAND sed -e "s/;$//g"
                OUTPUT_VARIABLE yamlFiles OUTPUT_STRIP_TRAILING_WHITESPACE)
SET(allYAMLs "")
FOREACH(yamlFile IN LISTS yamlFiles)
   makeUniqueTarget(validate_yaml "validate_${yamlFile}")

   SET(timestampFile ".${validate_yaml}.stamp")
   ADD_CUSTOM_COMMAND(OUTPUT ${timestampFile}
                      # COMMAND ${YAMLLINT} -d '{extends: default, rules: {document-start: {present: no}, line-length: {max: 80, allow-non-breakable-words: true, allow-non-breakable-inline-mappings: true}}}' ${yamlFile}
                      COMMAND ${YAMLLINT} -d '{extends: default, rules: {document-start: {present: no}, line-length: {max: 4096}, comments-indentation: disable}}' ${yamlFile}
                      COMMAND touch ${timestampFile}
                      DEPENDS ${yamlFile})
   ADD_CUSTOM_TARGET(${validate_yaml} DEPENDS ${timestampFile})

   LIST(APPEND allYAMLs ${validate_yaml})
ENDFOREACH()


# ###### Generate Juju Charms ###############################################
FILE(MAKE_DIRECTORY ${CHARMS_BUILD_DIRECTORY})
FOREACH(charmName IN LISTS CHARM_SOURCE_LIST)
   GET_FILENAME_COMPONENT(charmInputDirectory  ${CHARMS_SOURCE_DIRECTORY}/${charmName} ABSOLUTE)
   GET_FILENAME_COMPONENT(charmBuildDirectory  ${CHARMS_BUILD_DIRECTORY}               ABSOLUTE)
   GET_FILENAME_COMPONENT(charmOutputDirectory ${charmBuildDirectory}/${charmName}     ABSOLUTE)
   EXECUTE_PROCESS(COMMAND git ls-files ${charmInputDirectory}
                   COMMAND tr "\n" ";"
                   COMMAND sed -e "s/;$//g"
                   OUTPUT_VARIABLE charmInputFiles OUTPUT_STRIP_TRAILING_WHITESPACE)

   makeUniqueTarget(generate_charm "generate_${charmName}")
   SET(timestampFile "${charmOutputDirectory}.stamp")
   ADD_CUSTOM_COMMAND(OUTPUT  ${timestampFile}
                      COMMAND rm -rf ${charmOutputDirectory}
                      COMMAND ${CHARM} build --build-dir ${charmBuildDirectory}
                      # FIXME!
                      # COMMAND sed -e "s#^import shlex#import shlex\\\\nimport traceback#g" -i ${charmOutputDirectory}/lib/charms/sshproxy.py
                      COMMAND touch ${timestampFile}
                      WORKING_DIRECTORY ${charmInputDirectory}
                      DEPENDS ${charmInputFiles})
   ADD_CUSTOM_TARGET(${generate_charm} DEPENDS ${timestampFile})
ENDFOREACH()


# ###### Generate VNFDs #####################################################
SET(allVNFDs "")
FOREACH(vnfd IN LISTS VNFD_LIST)
   EXECUTE_PROCESS(COMMAND git ls-files ${vnfd}
                   COMMAND tr "\n" ";"
                   COMMAND sed -e "s/;$//g"
                   OUTPUT_VARIABLE vnfdFiles OUTPUT_STRIP_TRAILING_WHITESPACE)

   # ====== Copy the built Juju Charms ======================================
   SET(allCharmsInVNFD "")
   FOREACH(charmName IN LISTS CHARM_SOURCE_LIST)
      makeUniqueTarget(generate_charm      "generate_${charmName}")
      makeUniqueTarget(generate_vnfd_charm "generate_${vnfd}_${charmName}")
      GET_FILENAME_COMPONENT(charmOutputDirectory ${CHARMS_BUILD_DIRECTORY}/${charmName} ABSOLUTE)
      GET_FILENAME_COMPONENT(charmCopyDirectory   ${vnfd}/charms/${charmName}            ABSOLUTE)
      ADD_CUSTOM_COMMAND(OUTPUT  ${charmCopyDirectory}/version
                         COMMAND rm -rf ${charmCopyDirectory}
                         COMMAND mkdir -p ${charmCopyDirectory}
                         COMMAND cp -a ${charmOutputDirectory}/* ${charmCopyDirectory}/
                         DEPENDS ${charmOutputDirectory}/version)
      ADD_CUSTOM_TARGET(${generate_vnfd_charm} DEPENDS ${charmCopyDirectory}/version ${allYAMLs} ${generate_charm})
      LIST(APPEND allCharmsInVNFD ${generate_vnfd_charm})
   ENDFOREACH()

   # ====== Validate cloud-init YAML files ==================================
   EXECUTE_PROCESS(COMMAND git ls-files ${vnfd}/cloud_init
                   COMMAND grep -E -- "-init$"
                   COMMAND tr "\n" ";"
                   COMMAND sed -e "s/;$//g"
                   OUTPUT_VARIABLE vnfdCloudInitFiles OUTPUT_STRIP_TRAILING_WHITESPACE)
   MESSAGE("COMMAND git ls-files ${vnfd}/cloud-init: Cloud-Init: ${vnfdCloudInitFiles}")

   SET(allVNFDCloudInitFiles "")
   FOREACH(vnfdCloudInitFile IN LISTS vnfdCloudInitFiles)
      makeUniqueTarget(validate_cloudinit "validate_${vnfdCloudInitFile}")

      SET(timestampFile ".${validate_cloudinit}.stamp")
      ADD_CUSTOM_COMMAND(OUTPUT ${timestampFile}
                         COMMAND ${YAMLLINT} -d '{extends: relaxed, rules: {document-start: {present: no}}}' ${vnfdCloudInitFile}
                         COMMAND touch ${timestampFile}
                         DEPENDS ${vnfdCloudInitFile})
      ADD_CUSTOM_TARGET(${validate_cloudinit} DEPENDS ${timestampFile})

      LIST(APPEND allVNFDCloudInitFiles ${validate_cloudinit})
   ENDFOREACH()

   # ====== Generate the VNFD ===============================================
   SET(vnfdDefinition "${vnfd}/${vnfd}.yaml")
   SET(vnfdPackage    "${vnfd}.tar.gz")
   makeUniqueTarget(generate_vnfdPackage "generate_${vnfdPackage}")

   ADD_CUSTOM_COMMAND(OUTPUT  ${vnfdPackage}
                      COMMAND ${VALIDATE_DESCRIPTOR} ${vnfdDefinition}
                      COMMAND ${GENERATE_DESCRIPTOR} -t vnfd -N ${vnfd}/
                      COMMAND du -k ${vnfdPackage}
                      DEPENDS ${vnfdFiles})
   ADD_CUSTOM_TARGET(${generate_vnfdPackage}
                     DEPENDS ${vnfdPackage} ${allYAMLs} ${allVNFDCloudInitFiles} ${allCharmsInVNFD})

   LIST(APPEND allVNFDs ${generate_vnfdPackage})
ENDFOREACH()


# ###### Generate NSDs ######################################################
FOREACH(nsd IN LISTS NSD_LIST)
   EXECUTE_PROCESS(COMMAND git ls-files ${nsd}
                   COMMAND tr "\n" ";"
                   COMMAND sed -e "s/;$//g"
                   OUTPUT_VARIABLE nsdFiles OUTPUT_STRIP_TRAILING_WHITESPACE)

   # ====== Generate the NSD ================================================
   SET(nsdDefinition "${nsd}/${nsd}.yaml")
   SET(nsdPackage    "${nsd}.tar.gz")
   makeUniqueTarget(generate_nsdPackage "generate_${nsdPackage}")

   ADD_CUSTOM_COMMAND(OUTPUT  ${nsdPackage}
                      COMMAND ${VALIDATE_DESCRIPTOR} ${nsdDefinition}
                      COMMAND ${GENERATE_DESCRIPTOR} -t nsd -N ${nsd}/
                      COMMAND du -k ${nsdPackage}
                      DEPENDS ${nsdFiles})
   ADD_CUSTOM_TARGET(${generate_nsdPackage}
                     ALL DEPENDS ${nsdPackage} ${allYAMLs} ${allVNFDs})
ENDFOREACH()
