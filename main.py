import logging
import requests
import os
import sys
import pandas as pd
from collections import namedtuple
from shapely.geometry import Point, MultiPoint
import geojson
from geojson import FeatureCollection, Feature
import random

import locale
locale.setlocale(locale.LC_ALL, 'tr_TR.utf8')

logger = logging.getLogger(__name__)


BoundingBox = namedtuple("BoundingBox", ['min_lat', 'max_lat', 'min_lon', 'max_lon'])

def get_url_as_json(url, params=None):
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()


def convert_json_to_dataframe(json_objects, fields):
    data = {}
    for f in fields:
        data[f] = [o[f] for o in json_objects]
    df = pd.DataFrame(data=data, columns=fields)
    return df


neighbourhood_url = "http://www.beylikduzuhazir.com/Home/GetAllNeighborhood"
neighborhood_fields = ['id', 'neighborhoodid', 'neighborhoodname']
neighborhoods_csv = 'neighborhoods.csv'

street_url = "http://www.beylikduzuhazir.com/Home/GetStreetByNeighborhoodName"
street_fields = ['id', 'streetid', 'streetname']
streets_csv = 'streets.csv'

door_url = "http://www.beylikduzuhazir.com/Home/GetDoorNoByStreetId"
door_fields = ['id', 'neighborhood', 'street', 'addresstype', 'doorno', 'area', 'editor', 'datecreated', 'datemodified', 'rowversion']
doors_csv = 'doors.csv'

coordinate_url = "http://www.beylikduzuhazir.com/Home/GetCoordinateByDoorNo"
coordinates_csv = 'coordinates.csv'

batch_geocode_url = 'https://batch.geocoder.api.here.com/6.2/jobs'
app_id = ''
app_code = ''

beylikduzu_bbox = BoundingBox(40.955247, 41.031174, 28.591098, 28.700961)


def run():
    logging.basicConfig(level=logging.DEBUG)
    
    # Scrape Beylikduzu data 
    doors_df, areas_df = fetch_data()
    
    # Involves some manual steps (retriving the result as zip and unzipping) after the following call.
    # geocode_addresses(doors_df)
    # TODO: poll the status of the batch job and auto-get the result.

    # manually rename displayLatitude -> latitude and also for lon; street => street_name.
    geocoder_result_file = 'geocoder_result_20180822-10-28_out.csv'
    assert os.path.exists(geocoder_result_file)

    # Merge geocoded data with doors data
    if not os.path.exists('geocoded_doors_with_meeting_point_coords.csv'):
        geocoded_df = pd.read_csv(geocoder_result_file, delimiter='|')
        assert 'latitude' in geocoded_df.columns and 'longitude' in geocoded_df.columns

        # select the first result if multiple were returned
        geocoded_df = geocoded_df.loc[geocoded_df['SeqNumber'] == 1].reset_index()
        # geocoded_df['correct_geocoding'] = check_geocoding(geocoded_df, beylikduzu_bbox)
        geocoded_df.to_csv('unique_geocoded.csv')

        assert geocoded_df.shape[0] == doors_df.shape[0]
        # geocoded_doors_df = pd.concat([doors_df, geocoded_df], axis=1)
        geocoded_doors_df = doors_df.merge(geocoded_df, left_index=True, right_index=True)

        geocoded_doors_df.to_csv('deneeeeee.csv')
        # print(geocoded_doors_df.loc[geocoded_doors_df['recId'] == 42.0, 'locationLabel'].iloc[0].lower())  # 40602
        # print(geocoded_doors_df.loc[geocoded_doors_df['recId'] == 42.0, 'street'].iloc[0].lower())
        # return
        geocoded_doors_df['correct_geocoding'] = check_geocoding(geocoded_doors_df, beylikduzu_bbox)
        geocoded_doors_df.to_csv('geocoded_doors_with_meeting_point_coords.csv', index=False)
    else:
        geocoded_doors_df = pd.read_csv('geocoded_doors_with_meeting_point_coords.csv')

    # Generate geojson colored by area.
    area_colors = {}
    with open('area_colors.txt', 'w') as color_file:
        for area in geocoded_doors_df['area'].unique():  # areas_df['area']:
            c = get_random_color()
            area_colors[area] = c
            color_file.write("%s,%s\n" % (area, c))

    print("Number of door numbers: %d" % geocoded_doors_df.shape[0])
    geocoded_doors_df = geocoded_doors_df.loc[geocoded_doors_df['correct_geocoding'] == True]
    # geocoded_doors_df.to_csv('correctly_geocoded_doors_with_meeting_point_coords.csv')
    print("Number of correctly geocoded door numbers: %d" % geocoded_doors_df.shape[0])
    
    # geocoded_doors_df = geocoded_doors_df.loc[geocoded_doors_df['locationLabel'].unique()]
    # print("Number of unique location labels: %d" % geocoded_doors_df['locationLabel'].unique().shape[0])

    geocoded_doors_df.to_csv('correctly_geocoded_doors_with_meeting_point_coords.csv')

    write_area_coverage(geocoded_doors_df, area_colors)
    write_geojson(geocoded_doors_df, area_colors)


