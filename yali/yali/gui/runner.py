# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os
import sys
import gettext

_ = gettext.translation('yali', fallback=True).ugettext

from PyQt4.Qt import QTimer
from PyQt4.Qt import QStyleFactory
from PyQt4.Qt import QObject
from PyQt4.Qt import QShortcut
from PyQt4.Qt import Qt
from PyQt4.Qt import QApplication
from PyQt4.Qt import SIGNAL
from PyQt4.Qt import SLOT
from PyQt4.Qt import QKeySequence

import yali
import yali.util
import yali.context as ctx
import yali.gui.YaliWindow
import yali.gui.interface

class Runner:

    _window = None
    _application = None

    def __init__(self):
        self._application = QApplication(sys.argv)

        # Main Window Initialized..
        self._window = yali.gui.YaliWindow.Widget()
        ctx.mainScreen = self._window

        ctx.interface = yali.gui.interface.Interface()

        # These shorcuts for developers :)
        prevScreenShortCut = QShortcut(QKeySequence(Qt.SHIFT + Qt.Key_F1), self._window)
        nextScreenShortCut = QShortcut(QKeySequence(Qt.SHIFT + Qt.Key_F2), self._window)
        QObject.connect(prevScreenShortCut, SIGNAL("activated()"), self._window.slotBack)
        QObject.connect(nextScreenShortCut, SIGNAL("activated()"), self._window.slotNext)

        # VBox utils
        ctx.logger.debug("Starting VirtualBox tools..")
        #FIXME:sh /etc/X11/Xsession.d/98-vboxclient.sh
        #yali.util.run_batch("VBoxClient", ["--autoresize"])
        #yali.util.run_batch("VBoxClient", ["--clipboard"])

        # Cp Reboot, ShutDown
        yali.util.run_batch("cp", ["/sbin/reboot", "/tmp/reboot"])
        yali.util.run_batch("cp", ["/sbin/shutdown", "/tmp/shutdown"])

        # base connections
        QObject.connect(self._application, SIGNAL("lastWindowClosed()"),
                        self._application, SLOT("quit()"))
        QObject.connect(ctx.mainScreen, SIGNAL("signalProcessEvents"),
                        self._application.processEvents)
        QObject.connect(self._application.desktop(), SIGNAL("resized(int)"),
                        self._reinit_screen)

        # Font Resize
        fontMinusShortCut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Minus), self._window)
        fontPlusShortCut  = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Plus) , self._window)
        QObject.connect(fontMinusShortCut, SIGNAL("activated()"), self._window.setFontMinus)
        QObject.connect(fontPlusShortCut , SIGNAL("activated()"), self._window.setFontPlus)

    def _reinit_screen(self):
        QTimer.singleShot(700,self._init_screen)

    def _init_screen(self):
        # We want it to be a full-screen window
        # inside the primary display.
        screen = self._application.desktop().screenGeometry()
        self._window.resize(screen.size())
        self._window.setMaximumSize(screen.size())
        self._window.move(screen.topLeft())
        self._window.show()

    def setSteps(self, screens):
        self._window.createWidgets(screens)

    def run(self):
        ctx.mainScreen.setCurrent(ctx.flags.startup)
        # Use default theme;
        # if you use different Qt4 theme our works looks ugly :)
        self._application.setStyle(QStyleFactory.create('Plastique'))
        self._init_screen()

        # For testing..
        # self._window.resize(QSize(800,600))

        # Run run run
        self._application.exec_()

