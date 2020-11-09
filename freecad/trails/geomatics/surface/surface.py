# /**********************************************************************
# *                                                                     *
# * Copyright (c) 2019 Hakan Seven <hakanseven12@gmail.com>             *
# *                                                                     *
# * This program is free software; you can redistribute it and/or modify*
# * it under the terms of the GNU Lesser General Public License (LGPL)  *
# * as published by the Free Software Foundation; either version 2 of   *
# * the License, or (at your option) any later version.                 *
# * for detail see the LICENCE text file.                               *
# *                                                                     *
# * This program is distributed in the hope that it will be useful,     *
# * but WITHOUT ANY WARRANTY; without even the implied warranty of      *
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the       *
# * GNU Library General Public License for more details.                *
# *                                                                     *
# * You should have received a copy of the GNU Library General Public   *
# * License along with this program; if not, write to the Free Software *
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307*
# * USA                                                                 *
# *                                                                     *
# ***********************************************************************

'''
Create a Surface Object from FPO.
'''

import FreeCAD, FreeCADGui
from pivy import coin
from ..utils import GeoNodes
from freecad.trails import ICONPATH
import random



def create(points, index, name='Surface'):
    obj=FreeCAD.ActiveDocument.addObject("App::FeaturePython", name)
    obj.Label = name
    Surface(obj)
    obj.Points = points
    obj.Index = index
    ViewProviderSurface(obj.ViewObject)


class Surface:
    """
    This class is about Surface Object data features.
    """

    def __init__(self, obj):
        '''
        Set data properties.
        '''
        obj.addProperty(
            "App::PropertyVectorList",
            "Points",
            "Base",
            "List of group points").Points = ()

        obj.addProperty(
            "App::PropertyIntegerList",
            "Index",
            "Base",
            "Index of points").Index = ()

        obj.Proxy = self
        self.Points = None
        self.Index = None

    def onChanged(self, fp, prop):
        '''
        Do something when a data property has changed.
        '''
        return

    def execute(self, fp):
        '''
        Do something when doing a recomputation. 
        '''
        return


class ViewProviderSurface:
    """
    This class is about Point Group Object view features.
    """

    def __init__(self, obj):
        '''
        Set view properties.
        '''
        (r, g, b) = (random.random(),
                     random.random(),
                     random.random())

        obj.addProperty(
            "App::PropertyColor",
            "TriangleColor",
            "Surface Style",
            "Color of the point group").TriangleColor = (r, g, b)

        obj.Proxy = self

    def attach(self, obj):
        '''
        Create Object visuals in 3D view.
        '''
        # Get geo system and geo origin.
        geo_system, geo_origin = GeoNodes.create_origin(coords=obj.Object.Points[0])

        # Geo coordinates.
        self.geo_coords = coin.SoGeoCoordinate()
        self.geo_coords.geoSystem.setValues(geo_system)
        self.geo_coords.point.values = obj.Object.Points

        # Geo Seperator.
        geo_seperator = coin.SoGeoSeparator()
        geo_seperator.geoSystem.setValues(geo_system)
        geo_seperator.geoCoords.setValue(geo_origin[0], geo_origin[1], geo_origin[2])

        # Point group features.
        self.triangles = coin.SoIndexedFaceSet()
        index = obj.Object.Index
        for i in range(0, len(index)):
            self.triangles.coordIndex.set1Value(i,index[i])

        shape_hints = coin.SoShapeHints()
        shape_hints.vertex_ordering = coin.SoShapeHints.COUNTERCLOCKWISE
        self.mat_color = coin.SoMaterial()
        mat_binding = coin.SoMaterialBinding
        mat_binding.value = coin.SoMaterialBinding.OVERALL

        # Highlight for selection.
        highlight = coin.SoType.fromName('SoFCSelection').createInstance()
        #highlight.documentName.setValue(FreeCAD.ActiveDocument.Name)
        #highlight.objectName.setValue(obj.Object.Name)
        #highlight.subElementName.setValue("Main")
        highlight.addChild(self.geo_coords)
        highlight.addChild(self.triangles)

        # Point group root.
        surface_root = geo_seperator
        surface_root.addChild(shape_hints)
        surface_root.addChild(self.mat_color)
        #surface_root.addChild(mat_binding)
        surface_root.addChild(highlight)
        obj.addDisplayMode(surface_root,"Surface")

        # Take features from properties.
        self.onChanged(obj,"TriangleColor")

    def onChanged(self, vp, prop):
        '''
        Update Object visuals when a view property changed.
        '''
        # vp is view provider.
        if prop == "TriangleColor":
            color = vp.getPropertyByName("TriangleColor")
            self.mat_color.diffuseColor = (color[0],color[1],color[2])

    def updateData(self, fp, prop):
        '''
        Update Object visuals when a data property changed.
        '''
        # fp is feature python.
        if prop == "Points":
            points = fp.getPropertyByName("Points")
            self.geo_coords.point.values = points

        if prop == "Index":
            index = fp.getPropertyByName("Index")
            for i in range(0, len(index)):
                self.triangles.coordIndex.set1Value(i,index[i])

    def getDisplayModes(self,obj):
        '''
        Return a list of display modes.
        '''
        modes=[]
        modes.append("Surface")

        return modes

    def getDefaultDisplayMode(self):
        '''
        Return the name of the default display mode.
        '''
        return "Surface"

    def setDisplayMode(self,mode):
        '''
        Map the display mode defined in attach with those defined in getDisplayModes.
        '''
        return mode

    def getIcon(self):
        '''
        Return object treeview icon.
        '''
        return ICONPATH + '/icons/Surface.svg'

    def __getstate__(self):
        '''
        When saving the document this object gets stored using Python's json module.
        '''
        return None
 
    def __setstate__(self,state):
        '''
        When restoring the serialized object from document we have the chance to set some internals here.
        '''
        return None