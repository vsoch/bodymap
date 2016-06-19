# BodyMap

[annotation interface](http://vsoch.github.io/bodymap/)

This project will develop an interactive body map for use with various data visualizations. Generation of svg images and annotation interface courtesy of [svgtools](http://www.github.com/vsoch/svgtools)

**under development!**

Currently, the application displays all US Labor fatality records between the years 2010 and 2015 on a map, and the user can select records by date with an interactive slider, or by clicking on a body part. When selecting by date, the most relevant (indicated by count) word tags appear to the left.

![https://raw.githubusercontent.com/vsoch/bodymap/master/static/img/bodymap.png](https://raw.githubusercontent.com/vsoch/bodymap/master/static/img/bodymap.png)

Changes that need to be made:

 - application will be Dockerized
 - tags will be changed from counts to those words different from some baseline
 - bodymap area will serve as a heatmap to show deaths associated with body part(s)
 - view will be made to show better details for a set of records
