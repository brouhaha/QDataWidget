#!/usr/bin/env python3

# Copyright 2022 Eric Smith <spacewar@gmail.com>
# SPDX-License-Identifier: MIT

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice (including the
# next paragraph) shall be included in all copies or substantial portions
# of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from functools import partial

from PySide2 import QtCore as qtc
from PySide2 import QtGui as qtg
from PySide2 import QtWidgets as qtw

class QDataField:
    def __init__(self, data_type, default_value = None, min = None, max = None):
        self.data_type = data_type
        self.default_value = default_value
        self.min = min
        self.max = max

    def __set_name__(self, cls, name):
        self.name = name

        # Build a dictionary of fields in the subclass.
        if not hasattr(cls, '_fields'):
            cls._fields = {}
        cls._fields[name] = self

        # Create the signal.
        self.signal_name = name + 'Changed'
        # Saving a copy of the signal itself in our instance variable doesn't
        # yield something on which calling .emit works.
        setattr(cls, self.signal_name, qtc.Signal(self.data_type))

    def __get__(self, obj, objtype = None):
        return obj.__dict__[self.name]

    def __set__(self, obj, value):
        if self.name in obj.__dict__ and value == obj.__dict__[self.name]:
            return
        obj.__dict__[self.name] = value
        getattr(obj, self.signal_name).emit(value)

class QDataWidget(qtc.QObject):
    """Don't instantiate this class directly. A subclass must define
       one or more class attribute initialized to QDataField instances"""

    def __init__(self, *args, **kwargs):
        field_init = { }
        for kw, value in list(kwargs.items()):
            if kw in self._fields:
                field_init[kw] = value
                del kwargs[kw]
        super().__init__(*args, **kwargs)
        for kw, value in field_init.items():
            self._fields[kw].__set__(self, value)
        for kw in self._fields.keys():
            # set default value
            if kw not in self.__dict__ and self._fields[kw].default_value is not None:
                self.__dict__[kw] = self._fields[kw].default_value
            
            # create slot
            slot_name = 'set' + kw.capitalize()
            setattr(self, slot_name, partial(self._set_field, attr_name = kw))

    def _set_field(self, value, attr_name):
        self._fields[attr_name].__set__(self, value)

if __name__ == '__main__':
    class Resistor(QDataWidget):
        ref = QDataField(str)
        resistance = QDataField(float)
        tolerance = QDataField(float, default_value = 0.05)
        kind = QDataField(str, default_value = 'metal film')

    class Subscriber(qtc.QObject):
        def __init__(self, sname, *args, **kwargs):
            self.sname = sname
            super().__init__(*args, **kwargs)

        #@qtc.Slot(int)
        def print_value(self, value):
            print(f'{self.sname} signalled, type {type(value)}, value {value}')

    # pass in kw arg parent to make sure it gets through to QObject
    r1 = Resistor(ref = 'r1', resistance = 300.0, parent = None)

    # override default for kind
    r2 = Resistor(ref = 'r2', resistance = 100.0, kind = 'carbon comp')

    # make sure default values work correctly
    print(f'{r1.kind=}, should be metal film (default)')
    print(f'{r2.kind=}, should be carbon comp')

    # create some subscribers with normal (not dynamically created) slots
    subscriberR1 = Subscriber('r1')
    subscriberR2 = Subscriber('r2')

    # hook up automatically generated signals to the subscriber instances
    r1.refChanged.connect(subscriberR1.print_value)
    r1.resistanceChanged.connect(subscriberR1.print_value)
    r1.toleranceChanged.connect(subscriberR1.print_value)
    r1.kindChanged.connect(subscriberR1.print_value)

    r2.refChanged.connect(subscriberR2.print_value)
    r2.resistanceChanged.connect(subscriberR2.print_value)
    r2.toleranceChanged.connect(subscriberR2.print_value)
    r2.kindChanged.connect(subscriberR2.print_value)

    # test that setting attributes directly sends signals
    r1.resistance = 37.2
    r2.tolerance = 0.10

    # test that directly calling the dynamically generated slots sends signls
    r1.setResistance(99.99)
    r2.setTolerance(0.01)

    # test that the generated singals work with the generated
    # slots by linking some r1 and r2 fields together
    r1.resistanceChanged.connect(r2.setResistance)
    r2.kindChanged.connect(r1.setKind)
    r1.setResistance(33.3)
    r2.setKind('foo')
