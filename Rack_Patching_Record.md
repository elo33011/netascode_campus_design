# NetAsCode Campus Design: Master Rack & Stack & Patching Matrix

## 1. Rack Elevation & Equipment Placement Table

| Rack ID | Location / Suite | U Position | Device Name | Role / Failure Domain |
| :--- | :--- | :--- | :--- | :--- |
| **RACK-A01** | Main Equipment Room - Row A, Rack 1 | 41–42 | `abc-hq-wan-01` | WAN Router (FD-A) |
| **RACK-A01** | Main Equipment Room - Row A, Rack 1 | 39–40 | `abc-hq-cor-01` | Core Router (FD-A) |
| **RACK-A01** | Main Equipment Room - Row A, Rack 1 | 37–38 | `abc-hq-cor-02` | Core Router (FD-A) |
| **RACK-A01** | Main Equipment Room - Row A, Rack 1 | 35–36 | `abc-hq-agg-01` | Aggregation Switch (FD-A) |
| **RACK-A02** | Main Equipment Room - Row A, Rack 2 | 39–40 | `abc-hq-agg-02` | Aggregation Switch (FD-A) |
| **RACK-B01** | Main Equipment Room - Row B, Rack 1 | 41–42 | `abc-hq-wan-02` | WAN Router (FD-B) |
| **RACK-B01** | Main Equipment Room - Row B, Rack 1 | 39–40 | `abc-hq-cor-03` | Core Router (FD-B) |
| **RACK-B01** | Main Equipment Room - Row B, Rack 1 | 37–38 | `abc-hq-cor-04` | Core Router (FD-B) |
| **RACK-B01** | Main Equipment Room - Row B, Rack 1 | 35–36 | `abc-hq-agg-03` | Aggregation Switch (FD-B) |
| **RACK-B02** | Main Equipment Room - Row B, Rack 2 | 39–40 | `abc-hq-agg-04` | Aggregation Switch (FD-B) |
| **RACK-MGT01** | Main Equipment Room - Row MGT, Rack 1 | 41–42 | `abc-hq-mgt-wan-01` | Management WAN Router |
| **RACK-MGT01** | Main Equipment Room - Row MGT, Rack 1 | 39–40 | `abc-hq-mgt-cor-01` | Management Core Switch |
| **RACK-MGT01** | Main Equipment Room - Row MGT, Rack 1 | 37–38 | `abc-hq-mgt-ts-idf-main-01` | Terminal Server (Console) |
| **RACK-MGT01** | Main Equipment Room - Row MGT, Rack 1 | 35–36 | `abc-hq-mgt-acc-idf-main-01` | Management Access Switch (SSH) |

---

## 2. Production Network Cable Patching Matrix Table

