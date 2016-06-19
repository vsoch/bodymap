from flask import Flask, render_template, request, jsonify
from flask_restful import Resource, Api
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

            # Date range to start with (loaded data)
            self.start_date = "3/20/2010"
            self.end_date = "5/20/2012"

            # load data on start of application
            self.bodymap = "".join(open("data/bodymap.svg","r").readlines())
            self.labels = json.load(open("data/simpleFMA.json","r"))
            self.deaths = json.load(open("data/injuries_index.json","r"))
            self.fatalities = pandas.read_csv("data/fatalities_all.tsv",sep="\t",index_col=1)
            self.fatalities = self.fatalities.drop(["LATITUDE","LONGITUDE","LOCATION_RAW",
                                                    "LATITUDE_EPSG3857","LONGITUDE_EPSG3857",
                                                    "LOCATION_IMPORTANCE","ALTITUDE"],axis=1)
            self.fatalities = self.fatalities.rename(index=str, columns={"Unnamed: 0":"id"})

            # This takes a bit of computation and should be run at startup
            self.fatalities['INCIDENT_DATETIME'] = pandas.to_datetime(self.fatalities["INCIDENT_DATE"])
            self.wordcounts = pandas.read_csv("data/wordcounts.tsv",sep="\t",index_col=0)

            # generate list of descriptions associated with ids
            self.descriptions = self.fatalities.DESCRIPTION.copy()    
            self.descriptions.index = self.fatalities.id.tolist()  
            self.descriptions = self.descriptions.to_dict()      

app = BodyMapServer(__name__)
api = Api(app)

# API VIEWS ##########################################################################################

class apiIndex(Resource):
    """apiIndex
    Main view for REST API to display all available fatalities data
    """
    def get(self):
        fatalities_json = app.fatalities.to_dict(orient="records")
        fatalities_json = parse_unicode(fatalities_json)
        return fatalities_json

class apiQueryDates(Resource):
    """apiQueryDates
    return a list of ids for points that are within a range of dates
    /api/dates/0/6/2010/0/6/2010
    """
    def get(self, sm, sd, sy, em, ed, ey):
        start_date = pandas.to_datetime("%s/%s/%s" %(sm,sd,sy))
        end_date = pandas.to_datetime("%s/%s/%s" %(em,ed,ey))
        subset = app.fatalities[app.fatalities.INCIDENT_DATETIME >= start_date]
        subset = subset[subset.INCIDENT_DATETIME <= end_date]

        # Also return wordcounts
        # TODO: we probably want to find words that are different from some baseline
        words = app.wordcounts.loc[subset.index].sum()
        words = words[words>0].sort_values(ascending=False)

        return {"ids": subset.id.tolist(),
                "words":zip(words.index[0:60],words.values[0:60])}
              
# Add all resources
api.add_resource(apiIndex,'/api/deaths') # start month, day, year / end month, date, year
api.add_resource(apiQueryDates,'/api/dates/<int:sm>/<int:sd>/<int:sy>/<int:em>/<int:ed>/<int:ey>')


# Global variables and functions #####################################################################

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
            if isinstance(value,int) or isinstance(value,float):
                new_entry[key] = value
            else:
                new_entry[key] = unicode(value,"ISO-8859-1").encode('ascii',errors='replace').replace('?','')
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


# Views ##############################################################################################

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

    return render_template("map.html",bodymap=app.bodymap,
                                      labels=app.labels,
                                      deaths=deaths,
                                      descriptions=app.descriptions)
if __name__ == "__main__":
    app.debug = True
    app.run()

