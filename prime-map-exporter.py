#import json
import requests
import datetime
import urllib3
import os
import shutil
from os import path
from PIL import Image, ImageDraw, ImageFont#, ImageOps
from paramiko import SSHClient
from scp import SCPClient
import subprocess
import time
import paramiko

import device_credentials

# disables SSL insecurerequestwarning
import warnings
warnings.filterwarnings("ignore")

# Disable invalid certificate warnings. -> fehler kommt trotzdem
urllib3.disable_warnings()

#output files
map_folder = '/PATH/TO/YOUR/FOLDER/prime_maps'


# parameters
prime_hostname = device_credentials.prime['hostname']
prime_api_user = device_credentials.prime['user']
prime_api_pw = device_credentials.prime['password']
prime_base_url = 'https://' + prime_api_user + ':' + prime_api_pw + '@' + prime_hostname

default_font = ImageFont.load_default()
ubuntu_font = ImageFont.truetype('/PATH/TO/YOUR/FOLDER/Ubuntu-R.ttf', size=15)

def get_floors_from_prime():
    prime_url = prime_base_url + '/webacs/api/v4/data/ServiceDomains.json?.full=true&domainType=FLOOR_AREA&.maxResults=999'
    #use this if this is a outdoor area instead of floor
    #prime_url = prime_base_url + '/webacs/api/v4/data/ServiceDomains.json?.full=true&domainType=OUTDOOR_AREA&.maxResults=999'
    floors = requests.get(prime_url, verify=False).json()
    return floors

def get_building_details(building_id):
    prime_url = prime_base_url + '/webacs/api/v4/data/ServiceDomains/' + str(building_id) + '.json'
    building_details = requests.get(prime_url, verify=False).json()
    return building_details

def get_map_image(floor_id):
    prime_url = prime_base_url + '/webacs/api/v4/op/maps/' + str(floor_id) + '/image'
    map_image = requests.get(prime_url, verify=False, stream = True).raw
    return map_image

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_accesspoints_position(floor_id):
    prime_url = prime_base_url + '/webacs/api/v4/data/AccessPointDetails.json?.full=true&.maxResults=1000&serviceDomainId=' + str(floor_id)

    accesspoints = requests.get(prime_url, verify=False).json()
    accesspoints_position = []
    
    try:
        for accesspoint in accesspoints['queryResponse']['entity']:
            try:
                accesspoint_position = {'name':accesspoint['accessPointDetailsDTO']['name'], 'xcoordinate':accesspoint['accessPointDetailsDTO']['coordinates']['XCoordinate'], 'ycoordinate':accesspoint['accessPointDetailsDTO']['coordinates']['YCoordinate'], 'ap_type':accesspoint['accessPointDetailsDTO']['apType']}       
                accesspoints_position.append(accesspoint_position)
            except:
                print('INFO: no valid position for access point:', accesspoint['accessPointDetailsDTO']['name'])
    except:
        pass

    return accesspoints_position

def save_maps_from_floors(floors):

    # Color definition
    color_red = (255, 0, 0, 128) # red (3700 APs)
    color_orange = (230, 125, 0, 128) # orange (3800/4800 APs)
    color_black = (0, 0, 0, 128) # black (restliche APs)
    
    for floor in floors['queryResponse']['entity']:
        print("\nINFO: >>>>>>>>>>>>>>>>>> next floor >>>>>>>>>>>>>>>>>>")
        floor_id = floor['serviceDomainsDTO']['@id']
        floor_width = floor['serviceDomainsDTO']['width']
        floor_height = floor['serviceDomainsDTO']['length']
        building_id = floor['serviceDomainsDTO']['parentId']
        building_details = get_building_details(building_id)
        building_name = building_details['queryResponse']['entity'][0]['serviceDomainsDTO']['name']
        map_name = floor['serviceDomainsDTO']['name']
        try:
            # teils Bilder sind in Greyscale, deswegen gibts fehler, sobald rote Punkte/Schrift  
            # gezeichnet werden, deswegen wird das Bild nach "RGB" konvertiert
            map_image = Image.open(get_map_image(floor_id)).convert("RGB")
            print("INFO: floor ID:", floor_id)
            map_image_width, map_image_height = map_image.size
            x_factor = map_image_width / floor_width
            y_factor = map_image_height / floor_height
            building_directory = map_folder + '/' + building_name
            create_directory(building_directory)
            draw = ImageDraw.Draw(map_image)
            accesspoints_position = get_accesspoints_position(floor_id)
            ap_position_length = len(accesspoints_position)

            print("INFO: AP count:", ap_position_length)

            if ap_position_length != 0:
                for accesspoint_position in accesspoints_position:
                    x = accesspoint_position['xcoordinate'] * x_factor
                    y = accesspoint_position['ycoordinate'] * y_factor
                    ap_name = accesspoint_position['name']
                    ap_type = accesspoint_position['ap_type']
                    try:
                        # red color for 3700 AP's
                        if "3700" in ap_type:
                            color = color_red
                        # red color for 3800/4800 AP's
                        elif "800" in ap_type:
                            color = color_orange
                        # black color for others
                        else:
                            color = color_black

                        draw.rounded_rectangle((x-5, y-5, x+5, y+5), radius=5, fill=color, width=5)
                        #draw.text((x-50, y+5), ap_name, fill=(255, 0, 0, 128), font=ubuntu_font)

                        #create image with text, rotate it 90 degrease and paste it to the map
                        textimg_width, textimg_height = ubuntu_font.getsize(ap_name)
                        text_img = Image.new('RGB', (textimg_width, textimg_height), color=(255, 255, 255, 255))
                        text_img_draw = ImageDraw.Draw(text_img)
                        text_img_draw.text((0, 0), ap_name, font=ubuntu_font, fill=color)
                        text_img_rotate = text_img.rotate(90, expand=1)
                        map_image.paste(text_img_rotate, box=(int(x - textimg_height/2)  ,int(y - textimg_width - 10)))

                      
                    except Exception as e:
                        print("ERROR: not able to draw on floor ID / AP:", map_name, "/", ap_name)
                        print("ERROR: exception:", e)

                # AP Color Legende oben links von jedem Plan
                draw.rounded_rectangle((45, 45, 55, 55), radius=5, fill=color_red, width=5)
                draw.text((60, 45), 'AP Typ: 3700 -> zu ersetzen', fill=color_red, font=ubuntu_font)

                draw.rounded_rectangle((45, 75, 55, 85), radius=5, fill=color_orange, width=5)
                draw.text((60, 75), 'AP Typ: 3800/4800 -> Lifecycle 2024/25 (in Planung)', fill=color_orange, font=ubuntu_font)

                draw.rounded_rectangle((45, 105, 55, 115), radius=5, fill=color_black, width=5)
                draw.text((60, 105), 'kein Lifecycle geplant', fill=color_black, font=ubuntu_font)

            else:
                print('INFO: no access points on map:', map_name)


            map_image.save(building_directory + '/' + map_name + '.jpg')
            print('INFO: image saved:', building_name, '/', map_name)
        except Exception as e:
            print('INFO: no image found for building/floor:', building_name, '/', map_name)

      


