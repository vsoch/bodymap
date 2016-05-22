# Prepare bodymap will parse labels from the FMA 
# - including terms likely to be found in social media

from svgtools import create_pointilism_svg
from glob import glob
from time import sleep
import pandas
import re

# STEP 0: PREPARE BODYMAP ####################################################################

png_image = "data/body.png"

create_pointilism_svg(png_image,uid_base="bodymap",
                                sample_rate=8,width=330,height=800,
                                output_file="data/bodymappp.svg")


# STEP 1: PREPARE DATA #######################################################################

files = glob("data/*.csv")
fatalities = pandas.DataFrame(columns=["FISCAL_YEAR","SUMMARY_DATE","INCIDENT_DATE","COMPANY","DESCRIPTION"])

# Original headers

for f in files:
    print "\n%s" %(f)
    fatcat = pandas.read_csv(f)
    print ",".join(fatcat.columns.tolist())

#FISCAL_YEAR,SUMMARY_DATE,INCIDENT_DATE,COMPANY,DESCRIPTION 
# data/FatalitiesFY11.csv
# Fiscal Year ,Summary Report Date,Date of Incident,Company,Preliminary Description of Incident

# data/FatalitiesFY13.csv
# Date of Incident,Company, City, State, ZIP,Preliminary Description of Incident,Fatality or Catastrophe

# data/fatalitiesFY15.csv
# Date of Incident,Company, City, State, ZIP,Victim(s),Preliminary Description of Incident,Fatality or Catastrophe,Inspection #,Unnamed: 6,Unnamed: 7,Unnamed: 8,Unnamed: 9,Unnamed: 10,Unnamed: 11,Unnamed: 12,Unnamed: 13,Unnamed: 14,Unnamed: 15,Unnamed: 16,Unnamed: 17,Unnamed: 18,Unnamed: 19

# data/FatalitiesFY09.csv
# Fiscal Year ,Summary Report Date,Date of Incident,Company,Preliminary Description of Incident

# data/fatalitiesFY16.csv
# Date of Incident ,Employer/Address of Incident ,Victim(s) ,Hazard Description ,Fatality or Catastrophe ,Inspection # 

# data/FatalitiesFY14.csv
# Date of Incident,Company, City, State, ZIP,Preliminary Description of Incident,Fatality or Catastrophe,Unnamed: 4,Unnamed: 5,Unnamed: 6,Unnamed: 7,Unnamed: 8,Unnamed: 9,Unnamed: 10,Unnamed: 11,Unnamed: 12,Unnamed: 13,Unnamed: 14,Unnamed: 15,Unnamed: 16,Unnamed: 17

# data/FatalitiesFY12.csv
# Fiscal Year ,Summary Report Date,Date of Incident,Preliminary Description of Incident,Unnamed: 4

# data/fatalitiesFY10.csv
# Fiscal Year ,Summary Report Date,Date of Incident,Company,Preliminary Description of Incident

for f in files:
    print "Adding file %s" %(f)
    fatcat = pandas.read_csv(f)
    # Generate index based on year
    match = re.search("[0-9]+",f)
    year = f[match.start():match.end()]
    rownames = ["%s_%s" %(year,x) for x in range(fatcat.shape[0])]
    fatcat.index = rownames
    shared_columns = [c for c in fatcat.columns if c in fatalities.columns]
    fatalities = fatalities.append(fatcat[shared_columns])

fatalities
# [7852 rows x 5 columns]

# We have one null date from 2016 - assign year 2016
fatalities.INCIDENT_DATE[fatalities["INCIDENT_DATE"].isnull()] = "01/01/2016"
fatalities.to_csv("data/fatalities_all.tsv",sep="\t")

# STEP 3: COORDINATE-IZE #####################################################################

# The company variable has the company name and location, we need to split it
locations = []
companies = []
for row in fatalities.iterrows():
    company = row[1].COMPANY
    locations.append("".join(company.split(',')[-2:]).strip())
    companies.append("".join(company.split(',')[:2]).strip())

fatalities = fatalities.rename(index=str, columns={"COMPANY": "COMPANY_ORIGINAL"})
fatalities["LOCATION_RAW"] = locations
fatalities["COMPANY"] = companies
fatalities.to_csv("data/fatalities_all.tsv",sep="\t")

