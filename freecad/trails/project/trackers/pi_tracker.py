# -*- coding: utf-8 -*-
#**************************************************************************
#*                                                                     *
#* Copyright (c) 2019 Joel Graff <monograff76@gmail.com>               *
#*                                                                     *
#* This program is free software; you can redistribute it and/or modify*
#* it under the terms of the GNU Lesser General Public License (LGPL)  *
#* as published by the Free Software Foundation; either version 2 of   *
#* the License, or (at your option) any later version.                 *
#* for detail see the LICENCE text file.                               *
#*                                                                     *
#* This program is distributed in the hope that it will be useful,     *
#* but WITHOUT ANY WARRANTY; without even the implied warranty of      *
#* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the       *
#* GNU Library General Public License for more details.                *
#*                                                                     *
#* You should have received a copy of the GNU Library General Public   *
#* License along with this program; if not, write to the Free Software *
#* Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307*
#* USA                                                                 *
#*                                                                     *
#***********************************************************************
"""
Customized wire tracker for PI alignments
"""

from pivy import coin

from FreeCAD import Vector

import DraftTools

from DraftGui import todo

from .base_tracker import BaseTracker
from .node_tracker import NodeTracker
from .wire_tracker import WireTracker
from .drag_tracker import DragTracker

from ..support.utils import Constants as C
from ..support.mouse_state import MouseState

