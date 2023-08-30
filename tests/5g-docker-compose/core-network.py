"""
Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
contributor license agreements.  See the NOTICE file distributed with
this work for additional information regarding copyright ownership.
The OpenAirInterface Software Alliance licenses this file to You under
the OAI Public License, Version 1.1  (the "License"); you may not use this file
except in compliance with the License.
You may obtain a copy of the License at

      http://www.openairinterface.org/?page_id=698

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
------------------------------------------------------------------------------
For more information about the OpenAirInterface (OAI) Software Alliance:
      contact@openairinterface.org

------------------------------------------------------------------------------
"""

import yaml
import re
import subprocess
import time
import logging
import argparse
import sys

logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format="[%(asctime)s] %(name)s:%(levelname)s: %(message)s"
)

# Docker Compose files
MINI_W_NRF = 'docker-compose-mini-nrf.yaml' 
MINI_NO_NRF = 'docker-compose-mini-nonrf.yaml'
BASIC_W_NRF = 'docker-compose-basic-nrf.yaml'
BASIC_NO_NRF = 'docker-compose-basic-nonrf.yaml'
BASIC_VPP_W_NRF = 'docker-compose-basic-vpp-nrf.yaml'
BASIC_VPP_NO_NRF = 'docker-compose-basic-vpp-nonrf.yaml'

