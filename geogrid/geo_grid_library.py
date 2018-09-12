# --------------------------------------------------------
#    geo_grid_library - geogrid operation functions
#
#    begin                : 14 Feb 2016
#    copyright            : (c) 2016 by Konstantin Puzankov
#    email                : konst555@mail.ru
#
#   GEOGRID is free software and is offered without guarantee
#   or warranty. You can redistribute it and/or modify it 
#   under the terms of version 2 of the GNU General Public 
#   License (GPL v2) as published by the Free Software 
#   Foundation (www.gnu.org).
# --------------------------------------------------------

from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
import io
import csv
import sys
import time
import math
import urllib.request, urllib.parse, urllib.error
import os.path
import operator
import tempfile

# Import the PyQt and QGIS libraries
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from qgis.core import *
from qgis.gui import *

from math import *


# --------------------------------------------------------
#    GEOGRID Functions
# --------------------------------------------------------


# --------------------------------------------------------
#    make_geogrid - Grid shapefiles creation
# --------------------------------------------------------

def make_geogrid(qgis, savename, dLon, dLat, MinLon, MinLat, MaxLon, MaxLat,
                       n_brdminuts, n_subgrd, n_brdtik, n_lblminuts, addlayer):
  if len(savename) <= 0:
    return "No output filename given"

  # Выходные файлы  Output files
  outFeatures  = savename
  # убрать расширение если есть  remove extension if available
  if (outFeatures[-4] == "." ) : outFeatures = outFeatures[:-4]
  out_grd = outFeatures + "_grd.shp"
  out_brd = outFeatures + "_brd.shp"
  out_tik = outFeatures + "_tik.shp"
  out_lbl = outFeatures + "_lbl.shp"


                                            
  #==== Используемая координатная система ====== географическая на WGS84
  #==== Used coordinate system == geographical WGS84 ===
  crsWGS = QgsCoordinateReferenceSystem('EPSG:4326')
