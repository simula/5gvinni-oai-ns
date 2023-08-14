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
# Copyright (C) 2019-2023 by Thomas Dreibholz
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
# DEPENDENCIES
#############################################################################

# ====== Obtain list of all NSs =============================================
EXECUTE_PROCESS(COMMAND git ls-files
                COMMAND cut -d/ -f1
                COMMAND sort -u
                COMMAND grep "nsd$"
                COMMAND tr "\n" ";"
                COMMAND sed -e "s/;$//g"
                OUTPUT_VARIABLE NSD_LIST OUTPUT_STRIP_TRAILING_WHITESPACE)
MESSAGE("NSDs: ${NSD_LIST}")


# ====== Obtain list of all VNFDs ===========================================
EXECUTE_PROCESS(COMMAND git ls-files
                COMMAND cut -d/ -f1
                COMMAND sort -u
                COMMAND grep "vnfd$"
                COMMAND tr "\n" ";"
                COMMAND sed -e "s/;$//g"
                OUTPUT_VARIABLE VNFD_LIST OUTPUT_STRIP_TRAILING_WHITESPACE)
MESSAGE("VNFDs: ${VNFD_LIST}")


# ====== Obtain list of all Charms ==========================================
SET(CHARMS_BASELAYERS_DIRECTORY "${CMAKE_SOURCE_DIR}/baselayers/")
SET(CHARMS_SOURCE_DIRECTORY     "${CMAKE_SOURCE_DIR}/juju/")
SET(CHARMS_BUILD_DIRECTORY      ".build/")
EXECUTE_PROCESS(COMMAND git ls-files
                COMMAND cut -d/ -f1
                COMMAND sort -u
                COMMAND tr "\n" ";"
                COMMAND sed -e "s/;$//g"
                WORKING_DIRECTORY ${CHARMS_SOURCE_DIRECTORY}
                OUTPUT_VARIABLE CHARM_SOURCE_LIST OUTPUT_STRIP_TRAILING_WHITESPACE)
MESSAGE("Charms: ${CHARM_SOURCE_LIST}")


# ====== Obtain Charm dependencies of each VNFD =============================
FOREACH(vnfd IN LISTS VNFD_LIST)
   EXECUTE_PROCESS(COMMAND grep "^[ ]*charm:" ${vnfd}/${vnfd}.yaml
                   COMMAND sed -e "s/charm://g" -e "s/[ \t]*//g"
                   COMMAND sort -u
                   COMMAND tr "\n" ";"
                   COMMAND sed -e "s/;$//g"
                   OUTPUT_VARIABLE ${vnfd}_charms)
   MESSAGE("Charm dependencies of VNFD ${vnfd}: ${${vnfd}_charms}")
ENDFOREACH()


# ====== Obtain VNFD dependencies of each NSD ===============================
FOREACH(nsd IN LISTS NSD_LIST)
   EXECUTE_PROCESS(COMMAND grep "^[ -]*vnfd-id:" ${nsd}/${nsd}.yaml
                   COMMAND sed -e "s/^[ -]*vnfd-id://g" -e "s/[ \t]*//g" -e "/^$/d"
                   COMMAND sort -u
                   COMMAND tr "\n" ";"
                   COMMAND sed -e "s/;$//g"
                   OUTPUT_VARIABLE ${nsd}_vnfds)
   MESSAGE("VNFD dependencies of NSD ${nsd}: ${${nsd}_vnfds}")
ENDFOREACH()


# ====== Obtain list of VDUHelper files =====================================
EXECUTE_PROCESS(COMMAND git ls-files vduhelper
                COMMAND grep -v "README$"
                COMMAND sed -e "s#^#${CMAKE_SOURCE_DIR}/#g"
                COMMAND tr "\n" ";"
                COMMAND sed -e "s/;$//g"
                OUTPUT_VARIABLE vduHelperFiles OUTPUT_STRIP_TRAILING_WHITESPACE)