def _parse_args() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: the created parser
    """
    example_text = '''example:
        python3 core-network.py --type start-mini
        python3 core-network.py --type start-basic
        python3 core-network.py --type start-basic-vpp
        python3 core-network.py --type stop-mini
        python3 core-network.py --type start-mini --scenario 2
        python3 core-network.py --type start-basic --scenario 2'''

    parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK DEPLOY',
                                    epilog=example_text,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)

    # 5GCN function TYPE
    parser.add_argument(
        '--type', '-t',
        action='store',
        required=True,
        choices=['start-mini', 'start-basic', 'start-basic-vpp', 'stop-mini', 'stop-basic', 'stop-basic-vpp'],
        help='Functional type of 5g core network ("start-mini"|"start-basic"|"start-basic-vpp"|"stop-mini"|"stop-basic"|"stop-basic-vpp")',
    )
    # Deployment scenario with NRF/ without NRF
    parser.add_argument(
        '--scenario', '-s',
        action='store',
        choices=['1', '2'],
        default='1',
        help='Scenario with NRF ("1") and without NRF ("2")',
    )
	# Automatic PCAP capture
    parser.add_argument(
        '--capture', '-c',
        action='store',
        help='Add an automatic PCAP capture on docker networks to CAPTURE file',
    )
    return parser.parse_args()

def deploy(file_name, extra_interface=False):
    """Deploy the containers using the docker-compose template

    Returns:
        None
    """
    logging.debug('\033[0;34m Starting 5gcn components... Please wait\033[0m....')
    # The assumption is that all services described in docker-compose files
    # have explicit or built-in health checks.
    cmd = f'docker-compose -f {file_name} config --services | wc -l'
    res = run_cmd(cmd, True)
    ct = int(res)

    if args.capture is None:
        # When no capture, just deploy all at once.
        cmd = f'docker-compose -f {file_name} up -d'
        res = run_cmd(cmd, False)
    else:
        # First just deploy mysql container, all docker networks will be up.
        cmd = f'docker-compose -f {file_name} up -d mysql'
        res = run_cmd(cmd, False)
        if res is None:
            exit(f'\033[0;31m Incorrect/Unsupported executing command {cmd}')
        print(res)
        # Then we can start the capture on the "demo-oai" interface.
        # When we undeploy, the process will terminate automatically.
        # Explanation of the capture filter:
        #  - On all containers but oai-ext-dn
        #   * `not arp`                 --> NO ARP packets
        #   * `not port 53`             --> NO DNS requests from any container
        #   * `not port 2152`           --> When running w/ OAI RF simulator, remove all GTP packets
        #  - On oai-ext-dn container
        #   * `icmp`                    --> Only ping packets
        cmd = f'nohup sudo tshark -i demo-oai -f "(not host 192.168.70.135 and not arp and not port 53 and not port 2152) or (host 192.168.70.135 and icmp)" -w {args.capture} > /dev/null 2>&1 &'
        if extra_interface:
            cmd = re.sub('-i demo-oai', '-i demo-oai -i cn5g-core', cmd)
            cmd = re.sub('70', '73', cmd)
        res = run_cmd(cmd, False)
        if res is None:
            exit(f'\033[0;31m Incorrect/Unsupported executing command {cmd}')
        cmd = f'sleep 20; sudo chmod 666 {args.capture}'
        run_cmd(cmd)
        # Finally deploy the rest of the network functions.
        cmd = f'docker-compose -f {file_name} up -d'
        res = run_cmd(cmd, False)
    # sometimes first try does not go through
    if args.capture is not None:
        cmd = f'sudo chmod 666 {args.capture}'
        run_cmd(cmd)
    if res is None:
        exit(f'\033[0;31m Incorrect/Unsupported executing command {cmd}')
    print(res)
    logging.debug('\033[0;32m OAI 5G Core network started, checking the health status of the containers... takes few secs\033[0m....')
    notSilentForFirstTime = False
    for x in range(50):
        cmd = f'docker-compose -f {file_name} ps -a'
        res = run_cmd(cmd, notSilentForFirstTime)
        notSilentForFirstTime = True
        if res is None:
            exit(f'\033[0;31m Incorrect/Unsupported executing command "{cmd}"')
        time.sleep(2)
        cnt = res.count('(healthy)')
        if cnt == ct:
            logging.debug('\033[0;32m All components are healthy, please see below for more details\033[0m....')
            print(res)
            break
    if cnt != ct:
        logging.error('\033[0;31m Core network is un-healthy, please see below for more details\033[0m....')
        print(res)
        exit(-1)
    time.sleep(10)
    check_config(file_name)

def undeploy(file_name):
    """UnDeploy the docker container

    Returns:
        None
    """
    logging.debug('\033[0;34m UnDeploying OAI 5G core components\033[0m....')
    cmd = f'docker-compose -f {file_name} down -t 0'
    res = run_cmd(cmd, False)
    if res is None:
        exit(f'\033[0;31m Incorrect/Unsupported executing command {cmd}')
    print(res)
    cmd = f'docker volume prune -f'
    run_cmd(cmd, True)
    logging.debug('\033[0;32m OAI 5G core components are UnDeployed\033[0m....')


def check_config(file_name):
    """Checks the container configurations

    Returns:
        None
    """

    logging.debug('\033[0;34m Checking if the containers are configured\033[0m....')
    # With NRF configuration check
    if args.scenario == '1':
        logging.debug('\033[0;34m Checking if AMF, SMF and UPF registered with nrf core network\033[0m....')
        cmd = 'curl -s -X GET http://192.168.70.130/nnrf-nfm/v1/nf-instances?nf-type="AMF" | grep -o "192.168.70.132"'
        amf_registration_nrf = run_cmd(cmd, False)
        if amf_registration_nrf is not None:
            print(amf_registration_nrf)
        cmd = 'curl -s -X GET http://192.168.70.130/nnrf-nfm/v1/nf-instances?nf-type="SMF" | grep -o "192.168.70.133"'
        smf_registration_nrf = run_cmd(cmd, False)
        if smf_registration_nrf is not None:
            print(smf_registration_nrf)
        if file_name == BASIC_VPP_W_NRF:
            cmd = 'curl -s -X GET http://192.168.70.130/nnrf-nfm/v1/nf-instances?nf-type="UPF" | grep -o "192.168.70.201"'
        else:
            cmd = 'curl -s -X GET http://192.168.70.130/nnrf-nfm/v1/nf-instances?nf-type="UPF" | grep -o "192.168.70.134"'
        upf_registration_nrf = run_cmd(cmd, False)
        if upf_registration_nrf is not None:
            print(upf_registration_nrf)
        if file_name == BASIC_VPP_W_NRF or file_name == BASIC_W_NRF:
            logging.debug('\033[0;34m Checking if AUSF, UDM and UDR registered with nrf core network\033[0m....')
            cmd = 'curl -s -X GET http://192.168.70.130/nnrf-nfm/v1/nf-instances?nf-type="AUSF" | grep -o "192.168.70.138"'
            ausf_registration_nrf = run_cmd(cmd, False)
            if ausf_registration_nrf is not None:
                print(ausf_registration_nrf)
            cmd = 'curl -s -X GET http://192.168.70.130/nnrf-nfm/v1/nf-instances?nf-type="UDM" | grep -o "192.168.70.137"'
            udm_registration_nrf = run_cmd(cmd, False)
            if udm_registration_nrf is not None:
                print(udm_registration_nrf)
            cmd = 'curl -s -X GET http://192.168.70.130/nnrf-nfm/v1/nf-instances?nf-type="UDR" | grep -o "192.168.70.136"'
            udr_registration_nrf = run_cmd(cmd, False)
            if udr_registration_nrf is not None:
                print(udr_registration_nrf)
        else:
            ausf_registration_nrf = True
            udm_registration_nrf = True
            udr_registration_nrf = True
        if amf_registration_nrf is None or smf_registration_nrf is None or upf_registration_nrf is None or \
           ausf_registration_nrf is None or udm_registration_nrf is None or udr_registration_nrf is None:
             logging.error('\033[0;31m Registration problem with NRF, check the reason manually\033[0m....')
        else:
            if file_name == BASIC_VPP_W_NRF or file_name == BASIC_W_NRF:
                logging.debug('\033[0;32m AUSF, UDM, UDR, AMF, SMF and UPF are registered to NRF\033[0m....')
            else:
                logging.debug('\033[0;32m AMF, SMF and UPF are registered to NRF\033[0m....')
        if file_name == BASIC_VPP_W_NRF:
            logging.debug('\033[0;34m Checking if SMF is able to connect with UPF\033[0m....')
            cmd1 = 'docker logs oai-smf 2>&1 | grep "Received N4 ASSOCIATION SETUP RESPONSE from an UPF"'
            cmd2 = 'docker logs oai-smf 2>&1 | grep "Node ID Type FQDN: vpp-upf"'
            upf_logs1 = run_cmd(cmd1)
            upf_logs2 = run_cmd(cmd2)
            if upf_logs1 is None or upf_logs2 is None:
                logging.error('\033[0;31m UPF did not answer to N4 Association request from SMF\033[0m....')
                exit(-1)
            else:
                logging.debug('\033[0;32m UPF did answer to N4 Association request from SMF\033[0m....')
            cmd1 = 'docker logs oai-smf 2>&1 | grep "PFCP HEARTBEAT PROCEDURE"'
            upf_logs1 = run_cmd(cmd1)
            if upf_logs1 is None:
                logging.error('\033[0;31m SMF is NOT receiving heartbeats from UPF\033[0m....')
                exit(-1)
            else:
                logging.debug('\033[0;32m SMF is receiving heartbeats from UPF\033[0m....')
        elif file_name == BASIC_W_NRF:
            logging.debug('\033[0;34m Checking if SMF is able to connect with UPF\033[0m....')
            cmd1 = 'docker logs oai-smf 2>&1 | grep "Received N4 ASSOCIATION SETUP RESPONSE from an UPF"'
            cmd2 = 'docker logs oai-smf 2>&1 | grep "Node ID Type FQDN: oai-spgwu"'
            upf_logs1 = run_cmd(cmd1)
            upf_logs2 = run_cmd(cmd2)
            if upf_logs1 is None or upf_logs2 is None:
                logging.error('\033[0;31m UPF did not answer to N4 Association request from SMF\033[0m....')
                exit(-1)
            else:
                logging.debug('\033[0;32m UPF did answer to N4 Association request from SMF\033[0m....')
            cmd1 = 'docker logs oai-smf 2>&1 | grep "PFCP HEARTBEAT PROCEDURE"'
            upf_logs1 = run_cmd(cmd1)
            if upf_logs1 is None:
                logging.error('\033[0;31m SMF is NOT receiving heartbeats from UPF\033[0m....')
                exit(-1)
            else:
                logging.debug('\033[0;32m SMF is receiving heartbeats from UPF\033[0m....')
        else:
            logging.debug('\033[0;34m Checking if SMF is able to connect with UPF\033[0m....')
            cmd1 = 'docker logs oai-spgwu 2>&1 | grep "Received SX HEARTBEAT RESPONSE"'
            cmd2 = 'docker logs oai-spgwu 2>&1 | grep "Received SX HEARTBEAT REQUEST"'
            upf_logs1 = run_cmd(cmd1)
            upf_logs2 = run_cmd(cmd2)
            if upf_logs1 is None and upf_logs2 is None:
                logging.error('\033[0;31m UPF is NOT receiving heartbeats from SMF\033[0m....')
                exit(-1)
            else:
                logging.debug('\033[0;32m UPF is receiving heartbeats from SMF\033[0m....')
    # With noNRF configuration checks
    elif args.scenario == '2':
        logging.debug('\033[0;34m Checking if SMF is able to connect with UPF\033[0m....')
        if file_name == BASIC_VPP_NO_NRF:
            cmd1 = 'docker logs oai-smf 2>&1 | grep "Received N4 ASSOCIATION SETUP RESPONSE from an UPF"'
            cmd2 = 'docker logs oai-smf 2>&1 | grep "Node ID Type FQDN: gw1"'
            upf_logs1 = run_cmd(cmd1)
            upf_logs2 = run_cmd(cmd2)
            if upf_logs1 is None or upf_logs2 is None:
                logging.error('\033[0;31m UPF did not answer to N4 Association request from SMF\033[0m....')
                exit(-1)
            else:
                logging.debug('\033[0;32m UPF did answer to N4 Association request from SMF\033[0m....')
        status = 0
        for x in range(4):
            cmd = "docker logs oai-smf 2>&1 | grep  'handle_receive(16 bytes)'"
            res = run_cmd(cmd)
            if res is None:
               logging.error('\033[0;31m UPF is NOT receiving heartbeats from SMF, re-trying\033[0m....')
            else:
                status += 1
        if status > 2:
            logging.debug('\033[0;32m UPF is receiving heartbeats from SMF\033[0m....')
    logging.debug('\033[0;32m OAI 5G Core network is configured and healthy\033[0m....')

def run_cmd(cmd, silent=True):
    if not silent:
        logging.debug(cmd)
    result = None
    try:
        res = subprocess.run(cmd,
                        shell=True, check=True,
                        stdout=subprocess.PIPE, 
                        universal_newlines=True)
        result = res.stdout.strip()
    except:
        pass
    return result

if __name__ == '__main__':

    # Parse the arguments to get the deployment instruction
    args = _parse_args()
    if args.type == 'start-mini':
        # Mini function with NRF
        if args.scenario == '1':
            deploy(MINI_W_NRF)
        # Mini function without NRF
        elif args.scenario == '2':
            deploy(MINI_NO_NRF)
    elif args.type == 'start-basic':
        # Basic function with NRF
        if args.scenario == '1':
            deploy(BASIC_W_NRF)
        # Basic function without NRF
        elif args.scenario == '2':
            #deploy(BASIC_NO_NRF)
            logging.error('Basic deployments without NRF are no longer supported')
            sys.exit(-1)
    elif args.type == 'start-basic-vpp':
        # Basic function with NRF and VPP-UPF
        if args.scenario == '1':
            deploy(BASIC_VPP_W_NRF, True)
        # Basic function without NRF but with VPP-UPF
        elif args.scenario == '2':
            #deploy(BASIC_VPP_NO_NRF, True)
            logging.error('Basic deployments without NRF are no longer supported')
            sys.exit(-1)
    elif args.type == 'stop-mini':
        if args.scenario == '1':
            undeploy(MINI_W_NRF)
        elif args.scenario == '2':
            undeploy(MINI_NO_NRF)
    elif args.type == 'stop-basic':
        if args.scenario == '1':
            undeploy(BASIC_W_NRF)
        elif args.scenario == '2':
            undeploy(BASIC_NO_NRF)
    elif args.type == 'stop-basic-vpp':
        if args.scenario == '1':
            undeploy(BASIC_VPP_W_NRF)
        elif args.scenario == '2':
            undeploy(BASIC_VPP_NO_NRF)