#  crsWGS = QgsCoordinateReferenceSystem()
#  crsWGS.createFromProj4("+proj=longlat +datum=WGS84 +no_defs")

  #=========================================================
  #======== Построение сетки === Creating a Grid ===========
  #=========================================================
  
  # Cell size
  cW = float(dLon)
  cH = float(dLat)

  # Выравнивание на первую линию  Alignment to the first line
  minX = float( (int((MinLon+180)/cW)+1)*cW - 180 )  
  minY = float( (int((MinLat+90 )/cH)+1)*cH - 90  )
  maxX = float(MaxLon)
  maxY = float(MaxLat)  
  
  # SubStep
  ssX = float(n_subgrd)
  ssY = float(n_subgrd)
  
  try:
      fields = QgsFields()
      fields.append(QgsField("Line_XY", QVariant.Int, "int", 24, 16, "Line_XY"))
      fields.append(QgsField("Line_d", QVariant.Int, "int", 24, 16, "Line_d"))
      fields.append(QgsField("Line_m", QVariant.Int, "int", 24, 16, "Line_m"))
      fields.append(QgsField("nswe", QVariant.String, "text", 2, 0, "nswe"))

      if QFile(out_grd).exists():
        if not QgsVectorFileWriter.deleteShapeFile(out_grd):
          return "Failure deleting existing shapefile: " + out_grd

      shapetype = QgsWkbTypes.LineString

      outfile = QgsVectorFileWriter(out_grd, "utf-8", fields, shapetype, crsWGS, "ESRI Shapefile");

      if (outfile.hasError() != QgsVectorFileWriter.NoError):
          return "Failure creating output shapefile: " + str(outfile.errorMessage())

      #================================================== 
      #=============== Make Longitude lines, by X =======
      #================================================== 
      for i in range( int( (maxX-minX)/cW ) +1 ):
          polyline = []
          #== Дополнительная точка до рамки  Additional point to the frame
          if ( minY > (MinLat + 0.001) ):
              polyline.append(QgsPoint(float(minX+cW*i),float( MinLat)))

          for j in range( int( (maxY-minY)/(cH/ssY) ) ):
              polyline.append(QgsPoint( (minX+cW*i), (minY+(cH/ssY)* j)    )) 
              polyline.append(QgsPoint( (minX+cW*i), (minY+(cH/ssY)*(j+1)) ))

          #== Дополнительная точка до рамки  Additional point to the frame
          if ( MaxLat > (minY+(cH/ssY)*(j+1)) ):
              polyline.append(QgsPoint( float(minX+cW*i), float(MaxLat)) )

          feature = QgsFeature()
          feature.setGeometry(QgsGeometry.fromPolyline(polyline))
          pX  = minX+cW*i 
          pXd = int(abs(pX))
          pXm = int( (abs(pX)-pXd + 0.00001)*60 )
          pX_ew = "E"
          if (pX<0) : pX_ew = "W"

          feature.setAttributes([ 0, pXd, pXm, pX_ew ])
          outfile.addFeature(feature)

      #================================================== 
      #=============== Make Latitude lines, by Y =======
      #================================================== 
      for j in range( int( (maxY-minY)/cH ) +1 ): 
          polyline = []
          #== Дополнительная точка до рамки  Additional point to the frame
          if ( minX > (MinLon + 0.001) ):
              polyline.append(QgsPoint(MinLon, (minY+cH*j)))

          for i in range( int( (maxX-minX)/(cW/ssX) ) ): 
              polyline.append(QgsPoint( (minX+(cW/ssX)* i ),   (minY+cH*j) ))
              polyline.append(QgsPoint( (minX+(cW/ssX)*(i+1)), (minY+cH*j) ))

          #== Дополнительная точка до рамки  Additional point to the frame
          if ( MaxLon > (minX+(cW/ssX)*(i+1)) ):
              polyline.append(QgsPoint( MaxLon, (minY+cH*j) ))

          feature = QgsFeature()
          feature.setGeometry(QgsGeometry.fromPolyline(polyline))

          pY  = minY+cH*j 
          pYd = int(abs(pY))
          pYm = int( (abs(pY)-pYd + 0.00001)*60 )
          pY_ns = "N"
          if (pY<0) : pY_ns = "S"

          feature.setAttributes([ 1, pYd, pYm, pY_ns ])
          outfile.addFeature(feature)
  
  except Exception as e:
      return str(e)
  # Закрытие файла и удаление ссылки на него
  # Closing a file and deleting a link to it
  del outfile

  #=========================================================
  #========== Построение рамки === Creating a frame ========
  #=========================================================

  # Cell size
  cW = float(n_brdminuts)/60.0
  cH = float(n_brdminuts)/60.0
 
  # Рамка по всей области с точностью до минут
  # Frame throughout the area with an accuracy of minutes
  # Выравнивание Alignment
  minX = float( (int((MinLon+180)/cW)+1)*cW - 180 )  
  minY = float( (int((MinLat+90 )/cH)+1)*cH - 90  )
  maxX = float(MaxLon)
  maxY = float(MaxLat)  

  # SubStep
  ssX = 1.0
  ssY = 1.0
  
  #=============== Make List of coordinates (ID, X, Y) ========
  coordsList = []

  # Xmin - by Y - side 1
  Last_ID = 1  
  odd_id = 0
  #== Дополнительная точка Additional point
  if ( minY > MinLat ):
      coordsList.append([Last_ID, MinLon, MinLat, odd_id])
  for j in range( int( (maxY-minY)*(60.0/n_brdminuts) )+1 ):
      coordsList.append([Last_ID, MinLon, (minY+(cH/ssY)* j ), odd_id])
      if odd_id == 0 : odd_id = 1
      else : odd_id = 0 
  #== Дополнительная точка Additional point
  if ( minX > MinLon ):
      coordsList.append([Last_ID, MinLon, MaxLat, odd_id])
  odd_id1 = odd_id
          
  # Ymax - by X -side 2
  Last_ID = 2
  odd_id = 0
