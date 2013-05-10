#!/usr/bin/env python

###########################################################################
# PiMyRide_LCD_Prototype_Logger.py
#
# For use with 16x16 Character Display BreadBoard on Raspberry Pi
# This is the code for the Prototype version of PiMyRide
#
# Copyright 2013 Alan Kehoe, David O'Regan (www.pimyride.com)
#
# This file is part of PiMyRide.
#
# PiMyRide is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# PiMyRide is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PiMyRide; if not, visit http://www.gnu.org/licenses/gpl.html
###########################################################################

import obd_io
import serial
import platform
import obd_sensors
from datetime import datetime
import time
import sys
from CharLCD import CharLCD
from subprocess import * 
from time import sleep, strftime
from obd_utils import scanSerial
import os

class PiMyRide_Logger():
	def __init__(self, path, log_sensors):    
		self.port = None
		self.lcd = CharLCD()
		self.lcd.begin(16,1)
		self.sensorlist = []
		dest_file = path+(datetime.now().strftime('%d%b-%H:%M:%S')) + ".csv"
		self.log_csv = open(dest_file, "w", 128)
		self.log_csv.write("Time,RPM,MPH,Throttle-Position,Calculated-Load,Coolant-Temp,Air-Temp,Intake-Manifold-Pressure,Air-Flow-Rate,MPG\n");

		for sensor in log_sensors:
			self.add_log_sensor(sensor)

	def connect(self):
		portnames = scanSerial()
		print portnames
		for port in portnames:
			self.port = obd_io.OBDPort(port, None, 2, 2)
			if(self.port.State == 0):
				self.port.close()
				self.port = None
			else:
				break

		if(self.port):
			self.lcd.clear()
			self.lcd.message("Connected")
			print "Connected"
            
	def is_connected(self):
		return self.port
        
	def add_log_sensor(self, sensor):
		for index, e in enumerate(obd_sensors.SENSORS):
			if(sensor == e.shortname):
				self.sensorlist.append(index)
				print "Logging Sensor: "+e.name
				break
    
	def get_mpg(self, MPH, MAF):
		#Instant_MPG = (14.7 * 8.637571 * 4.54 * MPH) / (3600 * (MAF * 7.5599) / 100)#Diesel Inaccurate formula
		Instant_MPG = (14.7 * 7.273744 * 4.54 * MPH) / (3600 * MAF / 100)#Petrol Should be highly accurate			
		return Instant_MPG         
            
	def record_data(self):
		if(self.port is None):
			return None
        
		self.lcd.clear()
		self.lcd.message("Logging started")
		print "Logging started"
        
		while 1:
			log_time = datetime.now().strftime('%d%b-%H:%M:%S.%f')
			log_data = log_time
			result_set = {}
			for index in self.sensorlist:
				(name, value, unit) = self.port.sensor(index)
				print self.port.sensor(index)
				log_data = log_data + ","+str(value)
				result_set[obd_sensors.SENSORS[index].shortname] = value;
			# we dont want to log "NODATA" if the car drops the OBDII connetion rather exit the program
			if (result_set["rpm"]=="NODATA")or(result_set["speed"]=="NODATA")or(result_set["throttle_pos"]=="NODATA")or(result_set["load"]=="NODATA")or(result_set["temp"]=="NODATA")or(result_set["intake_air_temp"]=="NODATA")or(result_set["manifold_pressure"]=="NODATA")or(result_set["maf"]=="NODATA"):
				self.lcd.clear()
				self.lcd.message("Connection Error\n Disconnecting")   
				sleep(3) 
				self.lcd.message("  Disconnected")            
				sys.exit()
			Instant_MPG = self.get_mpg(result_set["speed"], result_set["maf"])
			self.lcd.clear()
			self.lcd.message('MPG ' + '%.2f' % Instant_MPG + '\n')
			self.lcd.message('RPM ' + str(result_set["rpm"]))
			log_data = log_data + "," + str(Instant_MPG)
			self.log_csv.write(log_data+"\n")
            
def ensure_dir(f): # Make a new directory for each day will make managing the logs easier
    d = os.path.dirname(f)
    if not os.path.exists(d): # check if directory exists if it does not create it
        os.makedirs(d)
            
dir_date = datetime.now()
path = datetime.now().strftime('%d-%b-%Y')

ensure_dir("/home/pi/logs/"+path+"/") # ensure the dir is available

log_sensors = ["rpm", "speed", "throttle_pos", "load", "temp", "intake_air_temp", "manifold_pressure", "maf"]
logger = PiMyRide_Logger("/home/pi/logs/"+path+"/", log_sensors)
logger.connect()
if not logger.is_connected():
	error = CharLCD()
	error.begin(16,1)
	error.message(" Not connected")
logger.record_data()




