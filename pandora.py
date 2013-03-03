#!/usr/bin/python2.5
import sys,time
import re
import os
import urllib
import urllib2

from subprocess import Popen, PIPE


class Config:
	def __init__(self):
		self.user = ""
		self.password = ""
		self.color = ""
		self.lastfm_user = ""
		self.lastfm_password = ""
		self.lastfm_scrobble_percent = "50"
		self.control_proxy = ""
		self.act_help = "?"
		self.act_songlove = "+"
		self.act_songban = "-"
		self.act_stationaddmusic = "a"
		self.act_stationcreate = "c"
		self.act_stationdelete = "d"
		self.act_songexplain = "e"

		self.act_stationaddbygenre = "g"
		self.act_songinfo = "i"
		self.act_addshared = "j"
		self.act_songmove = "m"
		self.act_songnext = "n"
		self.act_songpause = "p"
		self.act_quit = "q"
		self.act_stationrename = "r"
		self.act_stationchange = "s"
		self.act_songtired = "t"
		self.act_upcoming = "u"
		self.act_stationselectquickmix = "x"
		self.audio_format = "aacplus"
		self.autostart_station = ""
		self.config_opts = ['user','password','lastfm_user','lastfm_password','lastfm_scrobble_percent',
			'control_proxy','act_help','act_songlove','act_songban', 'act_stationaddmusic',
			'act_stationcreate', 'act_stationdelete', 'act_songexplain', 'act_stationaddbygenre',
			'act_songinfo', 'act_addshared', 'act_songmove', 'act_songpause', 'act_quit', 
			'act_stationrename', 'act_stationchange', 'act_songtired', 'act_upcoming', 
			'act_stationselectquickmix', 'audio_format', 'autostart_station', 'event_command']
		self.event_command = ""
		
	def load(self):
		if os.path.exists(os.path.expanduser("~")+'/.config/pianobar/config'):
			f = open(os.path.expanduser("~")+'/.config/pianobar/config', 'r')
			for line in f:
				line = line.replace(" ", "")
				
				if re.match("^#.*",line) is not None:
					continue
			
				for opt in self.config_opts:
					if re.match("^"+opt+"=(.+)$",line) is not None:
						setattr(self,opt, self.get_var(opt,line))
			f.close()
		
	def write(self):
		newfile = ""
		if os.path.exists(os.path.expanduser("~")+'/.config/pianobar/config'):
			f = open(os.path.expanduser("~")+'/.config/pianobar/config', 'r')
			for line in f:
				line = line.replace(" ", "")
				if len(self.user)>0 and re.match("#*user=",line) is not None:
					newfile+="user="+self.user+"\n"
				elif len(self.password)>0 and re.match("#*password=",line) is not None:
					newfile+="password="+self.password+"\n"
				elif len(self.lastfm_user)>0 and re.match("#*lastfm_user=",line) is not None:
					newfile+="lastfm_user="+self.lastfm_user+"\n"
				elif len(self.lastfm_password)>0 and re.match("#*lastfm_password=",line) is not None:
					newfile+="lastfm_password="+self.lastfm_password+"\n"
				else:
					newfile+=line
			f.close()
		else:
			if not os.path.exists(os.path.expanduser("~")+'/.config/pianobar'):
				os.mkdir(os.path.expanduser("~")+'/.config/pianobar')
			for opt in self.config_opts:
				if len(getattr(self,opt))>0:
					newfile+=opt+"="+getattr(self,opt)+"\n"
				else:
					newfile+="#"+opt+"="+getattr(self,opt)+"\n"

		f = open(os.path.expanduser("~")+'/.config/pianobar/config', 'w')
		newfile = newfile.replace("=", " = ")
		f.write(newfile)
		f.close()

	def get_var(self,var,line):
		r = re.match("^"+var+"=(.+)$",line)
		return r.group(1)
			
		
