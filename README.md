## Cisco Prime Map Exporter

Got the idea from https://github.com/pieewiee/CiscoPrimeMapExport and started building a new Tool.
Maybe this is useful for everybody who is going to replace prime or just need some daily exports for third party.

### Capabilities
We build a possibility to change the color of the APs based on device model. Useful for lifecycle or capacity planning.

#### Example
![image](https://github.com/user-attachments/assets/be9f34cc-d49a-49df-8be9-fb2c6fcb2cf0)

### Warranty
Tool is provided as is and no adjustments promised

### Compatibility
Tested on Prime Infrastructure 3.10.5

### Install
1. git clone to your server
2. edit device_credentials_template.py and save as device_credentials.py
3. install python environment (see requirements.txt)
4. add cronjob (keep in mind, the script could take some time)
