# coding: utf-8
import os
import urllib2

import arcpy

def load_geojson_struct(in_json_location):
    in_handle = None
    if os.path.isfile(in_json_location):
        in_handle = open(in_json_location, 'rb')
    else:
        in_handle = urllib2.urlopen(in_json_location)
    return json.load(in_handle)

# "Enumeration" for field type guesser
INT, FLOAT, STRING = 0, 1, 2

def guess_type(value):
    if value is None:
        return (INT, 0)
    elif isinstance(value, int):
        return (INT, 1)
    elif isinstance(value, float):
        return (FLOAT, 1)
    else:
        if not isinstance(value, basestring):
            value = json.dumps(value)
        return (STRING, len(value))

def determine_schema(json_struct):
    geometry_type_mapping  = {
        'LineString': "POLYLINE",
        'MultiLineString': "POLYLINE",
        'Point': "POINT",
        'Polygon': "POLYGON",
        'MultiPolygon': "POLYGON"
    }

    if not json_struct.get("type", None) == "FeatureCollection":
        raise TypeError("JSON is not a Feature Collection")
    geometry_type = None
    fields = {}
    for item in json_struct.get("features", []):
        # Ensure geometry type consistency
        geometry = item['geometry']
        row_geometry_type = geometry['type']
        if row_geometry_type not in geometry_type_mapping:
            raise ValueError(row_geometry_type)
        elif geometry_type is None:
            geometry_type = geometry_type_mapping[row_geometry_type]
        elif geometry_type_mapping[row_geometry_type] != geometry_type:
            raise TypeError("Inconsistent geometry types")
        # Set up fields
        for field_name, field_value in item['properties'].iteritems():
            guessed_type = guess_type(field_value)
            if field_name not in fields or guessed_type > fields[field_name]:
                fields[field_name] = guessed_type
    return (geometry_type, fields)

def create_feature_class(catalog_path, out_schema):
    raise NotImplementedError()

def write_features(out_feature_class, json_struct):
    raise NotImplementedError()

def geojson_to_feature(in_geojson, out_feature_class):
    json_struct = load_geojson_struct(in_geojson)
    out_schema = determine_schema(json_struct)
    create_feature_class(out_feature_class, out_schema)
    write_features(out_feature_class, json_struct)