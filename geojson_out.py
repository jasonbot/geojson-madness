# coding: utf-8
import json
import os
import urllib2

import arcpy

__all__ = ['write_geojson_file', 'post_gist', 'write_geojson_gist']

def part_split_at_nones(part_items):
    current_part = []
    for item in part_items:
        if item is None:
            if current_part:
                yield current_part
            current_part = []
        else:
            current_part.append((item.X, item.Y))
    if current_part:
        yield current_part

def geometry_to_struct(in_geometry):
    if in_geometry is None:
        return None
    elif isinstance(in_geometry, arcpy.PointGeometry):
        pt = in_geometry.getPart(0)
        return {
                    'type': "Point",
                    'coordinates': (pt.X, pt.Y)
               }
    elif isinstance(in_geometry, arcpy.Polyline):
        parts = [[(point.X, point.Y) for point in in_geometry.getPart(part)]
                 for part in xrange(in_geometry.partCount)]
        if len(parts) == 1:
            return {
                        'type': "LineString",
                        'coordinates': parts[0]
                   }
        else:
            return {
                        'type': "MultiLineString",
                        'coordinates': parts
                   }
    elif isinstance(in_geometry, arcpy.Polygon):
        parts = [list(part_split_at_nones(in_geometry.getPart(part)))
                 for part in xrange(in_geometry.partCount)]
        if len(parts) == 1:
            return {
                        'type': "Polygon",
                        'coordinates': parts[0]
                   }
        else:
            return {
                        'type': "MultiPolygon",
                        'coordinates': parts
                   }
    else:
        raise ValueError(in_geometry)

def utf8ify(fn_):
    def fn(*a, **k):
        for output in fn_(*a, **k):
            if isinstance(output, unicode):
                yield output.encode("utf-8")
            elif isinstance(output, str):
                try:
                    output.decode("utf-8")
                    yield output
                except:
                    # Magnificently hacky: don't know encoding, so just go nuts
                    # and strip all non-ASCII
                    yield (output.decode("ascii", "replace")
                                 .encode("ascii", "replace"))
            else:
                yield output
    return fn

@utf8ify
def geojson_lines_for_feature_class(in_feature_class):
    shape_field = arcpy.Describe(in_feature_class).shapeFieldName
    spatial_reference = arcpy.SpatialReference('WGS 1984')

    aliased_fields = {
                            field.name: (field.aliasName or field.name)
                            for field in arcpy.ListFields(in_feature_class)
                     }

    record_count = int(arcpy.management.GetCount(in_feature_class)[0])
    arcpy.SetProgressor("step", "Writing records", 0, record_count)

    with arcpy.da.SearchCursor(in_feature_class, ['SHAPE@', '*'],
                               spatial_reference=spatial_reference) as in_cur:
        col_names = [aliased_fields.get(f, f) for f in in_cur.fields[1:]]
        yield '{'
        yield '  "type": "FeatureCollection",'
        yield '  "features": ['
        for row_idx, row in enumerate(in_cur):
            if row_idx:
                yield "    ,"
            if (row_idx % 100 == 1):
                arcpy.SetProgressorPosition(row_idx)
            geometry_dict = geometry_to_struct(row[0])
            property_dict = dict(zip(col_names, row[1:]))
            if shape_field in property_dict:
                del property_dict[shape_field]
            row_struct = {
                            "type": "Feature",
                            "geometry": geometry_dict,
                            "properties": property_dict
                         }
            for line in json.dumps(row_struct, indent=2).split("\n"):
                yield "    " + line
        yield '  ]'
        yield '}'

def get_geojson_string(in_feature_class):
    return "\n".join(geojson_lines_for_feature_class(in_feature_class))

def write_geojson_file(in_feature_class, out_json_file):
    arcpy.AddMessage("Writing features from {} to {}".format(in_feature_class,
                                                             out_json_file))
    with open(out_json_file, 'wb') as out_json:
        for line in geojson_lines_for_feature_class(in_feature_class):
            out_json.write(line + "\n")

def post_gist(in_feature_class, feature_geojson):
    filename = os.path.basename(in_feature_class) + ".json"
    gist_payload = {
                        'description':
                            u"Feature Layer {}".format(in_feature_class),
                        'public': True,
                        'files': {
                            filename: { "content": feature_geojson }
                        }
                   }
    req = urllib2.Request("https://api.github.com/gists",
                          json.dumps(gist_payload),
                          headers = {'Content-Type': 'application/json'})
    reponse = urllib2.urlopen(req)
    return json.loads(reponse.read())["url"]

def write_geojson_gist(in_feature_class):
    arcpy.AddMessage("Getting GeoJSON from features")
    geojson = get_geojson_string(in_feature_class)
    arcpy.AddMessage("Posting Gist")
    gist_url = post_gist(in_feature_class, geojson)
    arcpy.AddMessage("Posted Gist to {}".format(gist_url))
    return gist_url

