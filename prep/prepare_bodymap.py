# Prepare bodymap will parse labels from the FMA 
# - including terms likely to be found in social media

import pandas
from svgtools import create_pointilism_svg

# First prepare the svg body!
png_image = "data/body.png"

create_pointilism_svg(png_image,uid_base="bodymap",
                                sample_rate=2,width=330,height=800
                                output_file="data/bodymap.svg"):

# Anatomical entities, Foundational Model of Anatomy
fma = pandas.read_csv("data/FMA.csv",sep=",",low_memory=False)

# Hmm this is too many, need to simplify.