#        #== Дополнительная точка Additional point
#        if ( minX > MinLon ):
#            coordsList.append([Last_ID, MinLon, MaxLat, odd_id])
  for i in range( int( (maxX-minX)*(60.0/n_brdminuts) )+1 ):
      coordsList.append([Last_ID, (minX+(cW/ssX)* i ), MaxLat, odd_id])
      if odd_id == 0 : odd_id = 1
      else : odd_id = 0 
  #== Дополнительная точка 
  if ( (minX+(cW/ssX)* i) < MaxLon ):
      coordsList.append([Last_ID, MaxLon, MaxLat, odd_id])
  odd_id2 = odd_id
  
  # Xmax - by Y - side 3
  Last_ID = 3
  odd_id = odd_id1
  for j in range( int( (maxY-minY)*(60.0/n_brdminuts) ), -1,-1 ):
      coordsList.append([Last_ID, MaxLon, (minY+(cH/ssY)* j ), odd_id])
      if odd_id == 0 : odd_id = 1
      else : odd_id = 0 
  #== Дополнительная точка 
  if ( minY > MinLat ):
      coordsList.append([Last_ID, MaxLon, MinLat, odd_id])
          
  # Ymin - by X -side 4
  Last_ID = 4
  odd_id = odd_id2
  for i in range( int( (maxX-minX)*(60.0/n_brdminuts) ), -1,-1 ):
      coordsList.append([Last_ID, (minX+(cW/ssX)* i ), MinLat, odd_id])
      if odd_id == 0 : odd_id = 1
      else : odd_id = 0 
  #== Дополнительная точка Additional point
  if ( minX > MinLon ):
      coordsList.append([Last_ID, MinLon, MinLat, odd_id])


  #============== Создание и запись shape ============
  #============== Creating and writing shape =========
  try:
      fields = QgsFields()
      fields.append(QgsField("sideID", QVariant.Int, "int", 24, 16, "sideID"))
      fields.append(QgsField("odd", QVariant.Int, "int", 24, 16, "odd"))

      if QFile(out_brd).exists():
        if not QgsVectorFileWriter.deleteShapeFile(out_brd):
          return "Failure deleting existing shapefile: " + out_brd

      shapetype = QgsWkbTypes.LineString

      outfile = QgsVectorFileWriter(out_brd, "utf-8", fields, shapetype, crsWGS, "ESRI Shapefile");

      if (outfile.hasError() != QgsVectorFileWriter.NoError):
          return "Failure creating output shapefile: " + str(outfile.errorMessage())


      # Initialize a variable for keeping track of a feature's ID.
      for i in range(len(coordsList)-1): 
          side_ID =coordsList[i+1][0]
          odd_id =coordsList[i+1][3]

          polyline = []
          polyline.append(QgsPoint(coordsList[i][1], coordsList[i][2]))
          polyline.append(QgsPoint(coordsList[i+1][1], coordsList[i+1][2]))
          feature = QgsFeature()
          feature.setGeometry(QgsGeometry.fromPolyline(polyline))
          feature.setAttributes([ side_ID, odd_id ])
          outfile.addFeature(feature)


      # ======== Угловые точки ==== The corner points ==========
      coordsList = []
      minX = MinLon  
      minY = MinLat
      maxX = MaxLon
      maxY = MaxLat  

      coordsList.append([11, minX+(cW/ssX), minY, 2])
      coordsList.append([11, minX, minY, 2])
      coordsList.append([11, minX, minY+(cH/ssY), 2])

      coordsList.append([22, minX, maxY-(cH/ssY), 2])
      coordsList.append([22, minX, maxY, 2])
      coordsList.append([22, minX+(cW/ssX), maxY, 2])

      coordsList.append([33, maxX-(cW/ssX), maxY, 2])
      coordsList.append([33, maxX, maxY, 2])
      coordsList.append([33, maxX, maxY-(cH/ssY), 2])

      coordsList.append([44, maxX, minY+(cH/ssY), 2])
      coordsList.append([44, maxX, minY, 2])
      coordsList.append([44, maxX-(cW/ssX), minY, 2])

      # Initialize a variable for keeping track of a feature's ID.
      for j in range(4):
          i = j*3 
          side_ID =coordsList[i][0]
          odd_id =coordsList[i][3]  
          
          polyline = []
          polyline.append(QgsPoint(coordsList[i][1], coordsList[i][2]))
          polyline.append(QgsPoint(coordsList[i+1][1], coordsList[i+1][2]))
          polyline.append(QgsPoint(coordsList[i+2][1], coordsList[i+2][2]))
          feature = QgsFeature()
          feature.setGeometry(QgsGeometry.fromPolyline(polyline))
          feature.setAttributes([ side_ID, odd_id ])
          outfile.addFeature(feature)

  except Exception as e:
      return str(e)
  # Закрытие файла и удаление ссылки на него = Closing a file 
  del outfile

  #=========================================================
  #==== Построение тиков == Creating tics ==================
  #=========================================================

  # Рамка и тики по всей области с точностью до минут
  # Frame and tics throughout the area with an accuracy of minutes
  minX = float(MinLon)  
  minY = float(MinLat)
  maxX = float(MaxLon)
  maxY = float(MaxLat)  
 
  # ======= Первый набор тиков == First set of ticks ============
  # === с заданным шагом от 1 минуты  with a given step from 1 minute
  # SubStep
  ssX = 1.0
  ssY = 1.0

  # Cell size
  cW = float(n_brdtik)/(60.0*ssX) 
  cH = float(n_brdtik)/(60.0*ssY) 

  # Выравнивание Alignment
  minX = float( (int((MinLon+180)/cW)+1)*cW - 180 )  
  minY = float( (int((MinLat+90 )/cH)+1)*cH - 90 )
  
  #=============== Make List of coordinates (ID, X, Y) ========
  coordsList = []

  # Xmin - by Y - side 1
  Last_ID = 1  
  for j in range( int( (maxY-minY)/cH )+1 ):
      coordsList.append([Last_ID, MinLon, (minY+cH*j)])
          
  # Ymax - by X -side 2
  Last_ID = 2
  for i in range( int( (maxX-minX)/cW )+1 ):
      coordsList.append([Last_ID, (minX+cW*i), maxY])
  
  # Xmax - by Y - side 3
  Last_ID = 3
  for j in range( int( (maxY-minY)/cH ), -1,-1 ):
      coordsList.append([Last_ID, maxX, (minY+cH*j)])
          
  # Ymin - by X -side 4
  Last_ID = 4
  for i in range( int( (maxX-minX)/cW ), -1,-1 ):
      coordsList.append([Last_ID, (minX+cW*i), MinLat])

  # ==== Второй набор тиков == The second set of ticks ========
  # === В соответствии с разбиением рамки
  # === In accordance with the partitioning of the frame
  #=============== Make List of coordinates (ID, X, Y) ========
  # SubStep
  ssX = 1.0
  ssY = 1.0

  # Cell size
  cW = float( n_brdminuts/(60.0*ssX) )
  cH = float( n_brdminuts/(60.0*ssY) )

  # Выравнивание 
  minX = float( (int((MinLon+180)/cW)+1)*cW - 180 )  
  minY = float( (int((MinLat+90 )/cH)+1)*cH - 90 )

  # Xmin - by Y - side 1
  Last_ID = 11  
  for j in range( int( (maxY-minY)/cH )+1 ):
      coordsList.append([Last_ID, MinLon, (minY+cH*j)])
          
  # Ymax - by X -side 2
  Last_ID = 21
  for i in range( int( (maxX-minX)/cW )+1 ):
      coordsList.append([Last_ID, (minX+cW*i), maxY])
  
  # Xmax - by Y - side 3
  Last_ID = 31
  for j in range( int( (maxY-minY)/cH ), -1,-1 ):
      coordsList.append([Last_ID, maxX, (minY+cH*j)])
          
  # Ymin - by X -side 4
  Last_ID = 41
  for i in range( int( (maxX-minX)/cW ), -1,-1 ):
      coordsList.append([Last_ID, (minX+cW*i), MinLat])

  # === третий набор тиков = third set of ticks =============
  # === 1/2 деления разбиением рамки = 1/2 division of the frame
  #=============== Make List of coordinates (ID, X, Y) ========
  # SubStep
  ssX = 2.0
  ssY = 2.0

  # Cell size
  cW = float( n_brdminuts/(60.0*ssX) )
  cH = float( n_brdminuts/(60.0*ssY) )

  # Выравнивание Alignment
  minX = float( (int((MinLon+180)/cW)+1)*cW - 180 )  
  minY = float( (int((MinLat+90 )/cH)+1)*cH - 90  ) 

  # Xmin - by Y - side 1
  Last_ID = 12  
  for j in range( int( (maxY-minY)/cH )+1 ):
      coordsList.append([Last_ID, MinLon, (minY+cH*j)])
          
  # Ymax - by X -side 2
  Last_ID = 22
  for i in range( int( (maxX-minX)/cW )+1 ):
      coordsList.append([Last_ID, (minX+cW*i), maxY])
  
  # Xmax - by Y - side 3
  Last_ID = 32
  for j in range( int( (maxY-minY)/cH ), -1,-1 ):
      coordsList.append([Last_ID, maxX, (minY+cH*j)])
          
  # Ymin - by X -side 4
  Last_ID = 42
  for i in range( int( (maxX-minX)/cW ), -1,-1 ):
      coordsList.append([Last_ID, (minX+cW*i), MinLat])

  
  #============== Создание и запись shape ============
  #============== Creating and writing shape =========
  try:
      fields = QgsFields()
      fields.append(QgsField("tikID", QVariant.Int, "int", 24, 16, "tikID"))


      if QFile(out_tik).exists():
        if not QgsVectorFileWriter.deleteShapeFile(out_tik):
          return "Failure deleting existing shapefile: " + out_tik

      shapetype = QgsWkbTypes.MultiPoint

      outfile = QgsVectorFileWriter(out_tik, "utf-8", fields, shapetype, crsWGS, "ESRI Shapefile");

      if (outfile.hasError() != QgsVectorFileWriter.NoError):
          return "Failure creating output shapefile: " + str(outfile.errorMessage())

      # Initialize a variable for keeping track of a feature's ID.
      multipoint = []
      for i in range(len(coordsList)-1): 
          side_ID =coordsList[i][0] 

          multipoint.append(QgsPointXY(coordsList[i][1], coordsList[i][2]))

          if (side_ID != coordsList[i+1][0]) :
              feature = QgsFeature()
              feature.setGeometry(QgsGeometry.fromMultiPointXY(multipoint))
              feature.setAttributes([ side_ID ])
              outfile.addFeature(feature)
              multipoint = []

      # Add the last feature
      multipoint.append(QgsPointXY(coordsList[len(coordsList)-1][1], coordsList[len(coordsList)-1][2]))
      feature = QgsFeature()
      feature.setGeometry(QgsGeometry.fromMultiPointXY(multipoint))
      feature.setAttributes([ side_ID ])
      outfile.addFeature(feature)
      multipoint = []

  except Exception as e:
      return str(e)
  # Закрытие файла и удаление ссылки на него
  del outfile

  # =================================================
  # ==   Построение надписей   == Creating labels ===
  # =================================================

  #=============== Make List of coordinates (ID, X, Y) ========
  # SubStep
  ssX = 1.0
  ssY = 1.0

  # Cell size
  cW = float(n_lblminuts)/(60.0*ssX)
  cH = float(n_lblminuts)/(60.0*ssY)

  # Выравнивание Alignment
  minX = (int((MinLon+180)/cW)+1)*cW - 180.0  
  minY = (int((MinLat+90 )/cH)+1)*cH - 90.0
  maxX = float(MaxLon)
  maxY = float(MaxLat)  

  coordsList = []
  # Xmin - by Y - side 1
  Last_ID = 1  
  for j in range( int( (maxY-minY)/cH )+1 ):
      pY  = minY+cH*j
      pYd = int(abs(pY))
      pYm = int( (abs(pY)-pYd + 0.00001)*60 )
      pY_ns = "N"
      if (pY<0) : pY_ns = "S"
      # корректировка 60' correction 60 '
      if (pYm == 60) :
          pYm = 0
          pYd = pYd+1            
      coordsList.append([Last_ID, MinLon, (minY+cH*j), pYd, pYm, pY_ns])
          
  # Ymax - by X -side 2
  Last_ID = 2
  for i in range( int( (maxX-minX)/cW )+1 ):
      pX  = minX+cW*i
      pXd = int(abs(pX))
      pXm = int( (abs(pX)-pXd + 0.00001)*60 )
      pX_ew = "E"
      if (pX<0) : pX_ew = "W"            
      # корректировка 60' correction 60 '
      if (pXm == 60) :
          pXm = 0
          pXd = pXd+1            
      coordsList.append([Last_ID, (minX+cW*i), maxY, pXd, pXm, pX_ew])
  
  # Xmax - by Y - side 3
  Last_ID = 3
  for j in range( int( (maxY-minY)/cH ), -1,-1 ):
      pY  = minY+cH*j
      pYd = int(abs(pY))
      pYm = int( (abs(pY)-pYd + 0.00001)*60 )
      pY_ns = "N"
      if (pY<0) : pY_ns = "S"
      # корректировка 60' correction 60 '
      if (pYm == 60) :
          pYm = 0
          pYd = pYd+1            
      coordsList.append([Last_ID, maxX, (minY+cH*j), pYd, pYm, pY_ns])
          
  # Ymin - by X -side 4
  Last_ID = 4
  for i in range( int( (maxX-minX)/cW ), -1,-1 ):
      pX  = minX+cW*i
      pXd = int(abs(pX))
      pXm = int( (abs(pX)-pXd + 0.00001)*60 )
      pX_ew = "E"
      if (pX<0) : pX_ew = "W"            
      # корректировка 60' correction 60 '
      if (pXm == 60) :
          pXm = 0
          pXd = pXd+1            
      coordsList.append([Last_ID, (minX+cW*i), MinLat, pXd, pXm, pX_ew])

  #============== Создание и запись shape ============
  #============== Creating and writing shape =========
  try:
      fields = QgsFields()
      fields.append(QgsField("sideID", QVariant.Int, "int", 24, 16, "sideID"))
      fields.append(QgsField("lbl_d", QVariant.Int, "int", 24, 16, "lbl_d"))
      fields.append(QgsField("lbl_m", QVariant.Int, "int", 24, 16, "lbl_m"))
      fields.append(QgsField("nswe", QVariant.String, "text", 2, 0, "nswe"))

      if QFile(out_lbl).exists():
        if not QgsVectorFileWriter.deleteShapeFile(out_lbl):
          return "Failure deleting existing shapefile: " + out_lbl

