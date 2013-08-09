import os

import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = u'GeoJSON Utilities'
        self.alias = ''
        self.tools = [ImportGeoJSON, ExportGeoJSON]

class ImportGeoJSON(object):
    def __init__(self):
        self.label = u'Import GeoJSON File'
        self.description = u''
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Input_File
        param_1 = arcpy.Parameter()
        param_1.name = u'Input_File'
        param_1.displayName = u'Input File'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'DEFile'

        # Output_File
        param_2 = arcpy.Parameter()
        param_2.name = u'Output_File'
        param_2.displayName = u'Output File'
        param_2.parameterType = 'Required'
        param_2.direction = 'Output'
        param_2.datatype = u'DEFeatureClass'

        return [param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        pass

    def updateMessages(self, parameters):
        pass

    def execute(self, parameters, messages):
        import imp
        import os
        
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
        # Input_Feature_Class
        param_1 = arcpy.Parameter()
        param_1.name = u'Input_Feature_Class'
        param_1.displayName = u'Input Feature Class'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = u'GPFeatureLayer'

        # Output_GeoJSON
        param_2 = arcpy.Parameter()
        param_2.name = u'Output_GeoJSON'
        param_2.displayName = u'Output GeoJSON'
        param_2.parameterType = 'Required'
        param_2.direction = 'Output'
        param_2.datatype = u'DEFile'

        return [param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if parameters[1].value:
            ext = os.path.splitext(parameters[1].valueAsText)[1]
            if ext.lower() not in ('.json', '.geojson'):
                parameters[1].value = parameters[1].valueAsText + ".json"

    def updateMessages(self, parameters):
        pass

    def execute(self, parameters, messages):
        import imp
        import os
        
        found_out = imp.find_module('geojson_out', [os.path.dirname(__file__)])
        json_out = imp.load_module('geojson_out', *found_out)
        
        args = [parameters[idx].valueAsText
                for idx in xrange(len(parameters))]
        
        json_out.write_geojson_file(*args)
