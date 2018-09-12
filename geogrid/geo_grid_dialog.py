# -*- coding: utf-8 -*-
"""
/***************************************************************************
 geogridDialog
                                 A QGIS plugin
 Lat-Lon grid
                             -------------------
        begin                : 2016-02-14
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

from builtins import str
import os
import os.path
import operator

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from qgis.core import *
from qgis.gui import *

from qgis.PyQt import QtGui

from .geo_grid_library import *

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

from .geo_grid_dialog_ui import Ui_geogridDialogBase

class geogridDialog(QDialog, Ui_geogridDialogBase):
    def __init__(self, iface):
        """Constructor."""
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)
        # connect to button signals
        self.Save_btn.clicked.connect(self.browse_outfile)
        self.btn_copy_minmax.clicked.connect(self.copy_minmax)

    #==== Save button ==========     
    def browse_outfile(self):
        newname, __ = QFileDialog.getSaveFileName(None, "Output Shapefile", 
                       self.Fname_lineEdit.displayText(), "Shapefile (*.shp)")
        if newname != None:
            self.Fname_lineEdit.setText(newname)

    #==== Copy button ==========     
    def copy_minmax(self):
        if self.mMapLayerComboBox.currentLayer() is None :
            QMessageBox.critical(self.iface.mainWindow(), "ERROR", "Can not open layer!")
            return

        from_extent = self.mMapLayerComboBox.currentLayer().extent() 
        from_crs = self.mMapLayerComboBox.currentLayer().crs()

        to_crsWGS = QgsCoordinateReferenceSystem('EPSG:4326')
        coordTransform = QgsCoordinateTransform(from_crs, to_crsWGS, QgsProject.instance())

        to_extent = coordTransform.transformBoundingBox(from_extent)
        QMessageBox.information(None, "Info", from_extent.toString() + '\n from_proj=' + from_crs.description()
                                     + '\n' + to_extent.toString()   + '\n to_proj=' + to_crsWGS.description() )
        
        # === Insert to dialog ===
        MinLon = to_extent.xMinimum()
        MinLat = to_extent.yMinimum()
        MaxLon = to_extent.xMaximum()
        MaxLat = to_extent.yMaximum()
        
        self.lon_min_d.setText(str( int(MinLon) ))
        self.lon_min_m.setText(str( abs((MinLon-int(MinLon))*60) ))
        self.lat_min_d.setText(str( int(MinLat) )) 
        self.lat_min_m.setText(str( abs((MinLat-int(MinLat))*60) )) 
        
        self.lon_max_d.setText(str( int(MaxLon) ))
        self.lon_max_m.setText(str( abs((MaxLon-int(MaxLon))*60) )) 
        self.lat_max_d.setText(str( int(MaxLat) ))
        self.lat_max_m.setText(str( abs((MaxLat-int(MaxLat))*60) ))
#        QMessageBox.information(None, "Info","Not work! Come back tomorrow...")

    def run(self):
        # =================== Set parameters from dialog ======================
        savename = str(self.Fname_lineEdit.displayText()).strip()
        dLon = float(self.lon_step_d.text())+float(self.lon_step_m.text())/60
        dLat = float(self.lat_step_d.text())+float(self.lat_step_m.text())/60
        
        # определение функции взятия знака
        sign = lambda x: math.copysign(1, x)
        
        MinLon = float(self.lon_min_d.text())
        MinLon = MinLon + sign(MinLon)*float(self.lon_min_m.text())/60

        MinLat = float(self.lat_min_d.text())
        MinLat = MinLat + sign(MinLat)*float(self.lat_min_m.text())/60

        MaxLon = float(self.lon_max_d.text())
        MaxLon = MaxLon + sign(MaxLon)*float(self.lon_max_m.text())/60

        MaxLat = float(self.lat_max_d.text())
        MaxLat = MaxLat + sign(MaxLat)*float(self.lat_max_m.text())/60

        n_brdminuts = float(self.combo_n_brdminuts.currentText())
        n_subgrd = self.spin_n_subgrd.value()
        n_brdtik = float(self.combo_n_brdtiks.currentText())
        n_lblminuts = float(self.combo_n_lblminuts.currentText())
        addlayer = self.add_layers.isChecked()

        #================ MAKE GEOGRID ========================
        message = make_geogrid(self.iface, savename, dLon, dLat, MinLon, MinLat, MaxLon, MaxLat,
                       n_brdminuts, n_subgrd, n_brdtik, n_lblminuts, addlayer)
#        message = make_geogrid(self.iface, savename, 1.0, 1.0, -10.0, -10.0, 10.0, 10.0,
#                                   1,2,3,60, 1)
        if message != None:
          QMessageBox.critical(self.iface.mainWindow(), "Grid", message)
