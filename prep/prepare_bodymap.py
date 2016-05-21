# Prepare bodymap will parse labels from the FMA 
# - including terms likely to be found in social media

from svgtools import create_pointilism_svg
from glob import glob
import pandas
import re

# First prepare the svg body!
png_image = "data/body.png"

create_pointilism_svg(png_image,uid_base="bodymap",
                                sample_rate=8,width=330,height=800,
                                output_file="data/bodymappp.svg")

# Next prepare data for fatalities

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

# Now prepare for annotation of yaml_file
# (can I do this without a server?)
yaml_file="data/simpleFMA.yml"


# Anatomical entities, Foundational Model of Anatomy
fma = pandas.read_csv("data/FMA.csv",sep=",",low_memory=False)

# Hmm this is too many, need to simplify.
