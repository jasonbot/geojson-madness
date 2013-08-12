import imp
import os

import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = u'GeoJSON Utilities'
        self.alias = 'geojsonconversion'
        self.tools = [ImportGeoJSON, ExportGeoJSON]

class ImportGeoJSON(object):
    def __init__(self):
        self.label = u'Import GeoJSON File'
        self.description = u''
        self.canRunInBackground = False

    def getParameterInfo(self):
        input_json_param = arcpy.Parameter()
        input_json_param.name = u'input_json'
        input_json_param.displayName = u'Input File'
        input_json_param.parameterType = 'Required'
        input_json_param.direction = 'Input'
        input_json_param.datatype = u'DEFile'

        output_feature_class_param = arcpy.Parameter()
        output_feature_class_param.name = u'output_feature_class'
        output_feature_class_param.displayName = u'Output Feature Class'
        output_feature_class_param.parameterType = 'Required'
        output_feature_class_param.direction = 'Output'
        output_feature_class_param.datatype = u'DEFeatureClass'

        return [input_json_param, output_feature_class_param]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        pass

    def updateMessages(self, parameters):
        pass

    def execute(self, parameters, messages):
        found_in = imp.find_module('geojson_in', [os.path.dirname(__file__)])
        json_in = imp.load_module('geojson_in', *found_in)

        args = [parameters[idx].valueAsText
                for idx in xrange(len(parameters))]

        json_in.geojson_to_feature(*args)

class ExportGeoJSON(object):
    def __init__(self):
        self.label = u'Export GeoJSON File'
        self.description = u''
        self.canRunInBackground = False

    def getParameterInfo(self):
        input_feature_class_param = arcpy.Parameter()
        input_feature_class_param.name = u'input_fc'
        input_feature_class_param.displayName = u'Input Feature Class'
        input_feature_class_param.parameterType = 'Required'
        input_feature_class_param.direction = 'Input'
        input_feature_class_param.datatype = u'GPFeatureLayer'

        output_json_param = arcpy.Parameter()
        output_json_param.name = u'output_json'
        output_json_param.displayName = u'Output GeoJSON'
        output_json_param.parameterType = 'Required'
        output_json_param.direction = 'Output'
        output_json_param.datatype = u'DEFile'

        post_as_gist_param = arcpy.Parameter()
        post_as_gist_param.name = u'post_as_gist'
        post_as_gist_param.displayName = u'Post As Gist'
        post_as_gist_param.parameterType = 'Optional'
        post_as_gist_param.direction = 'Input'
        post_as_gist_param.datatype = u'GPBoolean'

        output_url_param = arcpy.Parameter()
        output_url_param.name = u'output_url'
        output_url_param.displayName = u'Output URL'
        output_url_param.parameterType = 'Derived'
        output_url_param.direction = 'Output'
        output_url_param.datatype = u'GPString'

        return [input_feature_class_param, output_json_param,
                post_as_gist_param, output_url_param]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if parameters[1].value:
            ext = os.path.splitext(parameters[1].valueAsText)[1]
            if ext.lower() not in ('.json', '.geojson'):
                parameters[1].value = parameters[1].valueAsText + ".json"
        if parameters[2].value:
            parameters[1].enabled = (parameters[2].valueAsText != 'true')
            if not parameters[1].enabled and not parameters[1].value:
                parameters[1].value = "gist"
        else:
            parameters[1].enabled = True

    def updateMessages(self, parameters):
        pass

    def execute(self, parameters, messages):
        found_out = imp.find_module('geojson_out', [os.path.dirname(__file__)])
        json_out = imp.load_module('geojson_out', *found_out)

        args = [parameters[idx].valueAsText
                for idx in xrange(len(parameters))]
        write_gist = args[-1] == "true"

        if write_gist:
            out_url = json_out.write_geojson_gist(args[0])
            arcpy.SetParameterAsText(3, out_url)
        else:
            json_out.write_geojson_file(*(args[:-2]))
            arcpy.SetParameterAsText(3, "")
