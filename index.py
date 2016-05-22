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

@app.route("/map")
def bodymap():
    '''view deaths via bodymap'''
    return render_template("map.html",bodymap=app.bodymap,
                                      labels=app.labels)

@app.route("/summary")
def summary_view():
    '''summary view (not yet developed) will have summary statistics and global / high level plots
    '''
    methods = app.pubs.columns.tolist() 
    authors = app.authors.index.tolist()
    return render_template("index.html",methods=methods,
                                        authors=authors)    

@app.route("/method",methods=['POST','GET'])
def view_method():
    '''view_method views a list of publications most strongly associated with a particular method, 
    and gives the user the option to explore by clicking on an author. If POST data is provided, 
    the method is retrieved from the POST, otherwise a random method is selected
    '''
    methods = app.pubs.columns.tolist() 
    authors = app.authors.index.tolist()

    if request.method == "POST":
        method = request.form["method"]
    else:
        method = choice(methods)

    print "Method is %s" %(method)
 
    # Get publications and meta data for most highly matched papers
    ranked_papers = app.pubs[method].copy()
    ranked_papers.sort(inplace=True,ascending=False)
    ranked_papers = ranked_papers[ranked_papers>0]
    pub_ids = ranked_papers[ranked_papers>0].index.tolist()
    pub_meta, publications = get_publications(pub_ids,return_dict=False)
    pub_meta["score"] = ranked_papers.loc[pub_meta.index.tolist()]
    pub_meta = parse_unicode(pub_meta.to_dict(orient="records"))

    return render_template("method.html",methods=methods,
                                        authors=authors,
                                        themethod=method,
                                        pubs_meta=pub_meta,
                                        publications=publications,
                                        ranked_papers=ranked_papers.to_dict())

@app.route("/author",methods=['POST','GET'])
def view_author():
    '''view_author views a list of abstracts and associated meta data, and a table of method scores 
    for a particular author. If POST data is provided, the author is retrieved from the POST, 
    otherwise a random author is selected
    '''
    methods = app.pubs.columns.tolist() 
    authors = app.authors.index.tolist()

    # Retrieve author selection, or select randomly
    if request.method == "POST":
        author = request.form["author"]
    else:
        author = choice(authors)
    
    print "Author is %s" %(author)

    # Prepare meta data about papers
    pub_ids = app.authors.loc[author][app.authors.loc[author]!=0].index.tolist()
    pub_meta, publications = get_publications(pub_ids)

    # What methods does the author most strongly match to?
    ranked_methods = publications.mean()
    ranked_methods.sort_values(inplace=True,ascending=False)
    ranked_methods = ranked_methods[ranked_methods.isnull()==False]
    ranked_methods = ranked_methods.to_dict()

    return render_template("author.html",methods=methods,
                                         author=author,
                                         authors=authors,
                                         ranked_methods=ranked_methods,
                                         pubs_meta=pub_meta,
                                         publications=publications.to_dict(orient="records"))


if __name__ == "__main__":
    app.debug = True
    app.run()

