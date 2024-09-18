## Cisco Prime Map Exporter

Got the idea from https://github.com/pieewiee/CiscoPrimeMapExport and started building a new Tool.
Maybe this is useful for everybody who is going to replace prime or just need some daily exports for third party.

### Capabilities
We build a possibility to change the color of the APs based on device model. Useful for lifecycle or capacity planning.

#### Example
![image](https://github.com/user-attachments/assets/be9f34cc-d49a-49df-8be9-fb2c6fcb2cf0)

### Warranty
Tool is provided as is and no adjustments promised. Use at your own risk!

### Compatibility
Tested on Prime Infrastructure 3.10.5

## Install
1. git clone to your server
```
git clone https://github.com/yayaasd/cisco-prime-map-export.git cisco-prime-map-export
```
3. edit device_credentials_template.py and save as device_credentials.py
```
prime = {
        "hostname": "prime.domain.name",
        "user": "USERNAME",
        "password": "PASSWORD"
        }
```
4. install python environment (see requirements.txt)
```
pip install -r requirements.txt
```
5. add cronjob (keep in mind, the script could take some time)