| Connection ID | Source Device | Source Rack | Source Port | Dest Device | Dest Rack | Dest Port | Cable / Media Type | Link Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PROD-LNK-01** | `abc-hq-wan-01` | RACK-A01 | TenGigabitEthernet0/0/0 | Service Provider A | MM-01 | Demarc Port 1 | LC-LC OM4 Fiber | `wan_circuit` |
| **PROD-LNK-02** | `abc-hq-wan-02` | RACK-B01 | TenGigabitEthernet0/0/0 | Service Provider B | MM-01 | Demarc Port 2 | LC-LC OM4 Fiber | `wan_circuit` |
| **PROD-LNK-03** | `abc-hq-wan-01` | RACK-A01 | HundredGigE0/1/0 | `abc-hq-wan-02` | RACK-B01 | HundredGigE0/1/0 | MPO-MPO OM4 Fiber | `inter_device` |
| **PROD-LNK-04** | `abc-hq-wan-01` | RACK-A01 | HundredGigE0/2/0 | `abc-hq-cor-01` | RACK-A01 | HundredGigE0/0/1 | MPO-MPO OM4 Fiber | `inter_device` |
| **PROD-LNK-05** | `abc-hq-wan-01` | RACK-A01 | HundredGigE0/2/1 | `abc-hq-cor-03` | RACK-B01 | HundredGigE0/0/1 | MPO-MPO OM4 Fiber | `inter_device` |
| **PROD-LNK-06** | `abc-hq-wan-02` | RACK-B01 | HundredGigE0/2/0 | `abc-hq-cor-04` | RACK-B01 | HundredGigE0/0/1 | MPO-MPO OM4 Fiber | `inter_device` |
| **PROD-LNK-07** | `abc-hq-wan-02` | RACK-B01 | HundredGigE0/2/1 | `abc-hq-cor-02` | RACK-A01 | HundredGigE0/0/1 | MPO-MPO OM4 Fiber | `inter_device` |
| **PROD-LNK-08** | `abc-hq-cor-01` | RACK-A01 | HundredGigE0/0/2 | `abc-hq-cor-02` | RACK-A01 | HundredGigE0/0/2 | MPO-MPO OM4 Fiber | `inter_device` |
| **PROD-LNK-09** | `abc-hq-cor-01` | RACK-A01 | HundredGigE1/0/1 | `abc-hq-agg-01` | RACK-A01 | HundredGigE0/1 | MPO-MPO OM4 Fiber | `core_to_agg` |
| **PROD-LNK-10** | `abc-hq-cor-01` | RACK-A01 | HundredGigE1/0/2 | `abc-hq-agg-02` | RACK-A02 | HundredGigE0/1 | MPO-MPO OM4 Fiber | `core_to_agg` |
| **PROD-LNK-11** | `abc-hq-cor-02` | RACK-A01 | HundredGigE1/0/1 | `abc-hq-agg-01` | RACK-A01 | HundredGigE0/2 | MPO-MPO OM4 Fiber | `core_to_agg` |
| **PROD-LNK-12** | `abc-hq-cor-02` | RACK-A01 | HundredGigE1/0/2 | `abc-hq-agg-02` | RACK-A02 | HundredGigE0/2 | MPO-MPO OM4 Fiber | `core_to_agg` |
| **PROD-LNK-13** | `abc-hq-cor-03` | RACK-B01 | HundredGigE0/0/2 | `abc-hq-cor-04` | RACK-B01 | HundredGigE0/0/2 | MPO-MPO OM4 Fiber | `inter_device` |
| **PROD-LNK-14** | `abc-hq-cor-03` | RACK-B01 | HundredGigE1/0/1 | `abc-hq-agg-03` | RACK-B01 | HundredGigE0/1 | MPO-MPO OM4 Fiber | `core_to_agg` |
| **PROD-LNK-15** | `abc-hq-cor-03` | RACK-B01 | HundredGigE1/0/2 | `abc-hq-agg-04` | RACK-B02 | HundredGigE0/1 | MPO-MPO OM4 Fiber | `core_to_agg` |
| **PROD-LNK-16** | `abc-hq-cor-04` | RACK-B01 | HundredGigE1/0/1 | `abc-hq-agg-03` | RACK-B01 | HundredGigE0/2 | MPO-MPO OM4 Fiber | `core_to_agg` |
| **PROD-LNK-17** | `abc-hq-cor-04` | RACK-B01 | HundredGigE1/0/2 | `abc-hq-agg-04` | RACK-B02 | HundredGigE0/2 | MPO-MPO OM4 Fiber | `core_to_agg` |
| **PROD-LNK-18** | `abc-hq-agg-01` | RACK-A01 | HundredGigE0/48 | `abc-hq-agg-02` | RACK-A02 | HundredGigE0/48 | MPO-MPO OM4 Fiber | `inter_device` |
| **PROD-LNK-19** | `abc-hq-agg-03` | RACK-B01 | HundredGigE0/48 | `abc-hq-agg-04` | RACK-B02 | HundredGigE0/48 | MPO-MPO OM4 Fiber | `inter_device` |

---

## 3. Management Network Cable Patching Matrix Table

