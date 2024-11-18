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
MINI_NO_NRF = 'docker-compose-mini-nonrf.yaml'
BASIC_W_NRF = 'docker-compose-basic-nrf.yaml'
BASIC_VPP_W_NRF = 'docker-compose-basic-vpp-nrf.yaml'
BASIC_VPP_W_NRF_REDIRECT = 'docker-compose-basic-vpp-pcf-redirection.yaml'
BASIC_VPP_W_NRF_STEERING = 'docker-compose-basic-vpp-pcf-steering.yaml'
BASIC_EBPF_W_NRF = 'docker-compose-basic-nrf-ebpf.yaml'

COMPOSE_CONF_MAP = {
    'docker-compose-mini-nrf.yaml': 'conf/mini_nrf_config.yaml',
    'docker-compose-mini-nonrf.yaml' : 'conf/mini_nonrf_config.yaml',
    'docker-compose-basic-nrf.yaml' : 'conf/basic_nrf_config.yaml',
    'docker-compose-basic-vpp-nrf.yaml' : 'conf/basic_vpp_nrf_config.yaml',
    'docker-compose-basic-nrf-ebpf.yaml' : 'conf/basic_nrf_config_ebpf.yaml',
    'docker-compose-basic-vpp-pcf-redirection.yaml' : 'conf/redirection_steering_config.yaml',
    'docker-compose-basic-vpp-pcf-steering.yaml' : 'conf/redirection_steering_config.yaml'
}

