# -*- coding: utf-8 -*-
"""
/***************************************************************************
 geogrid3
                                 A QGIS plugin
 Lat-Lon grid
                              -------------------
        begin                : 2016-09-06
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Konstantin Puzankov
        email                : konst555@mail.ru
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import
from builtins import object
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
# Initialize Qt resources from file resources.py
from . import resources
# Import the code for the dialog
from .geo_grid_dialog import geogridDialog
import os.path  

import webbrowser, os
# Set up current path.
currentPath = os.path.dirname( __file__ )

class geogrid(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,'i18n','geogrid_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = geogridDialog(self.iface)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Geo Grid')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'geogrid')
        self.toolbar.setObjectName(u'geogrid')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('geogrid', message)

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(currentPath + "/icon.png"),
            u"Build Geo grid", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Geo Grid", self.action)
        
        self.help_action = QAction(
            QIcon(currentPath + "/help.png"),
            u"Help on Geo grid", self.iface.mainWindow())
        # connect the action to the run method
        self.help_action.triggered.connect(self.help)
        self.iface.addPluginToMenu(u"&Geo Grid", self.help_action)
        
       # core.QgsPluginLayerRegistry.instance().addPluginLayerType(LatLonGridType())

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&Geo Grid", self.action)
        self.iface.removePluginMenu(u"&Geo Grid", self.help_action)
        
        self.iface.removeToolBarIcon(self.action)
       # core.QgsPluginLayerRegistry.instance().removePluginLayerType(LatLonGridLayer.LAYER_TYPE)


    def help(self):
        webbrowser.open(currentPath + "/help/help_geogrid.html") 

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result: 
            self.dlg.run()
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

        