| Connection ID | Source Device | Source Rack | Source Port | Dest Device | Dest Rack | Dest Port | Cable / Media Type | Link Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MGT-LNK-01** | `abc-hq-mgt-wan-01` | RACK-MGT01 | GigabitEthernet0/0/0 | Management ISP | MM-01 | MGT Demarc Port 1 | Cat6 Patch Cable | `mgt_wan_circuit` |
| **MGT-LNK-02** | `abc-hq-mgt-wan-01` | RACK-MGT01 | TenGigabitEthernet0/1/0 | `abc-hq-mgt-cor-01` | RACK-MGT01 | TenGigabitEthernet1/1 | LC-LC OM4 Fiber | `mgt_backbone` |
| **MGT-LNK-03** | `abc-hq-mgt-cor-01` | RACK-MGT01 | TenGigabitEthernet1/2 | `abc-hq-mgt-acc-idf-main-01` | RACK-MGT01 | TenGigabitEthernet1/1 | LC-LC OM4 Fiber | `mgt_backbone` |
| **MGT-LNK-04** | `abc-hq-mgt-cor-01` | RACK-MGT01 | TenGigabitEthernet1/3 | `abc-hq-mgt-ts-idf-main-01` | RACK-MGT01 | TenGigabitEthernet1/1 | LC-LC OM4 Fiber | `mgt_backbone` |
| **MGT-LNK-05** | `abc-hq-mgt-acc-idf-main-01` | RACK-MGT01 | GigabitEthernet1/1 | `abc-hq-wan-01` | RACK-A01 | Management0 | Cat6 Shielded Cable | `mgt_ethernet` |
| **MGT-LNK-06** | `abc-hq-mgt-acc-idf-main-01` | RACK-MGT01 | GigabitEthernet1/2 | `abc-hq-cor-01` | RACK-A01 | GigabitEthernet0 | Cat6 Shielded Cable | `mgt_ethernet` |
| **MGT-LNK-07** | `abc-hq-mgt-ts-idf-main-01` | RACK-MGT01 | Async1 | `abc-hq-wan-01` | RACK-A01 | Console | RJ45 Rollover Cable | `mgt_console` |
| **MGT-LNK-08** | `abc-hq-mgt-ts-idf-main-01` | RACK-MGT01 | Async2 | `abc-hq-cor-01` | RACK-A01 | Console | RJ45 Rollover Cable | `mgt_console` |

## 4. Access Layer Rack Elevation & Patching Matrix Table