def write_area_coverage(geocoded_doors_df, area_colors):
    features = []
    for area, group_val in geocoded_doors_df.groupby(['area']):
        points = []
        for row in group_val.itertuples():
            points.append((row.latitude, row.longitude))
        area_polygon = MultiPoint(points).convex_hull
        props = {
                    'fill-color': area_colors[area],
                    'line-width': '0',
                    'area': str(row.area)
        }
        feature = Feature(geometry=area_polygon, properties=props)
        features.append(feature)
    write_features_as_geojson(features, "meeting_areas-mine.geojson")


def write_geojson(geocoded_doors_df, area_colors):
    features = []
    for row in geocoded_doors_df.itertuples():
        props = {
                    'fill-color': area_colors[row.area],
                    'line-width': '0',
                    'area': str(row.area)
        }
        # for f in row._fields:
        #     props[f] = getattr(row, f)
        
        p = Point(row.longitude, row.latitude) # xyz-style
        # p = Point(row.latitude, row.longitude)  # wgt-style
        feature = Feature(geometry=p, properties=props)
        features.append(feature)
    write_features_as_geojson(features, "geocoded_doors_with_meeting_point_coords-mine.geojson")

def write_features_as_geojson(features, geojson_name):
    feature_collection = FeatureCollection(features)
    with open(geojson_name, 'w') as geojson_file:
        dump = geojson.dumps(feature_collection)
        geojson_file.write(dump)
    


def get_random_color(opacity=0.4):
    return "rgba(%d, %d, %d, %.2f)" % (random.randint(0, 255),
                                       random.randint(0, 255),
                                       random.randint(0, 255),
                                       opacity)


def coord_is_within(coord, bbox: BoundingBox):
    return bbox.min_lat <= coord[0] <= bbox.max_lat and bbox.min_lon <= coord[1] <= bbox.max_lon


lower_map = {
    ord(u'I'): u'ı',
    ord('İ'): 'i'
}

def _check_geocoding(geocoded_row, bbox):
    try:
        locationLabel = geocoded_row.locationLabel.translate(lower_map).lower()
    except AttributeError:
        # print(geocoded_row.locationLabel)
        # print(geocoded_row.street)
        return False
    try:
        street = geocoded_row.street.translate(lower_map).lower()
    except AttributeError:
        # print(geocoded_row.street)
        return False
    street_found = locationLabel.find(street + ' ') == 0  # >= 0

    try:
        mahalle = geocoded_row.neighborhood.translate(lower_map).lower()
    except AttributeError:
        # print(geocoded_row.street)
        return False
    mahalle_found = locationLabel.find(mahalle) >= 0
    
    # if not street_found:
    #     print("%s %s" % (geocoded_row.locationLabel, locationLabel))
    #     print("%s %s" % (geocoded_row.street, street))
    #     # sys.exit(0)
    return coord_is_within([geocoded_row.latitude, geocoded_row.longitude], bbox) \
           and street_found and mahalle_found

def check_geocoding(points_df, bbox):
    """
    @return: A pandas series that indicates whether the point in the corresponding index is inside the given bounding box or not.
    """
    result = []
    for row in points_df.itertuples():
        result.append(_check_geocoding(row, bbox))
    return result

