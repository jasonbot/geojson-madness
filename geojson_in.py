# coding: utf-8
import json
import os
import re
import urllib2

import arcpy

def load_geojson_struct(in_json_location):
    arcpy.AddMessage("Importing JSON file")
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

def fix_field_name(field_name, field_index, used_field_names):
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

def determine_schema(json_struct):
    geometry_type_mapping  = {
        'LineString': "POLYLINE",
        'MultiLineString': "POLYLINE",
        'Point': "POINT",
	'MultiPoint': "MULTIPOINT",
        'Polygon': "POLYGON",
        'MultiPolygon': "POLYGON"
    }

    arcpy.AddMessage("Determining Schema")
    if not json_struct.get("type", None) == "FeatureCollection":
        raise TypeError("Data is not a Feature Collection")
    geometry_type = None
    fields = {}

    arcpy.AddMessage("Inspecting records to determine schema")
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
    arcpy.AddMessage("Geometry type: {}".format(geometry_type))
    used_field_names = set()
    field_names = {}
    for field_index, field_name in enumerate(sorted(fields)):
        sane_field_name = fix_field_name(field_name, field_index,
                                         used_field_names)
        used_field_names.add(sane_field_name)
        field_names[field_name] = sane_field_name

    return {'geometry_type': geometry_type or "POINT",
            'fields': fields,
            'field_names': field_names}

def field_info(field_tuple):
    dtype, dlength = field_tuple
    if dtype == NULL:
        return ("SHORT", 2)
    elif dtype == INT:
        return ("LONG", 8)
    elif dtype == FLOAT:
        return ("DOUBLE", 8)
    else:
        return ("TEXT", dlength)

def create_feature_class(catalog_path, out_schema):
    arcpy.AddMessage("Creating feature class")
    spatial_reference = arcpy.SpatialReference('WGS 1984')
    arcpy.management.CreateFeatureclass(os.path.dirname(catalog_path),
                                        os.path.basename(catalog_path),
                                        out_schema['geometry_type'],
                                        spatial_reference=spatial_reference)
    arcpy.AddMessage("Adding fields to feature class")
    for field_name, field_info_tuple in out_schema['fields'].iteritems():
        sane_field_name = out_schema['field_names'].get(field_name, field_name)
        field_type, field_length = field_info(field_info_tuple)
        arcpy.AddMessage("Field {} (type {})".format(sane_field_name,
                                                     field_type))
        arcpy.management.AddField(catalog_path, sane_field_name, field_type,
                                  field_length=field_length,
                                  field_alias=field_name,
                                  field_is_nullable="NULLABLE")

def geojson_to_geometry(geometry_struct):
    coordinates = geometry_struct['coordinates']
    if geometry_struct['type'] == "Point":
        return "POINT ({})".format(" ".join(str(f) for f in coordinates))
    elif geometry_struct['type'] == "MultiPoint":
        return "MULTIPOINT ({})".format(
            ", ".join(
                " ".join(str(f) for f in point))
            for point in coordinates)
    elif geometry_struct['type'] == "LineString":
        return "LINESTRING ({})".format(
            ", ".join(
                " ".join(str(f) for f in point))
            for point in coordinates)
    elif geometry_struct['type'] == "MultiLineString":
        return "MULTILINESTRING ({})".format(
            ", ".join("({})".format(
                ",".join(" ".join(str(f) for f in pair) for pair in segment))
            for segment in coordinates))
    elif geometry_struct['type'] == "Polygon":
        return "POLYGON ({})".format(
            ", ".join("({})".format(
                ",".join(" ".join(str(f) for f in pair) for pair in ring))
            for ring in coordinates))
    elif geometry_struct['type'] == "MultiPolygon":
        return "MULTIPOLYGON ({})".format(",".join("({})".format(
                ", ".join("({})".format(
                    ",".join(" ".join(str(f) for f in pair) for pair in ring)))
                for ring in polygon))
            for polygon in coordinates)
    else:
        raise TypeError("Geometry type {}".format(geometry_struct['type']))

def write_features(out_feature_class, out_schema, json_struct):
    arcpy.AddMessage("Writing features")
    # Create a list of (sane_field_name, field_name) tuples
    reverse_field_name_mapping = list(sorted((v, k)
                                      for k, v
                                      in out_schema['field_names'].iteritems()))
    fields = ["SHAPE@WKT"] + [f[0] for f in reverse_field_name_mapping]
    record_count = len(json_struct['features'])
    arcpy.SetProgressor("step", "Writing rows", 0, record_count)
    with arcpy.da.InsertCursor(out_feature_class, fields) as out_cur:
        for row_index, row_struct in enumerate(json_struct['features']):
            if (row_index % 100 == 1):
                arcpy.SetProgressorPosition(row_index)
            row_data = row_struct['properties']
            row_list = [row_data.get(k[1], None)
                        for k in reverse_field_name_mapping]
            wkt = geojson_to_geometry(row_struct['geometry'])
            out_cur.insertRow([wkt] + row_list)

def geojson_to_feature(in_geojson, out_feature_class):
    json_struct = load_geojson_struct(in_geojson)
    out_schema = determine_schema(json_struct)
    create_feature_class(out_feature_class, out_schema)
    write_features(out_feature_class, out_schema, json_struct)

