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

SET(VALIDATE_DESCRIPTOR_SCRIPT "../devops/descriptor-packages/tools/validate_descriptor.py")
SET(GENERATE_DESCRIPTOR_SCRIPT "../devops/descriptor-packages/tools/generate_descriptor_pkg.sh")

SET(VNFD_LIST SimulaMet-OAI-EPC_vnfd)
SET(NSD_LIST  SimulaMet-OAI-EPC_nsd)

# Automatically obtain list of charms:
SET(CHARMS_SOURCE_DIRECTORY "juju/")
SET(CHARMS_BUILD_DIRECTORY  ".build/")
EXECUTE_PROCESS(COMMAND git ls-files
                COMMAND cut -d/ -f1
                COMMAND sort -u
                COMMAND tr "\n" ";"
                WORKING_DIRECTORY ${CHARMS_SOURCE_DIRECTORY}
                OUTPUT_VARIABLE CHARM_SOURCE_LIST OUTPUT_STRIP_TRAILING_WHITESPACE)


#############################################################################
# REQUIREMENTS
#############################################################################

FIND_PROGRAM(YAMLLINT yamllint)
IF(NOT YAMLLINT)
   MESSAGE(FATAL_ERROR "yamllint (Ubuntu/Debian: yamllint) not found!")
ENDIF()

FIND_PROGRAM(VALIDATE_DESCRIPTOR ${VALIDATE_DESCRIPTOR_SCRIPT})
IF(NOT VALIDATE_DESCRIPTOR)
   MESSAGE(FATAL_ERROR "validate_descriptor.py (${VALIDATE_DESCRIPTOR_SCRIPT}) not found!")
ENDIF()

FIND_PROGRAM(GENERATE_DESCRIPTOR ${GENERATE_DESCRIPTOR_SCRIPT})
IF(NOT GENERATE_DESCRIPTOR)
   MESSAGE(FATAL_ERROR "validate_descriptor.py (${GENERATE_DESCRIPTOR_SCRIPT}) not found!")
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


# ###### Generate Juju Charms ###############################################
FILE(MAKE_DIRECTORY ${CHARMS_BUILD_DIRECTORY})
FOREACH(charmName IN LISTS CHARM_SOURCE_LIST)
   IF(NOT ${charmName} STREQUAL "")
      GET_FILENAME_COMPONENT(charmInputDirectory  ${CHARMS_SOURCE_DIRECTORY}/${charmName} ABSOLUTE)
      GET_FILENAME_COMPONENT(charmBuildDirectory  ${CHARMS_BUILD_DIRECTORY}               ABSOLUTE)
      GET_FILENAME_COMPONENT(charmOutputDirectory ${charmBuildDirectory}/${charmName}     ABSOLUTE)
      EXECUTE_PROCESS(COMMAND git ls-files ${charmInputDirectory}
                      COMMAND tr " \n" ";;"
                      OUTPUT_VARIABLE charmInputFiles OUTPUT_STRIP_TRAILING_WHITESPACE)

      makeUniqueTarget(generate_charm "generate_${charmName}")
      SET(timestampFile ${charmOutputDirectory}/version)
      ADD_CUSTOM_COMMAND(OUTPUT  ${timestampFile}
                         COMMAND charm build --build-dir ${charmBuildDirectory}
                         WORKING_DIRECTORY ${charmInputDirectory}
                         DEPENDS ${charmInputFiles})
      ADD_CUSTOM_TARGET(${generate_charm} DEPENDS ${timestampFile})
   ENDIF()
ENDFOREACH()


# ###### Validate YAML ######################################################
EXECUTE_PROCESS(COMMAND git ls-files ${vnfd}
                COMMAND grep -E ".yaml$"
                COMMAND tr " \n" ";;"
                OUTPUT_VARIABLE yamlFiles OUTPUT_STRIP_TRAILING_WHITESPACE)
SET(allYAMLs "")
FOREACH(yamlFile IN LISTS yamlFiles)
   IF(NOT ${yamlFile} STREQUAL "")
      makeUniqueTarget(validate_yaml "validate_${yamlFile}")

      SET(timestampFile ".${validate_yaml}.stamp")
      ADD_CUSTOM_COMMAND(OUTPUT ${timestampFile}
                         COMMAND yamllint -d '{extends: default, rules: {document-start: {present: no}}}' ${yamlFile}
                         COMMAND touch ${timestampFile}
                         DEPENDS ${yamlFile})
      ADD_CUSTOM_TARGET(${validate_yaml} DEPENDS ${timestampFile})

      LIST(APPEND allYAMLs ${validate_yaml})
   ENDIF()
ENDFOREACH()


# ###### Generate VNFDs #####################################################
SET(allVNFDs "")
FOREACH(vnfd IN LISTS VNFD_LIST)
   EXECUTE_PROCESS(COMMAND git ls-files ${vnfd}
                   COMMAND tr " \n" ";;"
                   OUTPUT_VARIABLE vnfdFiles OUTPUT_STRIP_TRAILING_WHITESPACE)

   # ====== Copy the built Juju Charms ======================================
   SET(allCharmsInVNFD "")
   FOREACH(charmName IN LISTS CHARM_SOURCE_LIST)
      IF(NOT ${charmName} STREQUAL "")
         makeUniqueTarget(generate_charm      "generate_${charmName}")
         makeUniqueTarget(generate_vnfd_charm "generate_${vnfd}_${charmName}")
         GET_FILENAME_COMPONENT(charmOutputDirectory ${CHARMS_BUILD_DIRECTORY}/${charmName} ABSOLUTE)
         GET_FILENAME_COMPONENT(charmCopyDirectory   ${vnfd}/charms/${charmName}            ABSOLUTE)
         ADD_CUSTOM_COMMAND(OUTPUT  ${charmCopyDirectory}/version
                            COMMAND rm -rf ${charmCopyDirectory}
                            COMMAND cp -a ${charmOutputDirectory} ${charmCopyDirectory}
                            DEPENDS ${charmOutputDirectory}/version)
         ADD_CUSTOM_TARGET(${generate_vnfd_charm} DEPENDS ${charmCopyDirectory}/version ${allYAMLs} ${generate_charm})
         LIST(APPEND allCharmsInVNFD ${generate_vnfd_charm})
      ENDIF()
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
                     DEPENDS ${vnfdPackage} ${allYAMLs} ${allCharmsInVNFD})

   LIST(APPEND allVNFDs ${generate_vnfdPackage})
ENDFOREACH()


# ###### Generate NSDs ######################################################
FOREACH(nsd IN LISTS NSD_LIST)
   EXECUTE_PROCESS(COMMAND git ls-files ${nsd}
                   COMMAND tr " \n" ";;"
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