def delete_folder(map_folder):
    try:
        shutil.rmtree(map_folder)
        print('INFO: deleted folder', map_folder)
    except Exception as e:
        print('WARNING: could not delete folder', map_folder, e)
    
def delete_file(file_name):
    try:
        os.remove(file_name)
        print('INFO: deleted file', file_name)
    except Exception as e:
        print('WARNING: could not delete', file_name, e)

def create_zip(zip_name, map_folder):
    try:
        shutil.make_archive(zip_name, 'zip', map_folder)
    except Exception as e:
        print('ERROR: could not create ZIP file', e)

def scp(src_file, dst_file):
    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.connect('user@server:path')
    with SCPClient(ssh.get_transport()) as scp:
        scp.put('my_file.txt', 'my_file.txt') # Copy my_file.txt to the server


if __name__ == '__main__':
    # delete existing folder with maps
    delete_folder(map_folder)

    # delete ZIP file with maps
    delete_file(map_folder + '.zip')

    # get floors from Prime
    floors = get_floors_from_prime()

    # save maps based on Prime floors to disk
    save_maps_from_floors(floors)

    # create zip file without date in filename
    zip_name = map_folder
    create_zip(zip_name, map_folder)

    # copy zip to EXTERNAL-SERVER, where the webservice for the Prime Maps runs
    print('INFO: copy zip file to EXTERNAL-SERVER')
    process = subprocess.Popen(["scp", "-i", "/PATH/TO/YOUR/ssh_host_rsa_key", zip_name + '.zip', "username@EXTERNAL-SERVER:/PATH/TO/YOUR/vHOST/htdocs/"])
    sts = os.waitpid(process.pid, 0)

    # create zip file with date in filename, example prime_maps_2023-06-23.zip
    today = datetime.date.today()
    year = str(today.year)
    # format month/day to 2 digits (June is 06 instead of 6)
    month = '%02d' % today.month
    day = '%02d' % today.day
    zip_name = map_folder + '_' + year + '-' + month + '-' + day
    create_zip(zip_name, map_folder)

    # prepare commands which are executed on EXTERNAL-SERVER
    commands = [
        'rm -rf /PATH/TO/YOUR/vHOST/htdocs/prime_maps/*',
        'unzip -q -o /PATH/TO/YOUR/vHOST/htdocs/prime_maps.zip -d /PATH/TO/YOUR/vHOST/htdocs/prime_maps/',
    ]

    # initialize the SSH client
    # we use the username for ssh fixed in the code - feel free to change as you like
    # also using ssh-key to auth. 
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname='EXTERNAL-SERVER', username='USERNAME', key_filename='/PATH/TO/YOUR/ssh_host_rsa_key')
    except Exception as e:
        print("ERROR: Cannot connect to the SSH Server: ", e)
        exit()

    # execute the commands
    for command in commands:
        print('INFO: execute command:', command)
        stdin, stdout, stderr = client.exec_command(command)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err:
            print('ERROR:', err)
