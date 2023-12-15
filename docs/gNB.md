   # Documentation

* <https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/NR_SA_Tutorial_OAI_CN5G.md>
* <https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/NR_SA_Tutorial_OAI_nrUE.md>
* <https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/NR_SA_Tutorial_COTS_UE.md>
* <https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/radio/rfsimulator/README.md>
* <https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/RUNMODEM.md>
* <https://github.com/mrouili/perfEval-5G>


# Using the gNB

## Connectivity Check
```
ping -c3 -i0.2 192.168.243.132   # AMF
ping -c3 -i0.2 192.168.10.2      # Ettus via fibre0
ping -c3 -i0.2 192.168.20.2      # Ettus via fibre1
ping -c3 -i0.2 10.193.4.119      # Ettus via copper
```

## Build

```
cd ~/src/openairinterface5g
source oaienv
./cmake_targets/build_oai -w USRP -c --eNB --gNB --nrUE --build-lib "nrqtscope" --run-with-gdb RelWithDebInfo


# With most options:
# ./cmake_targets/build_oai --ninja -w USRP -C --eNB --UE --nrUE --gNB --build-lib "telnetsrv enbscope uescope nrscope nrqtscope" --build-doxygen

```

Options:
* Use "-C" for a full cleanup first!
* Use "-I" to install external packages (asn1c, etc.)!


## Build with libuhd from sources using specific version

```
cd ~/src/openairinterface5g
source oaienv
export BUILD_UHD_FROM_SOURCE=True
export UHD_VERSION=4.6.0.0
./cmake_targets/build_oai -w USRP -c --eNB --gNB --nrUE --build-lib "nrqtscope" --run-with-gdb RelWithDebInfo
```


## Run with SDR

### Run on Ettus N310

```
cd ~/src/openairinterface5g
source oaienv
cd cmake_targets/ran_build/build
sudo nice -n -19 ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.band78.sa.fr1.106PRB.2x2.usrpn310.conf --gNBs.[0].min_rxtxtime 6 --sa --usrp-tx-thread-config 1
```

### Run on Ettus N310 with GDB:
```
cd ~/src/openairinterface5g
source oaienv
cd cmake_targets/ran_build/build
sudo nice -n -19 gdb ./nr-softmodem
run -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.band78.sa.fr1.106PRB.2x2.usrpn310.conf --gNBs.[0].min_rxtxtime 6 --sa --usrp-tx-thread-config 1
```

To set logging verbosity:
-g LEVEL
   LEVEL: 4 -> maximum

### Run on Ettus B210

```
cd ~/src/openairinterface5g
source oaienv
cd cmake_targets/ran_build/build
sudo nice -n -19 ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.fr1.106PRB.usrpb210.conf --gNBs.[0].min_rxtxtime 6 --sa -E --continuous-tx
```


## Run with RFsimulator

### Using Ettus N310 configuration file:
```
cd ~/src/openairinterface5g
source oaienv
cd cmake_targets/ran_build/build
sudo nice -n -19 ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.band78.sa.fr1.106PRB.2x2.usrpn310.conf --gNBs.[0].min_rxtxtime 6 --sa --rfsim
```

### Using Ettus B210 configuration file:
```
cd ~/src/openairinterface5g
source oaienv
cd cmake_targets/ran_build/build
sudo nice -n -19 ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.fr1.106PRB.usrpb210.conf --gNBs.[0].min_rxtxtime 6 --sa --rfsim
```

### Notes
Important: The configuration file needs to have an "rfsimulator" block, to work in server mode. If nr-softmodem starts in client mode (tries to connect to server), check the configuration file:
```
THREAD_STRUCT = {
...
};

rfsimulator :
{
  serveraddr = "server";
  serverport = 4043;
  options = (); #("saviq"); or/and "chanmod"
  modelname = "AWGN";
  IQfile = "/tmp/rfsimulator.iqs";
};

security = { ...
```


# Using the UE

## Simcard Settings

Defaults are defined in openair3/UICC/usim_interface.c!

targets/PROJECTS/GENERIC-NR-5GC/CONF/ue.conf:
```
uicc0 = {
   imsi      = "242881234500088";
   key       = "449c4b91aeacd0ace182cf3a5a72bfa1";
   opc       = "9245cd6283cc53ce24ac1186a60dee6b";
   dnn       = "oai";
   nssai_sst = 1;
   # nssai_sd  = 0;   # Default: 0xffffff
}
```

## Run on Ettus B210

```
cd ~/src/openairinterface5g
source oaienv
cd cmake_targets/ran_build/build
sudo ./nr-uesoftmodem  -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/ue.conf -r 106 --numerology 1 --band 78 -C 3619200000 --ssb 516 --sa -E
```

Notes:

* Option -E must be added for Ettus B210!
* If the gNodeB is started with "-E" option, it must be added here as well!

## Run with RFsimulator

```
cd ~/src/openairinterface5g
source oaienv
cd cmake_targets/ran_build/build
sudo ./nr-uesoftmodem  -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/ue.conf -r 106 --numerology 1 --band 78 -C 3619200000 --ssb 516 --sa --rfsim --rfsimulator.serveraddr 10.193.4.68
```

Notes:

* The IP address of the gNodeB RFsimulator instance has to be specified here (10.193.4.68 = 5g.fire.smil)!
* If the gNodeB is started with "-E" option, it must be added here as well!


# Using Tracer for Debugging


## Documentation

* <https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/common/utils/T/DOC/T/wireshark.md>

## Starting OAI component with Tracer:

Add option: --T_stdout 2


## Run Live Tracer:

```
cd ~/src/openairinterface5g/cmake_targets/ran_build/build/common/utils/T/tracer/
./macpdu2wireshark -d ../T_messages.txt -live
```

Use Wireshark:

* Record on loopback interface (lo), UDP traffic for port 9999 (filter: udp.port==9999)
* Ensure that MAC-NR decoding is enabled (see <https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/common/utils/T/DOC/T/wireshark.md#configure-wireshark-for-nr>)