MESSAGE("VDUHelper files: ${vduHelperFiles}")


#############################################################################
# REQUIREMENTS
#############################################################################

FIND_PROGRAM(CHARM charm)
IF(NOT CHARM)
   MESSAGE(FATAL_ERROR "charm (Ubuntu: sudo snap install charm --classic) not found!")
ENDIF()

FIND_PROGRAM(OSM osm)
IF(NOT OSM)
   MESSAGE(FATAL_ERROR "osm (Ubuntu: sudo snap install osmclient) not found!")
ENDIF()

FIND_PROGRAM(YAMLLINT yamllint)
IF(NOT YAMLLINT)
   MESSAGE(FATAL_ERROR "yamllint (Ubuntu: sudo apt install -y yamllint) not found!")
ENDIF()


#############################################################################
# Validate all YAML files
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


# ###### Run yamllint for each YAML file ====================================
EXECUTE_PROCESS(COMMAND git ls-files .
                COMMAND grep -E ".yaml$"
                COMMAND tr "\n" ";"
                COMMAND sed -e "s/;$//g"
                OUTPUT_VARIABLE yamlFiles OUTPUT_STRIP_TRAILING_WHITESPACE)
SET(allYAMLsChecked "")
FOREACH(yamlFile IN LISTS yamlFiles)
   makeUniqueTarget(generate_yamlCheckedTimestampFile "validate_${yamlFile}")
   SET(yamlCheckedTimestampFile ".${generate_yamlCheckedTimestampFile}.stamp")

   ADD_CUSTOM_COMMAND(OUTPUT ${yamlCheckedTimestampFile}
                      # COMMAND ${YAMLLINT} -d '{extends: default, spaces: 4, rules: {document-start: {present: no}, line-length: {max: 80, allow-non-breakable-words: true, allow-non-breakable-inline-mappings: true}}}' ${yamlFile}
                      # !!! COMMAND ${YAMLLINT} -d '{extends: default, spaces: 4, rules: {document-start: {present: no}, line-length: {max: 4096}, comments-indentation: disable}}' ${yamlFile}
                      COMMAND touch ${yamlCheckedTimestampFile}
                      DEPENDS ${yamlFile})
   ADD_CUSTOM_TARGET(${generate_yamlCheckedTimestampFile} DEPENDS ${yamlCheckedTimestampFile})

   LIST(APPEND allYAMLsChecked ${generate_yamlCheckedTimestampFile})
ENDFOREACH()



#############################################################################
# Generate Charms
#############################################################################

# ###### Generate Juju Charms ###############################################
MESSAGE("Generating charms ...")

GET_FILENAME_COMPONENT(charmsOutputDirectory ${CHARMS_BUILD_DIRECTORY} ABSOLUTE)
FILE(MAKE_DIRECTORY ${charmsOutputDirectory})

FOREACH(charmName IN LISTS CHARM_SOURCE_LIST)
   GET_FILENAME_COMPONENT(charmSourceDirectory ${CHARMS_SOURCE_DIRECTORY}/${charmName} ABSOLUTE)
   GET_FILENAME_COMPONENT(charmBuildDirectory  ${charmsOutputDirectory}/${charmName}  ABSOLUTE)
   EXECUTE_PROCESS(COMMAND git ls-files ${charmSourceDirectory}
                   COMMAND tr "\n" ";"
                   COMMAND sed -e "s/;$//g"
                   OUTPUT_VARIABLE charmInputFiles OUTPUT_STRIP_TRAILING_WHITESPACE)

   makeUniqueTarget(generate_charmBuildTimestampFile "generate_charm_${charmName}")
   SET(charmBuildTimestampFile "${charmBuildDirectory}.stamp")
   ADD_CUSTOM_COMMAND(OUTPUT  ${charmBuildTimestampFile}
                      COMMAND echo cp ${vduHelperFiles} ${charmSourceDirectory}
                      COMMAND cp ${vduHelperFiles} ${charmSourceDirectory}/reactive
                      COMMAND rm -rf ${charmBuildDirectory}
                      COMMAND pwd
                      COMMAND echo env CHARM_LAYERS_DIR=${CHARMS_BASELAYERS_DIRECTORY} ${CHARM} build --build-dir ${charmsOutputDirectory}
                      COMMAND env CHARM_LAYERS_DIR=${CHARMS_BASELAYERS_DIRECTORY} ${CHARM} build --build-dir ${charmsOutputDirectory}
                      COMMAND touch ${charmBuildTimestampFile}
                      WORKING_DIRECTORY ${charmSourceDirectory}
                      DEPENDS ${charmInputFiles} ${vduHelperFiles} ${allYAMLsChecked})
   ADD_CUSTOM_TARGET(${generate_charmBuildTimestampFile} DEPENDS ${charmBuildTimestampFile})

   MESSAGE("Charm to build: ${charmName}")
