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

# Manual work to find above # (reason failed)
for mi in not_found:
    print 'fatalities.loc[%s,"LOCATION_RAW"] = "" #' %mi



fatalities.loc[7680,"LOCATION_RAW"] = "FL 34945" # wrong zip code
fatalities.loc[7666,"LOCATION_RAW"] = "TX 77351" # nearby town Leggett
fatalities.loc[7623,"LOCATION_RAW"] = "TN 37868" # wrong zip code
fatalities.loc[7581,"LOCATION_RAW"] = "MO 64836" # wrong zip code
fatalities.loc[7579,"LOCATION_RAW"] = "MA 02108" # wrong zip code
fatalities.loc[7577,"LOCATION_RAW"] = "IL 62701" #
fatalities.loc[7561,"LOCATION_RAW"] = "TX 77541" #
fatalities.loc[7546,"LOCATION_RAW"] = "IA 50644" #
fatalities.loc[7541,"LOCATION_RAW"] = "ND 58201" #
fatalities.loc[7521,"LOCATION_RAW"] = "UT 84078" #
fatalities.loc[7479,"LOCATION_RAW"] = "TX 78836" #
fatalities.loc[7335,"LOCATION_RAW"] = "ND 58601" #
fatalities.loc[7232,"LOCATION_RAW"] = "WA 98003" # wrong zip code
fatalities.loc[7185,"LOCATION_RAW"] = "TX 77001" #
fatalities.loc[7182,"LOCATION_RAW"] = "TX 75956" #
fatalities.loc[7148,"LOCATION_RAW"] = "MD 21201" #
fatalities.loc[7060,"LOCATION_RAW"] = "TX 75766" # had name of center
fatalities.loc[7053,"LOCATION_RAW"] = "OR 97503" # had name of department
fatalities.loc[7027,"LOCATION_RAW"] = "IN 46806" # pizza shop!
fatalities.loc[7024,"LOCATION_RAW"] = "TX 75560" # too much in address
fatalities.loc[7013,"LOCATION_RAW"] = "TX 77662" # too much in address
fatalities.loc[7005,"LOCATION_RAW"] = "AZ 85262" # ""
fatalities.loc[6996,"LOCATION_RAW"] = "MD 20847" # wrong zip code
fatalities.loc[6986,"LOCATION_RAW"] = "MN 55421" #
fatalities.loc[6985,"LOCATION_RAW"] = "MA 02130" # city misspelled
fatalities.loc[6890,"LOCATION_RAW"] = "TX 78401" #
fatalities.loc[6887,"LOCATION_RAW"] = "IL 60415" # no address
fatalities.loc[6809,"LOCATION_RAW"] = "WA 98101" #
fatalities.loc[6804,"LOCATION_RAW"] = "TN 38478" # different sites mentioned
fatalities.loc[6792,"LOCATION_RAW"] = "MN 55992" # different sites mentioned
fatalities.loc[6716,"LOCATION_RAW"] = "IN 47901" # only company name
fatalities.loc[6477,"LOCATION_RAW"] = "CA 95526" #
fatalities.loc[6452,"LOCATION_RAW"] = "NM 87501" #
fatalities.loc[6431,"LOCATION_RAW"] = "TX 79754" #
fatalities.loc[6414,"LOCATION_RAW"] = "ME 04945" # wrong state! 
# this is conspicuous - reported twice, wrong state
fatalities.loc[6412,"LOCATION_RAW"] = "ME 04945" # same
fatalities.loc[6384,"LOCATION_RAW"] = "AK 72315" #
fatalities.loc[6301,"LOCATION_RAW"] = "TX 79754" # this place has already been reported
# Reeco Well Services and  Joyce Fisher Limited Partnership
fatalities.loc[6217,"LOCATION_RAW"] = "CA 92331" #
fatalities.loc[6123,"LOCATION_RAW"] = "AR 72175" #
fatalities.loc[5996,"LOCATION_RAW"] = "ND 58847" #
fatalities.loc[5976,"LOCATION_RAW"] = "ND 58847" #
fatalities.loc[5559,"LOCATION_RAW"] = "CA 95050" #
fatalities.loc[5412,"LOCATION_RAW"] = "MS 39567" #
fatalities.loc[5402,"LOCATION_RAW"] = "TX 77573" #
fatalities.loc[5389,"LOCATION_RAW"] = "TX 78836" # second one in Catarina
fatalities.loc[5354,"LOCATION_RAW"] = "TX 77840" #
fatalities.loc[5238,"LOCATION_RAW"] = "WI 53705" #
fatalities.loc[5020,"LOCATION_RAW"] = "TX 78021" #
fatalities.loc[4932,"LOCATION_RAW"] = "AS 96799" #
fatalities.loc[4761,"LOCATION_RAW"] = "OH 44101" #
fatalities.loc[4631,"LOCATION_RAW"] = "KY 40502" # spelling error
fatalities.loc[4546,"LOCATION_RAW"] = "CT 06840" #
fatalities.loc[4436,"LOCATION_RAW"] = "TX 75421" #
fatalities.loc[4395,"LOCATION_RAW"] = "MI 49201" #
fatalities.loc[4320,"LOCATION_RAW"] = "IL 62640" #
fatalities.loc[4251,"LOCATION_RAW"] = "CA 91722" #
fatalities.loc[4140,"LOCATION_RAW"] = "KY 42440" # lowecase state letter
fatalities.loc[4123,"LOCATION_RAW"] = "TX 79401" #
fatalities.loc[3928,"LOCATION_RAW"] = "FL 33101" #
fatalities.loc[3820,"LOCATION_RAW"] = "NM 97743" #
fatalities.loc[3812,"LOCATION_RAW"] = "NM 87420" # wrong zip code
fatalities.loc[3758,"LOCATION_RAW"] = "TX 75960" #
fatalities.loc[3666,"LOCATION_RAW"] = "TX 78864" #
fatalities.loc[3661,"LOCATION_RAW"] = "LA 70001" #
fatalities.loc[3643,"LOCATION_RAW"] = "NY 11215" #
fatalities.loc[3627,"LOCATION_RAW"] = "TX 77070" #
fatalities.loc[3618,"LOCATION_RAW"] = "TX 75022" #
fatalities.loc[3446,"LOCATION_RAW"] = "IN 46507" # wrong state
fatalities.loc[3344,"LOCATION_RAW"] = "TX 77572" #
fatalities.loc[3197,"LOCATION_RAW"] = "AZ 85206" # WalMart store number
fatalities.loc[3133,"LOCATION_RAW"] = "NJ 09753" #
fatalities.loc[2984,"LOCATION_RAW"] = "AK 99501" #
fatalities.loc[2770,"LOCATION_RAW"] = "KY 42431" # wrong zip code
fatalities.loc[2749,"LOCATION_RAW"] = "TX 78349" #
fatalities.loc[2305,"LOCATION_RAW"] = "OK 73043" #
fatalities.loc[2283,"LOCATION_RAW"] = "CA 95618" # zip for wrong state
fatalities.loc[2280,"LOCATION_RAW"] = "WA 98036" #
fatalities.loc[2226,"LOCATION_RAW"] = "FL 33178" #
fatalities.loc[2058,"LOCATION_RAW"] = "MS 39701" #
fatalities.loc[2032,"LOCATION_RAW"] = "OK 73660" #
fatalities.loc[1980,"LOCATION_RAW"] = "WV 24931" #
fatalities.loc[1962,"LOCATION_RAW"] = "CA 92501" #
fatalities.loc[1959,"LOCATION_RAW"] = "TX 77571" #
fatalities.loc[1915,"LOCATION_RAW"] = "IL 61748" #
fatalities.loc[1898,"LOCATION_RAW"] = "WA 98660" #
fatalities.loc[1873,"LOCATION_RAW"] = "TX 78201" # extra number in zip
fatalities.loc[1863,"LOCATION_RAW"] = "TX 78353" #
fatalities.loc[1635,"LOCATION_RAW"] = "AS 96799" # American Samoa?
fatalities.loc[1492,"LOCATION_RAW"] = "AS 96799" #
fatalities.loc[1477,"LOCATION_RAW"] = "TN 38340" #
fatalities.loc[1406,"LOCATION_RAW"] = "TX 77501" #
fatalities.loc[1335,"LOCATION_RAW"] = "TX 78353" #
fatalities.loc[1224,"LOCATION_RAW"] = "CA 92879" #
fatalities.loc[1065,"LOCATION_RAW"] = "OK 73030" # wrong zip code
fatalities.loc[806,"LOCATION_RAW"] = "IA 52240" #
fatalities.loc[618,"LOCATION_RAW"] = "CA 90401" #
fatalities.loc[543,"LOCATION_RAW"] = "OK 73101" #
fatalities.loc[509,"LOCATION_RAW"] = "TN 37738" #
fatalities.loc[504,"LOCATION_RAW"] = "TX 78836" #
fatalities.loc[453,"LOCATION_RAW"] = "FL 32899" #
fatalities.loc[449,"LOCATION_RAW"] = "NY 11201" #
fatalities.loc[445,"LOCATION_RAW"] = "IA 50701" #
fatalities.loc[364,"LOCATION_RAW"] = "KY 41413" #
fatalities.loc[318,"LOCATION_RAW"] = "TX 75029" #
fatalities.loc[311,"LOCATION_RAW"] = "MA 02151" #
fatalities.loc[182,"LOCATION_RAW"] = "KY 40201" #

