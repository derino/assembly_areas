Locating Safe Assembly Areas: 
==================
The case of Earthquake preparedness in Beylikduzu, Istanbul
==================

# Motivation
Earthquake is the major disaster type in Turkey that accounts for 61% of the collapsed buildings among all disaster 
types in the last 70 years [1]. In the aftermath of the big Istanbul earthquake on August 17, 1999, which claimed 
lives of tens of thousands of people, Turkey has initiated a nation-wide Earthquake-preparedness program and mobilized many of 
its governmental and non-governmental organizations. The goal was to be ready for the next earthquake that was expected to 
hit Istanbul probably within the next 20 years. The strategic report on natural disasters [2] and in particular 
the disaster prevention and mitigation plan [3] for Istanbul provide detailed guidelines for municipalities. One of the 
important items in the guidelines is the allocation of assembly areas. Assembly areas are designated spots 
where people gather immediately after a disaster. 
They help minimize the losses due to secondary effects as well as enable proper organization of the recovery activities.
It is crucial that every citizen is well informed about the nearest assembly area to their house, workplace or 
current location.

Over the years as the memory of the 1999 Earthquake has faded away, the commitment to fight the next earthquake seems 
to have also vanished.
It has been reported by several newspapers that the municipalities were issuing building permits in the reserved assembly areas, 
which should normally remain as open space and building-free [4]. Recently some newspapers reported that 
Disaster and Emergency Management Authority (AFAD) was hiding information about assembly areas from the public [5].
At the time of writing, AFAD requires one to send an e-mail with the name and address of the person to get the location
of the nearest assembly area for that address. It is left to the reader to judge whether this is a good practice to 
spread such crucial information.

Searching for a dataset of assembly points, we have come across the great work that Municipality of Beylikduzu (Istanbul)
has done (http://beylikduzuhazir.com). Aside from publishing a comprehensive emergency response plan, they have created a mobile app for the citizens to get them prepared for the earthquake. Most importantly, they have provided a web form that shows
the assembly point on the map for a given address.

# Goal
This work aims at solving the problem of finding assembly areas for cities where 
such information is not available or made public.

- Understand the features that qualify an area as an assembly area.
- Check whether these features can be derived programmatically with the map data.
- Develop an algorithm to determine the assembly areas in a given region,
  possibly by training a classification model with the Beylikduzu dataset.


# What has been accomplished

### Created the Beylikduzu dataset

We have written a script that uses four REST endpoints from the Municipality of Beylikduzu 
to collect the addresses of around 45'000 houses and the coordinates of 
the assembly area they are associated to.

Then the coordinates of each address is obtained using the HERE Batch Geocoder API.
Some heuristics are used to filter out incorrectly geocoded addresses. 

[Link to the dataset](https://github.com/derino/assembly_areas/raw/master/data/beylikduzu.zip)

### A map of assembly points

[Go to map](http://geojson.tools/index.html?url=https://xyz.api.here.com/hub/spaces/AEaJeP73/search?limit=5000&access_token=xAwk52zn8nbnijis8ZhTBA)

![Beylikduzu assembly points](https://github.com/derino/assembly_areas/raw/master/imgs/beylikduzu_assembly_points.png)

*Assembly points in Beylikduzu*

### A map of every house in Beylikduzu with the assembly area added as a property
This makes it possible to see all other houses that share the same assembly area 
(by clicking on the property named "area").

[Go to the map](http://geojson.tools/index.html?url=https://xyz.api.here.com/hub/spaces/OdtvVjSm/search?limit=5000&access_token=xAwk52zn8nbnijis8ZhTBA)

This information is not available elsewhere. We believe this is important because 
people can spread this information to their neighbors 
that are assigned to the same assembly area.

![Addresses assigned to the assembly point P159](https://github.com/derino/assembly_areas/raw/master/imgs/P159.png)

*Example of addresses assigned to an assembly point*


### Ability to detect incorrect assignments of houses to assembly areas 

![Bad assignment](https://github.com/derino/assembly_areas/raw/master/imgs/bad_assignment_example.png)

*Example of bad/distant assignment*

This can be due to a manual error 
or it can be that some houses are assigned to distant assembly areas in order to 
comply with the population constraints of an assembly area. 

### A map of the convex hull of the buildings that share an assembly point.

![Inferred regions for each assembly point](https://github.com/derino/assembly_areas/raw/master/imgs/assignment_polygons.png)

*Inferred regions for each assembly point*

We observe that there are many overlapping polygons. 
This is an indication of non-optimal house-assembly point association.

### Auto-generation of such polygons by using the map
 
![Generated map faces](https://github.com/derino/assembly_areas/raw/master/imgs/faces_example.png)

These polygons can help municipalities during the allocation of buildings to assembly areas.
Faces are generated by using the topology and roads layers in TMOB.

# Conclusion
Maps and location data can be great tools for effective disaster management.
We had an ambitious goal for the short duration of the hackathon and we discovered 
several challenges during the week, such as,
- Beylikduzu data only has assembly points and not assembly polygons.
- Geocoding was not perfect. Took time to clean some results.
- The planned machine learning task could not be done due to lack of data, mainly, 
population per building, height of the buildings (number of floors), 
incomplete building footprints. 
(note: an assembly area has to be as far as twice the height of any nearby building)

# Acknowledgment
We would like to thank the HERE team for the following tools:
- XYZ
- TMOB
- Batch Geocoder

# References

1. Ergunay, O. 1999, A Perspective of Disaster in Turkey: Issues and Prospects, Urban
Settlements and Natural Disasters, Proceedings of UIA Region II Workshop,
Chamber of Architects of Turkey

2. Japon Uluslararası İşbirliği Ajansı ( JICA) (2004). “Türkiye’de Doğal Afetler
Konulu Ülke Strateji Raporu”, Ankara.

3. Japon Uluslararası İşbirliği Ajansı ( JICA) İstanbul Büyükşehir Belediyesi
(İBB). (2002). Türkiye Cumhuriyeti, İstanbul İli Sismik Mikro-Bölgeleme Dâhil 
Afet Önleme/Azaltma Temel Planı Çalışması, İstanbul.

4. "İstanbul'da sığınacak yer yok" Cumhuriyet Gazetesi Haber Portali (13 Mayıs 2017)
http://www.cumhuriyet.com.tr/haber/cevre/740101/istanbul_da_siginacak_yer_yok.html

5. "İstanbul'daki deprem toplanma alanları halktan gizleniyor", Cumhuriyet Gazetesi Haber Portali (17 Ağustos 2017)
http://www.cumhuriyet.com.tr/haber/turkiye/805778/istanbul_daki_deprem_toplanma_alanlari_halktan_gizleniyor.html