class PiTracker(BaseTracker):
    """
    Tracker class which manages alignment PI  and tangnet
    picking and editing
    """

    def __init__(self, doc, view, object_name, node_name, points):
        """
        Constructor
        """

        #dict which tracks actions on nodes in the gui
        self.gui_action = {
            'drag': None,
            'rollover': None,
            'selected': {},
        }

        self.trackers = {
            'NODE': {},
            'WIRE': {},
        }

        self.callbacks = []
        self.mouse = MouseState()
        self.datum = Vector()
        self.view = view

        self.transform = coin.SoTransform()
        self.transform.translation.setValue([0.0, 0.0, 0.0])

        _names = [doc.Name, object_name, node_name]

        self.build_trackers(points, _names)

        child_nodes = [self.transform]

        super().__init__(
            names=_names, children=child_nodes, select=False, group=True
        )

        for _tracker in {
                **self.trackers['NODE'],
                **self.trackers['WIRE']
            }.values():

            self.insert_child(_tracker.node)

        self.color.rgb = (0.0, 0.0, 1.0)

        self.insert_node(self.node)

    def setup_callbacks(self, view):
        """
        Setup event handling callbacks and return as a list
        """

        return [
            ('SoKeyboardEvent',
             view.addEventCallback('SoKeyboardEvent', self.key_action)
            ),
            ('SoLocation2Event',
             view.addEventCallback('SoLocation2Event', self.mouse_action)
            ),
            ('SoMouseButtonEvent',
             view.addEventCallback('SoMouseButtonEvent', self.button_action)
            )
        ]

    def key_action(self, arg):
        """
        Keypress actions
        """

        return

    def unhighlight(self):
        """
        Disable rollover node
        """

        if self.gui_action['rollover']:
            self.gui_action['rollover'].whichChild = 0
            self.gui_action['rollover'] = None

    def on_rollover(self, pos):
        """
        Manage element highlighting
        """

        info = self.view.getObjectInfo(pos)

        roll_node = self.gui_action['rollover']

        #if we rolled over nothing or an invalid object,
        #unhighlight the existing node
        if not self.validate_info(info):

            if roll_node:
                roll_node.switch.whichChild = 0

            self.gui_action['rollover'] = None

            return

        component = info['Component'].split('.')[0]

        _tracker = self.trackers['NODE'].get(component)

        if _tracker:

            #unhighlight existing node
            if roll_node and roll_node.name != component:
                roll_node.switch.whichChild = 0

            _tracker.switch.whichChild = 1

            self.gui_action['rollover'] = _tracker

    def start_drag(self, arg):
        """
        Set up scenegraph and object for dragging
        """

        self.unhighlight()

        pos = self.mouse.button1.pos
        info = self.validate_info(self.view.getObjectInfo((pos.x, pos.y)))

        if not info:
            return

        component = info['Component'].split('.')[0]

        if not component in self.gui_action['selected']:
            return

        _selected = self.gui_action['selected']

        for _node in _selected.values():
            _node.off()

        _drag = DragTracker(self.view, self.names[:2])

        _drag.set_trackers(
            self.trackers['NODE'], list(_selected.keys()), component,
            self.datum
        )

        self.gui_action['drag'] = _drag

        self.insert_child(_drag.nodes['switch'])

    def end_drag(self):
        """
        Teardown for dragging
        """

        _drag = self.gui_action['drag']

        if not _drag:
            return

        todo.delay(self.remove_child, _drag.nodes['switch'])

        result = _drag.get_transformed_coordinates()

        self.update_points(result)

        self.gui_action['drag'] = None

    def on_drag(self, pos, rotate, modify):
        """
        Drag operation in view
        """

        _drag = self.gui_action['drag']

        if not _drag:
            return

        vec = self.view.getPoint(pos).sub(self.datum)

        _drag.update(vec, rotate, modify)

    def on_selection(self, arg, pos):
        """
        Mouse selection in view
        """

        self.unhighlight()

        info = self.validate_info(self.view.getObjectInfo(pos))

        #deselect all and quit if no valid object is picked
        if not info:
            self.deselect_geometry('all')
            return

        #quit if this is a previously-picked object
        component = info['Component'].split('.')[0]

        if component in self.gui_action['selected']:
            return

        #still here - deselect and select
        self.deselect_geometry('all')

        _split = component.split('-')
        _idx = int(_split[1])
        _max = _idx + 1

        if (_split[0] == 'WIRE'):
            _max += 1

        if arg['AltDown']:
            _max = len(self.trackers['NODE'])

        self.gui_action['selected'] = {}

        for _node in list(self.trackers['NODE'].values())[_idx:_max]:
            _node.selected()
            self.gui_action['selected'][_node.name] = _node

        if (_max - _idx) > 1:
            for _wire in list(self.trackers['WIRE'].values())[_idx:_max -1]:
                _wire.selected()

    def mouse_action(self, arg):
        """
        Mouse movement actions
        """

        #need to determine if we're in a special mode.
        #if not in a special mode, then it's just highlight operations

        _p = self.view.getCursorPos()

        #don't do highlighting if dragging is enabled
        if not (self.mouse.button1.dragging or self.mouse.button1.pressed):

            self.mouse.update(arg, _p)
            self.on_rollover(_p)

            if self.gui_action['drag']:
                self.end_drag()

        #manage dragging
        else:

            if self.gui_action['drag']:
                self.on_drag(_p, arg['AltDown'], arg['ShiftDown'])

            else:
                self.start_drag(arg)

    def button_action(self, arg):
        """
        Button click trapping
        """

        _p = self.view.getCursorPos()
        self.mouse.update(arg, _p)

        #manage selection
        if self.mouse.button1.pressed:
            self.on_selection(arg, _p)

        DraftTools.redraw3DView()

    def set_datum(self, datum):
        """
        Set the datum for coordinate transformations
        """

        self.datum = datum

    def validate_info(self, info):
        """
        If the info is not none and contains a reference to a node
        or wire tracker, return true
        """

        #abort if no info passed
        if not info:
            return None

        component = info['Component']

        #abort if this isn't the geometry we're looking for
        if not (('NODE-' in component)): # or ('WIRE-' in component)):
            return None

        return info

    def deselect_geometry(self, geo_type):
        """
        Deselect geometry
        geo_types:
        'all', 'node', 'wire'
        """

        for _grp in self.trackers.values():
            for _tracker in _grp.values():
                _tracker.default()

        self.gui_action = {
            'drag': None,
            'rollover': None,
            'selected': {},
        }

    def update(self, points=None, placement=None):
        """
        Update
        """

        if points:
            self.update_points(points)

        if placement:
            self.update_placement(placement)

    def update_points(self, points):
        """
        Updates existing coordinates
        """

        for _i, _node in enumerate(self.gui_action['selected'].values()):
            _node.update(points[_i])
            _node.on()

        for _wire in self.trackers['WIRE'].values():
            _wire.update()

    def build_trackers(self, points, names):
        """
        Builds node and wire trackers
        """

        self.finalize_trackers()

        for _i, _pt in enumerate(points):

            #set z value on top
            _pt.z = C.Z_DEPTH[2]

            #build node trackers
            _tr = NodeTracker(
                names=names[:2] + ['NODE-' + str(_i)],
                point=_pt
            )

            _tr.update(_pt)

            self.trackers['NODE'][_tr.name] = _tr

        _prev = None

        for _i, _tr in enumerate(self.trackers['NODE'].values()):

            if not _prev:
                _prev = _tr
                continue

            points = [_prev, _tr]

            _wt = WireTracker(
                names=names[:2] + ['WIRE-' + str(_i - 1)], points=points)

            self.trackers['WIRE'][_wt.name] = _wt

            _prev = _tr

    def update_placement(self, vector):
        """
        Updates the placement for the wire and the trackers
        """

        self.transform.translation.setValue(tuple(vector))

    def finalize_trackers(self, tracker_list=None):
        """
        Destroy existing trackers
        """

        if self.trackers['NODE'] or self.trackers['WIRE']:

            for _grp in self.trackers.values():

                for _tracker in _grp.values():
                    _tracker.finalize()

            self.trackers.clear()

    def finalize(self, node=None):
        """
        Override of the parent method
        """

        self.finalize_trackers()

        if not node:
            node = self.node

        super().finalize(node)