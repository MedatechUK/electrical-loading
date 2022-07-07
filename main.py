from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
import uuid
import os
import shutil
import yaml
import logging
import requests

# <ID>1</ID>
# <DESCRIPTION>Main leads, female for LTSL</DESCRIPTION>
# <MANUFACTURER>Eldon</MANUFACTURER>
# <PART_NUMBER>CLF2005L</PART_NUMBER>
# <INTERNAL_CODE>RMGE678</INTERNAL_CODE>
# <QUANTITY>1</QUANTITY>

# Get file name to be the parent PART NUMBER
# Loop through ROWS and get child parts
# POST into Interim Table


#region Global variables
config = yaml.safe_load(open("config.yml"))

COMPANY = config["COMPANY"]
API_URL = config["API_URL"]
PRIORITY_API_USERNAME= config["PRI_API_USERNAME"]
PRIORITY_API_PASSWORD= config["PRI_API_PASSWORD"]
#endregion

#region Error logger setup
path = r"error.log"
assert os.path.isfile(path)
logging.basicConfig(filename=path, level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
#endregion

#region Data logging
def log_response(res):
    if res.ok:
        logging.info("Data posted succesfully to Priority.")
    elif res.status_code == 409:
        # send_email(f"Error message: {res.json()['error']['message']}")
        logging.error(f"Error message: {res.json()['error']['message']}")
        # send_email("Error", f"Error message: {res.json()['error']['message']}")
    elif res.status_code == 500:
        logging.error("Status code 500: Either Priority or the Python program is having problems.")
        # send_email("Error", "Status code 500: Either Priority or the Flask server is down/having problems.")
    else:
        logging.error(f"Error status code: {res.status_code}")
        # send_email("Error", f"Error status code: {res.status_code}")
#endregion

def get_attributes(row):
    ID = row.find('ID').text
    DESCRIPTION = row.find('DESCRIPTION').text
    MANUFACTURER = row.find('MANUFACTURER').text
    PART_NUMBER = row.find('PART_NUMBER').text
    INTERNAL_CODE = row.find('INTERNAL_CODE').text
    QUANTITY = row.find('QUANTITY').text
    
    return {'ID': ID, 'DESCRIPTION': DESCRIPTION, 'MANUFACTURER': MANUFACTURER, 'PART_NUMBER': PART_NUMBER, 
            'INTERNAL_CODE': INTERNAL_CODE, 'QUANTITY': QUANTITY }    

def post_zoda_trans(data):
    r = requests.post(f"{API_URL}{COMPANY}/ZODA_TRANS", json=data, auth=(PRIORITY_API_USERNAME, PRIORITY_API_PASSWORD))
    log_response(r)
    return r

def post_zoda_load(data):
    r = requests.post(f"{API_URL}{COMPANY}/ZODA_LOAD", json=data, auth=(PRIORITY_API_USERNAME, PRIORITY_API_PASSWORD))
    log_response(r)
    return r

def parse_xml(path):
    myuuid = str(uuid.uuid4())

    doc = ET.parse(path).getroot()

    rows = doc.findall('./Row')

    parent_partname = os.path.basename(path).split('.')[0]
    
    data =  {
        "TYPENAME": "EL",
        "BUBBLEID": myuuid,
        "ZODA_LOAD_SUBFORM": [
            {
                "RECORDTYPE": "1",
                "TEXT1": parent_partname,
                "TEXT21": parent_partname,
            }
        ]
    }
    
    for row in rows:
        attr = get_attributes(row)
        #POST CHILDREN TO ZODA_LOAD
        child_part = {
            "RECORDTYPE": "2",
            "TEXT1": attr['INTERNAL_CODE'] if attr['INTERNAL_CODE'] else attr['PART_NUMBER'],
            "TEXT2": attr['MANUFACTURER'],
            "TEXT21": attr['DESCRIPTION'][:60],
            "REAL1": int(attr['QUANTITY']),
            "INT1": int(attr['ID']),
        }

        data["ZODA_LOAD_SUBFORM"].append(child_part)
        
    # print(data)
        
    r = post_zoda_trans(data)
    return r

def handle_files():
    logging.info('Parsing files in directory...')
    input_dir = os.fsencode('//vm-pdm/Priority Electric Exports/')

    for file in os.listdir(input_dir):
        filename = os.fsdecode(file)
        if filename.endswith(".xml"):
            response = parse_xml(os.path.join('//vm-pdm/Priority Electric Exports/', filename))
            status = response.ok
            print(response.json())
            path_to_current_file = os.path.join('//vm-pdm/Priority Electric Exports/', filename)
            path_to_new_file = os.path.join('//vm-pdm/Priority Electric Exports/save', filename)

            if(status):
                shutil.move(path_to_current_file, path_to_new_file)
    logging.info('Parsed all existing files in directory...')

# print(parse_xml(os.path.join(os.path.join('XML-Input','rmged204-1.xml'))))
handle_files()
    