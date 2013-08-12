GeoJSON Geoprocessing Tool
==========================

GeoJSON is some new upstart format that's come around in the past few weeks. Here's a set of tools to get GeoJSON in/out of ArcGIS.

Usage should be self-explanatory: open up the toolbox in Arc{Catalog,Map,Scene}, select your features to export or import, and blam.

This tool _always_ exports to WGS 1984, because most people on the internet shuffling GeoJSON around are barbarians who don't know the first thing about spatial reference systems. The same applies for import, right now it assumes coordinates are all in WGS 1984.

License
-------

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

