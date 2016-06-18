from flask import Flask, render_template, request
from random import choice
import itertools
import random
import numpy
import json
import pandas
import pickle
import re


# SERVER CONFIGURATION ##############################################
class BodyMapServer(Flask):

    def __init__(self, *args, **kwargs):
            super(BodyMapServer, self).__init__(*args, **kwargs)

            # load data on start of application
            self.bodymap = "".join(open("data/bodymap.svg","r").readlines())
            self.labels = json.load(open("data/simpleFMA.json","r"))
            self.deaths = json.load(open("data/injuries_index.json","r"))
            self.fatalities = pandas.read_csv("data/fatalities_all.tsv",sep="\t",index_col=1)
            self.fatalities = self.fatalities.drop(["LATITUDE","LONGITUDE","LOCATION_RAW",
                                                    "LATITUDE_EPSG3857","LONGITUDE_EPSG3857",
                                                    "LOCATION_IMPORTANCE","ALTITUDE"],axis=1)
            self.fatalities = self.fatalities.rename(index=str, columns={"Unnamed: 0":"id"})
            # generate list of descriptions associated with ids
            self.descriptions = self.fatalities.DESCRIPTION.copy()    
            self.descriptions.index = self.fatalities.id.tolist()  
            self.descriptions = self.descriptions.to_dict()      

app = BodyMapServer(__name__)

# Global variables and functions

def parse_unicode(meta):
    '''parse_unicode: decodes to utf-8 and encodes in ascii, replacing weird characters with empty space.
    :param meta: a dictionary or list of dictionaries to parse
    '''
    if not isinstance(meta,list):
        meta = [meta]

    parsed = []
    for entry in meta:
        new_entry = dict()
        for key,value in entry.iteritems():
            if key == "authors":
                authors = value.decode('utf-8').encode('ascii',errors='replace').replace('?',' ')
                new_entry[key] = ", ".join(parse_authors(authors))
            elif key == "score": # This is a float
                new_entry[key] = value
            elif key == "url": # Don't want to replace ? with space
                new_entry[key] = value.decode('utf-8').encode('ascii',errors='replace')                 
            else:
                new_entry[key] = value.decode('utf-8').encode('ascii',errors='replace').replace('?',' ')
        parsed.append(new_entry)
    return parsed


def random_colors(concepts):
    '''Generate N random colors (not used yet)'''
    colors = {}
    for x in range(len(concepts)):
        concept = concepts[x]
        r = lambda: random.randint(0,255)
        colors[concept] = '#%02X%02X%02X' % (r(),r(),r())
    return colors


@app.route("/")
def index():
    '''index view displays the bodymap'''
    return render_template("index.html",bodymap=app.bodymap,
                                        labels=app.labels)

@app.route("/detail")
def detail():
    '''view details for a set of ids'''
    # We will render dates across the bottom along with general counts
    # need lookup with date --> ids
    dates = app.fatalities["INCIDENT_DATE"].copy()
    dates.index = app.fatalities["id"]
    dates = pandas.DataFrame(dates).groupby(by="INCIDENT_DATE").groups

    df = pandas.DataFrame(columns=["date","count"])
    df["date"] = dates.keys()
    df["count"] = [len(dates[x]) for x in dates.keys()]

    return render_template("brush.html",bodymap=app.bodymap,
                                        labels=app.labels,
                                        descriptions=app.descriptions,
                                        dates=df.to_dict(orient="records"),
                                        lookup=dates)

@app.route("/map")
def bodymap():
    '''view deaths via bodymap'''
    deaths = dict()
    for part,idx in app.deaths.iteritems():
        deaths[str(part)] = idx

    # Get a list of dates
    dates = app.fatalities.INCIDENT_DATE.tolist()
    dates.sort()

    return render_template("map.html",bodymap=app.bodymap,
                                      labels=app.labels,
                                      deaths=deaths,
                                      descriptions=app.descriptions,
                                      start_date=dates[0],
                                      end_date=dates[-1])

if __name__ == "__main__":
    app.debug = True
    app.run()