def _generate_post_data(addresses_df):

    rows = ['recId|searchText|country']
    for i, row in enumerate(addresses_df.itertuples()):
        if row.addresstype.upper() == 'CADDE':
            street_type = 'Caddesi'
        elif row.addresstype.upper() == 'SOKAK':
            street_type = 'Sokak'
        elif row.addresstype.upper() == 'BULVAR':
            street_type = 'Bulvarı'
        else:
            street_type = row.addresstype
            print("new street type: %s" % street_type)
        row_str = "{recId}|{street} {street_type} {house_number} {neighborhood} Beylikdüzü Istanbul|TUR".format(recId=i+1,
                                                                                                                neighborhood=row.neighborhood,
                                                                                                                street=row.street,
                                                                                                                street_type=street_type,
                                                                                                                house_number=row.doorno)
        rows.append(row_str)
    post_data = '\n'.join(rows)
    with open('post_data.txt', 'w') as p:
        p.write(post_data)
    return post_data


def geocode_addresses(addresses_df):

    post_str = _generate_post_data(addresses_df)

    # print(post_str)
    params = {
        'gen': '8',
        'app_id': app_id,
        'app_code':  app_code,
        'action': 'run',
        'mailto': '',
        'header': 'true',
        'indelim': '|',
        'outdelim': '|',
        'outcols': 'displayLatitude,displayLongitude,locationLabel,houseNumber,street,district,city,postalCode,county,state,country',
        'outputCombined': 'false'
    }
    r = requests.post(batch_geocode_url, params=params, data=post_str.encode('utf-8'))
    print(r.text)


def fetch_data():
    """
    @return: (DataFrame of addresses and their meeting coordinates, DataFrame of only meeting points).
    """

    # Get Neighborhoods
    if not os.path.exists(neighborhoods_csv):
        neighborhoods = get_url_as_json(neighbourhood_url)
        neighborhoods_df = convert_json_to_dataframe(neighborhoods, neighborhood_fields)
        neighborhoods_df.to_csv(neighborhoods_csv, index=False)
    else:
        neighborhoods_df = pd.read_csv(neighborhoods_csv)

    # Get streets
    if not os.path.exists(streets_csv):
        street_dfs = []
        for row in neighborhoods_df.itertuples():
            neighborhood_streets = get_url_as_json(street_url, params={'streetname': row.neighborhoodname})
            neighborhood_streets_df = convert_json_to_dataframe(neighborhood_streets, street_fields)
            neighborhood_streets_df['neighborhood_id'] = row.id
            street_dfs.append(neighborhood_streets_df)
        streets_df = pd.concat(street_dfs)
        streets_df.to_csv(streets_csv, index=False)
    else:
        streets_df = pd.read_csv(streets_csv)

    # Get doors
    if not os.path.exists(doors_csv):
        door_dfs = []
        for row in streets_df.itertuples():
            street_doors = get_url_as_json(door_url, params={'neighborhoodname': row.streetid, 'streetname': row.streetname})
            street_doors_df = convert_json_to_dataframe(street_doors, door_fields)
            door_dfs.append(street_doors_df)
        doors_df = pd.concat(door_dfs)
        doors_df.to_csv(doors_csv, index=False)
    else:
        doors_df = pd.read_csv(doors_csv)

    # Get coordinates
    if not os.path.exists(coordinates_csv):
        doors_df['meetLatitude'] = None
        doors_df['meetLongitude'] = None
        for area in doors_df['area'].unique():
            area_coordinates = get_url_as_json(coordinate_url, params={'doorno': area})
            doors_df.loc[doors_df['area'] == area, ['meetLatitude', 'meetLongitude']] = float(area_coordinates[0]['latitude'].replace(',', '.')), \
                                                                                        float(area_coordinates[0]['longitude'].replace(',', '.'))
        
        doors_df.to_csv(coordinates_csv, index=False)
        coordinates_df = doors_df
    else:
        coordinates_df = pd.read_csv(coordinates_csv)

    # Write meeting_points.csv
    if not os.path.exists("meeting_points.csv"):
        rows = []
        for area, group_val in coordinates_df.groupby(['area']):
            rows.append([area, group_val.iloc[0]['meetLatitude'], group_val.iloc[0]['meetLongitude']])
        areas_df = pd.DataFrame(data=rows, columns=['area', 'latitude', 'longitude'])
        areas_df.to_csv("meeting_points.csv", index=False)
    else:
        areas_df = pd.read_csv("meeting_points.csv")

    return coordinates_df, areas_df


if __name__ == '__main__':

    try:
        run()
    except KeyboardInterrupt:
        logger.error('Program interrupted!')
    finally:
        logging.shutdown()