ENDFOREACH()



#############################################################################
# Generate VNFDs
#############################################################################

# ###### Generate VNFDs #####################################################
MESSAGE("Generating VNFDs ...")
FOREACH(vnfd IN LISTS VNFD_LIST)
   EXECUTE_PROCESS(COMMAND git ls-files ${vnfd}
                   COMMAND tr "\n" ";"
                   COMMAND sed -e "s/;$//g"
                   OUTPUT_VARIABLE vnfdFiles OUTPUT_STRIP_TRAILING_WHITESPACE)

   # ====== Copy the built Juju Charms ======================================
   SET(allCharmsCopyedIntoVNFD "")
   FOREACH(charmName IN LISTS ${vnfd}_charms)
      GET_FILENAME_COMPONENT(charmBuildDirectory ${CHARMS_BUILD_DIRECTORY}/${charmName}   ABSOLUTE)
      GET_FILENAME_COMPONENT(charmCharmsInVNFDirectory ${vnfd}/charms                     ABSOLUTE)
      GET_FILENAME_COMPONENT(charmCopyDirectory ${charmCharmsInVNFDirectory}/${charmName} ABSOLUTE)

      makeUniqueTarget(generate_charmBuildTimestampFile "generate_charm_${charmName}")
      SET(charmBuildTimestampFile "${charmBuildDirectory}.stamp")
      makeUniqueTarget(generate_charmCopiedTimestampFile "generate_charm-in-vnfd-${vnfd}_${charmName}")
      SET(charmCopiedTimestampFile "${charmBuildDirectory}-in-vnfd-${vnfd}.stamp")

      ADD_CUSTOM_COMMAND(OUTPUT  ${charmCopiedTimestampFile}
                         COMMAND mkdir -p ${charmCharmsInVNFDirectory}
                         COMMAND rm -rf ${charmCopyDirectory}
                         COMMAND cp -a ${charmBuildDirectory} ${charmCopyDirectory}
                         COMMAND touch ${charmCopiedTimestampFile}
                         DEPENDS ${generate_charmBuildTimestampFile} ${charmBuildTimestampFile})
      ADD_CUSTOM_TARGET(${generate_charmCopiedTimestampFile} DEPENDS ${charmCopiedTimestampFile})
      LIST(APPEND allCharmsCopyedIntoVNFD ${generate_charmCopiedTimestampFile} ${charmCopiedTimestampFile})
   ENDFOREACH()

   # ====== Validate cloud-init YAML files ==================================
   EXECUTE_PROCESS(COMMAND git ls-files ${vnfd}/cloud_init
                   COMMAND grep -E -- "-init$"
                   COMMAND tr "\n" ";"
                   COMMAND sed -e "s/;$//g"
                   OUTPUT_VARIABLE vnfdCloudInitFiles OUTPUT_STRIP_TRAILING_WHITESPACE)

   SET(allCloudInitFilesChecked "")
   FOREACH(vnfdCloudInitFile IN LISTS vnfdCloudInitFiles)
      makeUniqueTarget(generate_cloudInitCheckedTimestampFile "validate_${vnfdCloudInitFile}")
      SET(cloudInitCheckedTimestampFile ".${generate_cloudInitCheckedTimestampFile}.stamp")

      ADD_CUSTOM_COMMAND(OUTPUT ${cloudInitCheckedTimestampFile}
                         COMMAND ${YAMLLINT} -d '{extends: relaxed, rules: {document-start: {present: no}}}' ${vnfdCloudInitFile}
                         COMMAND touch ${cloudInitCheckedTimestampFile}
                         DEPENDS ${vnfdCloudInitFile})
      ADD_CUSTOM_TARGET(${generate_cloudInitCheckedTimestampFile} DEPENDS ${cloudInitCheckedTimestampFile})

      LIST(APPEND allCloudInitFilesChecked ${generate_cloudInitCheckedTimestampFile} ${cloudInitCheckedTimestampFile})
   ENDFOREACH()

   # ====== Generate the VNFD ===============================================
   SET(vnfdDefinition "${vnfd}/${vnfd}.yaml")
   SET(vnfdPackage    "${vnfd}.tar.gz")
   makeUniqueTarget(generate_vnfdPackage "generate_vnfd_${vnfdPackage}")

   ADD_CUSTOM_COMMAND(OUTPUT  ${vnfdPackage}
                      COMMAND ${OSM} package-validate ${vnfd}
                      COMMAND ${OSM} package-build ${vnfd}
                      COMMAND du -k ${vnfdPackage}
                      DEPENDS ${vnfdFiles} ${allYAMLsChecked} ${allCloudInitFilesChecked} ${allCharmsCopyedIntoVNFD})
   ADD_CUSTOM_TARGET(${generate_vnfdPackage} DEPENDS ${vnfdPackage})

   MESSAGE("VNFD to build: ${vnfd}, depending on Charms ${${vnfd}_charms}")
