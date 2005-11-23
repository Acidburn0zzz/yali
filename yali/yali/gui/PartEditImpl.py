# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

from qt import *

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import yali.gui.context as ctx
import yali.partitiontype as parttype
import yali.parteddata as parteddata
import yali.partitionrequest as request

from yali.gui.parteditbuttons import PartEditButtons
from yali.gui.parteditwidget import PartEditWidget



editState, createState, deleteState = range(3)
  
##
# Edit partition widget
class PartEdit(QWidget):

    _d = None
    _state = None

    ##
    # Initialize PartEdit
    def __init__(self, *args):
        apply(QWidget.__init__, (self,) + args)

        self.vbox = QVBoxLayout(self)

        self.edit = PartEditWidgetImpl(self)
        self.vbox.addWidget(self.edit)

        self.warning = QLabel(self)
        self.vbox.addWidget(self.warning, 0, self.vbox.AlignCenter)

        self.buttons = PartEditButtons(self)
        self.vbox.addWidget(self.buttons)

        self.connect(self.buttons.applyButton, SIGNAL("clicked()"),
                     self.slotApplyClicked)
        self.connect(self.buttons.cancelButton, SIGNAL("clicked()"),
                     self.slotCancelClicked)

        # use available
        self.connect(self.edit.use_available, SIGNAL("toggled(bool)"),
                     self.slotUseAvailable)


    def slotUseAvailable(self, b):
        if b:
            s = 0
            t = self._d.getType()
            if t == parteddata.deviceType:
                s = self._d.getFreeMB()
            else:
                s = self._d.getMB()

            self.edit.size.setValue(s)
            self.edit.size.setEnabled(False)
        else:
            self.edit.size.setEnabled(True)

    ##
    # set up widget for use.
    def setState(self, state, dev):
        self._d = dev

        # Hacky: show only one widget for an action.
        self.warning.hide()
        self.edit.hide()
        self.show()

        t = self._d.getType()

        if t == parteddata.deviceType:
            if state == createState:
                self.edit.size.setMaxValue(self._d.getFreeMB())
                self.edit.setState(state)
                self.edit.show()

            elif state == deleteState:
                self.warning.setText(
                    _("You are going to delete all partitions on device '%s'")
                    %(self._d.getModel()))
                self.warning.show()

        elif t ==  parteddata.partitionType:
            if state == deleteState:
                self.warning.setText(
                    _("You are going to delete partition '%s' on device '%s'!")
                    % (self._d.getMinor(), self._d.getDevice().getModel()))
                self.warning.show()

            elif state == editState:
                self.edit.setState(state, self._d)
                self.edit.show()

        elif t == parteddata.freeSpaceType:
            if state == createState:
                # get free space
                self.edit.size.setMaxValue(self._d.getMB())
                self.edit.setState(state)
                self.edit.show()


        self._state = state


    ##
    # Apply button is clicked, make the necessary modifications and
    # emit a signal.
    def slotApplyClicked(self):
        state = self._state
        t = self._d.getType()

        # get partition type from checked
        def get_part_type():
            if self.edit.root.isChecked():
                return parttype.root
            elif self.edit.home.isChecked():
                return parttype.home
            elif self.edit.swap.isChecked():
                return parttype.swap

        # disable requested partition types in gui
        def disable_selected_part_types():
            self.edit.root.setEnabled(True)
            self.edit.home.setEnabled(True)
            self.edit.swap.setEnabled(True)
            for r in ctx.partrequests.searchReqType(request.mountRequestType):
                pt = r.partitionType()
                if pt == parttype.root:
                    self.edit.root.setEnabled(False)
                elif pt == parttype.home:
                    self.edit.home.setEnabled(False)
                elif pt == parttype.swap:
                    self.edit.swap.setEnabled(False)

        def create_new_partition(device):
            t = get_part_type()

            if t == parttype.root:
                size = self.edit.size.text().toInt()[0]
                min = ctx.consts.min_root_size
                if size < min:
                    self.warning.setText(
                        _("'Install Root' size must be larger than %s MB.") %min)
                    self.warning.show()
                    return False


            size = self.edit.size.text().toInt()[0]

            # FIXME: type doesn't work!
            p = device.addPartition(0, t.filesystem, size)
            device.commit()
            partition = device.getPartition(p.num)

            if not edit_requests(partition):
                return False

            return True

        def edit_requests(partition):
            t = get_part_type()

            if t == parttype.root:
                size = partition.getMB()
                if size < ctx.consts.min_root_size:
                    self.warning.setText(
                        _("'Install Root' size must be larger than %s MB.") % (
                            ctx.consts.min_root_size))
                    self.warning.show()
                    return False

            try:
                ctx.partrequests.append(
                    request.MountRequest(partition, t))
            
                if self.edit.format.isChecked():
                    ctx.partrequests.append(
                        request.FormatRequest(partition, t))
                else:
                    # remove previous format requests for partition (if
                    # there are any)
                    ctx.partrequests.removeRequest(
                        partition, request.formatRequestType)
            except request.RequestException, e:
                self.warning.setText("%s" % e)
                self.warning.show()
                return False

            return True


        if t == parteddata.deviceType:
            if state == createState:
                device = self._d
                if not create_new_partition(device):
                    return False

            elif state == deleteState:
                # delete requests
                for p in self._d.getPartitions():
                    ctx.partrequests.removeRequest(p, request.mountRequestType)
                    ctx.partrequests.removeRequest(p, request.formatRequestType)

                self._d.deleteAllPartitions()
                self._d.commit()

        elif t ==  parteddata.partitionType:
            if state == deleteState:
                device = self._d.getDevice()
                device.deletePartition(self._d)
                device.commit()

                # delete requests
                ctx.partrequests.removeRequest(self._d, request.mountRequestType)
                ctx.partrequests.removeRequest(self._d, request.formatRequestType)

            elif state == editState:
                partition = self._d
                if not edit_requests(partition):
                    return

        elif t == parteddata.freeSpaceType:
            if state == createState:
                device = self._d.getDevice()
                if not create_new_partition(device):
                    return False

        else:
            raise GUIError, "unknown action called (%s)" %(self._action)



        disable_selected_part_types()
        self.hide()
        self.emit(PYSIGNAL("signalApplied"), ())

    ##
    # Cancel button clicked.
    def slotCancelClicked(self):
        self.emit(PYSIGNAL("signalCanceled"), ())


class PartEditWidgetImpl(PartEditWidget):

    def setState(self, state, partition=None):
        self._state = state

        if self._state == editState:
            self.size.hide()
            self.use_available.hide()
            self.size_label.hide()

        elif self._state == createState:
            self.size.show()
            self.use_available.show()
            self.size_label.show()