# coding: utf-8
import json
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
NULL, INT, FLOAT, STRING = 0, 1, 2, 3

def guess_type(value):
    if value is None:
        return (NULL, 0)
    elif isinstance(value, int):
        return (INT, 4 if value > 256 else 2)
    elif isinstance(value, float):
        return (FLOAT, 8)
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
        raise TypeError("Data is not a Feature Collection")
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
    return {'geometry_type': geometry_type or "POINT",
            'fields': fields,
            'field_names': {f: None for f in fields}}

def sane_field_name(field_name, field_index, used_field_names):
    if not (field_name or '1')[0].isalpha():
        field_name = "F" + field_name
        field_name = re.sub("[^a-z0-9]+", "_", field_name, flags=re.I)[:8]
        if field_name not in used_field_names:
            return field_name
        num = 1
        f_field_name = field_name
        while f_field_name in used_field_names:
            fieldstring = str(num)
            f_field_name = field_name[:-len(fieldstring)] + fieldstring
            num += 1
        return f_field_name

def create_feature_class(catalog_path, out_schema):
    arcpy.management.CreateFeatureclass(os.path.dirname(catalog_path),
                                        os.path.basename(catalog_path),
                                        out_schema['geometry_type'])
    used_field_names = set()
    for field_index, field_name in enumerate(sorted(out_schema['fields'])):
        sane_field_name = fix_field_name(field_name, field_index,
                                         used_field_names)
        used_field_names.add(sane_field_name)
        out_schema['field_names'][field_name] = sane_field_name
        field_type, field_length = field_info(out_schema['fields'][field_name])
        arcpy.management.AddField(catalog_path, sane_field_name, field_type,
                                  field_length=field_length,
                                  field_alias=field_name,
                                  field_is_nullable="NULLABLE")

def write_features(out_feature_class, json_struct):
    raise NotImplementedError()

def geojson_to_feature(in_geojson, out_feature_class):
    json_struct = load_geojson_struct(in_geojson)
    out_schema = determine_schema(json_struct)
    create_feature_class(out_feature_class, out_schema)
    write_features(out_feature_class, out_schema, json_struct)