def search_locations(fatalities,not_found,found):
    for mi in not_found:
        row = fatalities.loc[mi]
        address = row.LOCATION_RAW
        location = geolocator.geocode(address)
        sleep(0.5)
        if location != None:
            print "FOUND %s" %(address)
            fatalities = add_entry(index,location,fatalities)
            # Save the address that was used
            fatalities.loc[index,"LOCATION_RAW"] = address
            found.append(mi)
    not_found = [x for x in not_found if x not in found]
    return fatalities,not_found,found

fatalities,not_found,found = search_locations(fatalities,not_found,found)
fatalities = normalize_locations(fatalities)
fatalities.to_csv("data/fatalities_all.tsv",sep="\t")

# One more round! Want to get these all mapped!
# This time I will look up the company address

fatalities.loc[7479,"LOCATION_RAW"] = "TX 78119" #
fatalities.loc[6431,"LOCATION_RAW"] = "TX 79772" # nearby town, pecos TX
fatalities.loc[6384,"LOCATION_RAW"] = "TX 76006" #
fatalities.loc[6301,"LOCATION_RAW"] = "TX 79772" #
fatalities.loc[5996,"LOCATION_RAW"] = "ND 58831" #
fatalities.loc[5976,"LOCATION_RAW"] = "ND 58601" #
fatalities.loc[5389,"LOCATION_RAW"] = "TX 78109" #
fatalities.loc[5020,"LOCATION_RAW"] = "TX 78022" #
fatalities.loc[4932,"LOCATION_RAW"] = "AS 96799" #
fatalities.loc[3758,"LOCATION_RAW"] = "TX 79772" #
fatalities.loc[3666,"LOCATION_RAW"] = "TX 78664" # wrong zip code
fatalities.loc[3344,"LOCATION_RAW"] = "CA 94545" #
fatalities.loc[3133,"LOCATION_RAW"] = "NJ 08754" #
fatalities.loc[2749,"LOCATION_RAW"] = "TX 78376" #
fatalities.loc[2305,"LOCATION_RAW"] = "OK 73040" #
fatalities.loc[1863,"LOCATION_RAW"] = "TX 78542" # wrong zip
fatalities.loc[1635,"LOCATION_RAW"] = "AS 96799" #
fatalities.loc[1492,"LOCATION_RAW"] = "AS 96799" #
fatalities.loc[1406,"LOCATION_RAW"] = "TX 77502" #
fatalities.loc[1335,"LOCATION_RAW"] = "TX 77081" #
fatalities.loc[504,"LOCATION_RAW"] = "TX 78405" #
fatalities.loc[364,"LOCATION_RAW"] = "KY 41412" #
fatalities.loc[318,"LOCATION_RAW"] = "MS 39232" #

samoas = [4932,1635,1492]
for samoa in samoas:
    fatalities.loc[samoa,"LATITUDE"] = 14.2710 
    fatalities.loc[samoa,"LONGITUDE"] = 170.1322

# We don't have altitude data, drop column for now
fatalities = fatalities.drop(["ALTITUDE"],axis=1)

# Which ones don't have latitude and longitude? Run this over until we get them all
not_found = fatalities.index[fatalities.LATITUDE.isnull()==True].tolist()
while len(not_found) > 0:
    index = not_found.pop()
    row = fatalities.loc[index]
    # Try finding the state, and keeping one word before it, adding comma
    address = row.LOCATION_RAW
    # First try removing zip code
    match = re.search("[0-9]{5}",address)
    if match!= None:
        address = address[:match.start()].strip()
        location = geolocator.geocode(address)
        sleep(0.5)
        if location != None:
            print "FOUND %s" %(address)
            fatalities = add_entry(index,location,fatalities)
            # Save the address that was used
            fatalities.loc[index,"LOCATION_RAW"] = address
    else:
        print "No match for %s" %(address)

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

