#!/usr/bin/python

from numpy.random import choice
from PIL import Image
import pandas
import numpy
import json
import os

# svg functions 
def get_coordinates(png_image,transparent_filter=True,white_filter=True,sample_rate=2):
    """get_coordinates: reads in a png image, and returns xy coordinates of non transparent pixels 
    :param png_image: the image to read
    :param transparent_filter: don't include transparent pixels (default True)
    :param white_filter: don't include white pixels (default True)
    :param sample_rate: the sampling rate to include in range (eg, every N pixel)
    """

    img = Image.open(png_image)
    width, height = img.size

    # make a list of all pixels in the image
    pixels = img.load()
    coords = []
    data = []
    for x in range(0,width,sample_rate):
        for y in range(0,height,sample_rate):
            cpixel = pixels[x, y]
            coords.append([x,y])
            data.append(cpixel)

    print "Parsing %s pixels for image of size %sx%s with sample rate %s" %(len(data),width,height,sample_rate)
    print "To decrease time, you can increase the sample rate."

    df = pandas.DataFrame(columns=["x","y"])
    count = 0
    for x in range(len(data)):
        include_point = True

        # Include transparent filter?
        if transparent_filter==True:
            if (data[x][3] == 0):
                include_point = False

        # Include white filter?
        if white_filter == True:
            if (data[x][0] == 255 and data[x][1] == 255 and data[x][2] == 255):
                include_point = False

        if include_point == True:
            df.loc[count] = coords[x]
            count+=1

    print "Finished adding %s pixel coordinates." %(count+1)
    return df


def create_circle(uid,x,y,diameter=1,fill_opacity=1,fill="#666666",stroke="none",
                  upper_leftx=10,upper_lefty=10):
    '''create_circle returns a circle path (right now most is hard coded)
    :uid: the identifier to give the circle path
    :x: x coordinate
    :y: y coordinate
    :diameter: diameter of circle, in pixels (default is 4)
    :param fill_opacity: default 1
    :param fill: default gray (#666666)
    :stroke: default is none
    :param upper_leftx: upper left x coordinate
    :param upper_lefty: upper left y coordinate
    '''
    circle = '''<path
       d="m %s,%s a 2.2728431,2.2728431 0 1 1 -4.54569,0 2.2728431,2.2728431 0 1 1 4.54569,0 z"
       transform="matrix(0.87995515,0,0,0.87995515,%s,%s)"
       id="%s"
       style="fill:%s;fill-opacity:%s;stroke:%s" />''' %(upper_leftx,upper_lefty,
                                                         x,y,uid,fill,fill_opacity,stroke)
    return circle


def create_pointilism_svg(png_image,uid_base="uid",transparent_filter=True,white_filter=True,
                          sample_rate=2,width=300,height=900,diameter=4,fill_opacity=1,
                          fill="#666666",stroke="none",output_file=None):
    '''create_svg will return an svg string (or file, if output specified) for some png_image.
    :param png_image: the image to read
    :param transparent_filter: don't include transparent pixels (default True)
    :param white_filter: don't include white pixels (default True)
    :param sample_rate: the sampling rate to include in range (eg, every N pixel)
    :output_file: if specified, will save svg to file, Otherwise returns string
    :diameter: diameter of circle, in pixels (default is 4)
    :param fill_opacity: default 1
    :param fill: default gray (#666666)
    :stroke: default is none
    '''
    coords = get_coordinates(png_image,transparent_filter=transparent_filter,
                                       white_filter=white_filter,
                                       sample_rate=sample_rate)
    base = get_svg_base(uid_base,width,height)
    paths = ""

    print "Generating paths..."
    for uid,xy in coords.iterrows():
        path = create_circle(uid,x=xy["x"],y=xy["y"],
                             diameter=diameter,
                             fill_opacity=fill_opacity,
                             fill=fill,
                             stroke=stroke)
        paths = "%s\n%s" %(paths,path)
        
    svg = base.replace("[SUB_PATHS_SUB]",paths)
    if output_file == None:
        return svg
    save_svg(output_file,svg)

def save_svg(output_file,svg):
    print "Saving svg file to %s" %(output_file)
    filey = open(output_file,"w")
    filey.writelines(svg)
    filey.close()


def get_svg_base(uid,width=700,height=1000):
    return '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   version="1.1"
   width="%s"
   height="%s"
   id="%s">
  <defs
     id="defs66559" />
  <metadata
     id="metadata66562">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title></dc:title>
      </cc:Work>
    </rdf:RDF>
  </metadata>
  <g
     id="layer1">
   [SUB_PATHS_SUB]
   />
  </g>
</svg>''' %(width,height,uid)

# utils 
def read_json(json_file):
    '''read_json reads in a json structure, corresponding to different regions to annotate
    :param json_file: path to json_file
    '''
    return json.load(open(json_file,'r'),encoding="utf-8")

# generate annotator
def generate_annotator(svg_file,labels):
    '''generate_annotator will return a static web page to allow for annotation of an svg image with some set of labels.
    :param svg_file: full path to svg file to annotate
    :param labels: list of labels to provide to user
    '''
    template = "\n".join(open("data/annotator.html","r").readlines())
    svg = "\n".join(open(svg_file,"r").readlines())
    