def _parse_args() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: the created parser
    """
    example_text = '''example:
        python3 core-network.py --type start-mini
        python3 core-network.py --type start-basic
        python3 core-network.py --type start-basic-vpp
        python3 core-network.py --type start-basic-ebpf
        python3 core-network.py --type stop-mini
        python3 core-network.py --type start-mini --scenario 2
        python3 core-network.py --type start-basic --scenario 2
        python3 core-network.py --type start-vpp-redirection
        python3 core-network.py --type start-vpp-steering'''

    parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK DEPLOY',
                                    epilog=example_text,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)

    # 5GCN function TYPE
    parser.add_argument(
        '--type', '-t',
        action='store',
        required=True,
        choices=['start-mini', 'start-basic', 'start-basic-vpp', 'start-basic-ebpf','start-vpp-redirection', 'start-vpp-steering',\
                 'stop-vpp-redirection', 'stop-vpp-steering','stop-mini', 'stop-basic', 'stop-basic-vpp', 'stop-basic-ebpf'],
        help='Functional type of 5g core network',
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
            sys.exit(f'\033[0;31m Incorrect/Unsupported executing command {cmd}')
        print(res)
        # Then we can start the capture on the "demo-oai" interface.
        # When we undeploy, the process will terminate automatically.
        # Explanation of the capture filter:
        #   * `sctp`                    --> RAN NGAP packets
        #   * port 80                   --> Usual HTTP/1 port
        #   * port 8080                 --> Usual HTTP/2 port
        #   * port 8805                 --> PFCP traffic
        #   * `icmp`                    --> ping traffic
        #   * port 3306                 --> mysql traffic
        cmd = f'nohup sudo tshark -i demo-oai -f "sctp or port 80 or port 8080 or port 8805 or icmp or port 3306" -w {args.capture} > /dev/null 2>&1 &'
        if extra_interface:
            if file_name == BASIC_VPP_W_NRF:
                cmd = re.sub('-i demo-oai', '-i demo-oai -i cn5g-core', cmd)
            if file_name == BASIC_EBPF_W_NRF:
                cmd = re.sub('-i demo-oai', '-i demo-oai -i demo-n3 -i demo-n6', cmd)
        res = run_cmd(cmd, False)
        if res is None:
            sys.exit(f'\033[0;31m Incorrect/Unsupported executing command {cmd}')
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
        sys.exit(f'\033[0;31m Incorrect/Unsupported executing command {cmd}')
    print(res)
    logging.debug('\033[0;32m OAI 5G Core network started, checking the health status of the containers... takes few secs\033[0m....')
    notSilentForFirstTime = False
    for x in range(50):
        cmd = f'docker-compose -f {file_name} ps -a'
        res = run_cmd(cmd, notSilentForFirstTime)
        notSilentForFirstTime = True
        if res is None:
            sys.exit(f'\033[0;31m Incorrect/Unsupported executing command "{cmd}"')
        time.sleep(2)
        cnt = res.count('(healthy)')
        if cnt == ct:
            logging.debug('\033[0;32m All components are healthy, please see below for more details\033[0m....')
            print(res)
            break
    if cnt != ct:
        logging.error('\033[0;31m Core network is un-healthy, please see below for more details\033[0m....')
        print(res)
        sys.exit(-1)
    time.sleep(10)
    status = check_config(file_name)
    if not status:
        sys.exit(-1)

def undeploy(file_name):
    """UnDeploy the docker container

    Returns:
        None
    """
    logging.debug('\033[0;34m UnDeploying OAI 5G core components\033[0m....')
    cmd = f'docker-compose -f {file_name} down -t 30'
    res = run_cmd(cmd, False)
    if res is None:
        sys.exit(f'\033[0;31m Incorrect/Unsupported executing command {cmd}')
    print(res)
    cmd = f'docker volume prune -f'
    run_cmd(cmd, True)
    logging.debug('\033[0;32m OAI 5G core components are UnDeployed\033[0m....')

class CoreNetwork():
    def __init__(self):
        self.NRF_IP_ADDRESS='192.168.70.130'
        self.AMF_IP_ADDRESS='192.168.70.132'
        self.SMF_IP_ADDRESS='192.168.70.133'
        self.UPF_IP_ADDRESS='192.168.70.134'
        self.AUSF_IP_ADDRESS='192.168.70.138'
        self.UDM_IP_ADDRESS='192.168.70.137'
        self.UDR_IP_ADDRESS='192.168.70.136'

    def generate_nrf_curl_cmd(self, compose_file):
        # if not found, there is an exception here, but it is fine because then we have to update our scenarios
        conf_file = COMPOSE_CONF_MAP[compose_file]
        with open(conf_file) as f:
            y = yaml.safe_load(f)
            http_version = y.get('http_version', 1)
            nrf_port = 80

            if y.get('nfs') and y['nfs'].get('nrf'):
                nrf_cfg = y['nfs']['nrf']
                if nrf_cfg.get('sbi') and nrf_cfg['sbi'].get('port'):
                    nrf_port = nrf_cfg['sbi']['port']

            cmd = 'curl -s -X GET '
            if http_version == 2:
                cmd = cmd + '--http2-prior-knowledge '
            cmd = cmd + f'http://{self.NRF_IP_ADDRESS}:{nrf_port}/nnrf-nfm/v1/nf-instances?nf-type='
            return cmd

    def check_ip_addresses(self, compose_file):
        with open(compose_file) as f:
            y = yaml.safe_load(f)
            if y.get('services') and y['services'].get('oai-nrf'):
                nrf_cfg = y['services']['oai-nrf']
                if nrf_cfg.get('networks') and nrf_cfg['networks'].get('public_net') and nrf_cfg['networks']['public_net'].get('ipv4_address'):
                    self.NRF_IP_ADDRESS = nrf_cfg['networks']['public_net'].get('ipv4_address', self.NRF_IP_ADDRESS)
                else:
                    cmd = 'docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" oai-nrf'
                    self.NRF_IP_ADDRESS = run_cmd(cmd, silent=True)
            if y.get('services') and y['services'].get('oai-amf'):
                amf_cfg = y['services']['oai-amf']
                if amf_cfg.get('networks') and amf_cfg['networks'].get('public_net') and amf_cfg['networks']['public_net'].get('ipv4_address'):
                    self.AMF_IP_ADDRESS = amf_cfg['networks']['public_net'].get('ipv4_address', self.AMF_IP_ADDRESS)
                else:
                    cmd = 'docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" oai-amf'
                    self.AMF_IP_ADDRESS = run_cmd(cmd, silent=True)
            if y.get('services') and y['services'].get('oai-smf'):
                smf_cfg = y['services']['oai-smf']
                if smf_cfg.get('networks') and smf_cfg['networks'].get('public_net') and smf_cfg['networks']['public_net'].get('ipv4_address'):
                    self.SMF_IP_ADDRESS = smf_cfg['networks']['public_net'].get('ipv4_address', self.SMF_IP_ADDRESS)
                else:
                    cmd = 'docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" oai-smf'
                    self.SMF_IP_ADDRESS = run_cmd(cmd, silent=True)
            if y.get('services') and y['services'].get('oai-upf'):
                upf_cfg = y['services']['oai-upf']
                if upf_cfg.get('networks') and upf_cfg['networks'].get('public_net') and upf_cfg['networks']['public_net'].get('ipv4_address'):
                    self.UPF_IP_ADDRESS = upf_cfg['networks']['public_net'].get('ipv4_address', self.UPF_IP_ADDRESS)
                else:
                    cmd = 'docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" oai-upf'
                    self.UPF_IP_ADDRESS = run_cmd(cmd, silent=True)
            if y.get('services') and y['services'].get('oai-ausf'):
                ausf_cfg = y['services']['oai-ausf']
                if ausf_cfg.get('networks') and ausf_cfg['networks'].get('public_net') and ausf_cfg['networks']['public_net'].get('ipv4_address'):
                    self.AUSF_IP_ADDRESS = ausf_cfg['networks']['public_net'].get('ipv4_address', self.AUSF_IP_ADDRESS)
                else:
                    cmd = 'docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" oai-ausf'
                    self.AUSF_IP_ADDRESS = run_cmd(cmd, silent=True)
            if y.get('services') and y['services'].get('oai-udm'):
                udm_cfg = y['services']['oai-udm']
                if udm_cfg.get('networks') and udm_cfg['networks'].get('public_net') and udm_cfg['networks']['public_net'].get('ipv4_address'):
                    self.UDM_IP_ADDRESS = udm_cfg['networks']['public_net'].get('ipv4_address', self.UDM_IP_ADDRESS)
                else:
                    cmd = 'docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" oai-udm'
                    self.UDM_IP_ADDRESS = run_cmd(cmd, silent=True)
            if y.get('services') and y['services'].get('oai-udr'):
                udr_cfg = y['services']['oai-udr']
                if udr_cfg.get('networks') and udr_cfg['networks'].get('public_net') and udr_cfg['networks']['public_net'].get('ipv4_address'):
                    self.UDR_IP_ADDRESS = udr_cfg['networks']['public_net'].get('ipv4_address', self.UDR_IP_ADDRESS)
                else:
                    cmd = 'docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" oai-udr'
                    self.UDR_IP_ADDRESS = run_cmd(cmd, silent=True)

def check_config(file_name):
    """Checks the container configurations

    Returns:
        None
    """

    logging.debug('\033[0;34m Checking if the containers are configured\033[0m....')
    deployStatus = True
    cn = CoreNetwork()
    cn.check_ip_addresses(file_name)
    curl_cmd = cn.generate_nrf_curl_cmd(file_name)

    # With NRF configuration check
    if args.scenario == '1':
        logging.debug('\033[0;34m Checking if AMF, SMF and UPF registered with nrf core network\033[0m....')
        cmd = f'{curl_cmd}"AMF" | grep -o "{cn.AMF_IP_ADDRESS}"'
        amf_registration_nrf = run_cmd(cmd, False)
        if amf_registration_nrf is not None:
            print(amf_registration_nrf)
        cmd = f'{curl_cmd}"SMF" | grep -o "{cn.SMF_IP_ADDRESS}"'
        smf_registration_nrf = run_cmd(cmd, False)
        if smf_registration_nrf is not None:
            print(smf_registration_nrf)
        if file_name == BASIC_VPP_W_NRF or file_name == BASIC_VPP_W_NRF_REDIRECT or file_name == BASIC_VPP_W_NRF_STEERING:
            cmd = f'{curl_cmd}"UPF" | grep -o "192.168.70.201"'
        elif file_name == BASIC_EBPF_W_NRF:
            cmd = f'{curl_cmd}"UPF" | grep -o "192.168.70.129"'
        else:
            cmd = f'{curl_cmd}"UPF" | grep -o "{cn.UPF_IP_ADDRESS}"'
        upf_registration_nrf = run_cmd(cmd, False)
        if upf_registration_nrf is not None:
            print(upf_registration_nrf)
        if file_name == BASIC_VPP_W_NRF or file_name == BASIC_W_NRF or file_name == BASIC_EBPF_W_NRF:
            logging.debug('\033[0;34m Checking if AUSF, UDM and UDR registered with nrf core network\033[0m....')
            cmd = f'{curl_cmd}"AUSF" | grep -o "{cn.AUSF_IP_ADDRESS}"'
            ausf_registration_nrf = run_cmd(cmd, False)
            if ausf_registration_nrf is not None:
                print(ausf_registration_nrf)
            cmd = f'{curl_cmd}"UDM" | grep -o "{cn.UDM_IP_ADDRESS}"'
            udm_registration_nrf = run_cmd(cmd, False)
            if udm_registration_nrf is not None:
                print(udm_registration_nrf)
            cmd = f'{curl_cmd}"UDR" | grep -o "{cn.UDR_IP_ADDRESS}"'
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
             deployStatus = False
        else:
            if file_name == BASIC_VPP_W_NRF or file_name == BASIC_W_NRF:
                logging.debug('\033[0;32m AUSF, UDM, UDR, AMF, SMF and UPF are registered to NRF\033[0m....')
            else:
                logging.debug('\033[0;32m AMF, SMF and UPF are registered to NRF\033[0m....')
        if file_name == BASIC_VPP_W_NRF or file_name == BASIC_VPP_W_NRF_REDIRECT or file_name == BASIC_VPP_W_NRF_STEERING:
            logging.debug('\033[0;34m Checking if SMF is able to connect with UPF\033[0m....')
            cmd1 = 'docker logs oai-smf 2>&1 | grep "Received N4 ASSOCIATION SETUP RESPONSE from an UPF"'
            cmd2 = 'docker logs oai-smf 2>&1 | grep "Node ID Type FQDN: vpp-upf"'
            upf_logs1 = run_cmd(cmd1)
            upf_logs2 = run_cmd(cmd2)
            if upf_logs1 is None or upf_logs2 is None:
                logging.error('\033[0;31m UPF did not answer to N4 Association request from SMF\033[0m....')
                deployStatus = False
            else:
                logging.debug('\033[0;32m UPF did answer to N4 Association request from SMF\033[0m....')
            cmd1 = 'docker logs oai-smf 2>&1 | grep "PFCP HEARTBEAT PROCEDURE"'
            upf_logs1 = run_cmd(cmd1)
            if upf_logs1 is None:
                logging.error('\033[0;31m SMF is NOT receiving heartbeats from UPF\033[0m....')
                deployStatus = False
            else:
                logging.debug('\033[0;32m SMF is receiving heartbeats from UPF\033[0m....')
        elif file_name == BASIC_W_NRF:
            logging.debug('\033[0;34m Checking if SMF is able to connect with UPF\033[0m....')
            cmd1 = 'docker logs oai-smf 2>&1 | grep "Received N4 ASSOCIATION SETUP RESPONSE from an UPF"'
            cmd2 = f'docker logs oai-smf 2>&1 | grep "Resolve IP Addr {cn.UPF_IP_ADDRESS}, FQDN oai-upf"'
            upf_logs1 = run_cmd(cmd1)
            upf_logs2 = run_cmd(cmd2)
            if upf_logs1 is None or upf_logs2 is None:
                logging.error('\033[0;31m UPF did not answer to N4 Association request from SMF\033[0m....')
                deployStatus = False
            else:
                logging.debug('\033[0;32m UPF did answer to N4 Association request from SMF\033[0m....')
            cmd1 = 'docker logs oai-smf 2>&1 | grep "PFCP HEARTBEAT PROCEDURE"'
            upf_logs1 = run_cmd(cmd1)
            if upf_logs1 is None:
                logging.error('\033[0;31m SMF is NOT receiving heartbeats from UPF\033[0m....')
                deployStatus = False
            else:
                logging.debug('\033[0;32m SMF is receiving heartbeats from UPF\033[0m....')
        else:
            logging.debug('\033[0;34m Checking if SMF is able to connect with UPF\033[0m....')
            cmd1 = 'docker logs oai-upf 2>&1 | grep "Received SX HEARTBEAT RESPONSE"'
            cmd2 = 'docker logs oai-upf 2>&1 | grep "Received SX HEARTBEAT REQUEST"'
            upf_logs1 = run_cmd(cmd1)
            upf_logs2 = run_cmd(cmd2)
            if upf_logs1 is None and upf_logs2 is None:
                logging.error('\033[0;31m UPF is NOT receiving heartbeats from SMF\033[0m....')
                deployStatus = False
            else:
                logging.debug('\033[0;32m UPF is receiving heartbeats from SMF\033[0m....')
    # With noNRF configuration checks
    # Only the Mini-No-NRF is supported anymore.
    elif args.scenario == '2':
        logging.debug('\033[0;34m Checking if SMF is able to connect with UPF\033[0m....')
        cmd1 = 'docker logs oai-smf 2>&1 | grep "Received N4 ASSOCIATION SETUP RESPONSE from an UPF"'
        cmd2 = 'docker logs oai-smf 2>&1 | grep "Resolve IP Addr 192.168.70.134, FQDN oai-upf"'
        upf_logs1 = run_cmd(cmd1)
        upf_logs2 = run_cmd(cmd2)
        if upf_logs1 is None or upf_logs2 is None:
            logging.error('\033[0;31m UPF did not answer to N4 Association request from SMF\033[0m....')
            deployStatus = False
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
        else:
            deployStatus = False
    if deployStatus:
        logging.debug('\033[0;32m OAI 5G Core network is configured and healthy\033[0m....')
    else:
        logging.error('\033[0;32m OAI 5G Core network may not be properly deployed\033[0m....')
    return deployStatus

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
            logging.error('Mini deployments with NRF are no longer supported')
            sys.exit(-1)
        # Mini function without NRF
        elif args.scenario == '2':
            deploy(MINI_NO_NRF)
    elif args.type == 'start-basic':
        # Basic function with NRF
        if args.scenario == '1':
            deploy(BASIC_W_NRF)
        # Basic function without NRF
        elif args.scenario == '2':
            logging.error('Basic deployments without NRF are no longer supported')
            sys.exit(-1)
    elif args.type == 'start-basic-vpp':
        # Basic function with NRF and VPP-UPF
        if args.scenario == '1':
            deploy(BASIC_VPP_W_NRF, True)
        # Basic function without NRF but with VPP-UPF
        elif args.scenario == '2':
            logging.error('Basic deployments without NRF are no longer supported')
            sys.exit(-1)
    elif args.type == 'start-basic-ebpf':
        # Basic function with NRF and UPF-eBPF
        if args.scenario == '1':
            deploy(BASIC_EBPF_W_NRF, True)
        # Basic function without NRF but with UPF-eBPF
        elif args.scenario == '2':
            logging.error('Basic deployments without NRF are no longer supported')
            sys.exit(-1)
    elif args.type == 'start-vpp-redirection':
        # Basic function with NRF and VPP-UPF
        if args.scenario == '1':
            deploy(BASIC_VPP_W_NRF_REDIRECT, True)
        # Basic function without NRF but with VPP-UPF
        elif args.scenario == '2':
            logging.error('Basic deployments without NRF are no longer supported')
            sys.exit(-1)
    elif args.type == 'start-vpp-steering':
        # Basic function with NRF and VPP-UPF
        if args.scenario == '1':
            deploy(BASIC_VPP_W_NRF_STEERING, True)
        # Basic function without NRF but with VPP-UPF
        elif args.scenario == '2':
            logging.error('Basic deployments without NRF are no longer supported')
            sys.exit(-1)
    elif args.type == 'stop-mini':
        if args.scenario == '2':
            undeploy(MINI_NO_NRF)
    elif args.type == 'stop-basic':
        if args.scenario == '1':
            undeploy(BASIC_W_NRF)
    elif args.type == 'stop-basic-vpp':
        if args.scenario == '1':
            undeploy(BASIC_VPP_W_NRF)
    elif args.type == 'stop-vpp-redirection':
        if args.scenario == '1':
            undeploy(BASIC_VPP_W_NRF_REDIRECT)
    elif args.type == 'stop-vpp-steering':
        if args.scenario == '1':
            undeploy(BASIC_VPP_W_NRF_STEERING)
    elif args.type == 'stop-basic-ebpf':
        if args.scenario == '1':
            undeploy(BASIC_EBPF_W_NRF)