# Replace weird latin characters
normalized = [x.replace('\xa0', '') for x in fatalities["LOCATION_RAW"]]
fatalities.LOCATION_RAW = normalized

# https://pypi.python.org/pypi/geopy
from geopy.geocoders import Nominatim
geolocator = Nominatim()

# Function to add an entry
def add_entry(index,location,fatalities):
    fatalities.loc[index,"LOCATION"] = location.address
    fatalities.loc[index,"ALTITUDE"] = location.altitude
    fatalities.loc[index,"LATITUDE"] = location.latitude
    fatalities.loc[index,"LONGITUDE"] = location.longitude
    fatalities.loc[index,"LOCATION_IMPORTANCE"] = location.raw["importance"]
    return fatalities

manual_inspection = []
for row in fatalities.iterrows():
    index = row[0]
    address = row[1].LOCATION_RAW
    if row[1].LOCATION == "" and index not in manual_inspection:
        location = geolocator.geocode(address)
        sleep(0.5)
        if location != None:
            fatalities = add_entry(index,location,fatalities)
        else:
            print "Did not find %s" %(address)
            manual_inspection.append(index)

# Function to normalize unicode to ascii, remove characters
def normalize_locations(fatalities):
    locs=[]
    for fat in fatalities.LOCATION.tolist():
        if isinstance(fat,float):
            locs.append("")
        elif isinstance(fat,unicode):
            locs.append(unicodedata.normalize("NFC",fat).encode('ASCII', 'ignore'))
        else:
            locs.append(fat)
    fatalities.LOCATION=locs
    return fatalities
    
fatalities = normalize_locations(fatalities)
fatalities.to_csv("data/fatalities_all.tsv",sep="\t")


found = []
not_found = []
while len(manual_inspection) > 0:
    mi = manual_inspection.pop()
    row = fatalities.loc[mi]
    # Try finding the state, and keeping one word before it, adding comma
    address = row.LOCATION_RAW
    match = re.search("\s\w+\s[A-Z]{2}",address)
    wasfound = False
    if match!= None:
        address = address[match.start():].strip()
        location = geolocator.geocode(address)
        sleep(0.5)
        if location != None:
            print "FOUND %s" %(address)
            wasfound = True
            fatalities = add_entry(index,location,fatalities)
            # Save the address that was used
            fatalities.loc[index,"LOCATION_RAW"] = address
            found.append(mi)
    if wasfound == False:
        not_found.append(mi)

manual_inspection = [x for x in manual_inspection if x not in found]

fatalities = normalize_locations(fatalities)
fatalities.to_csv("data/fatalities_all.tsv",sep="\t")

# Try just using zip code - this might be best strategy
found = []
not_found = []
while len(manual_inspection) > 0:
    mi = manual_inspection.pop()
    row = fatalities.loc[mi]
    # Try finding the state, and keeping one word before it, adding comma
    address = row.LOCATION_RAW
    match = re.search("[A-Z]{2}",address)
    wasfound = False
    if match!= None:
        address = address[match.start():].strip()
        location = geolocator.geocode(address)
        sleep(0.5)
        if location != None:
            print "FOUND %s" %(address)
            wasfound = True
            fatalities = add_entry(index,location,fatalities)
            # Save the address that was used
            fatalities.loc[index,"LOCATION_RAW"] = address
            found.append(mi)
    if wasfound == False:
        not_found.append(mi)


fatalities = normalize_locations(fatalities)
fatalities.to_csv("data/fatalities_all.tsv",sep="\t")

# STEP 4: GEO-JSON ###########################################################################

# https://pypi.python.org/pypi/geojson/

from geojson import Point, Feature

# STOPPED HERE - haven't done this yet (locations still parsing)
seen = []
for row in fatalities.iterrows():
    index = row[0]

    # Point gets latitude and longitude
    lat = row[1].LATITUDE
    lon = row[1].LONGITUDE
    point = Point((lat,lon))

    # Prepare some properties
    properties = {"altitude":row[1].ALTITUDE,
                  "importance":row[1].LOCATION_IMPORTANCE
                  ""}
    feature = Feature(geometry=point,id=index,properties=properties)

