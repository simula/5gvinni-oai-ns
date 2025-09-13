# Using the eNB

## Connectivity Check
```
ping 192.168.247.10    # MME -> eNodeB
ping 192.168.248.10    # SPGW-U -> eNodeB
ping 192.168.246.10    # FlexRAN Controller -> eNodeB

ping -c1 192.168.247.102   # eNodeB -> MME
ping -c1 192.168.248.159   # eNodeB -> SPGW-U
ping -c1 192.168.246.100   # eNodeB -> FlexRAN Controller
```


## Build

```
cd ~/src/openairinterface5g
source oaienv
./cmake_targets/build_oai -w USRP -x -c --eNB --run-with-gdb RelWithDebInfo --build-doxygen --enable-deadline --enable-cpu-affinity

```

Options:
* Use "-C" for a full cleanup first!
* Use "-I" to install external packages (asn1c, etc.)!


## Debug Run (with GDB)

```
cd /home/nornetpp/src/openairinterface5g/cmake_targets/ran_build/build
sudo nice -n -19 gdb ./lte-softmodem
run -O /home/nornetpp/src/openairinterface5g/targets/PROJECTS/GENERIC-LTE-EPC/CONF/enb.band7.tm1.50PRB.usrpb210.conf

--T_stdout 0
```


## Normal Run (without GDB)
```
cd /home/nornetpp/src/openairinterface5g/cmake_targets/ran_build/build
sudo nice -n -19 ./lte-softmodem -O /home/nornetpp/src/openairinterface5g/targets/PROJECTS/GENERIC-LTE-EPC/CONF/enb.band7.tm1.50PRB.usrpb210.conf
```
