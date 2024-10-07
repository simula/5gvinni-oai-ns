# OAI 5G Core Network Topology

Service Based Interfaces (SBIs) (i.e. interfaces that are labeled `Nxxx`), are used in the Control Plane in the 5G Network to connect between different Network Functions.
All Network Functions in the Control Plane in the 5G Network, are using a common bus to exchange control plane messages between each other.
Each Network Function is using a Service Based Interface (SBI), in order to connect to this common bus.

## In detail for the core:

 - **MYSQL**: 
	 - image: mysql:8.0
	 - build file: https://github.com/docker-library/mysql/blob/3e6dfd03b956727c7fb5b30360512a11751a3e9d/8.0/Dockerfile.oracle
	 - It is needed for the `oai-udr` network function. Not part of a typical 5G core.
 - **oai-udr**: 
	 - image: oaisoftwarealliance/oai-udr:v1.5.1
	 - source: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-udr/-/tree/89a82cc065c17faf2fe113bda0b9f9bae9f3d7da
 - **oai-ausf**
	 - image: oaisoftwarealliance/oai-ausf:v1.5.1
	 - source: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-ausf/-/tree/v1.5.1?ref_type=tags
 - **oai-nrf**:
	 - image: oaisoftwarealliance/oai-nrf:v1.5.1
	 - source: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-nrf/-/tree/v1.5.1?ref_type=tags
 - **oai-amf**
	 - image:  oaisoftwarealliance/oai-amf:v1.5.1
	 - source: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-amf/-/tree/v1.5.1?ref_type=tags
 - **oai-upf (oai-spgwu)** (<font style="color:red"> to be replaced with `oai-cn5g-upf` </font>)
	 - image: oaisoftwarealliance/oai-spgwu-tiny:v1.5.1
	 - current source: https://github.com/OPENAIRINTERFACE/openair-spgwu-tiny/tree/v1.5.1
	 - future source: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-upf
 - **oai-ext-dn**:
	 - image: oaisoftwarealliance/trf-gen-cn5g:latest
	 - source: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed/-/blob/v1.5.1/ci-scripts/Dockerfile.traffic.generator.ubuntu?ref_type=tags
	 - It is just a traffic generator. It is not needed in the core.
 - **oai-smf**
	 - image: oaisoftwarealliance/oai-smf:v1.5.1
	 - source: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-smf/-/tree/v1.5.1?ref_type=tags
 - **oai-udm**
	 - image: oaisoftwarealliance/oai-udm:v1.5.1
	 - source: https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-udm/-/tree/v1.5.1?ref_type=tags


## In detail for the RAN

- source: [https://gitlab.eurecom.fr/oai/openairinterface5g](https://gitlab.eurecom.fr/oai/openairinterface5g)
- We use the latest weekly tag. Latest version we tested `2024.w03`.
- We modify some parameters like MCC / MNC and IP addresses.