class Pandora():

	def __init__(self, config):
		self.sTitle = ""
		self.sArtist = ""
		self.sAlbum = ""
		self.sLike = ""
		self.last = ""
		self.playing = 0
		self.drun = 1
		self.stations = [""] 
		self.length = ""
		self.error = ""
		self.crash = 0
		self.config = config


        """A user should override these functions"""
        def username_callback(self, username):
                pass

        def password_callback(self, password):
                pass

        def error_callback(self, error):
                pass

        def station_callback(self, station):
                print "Station Loaded %s" % station
        
        def song_callback(self, title, artist, album,
                          like):
                print "Begin Playing %s %s %s (%s)" % (title, artist,
                                                       album, like)

        def second_callback(self, time):
                print "Second Elapsed: %s" % time

        def start(self):
                import threading
                self.thread = threading.Thread(target=self.run)
                self.thread.start()

	def run(self):
		self.pandora = Popen("pianobar",stdout=PIPE,stdin=PIPE)
		newline = ""
		listStation = 0
		while self.drun:
			char = self.pandora.stdout.read(1)
			newline += char
			if re.match(".+Username$",newline) is not None and "Error" not in newline:
				self.username_callback(self.sTitle)
				self.last = "username"
					
			if re.match(".+Password$",newline) is not None:
				self.password_callback(self.sTitle)
				self.last = "password"
			
			elif char == "\n":
				output = newline.split("\x1b[2K")
				newline = ""
				for line in output:
					if line == "":
						continue
					title = re.match(".+\"(.+)\".+by.+\"(.+)\".+on.+\"(.+)\"(.*)",line)
					stations = re.match("\s+(\d+)\)\s(.+)$",line)
					merror = re.match(".*Error: (.+)$",line)
						
					if merror is not None:
						self.error = merror.group(1)
						self.error_callback(self.error)
						self.drun = 0
						self.pandora.stdin.close()
						self.pandora.stdout.close()

					if stations is not None:
						if int(stations.group(1)) == 0:
							self.stations = []
							self.crash = 0

						if re.match("^[Q|q]\s+(.+)",stations.group(2).lstrip()):
							station = re.match("^[Q|q]\s+(.+)",stations.group(2).lstrip()).group(1)
						else:
							station = stations.group(2).lstrip()

						if len(self.stations) > int(stations.group(1)):
							
							self.stations[int(stations.group(1))] = station
						else:
							self.stations.append(station)

						self.last = "stations"	
                                                if not hasattr(self, "station"):
                                                        self.station = station
						self.station_callback(station)
						
					
					if title is not None:
						self.close = 0
						self.sTitle = title.group(1)
						self.sArtist = title.group(2)
						self.sAlbum = title.group(3)
						if re.match(".+\<3",title.group(4)):
							self.sLike = 1
						else:
							self.sLike = 0
						
						self.last = "song"
                                                self.song_callback(self.sTitle, self.sArtist, self.sAlbum,
                                                                   self.sLike)
		
			elif re.match("^.+(\d+\:\d+)\/(\d+\:\d\d)$", newline):
				stime = re.match("^.+(\d+\:\d+)\/(\d+\:\d\d)$", newline)
				self.length = stime.group(1)+"/"+stime.group(2)
				self.second_callback(newline)
				newline = ""
			else:
				continue
			


	def stations(self):
		return self.stations

	def setStation(self, station):		
                if self.last == "song":
                        self.pandora.stdin.write(self.config.act_stationchange)
		
                self.station = station
                self.pandora.stdin.write(str(self.stations.index(station))+"\n")

                
	def tiredSong(self):
		if self.last == "song":
			self.pandora.stdin.write(self.config.act_songtired)
	
	def uSecond(self):
		return self.length

	def newsong(self):
		self.a.conf (self.sArtist, self.sAlbum)
		self.a.start()

		if not self.playing:
			self.playing = 1
		
	def love(self):
		if self.last == "song":
	 		self.pandora.stdin.write(self.config.act_songlove)
	
	def hate(self):
		if self.last == "song":
			self.pandora.stdin.write(self.config.act_songban)

	def next(self):
		if self.last == "song":
			self.pandora.stdin.write(self.config.act_songnext)

	def toggle(self):
		if self.last == "stations":
			self.pandora.stdin.write(str(0)+"\n")
		else:
			self.pandora.stdin.write(self.config.act_songpause)

		if self.playing:
			self.playing = 0
		else:
			self.playing = 1
	
	def quit(self):
		self.drun = 0
		self.pandora.stdin.write('\n'+self.config.act_quit)
		self.pandora.wait()

	def closeEvent(self, event):
		self.drun = 0
		self.pandora.stdin.write('\n'+self.config.act_quit)
		self.pandora.wait()
		self.exit()
		self.doQuit()

	
	def doError(self):
		if self.crash < 2:
			if re.match("^Username and/or password not correct.+",self.error) is not None:
				self.showUsername()
				self.showPassword()
			self.crash += 1
			self.drun = 1
			self.start()
		else:
			self.drun = 0
			self.pandora.wait()
			self.exit()
			self.doQuit()
			
if __name__ == '__main__':
        c = Config()
        c.load()
        p = Pandora(c)
        p.start()
        pandora = p
        try:
                import pdb
                pdb.set_trace()
        except:
                p.quit()

        p.quit()