ENDFOREACH()


# ###### Generate NSDs ######################################################
MESSAGE("Generating NSDs ...")
FOREACH(nsd IN LISTS NSD_LIST)
   EXECUTE_PROCESS(COMMAND git ls-files ${nsd}
                   COMMAND tr "\n" ";"
                   COMMAND sed -e "s/;$//g"
                   OUTPUT_VARIABLE nsdFiles OUTPUT_STRIP_TRAILING_WHITESPACE)

   # ====== Obtain all required VNFD packages ===============================
   SET(allRequiredVNFDPackages "")
   FOREACH(vnfd IN LISTS ${nsd}_vnfds)
      SET(vnfdPackage "${vnfd}.tar.gz")
      makeUniqueTarget(generate_vnfdPackage "generate_vnfd_${vnfdPackage}")
      LIST(APPEND allRequiredVNFDPackages ${generate_vnfdPackage} ${vnfdPackage})
   ENDFOREACH()

   # ====== Generate the NSD ================================================
   SET(nsdDefinition "${nsd}/${nsd}.yaml")
   SET(nsdPackage    "${nsd}.tar.gz")
   makeUniqueTarget(generate_nsdPackage "generate_nsd_${nsdPackage}")

   ADD_CUSTOM_COMMAND(OUTPUT  ${nsdPackage}
                      COMMAND ${OSM} package-validate ${nsd}
                      COMMAND ${OSM} package-build ${nsd}
                      COMMAND du -k ${nsdPackage}
                      DEPENDS ${nsdFiles} ${allYAMLsChecked} ${allRequiredVNFDPackages})
   ADD_CUSTOM_TARGET(${generate_nsdPackage} ALL DEPENDS ${nsdPackage})

   MESSAGE("NSD to build: ${nsd}, depending on VNFDs ${${nsd}_vnfds}")
ENDFOREACH()
