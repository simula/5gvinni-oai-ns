= Software Simcard for the RAN Simulator =

uicc0 = {
   imsi      = "242881234500088";
   key       = "449c4b91aeacd0ace182cf3a5a72bfa1";
   opc       = "9245cd6283cc53ce24ac1186a60dee6b";
   dnn       = "oai";
   nssai_sst = 1;
   # nssai_sd  = 0;   # Default: 0xffffff
}

= Universal simcard =

== Simcard writer software ==
 git clone https://gitea.osmocom.org/sim-card/pysim

== Write data to simcard ==
 OPERATOR="SimulaMet"
 IMSI=242881234500086
 ICCID=8924288123456000086
 KI=449c4b91aeacd0ace182cf3a5a72bfa1
 OPC=9245cd6283cc53ce24ac1186a60dee6b
 MCC=242
 MNC=88
 ACC=0002
 ADM_PIN=24376726   # !!! for card 999700000054252 !!!
 ./pySim-prog.py -p 0 -a ${ADM_PIN} \
    -n "${OPERATOR}" -k ${KI} -o ${OPC} --acc ${ACC} \
    -x ${MCC} -y ${MNC} -i ${IMSI} -s ${ICCID} \
    --fplmn 24202 --fplmn 24201 \
    --dry-run

Note: --dry-run performs a test, *without writing*! To actually write to the card, remove --dry-run.

⚠Double-check the usage of the correct Admin PIN when writing a simcard! Using the wrong PIN multiple times will destory the simcard!⚠