| Floor / Switch Name | Failure Domain | Rack ID & Location | U Position | Uplink Ports | Connected Aggregations (Dest Rack & Port) | Cable & Media Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Floor 1** <br>`abc-hq-f01-acc-01` | FD-A | Floor-01 IDF-A Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-01` (RACK-A01, Port `TenGigabitEthernet1/0/1`) <br>`abc-hq-agg-02` (RACK-A02, Port `TenGigabitEthernet1/0/1`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 1** <br>`abc-hq-f01-acc-02` | FD-B | Floor-01 IDF-B Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-03` (RACK-B01, Port `TenGigabitEthernet1/0/1`) <br>`abc-hq-agg-04` (RACK-B02, Port `TenGigabitEthernet1/0/1`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 2** <br>`abc-hq-f02-acc-01` | FD-A | Floor-02 IDF-A Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-01` (RACK-A01, Port `TenGigabitEthernet1/0/2`) <br>`abc-hq-agg-02` (RACK-A02, Port `TenGigabitEthernet1/0/2`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 2** <br>`abc-hq-f02-acc-02` | FD-B | Floor-02 IDF-B Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-03` (RACK-B01, Port `TenGigabitEthernet1/0/2`) <br>`abc-hq-agg-04` (RACK-B02, Port `TenGigabitEthernet1/0/2`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 3** <br>`abc-hq-f03-acc-01` | FD-A | Floor-03 IDF-A Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-01` (RACK-A01, Port `TenGigabitEthernet1/0/3`) <br>`abc-hq-agg-02` (RACK-A02, Port `TenGigabitEthernet1/0/3`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 3** <br>`abc-hq-f03-acc-02` | FD-B | Floor-03 IDF-B Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-03` (RACK-B01, Port `TenGigabitEthernet1/0/3`) <br>`abc-hq-agg-04` (RACK-B02, Port `TenGigabitEthernet1/0/3`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 4** <br>`abc-hq-f04-acc-01` | FD-A | Floor-04 IDF-A Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-01` (RACK-A01, Port `TenGigabitEthernet1/0/4`) <br>`abc-hq-agg-02` (RACK-A02, Port `TenGigabitEthernet1/0/4`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 4** <br>`abc-hq-f04-acc-02` | FD-B | Floor-04 IDF-B Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-03` (RACK-B01, Port `TenGigabitEthernet1/0/4`) <br>`abc-hq-agg-04` (RACK-B02, Port `TenGigabitEthernet1/0/4`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 5** <br>`abc-hq-f05-acc-01` | FD-A | Floor-05 IDF-A Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-01` (RACK-A01, Port `TenGigabitEthernet1/0/5`) <br>`abc-hq-agg-02` (RACK-A02, Port `TenGigabitEthernet1/0/5`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 5** <br>`abc-hq-f05-acc-02` | FD-B | Floor-05 IDF-B Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-03` (RACK-B01, Port `TenGigabitEthernet1/0/5`) <br>`abc-hq-agg-04` (RACK-B02, Port `TenGigabitEthernet1/0/5`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 6** <br>`abc-hq-f06-acc-01` | FD-A | Floor-06 IDF-A Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-01` (RACK-A01, Port `TenGigabitEthernet1/0/6`) <br>`abc-hq-agg-02` (RACK-A02, Port `TenGigabitEthernet1/0/6`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 6** <br>`abc-hq-f06-acc-02` | FD-B | Floor-06 IDF-B Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-03` (RACK-B01, Port `TenGigabitEthernet1/0/6`) <br>`abc-hq-agg-04` (RACK-B02, Port `TenGigabitEthernet1/0/6`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 7** <br>`abc-hq-f07-acc-01` | FD-A | Floor-07 IDF-A Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-01` (RACK-A01, Port `TenGigabitEthernet1/0/7`) <br>`abc-hq-agg-02` (RACK-A02, Port `TenGigabitEthernet1/0/7`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 7** <br>`abc-hq-f07-acc-02` | FD-B | Floor-07 IDF-B Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-03` (RACK-B01, Port `TenGigabitEthernet1/0/7`) <br>`abc-hq-agg-04` (RACK-B02, Port `TenGigabitEthernet1/0/7`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 8** <br>`abc-hq-f08-acc-01` | FD-A | Floor-08 IDF-A Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-01` (RACK-A01, Port `TenGigabitEthernet1/0/8`) <br>`abc-hq-agg-02` (RACK-A02, Port `TenGigabitEthernet1/0/8`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 8** <br>`abc-hq-f08-acc-02` | FD-B | Floor-08 IDF-B Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-03` (RACK-B01, Port `TenGigabitEthernet1/0/8`) <br>`abc-hq-agg-04` (RACK-B02, Port `TenGigabitEthernet1/0/8`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 9** <br>`abc-hq-f09-acc-01` | FD-A | Floor-09 IDF-A Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-01` (RACK-A01, Port `TenGigabitEthernet1/0/9`) <br>`abc-hq-agg-02` (RACK-A02, Port `TenGigabitEthernet1/0/9`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 9** <br>`abc-hq-f09-acc-02` | FD-B | Floor-09 IDF-B Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-03` (RACK-B01, Port `TenGigabitEthernet1/0/9`) <br>`abc-hq-agg-04` (RACK-B02, Port `TenGigabitEthernet1/0/9`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 10** <br>`abc-hq-f10-acc-01` | FD-A | Floor-10 IDF-A Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-01` (RACK-A01, Port `TenGigabitEthernet1/0/10`) <br>`abc-hq-agg-02` (RACK-A02, Port `TenGigabitEthernet1/0/10`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
| **Floor 10** <br>`abc-hq-f10-acc-02` | FD-B | Floor-10 IDF-B Rack 1 | 41–42 | TenGigabitEthernet1/1/1 <br>TenGigabitEthernet1/1/2 | `abc-hq-agg-03` (RACK-B01, Port `TenGigabitEthernet1/0/10`) <br>`abc-hq-agg-04` (RACK-B02, Port `TenGigabitEthernet1/0/10`) | 10GBASE-SR_Fiber <br>(OM4 LC-LC Vertical Risers) |
