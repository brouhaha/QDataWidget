#!/usr/bin/env python3
# Copyright 2022 Eric Smith <spacewar@gmail.com>
# SPDX-License-Identifier: MIT

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
        # This is a horrible hack because QLineEdit, and even our
        # GenericEdit, always emit strings
        if self.data_type == float:
            value = float(value)
        elif self.data_type == int:
            value = int(value)

        if self.name in obj.__dict__ and value == obj.__dict__[self.name]:
            return
        obj.__dict__[self.name] = value
        getattr(obj, self.signal_name).emit(value)


class GenericEdit(qtw.QLineEdit):
    def setText(self, value):
        if type(value) != str:
            value = str(value)
        super().setText(value)


class QDataWidget(qtw.QWidget):
    """Don't instantiate this class directly. A subclass must define
       one or more class attribute initialized to QDataField instances"""

    def __init__(self, *args, **kwargs):
        # Pull our field initializers out of kwargs into field_init.
        # Do this _before_ calling superclass init, because we don't want
        # to forward the keyword arguments we consume
        field_init = { }
        for kw, value in list(kwargs.items()):
            if kw in self._fields:
                field_init[kw] = value
                del kwargs[kw]

        # Initialize the QWidget.
        super().__init__(*args, **kwargs)

        self.layout = qtw.QGridLayout()

        # Initialize fields based on keyword arguments.
        for field_name, value in field_init.items():
            self._fields[field_name].__set__(self, value)

        layout_row = 0
        for field_name in self._fields.keys():
            field = self._fields[field_name]

            # Set field's default value if not initialized.
            if field_name not in self.__dict__ and self._fields[field_name].default_value is not None:
                self.__dict__[field_name] = self._fields[field_name].default_value

            # Create slot.
            slot_name = 'set' + field_name.capitalize()
            setattr(self,
                    slot_name,
                    partial(self._set_field, attr_name = field_name))

            # Create field label and widget.
            label = qtw.QLabel(field_name)
            widget = GenericEdit(parent = self)

            # save widget?
            #self._fields[field_name].widget = widget

            # Set initial widget contents.
            widget.setText(str(getattr(self, field_name)))

            # Connect field changed signal to widget set slot.
            getattr(self, field.signal_name).connect(widget.setText)

            # Connect widget changed signal to our slot
            widget.textEdited.connect(getattr(self, slot_name))

            # Add label and widget to layout.
            self.layout.addWidget(label, layout_row, 0)
            self.layout.addWidget(widget, layout_row, 1)
            layout_row += 1

        self.setLayout(self.layout)

    def _set_field(self, value, attr_name):
        self._fields[attr_name].__set__(self, value)