#      shapetype = qgis.WKBPoint
      shapetype = QgsWkbTypes.Point
      outfile = QgsVectorFileWriter(out_lbl, "utf-8", fields, shapetype, crsWGS, "ESRI Shapefile");

      if (outfile.hasError() != QgsVectorFileWriter.NoError):
          return "Failure creating output shapefile: " + str(outfile.errorMessage())

      # Initialize a variable for keeping track of a feature's ID.
      for i in range(len(coordsList)):
          side_ID =coordsList[i][0]
          pd = coordsList[i][3]
          pm = coordsList[i][4]
          pnswe =  coordsList[i][5]
          feature = QgsFeature()
          feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(coordsList[i][1], coordsList[i][2])))
          feature.setAttributes([ side_ID, pd, pm, pnswe ])
          outfile.addFeature(feature)

  except Exception as e:
      return str(e)
  # Закрытие файла и удаление ссылки на него Close file
  del outfile

  #===========================================
  #============== Append to work project =====
  #===========================================
  if addlayer:
    Vlayer_grd = qgis.addVectorLayer(out_grd, os.path.basename(out_grd), "ogr")
    if not Vlayer_grd:
      return "Can not load " + str(out_grd)
    Vlayer_brd = qgis.addVectorLayer(out_brd, os.path.basename(out_brd), "ogr")
    if not Vlayer_brd:
      return "Can not load " + str(out_brd)
    Vlayer_tik = qgis.addVectorLayer(out_tik, os.path.basename(out_tik), "ogr")
    if not Vlayer_tik:
      return "Can not load " + str(out_tik)
    Vlayer_lbl = qgis.addVectorLayer(out_lbl, os.path.basename(out_lbl), "ogr")
    if not Vlayer_lbl:
      return "Can not load " + str(out_lbl)
    
    style_path = os.path.join( os.path.dirname(__file__), "base_grd.qml" )
    (errorMsg, result) = Vlayer_grd.loadNamedStyle( style_path )
    style_path = os.path.join( os.path.dirname(__file__), "base_brd.qml" )
    (errorMsg, result) = Vlayer_brd.loadNamedStyle( style_path )
    style_path = os.path.join( os.path.dirname(__file__), "base_tik.qml" )
    (errorMsg, result) = Vlayer_tik.loadNamedStyle( style_path )
    style_path = os.path.join( os.path.dirname(__file__), "base_lbl.qml" )
    (errorMsg, result) = Vlayer_lbl.loadNamedStyle( style_path )
    
  qgis_completion_message(qgis, str(outFeatures) + "[ _grd,_brd,_tik,_lbl ].shp features grid shapefiles created")

  return None

#======== Local Utils ============
def qgis_status_message(qgis, message):
  qgis.mainWindow().statusBar().showMessage(message)

def qgis_completion_message(qgis, message):
  qgis_status_message(qgis, message)
  qgis.messageBar().pushMessage(message, 0, 3)

