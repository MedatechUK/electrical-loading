from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
import uuid
import os
import shutil
import pyodbc

# <ID>1</ID>
# <DESCRIPTION>Main leads, female for LTSL</DESCRIPTION>
# <MANUFACTURER>Eldon</MANUFACTURER>
# <PART_NUMBER>CLF2005L</PART_NUMBER>
# <INTERNAL_CODE>RMGE678</INTERNAL_CODE>
# <QUANTITY>1</QUANTITY>

# Get file name to be the parent PART NUMBER
# Loop through ROWS and get child parts
# POST into Interim Table
# 

conn = pyodbc.connect('Driver={SQL Server};'
                      'Server=TEST-SERVER\PRI;'
                      'Database=demo;'
                      'UID=tabula;'
                      'PWD=R33sM4chin3r4!')

cursor = conn.cursor()

def get_attributes(row):
    ID = row.find('ID').text
    DESCRIPTION = row.find('DESCRIPTION').text
    MANUFACTURER = row.find('MANUFACTURER').text
    PART_NUMBER = row.find('PART_NUMBER').text
    INTERNAL_CODE = row.find('INTERNAL_CODE').text
    QUANTITY = row.find('QUANTITY').text
    
    return {'ID': ID, 'DESCRIPTION': DESCRIPTION, 'MANUFACTURER': MANUFACTURER, 'PART_NUMBER': PART_NUMBER, 
            'INTERNAL_CODE': INTERNAL_CODE, 'QUANTITY': QUANTITY }    

def get_pri_time():
    fmt = '%d/%m/%y'

    d1 = datetime.strptime('01/01/88', fmt)
    d2 = datetime.strptime(datetime.now().strftime('%d/%m/%y'), fmt)

    daysDiff = (d2-d1).days

    # Convert days to minutes
    minutesDiff = daysDiff * 24 * 60

    return minutesDiff

def get_max_line_trans():
    cursor.execute('SELECT MAX(LINE) FROM ZODAT_TRANS;')
    return cursor.fetchone()[0]

def get_max_line_load():
    cursor.execute('SELECT MAX(LINE) FROM ZODAT_TRANS;')
    return cursor.fetchone()[0]

def parse_xml(path):
    myuuid = str(uuid.uuid4())

    doc = ET.parse(path).getroot()

    rows = doc.findall('./Row')

    parent_partname = os.path.basename(path).split('.')[0]
    
    max_line_parent = get_max_line_trans()
    # GET LOADTYPE BY SELECTING 'EL' FROM ZODAT_TYPE
    sql = '''SET IDENTITY_INSERT ZODAT_TRANS ON
            INSERT INTO ZODAT_TRANS (LINE, BUBBLEID, LOADTYPE, CREATEDATE) 
            VALUES (?, ?, ?, ?)
            SET IDENTITY_INSERT ZODAT_TRANS OFF'''
    val = (max_line_parent + 1, myuuid, 2, get_pri_time())
    cursor.execute(sql, val)

    max_line_load = get_max_line_load()
    sql = '''INSERT INTO ZODAT_LOAD (LINE, RECORDTYPE, TEXT1, TEXT2) 
            VALUES (?, ?, ?, ?)'''
    val = (max_line_load + 1, '1', parent_partname, parent_partname)
    cursor.execute(sql, val)
    
    for row in rows:
        attr = get_attributes(row)
        max_line_load = get_max_line_load()
        
        sql = '''INSERT INTO ZODAT_LOAD (LINE, RECORDTYPE, PARENT, TEXT1, TEXT2, TEXT3, TEXT4, INT1, INT2) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        val = (int(attr['ID']), '1', max_line_parent + 1, attr['INTERNAL_CODE'], attr['DESCRIPTION'], attr['MANUFACTURER'], attr['INTERNAL_CODE'], int(attr['QUANTITY']), int(attr['ID']))
        cursor.execute(sql, val)
        
    conn.commit()
    
parse_xml(os.path.join('rmged204-1.xml'))

    