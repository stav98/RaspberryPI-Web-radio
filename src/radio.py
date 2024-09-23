#!/usr/bin/env python
#nmap -sP 192.168.42.0/24
#import os, subprocess
import time, socket
#from urllib.parse import urlencode
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime
import RPi.GPIO as GPIO
vol = 90
from page import *
from playctrl import *

#Καθολικές μεταβλητές

mute = False; info = False
SOCKPATH = "/var/run/lirc/lircd" #Υπέρυθρες
sock = None
p = None #Η διεργασία του mplayer
num_Buttons = [b'BTN_0', b'BTN_1', b'BTN_2', b'BTN_3', b'BTN_4', b'BTN_5', b'BTN_6', b'BTN_7', b'BTN_8', b'BTN_9']

#Αρχικοποίηση του δέκτη υπερύθρων
def init_irw():
	global sock
	sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	print ('starting up on %s' % SOCKPATH)
	sock.connect(SOCKPATH)

#Αν πατήθηκε κάποιο πλήκτρο στο RC
def next_key():
	while True:
		data = sock.recv(128)
		# print("Data: " + data)
		data = data.strip()
		if data:
			break
	words = data.split()
	return words[2], words[1]

#Βρίσκει την τοπική IP
def get_local_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		# doesn't even have to be reachable
		s.connect(('192.255.255.255', 1))
		IP = s.getsockname()[0]
	except:
		IP = '127.0.0.1'
	finally:
		s.close()
	return IP
 
#Thread για WebServer
def start_httpserver():
	webServer.serve_forever()

def shutdown(gpio):
	stop_radio()
	speakSpeechFromText("Γειά σας, και καλή συνέχεια", "el", "OFFLINE")
	os.system('sudo shutdown now')

#Κυρίως πρόγραμμα
if __name__ == "__main__":
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.add_event_detect(3, GPIO.RISING, callback=shutdown)
	GPIO.setup(17, GPIO.OUT)
	GPIO.output(17, GPIO.HIGH)
	
	local_ip = get_local_ip() #Βρες τοπική IP
	hostName = local_ip #Βάλε το hostname για http server
	serverPort = 8080 #Πόρτα για webserver
	
	#Διαβάζει τους σταθμούς από το αρχείο stations.txt
	full_path = os.path.realpath(__file__)
	dir_path = os.path.dirname(full_path)
	filename = dir_path + "/stations.txt"
	file = open(filename, "r")
	for i, line in enumerate(file, 1):
		if not '#' in line: #Αν δεν υπάρχουν σχόλια στην γραμμή
			l = line.strip()
			a, b = l.split(":::")
			print(i, '. ', a, sep='')
			radios_names += [a]
			radios_urls += [b]
	file.close()
	#Διαβάζει αρχείο με τις τελευταίες ρυθμίσεις conf.txt
	filename = dir_path + "/conf.txt"
	#Αν υπάρχει το αρχείο
	if os.path.isfile(filename):
		print("Find config file.")
		file = open(filename, "r")
		for line in file:
			if not '#' in line: #Αν δεν υπάρχουν σχόλια στην γραμμή
				l = line.strip()
				a, b = l.split(":")
				if a == 'LastMem':
					lastMem = b
					print('LastMem =', lastMem)
				elif a == 'Volume':
					volume = b
					print('Volume =', volume)
		file.close()
	#Αλλιώς βάλε τιμές default
	else:
		print("Config file not exists.")
		lastMem = 0
		volume = 90
	Set_StationIdx(int(lastMem))
	Set_Volume(int(volume))
	vol = int(volume)
	#print(vol) #Debug
	#------ I.R. Receiver ----------------------------------	
	init_irw() #Ξεκίνα δέκτη υπερύθρων
	#Θέσε την ένταση του μίξερ στο 90%
	cmd = 'amixer set PCM ' + str(vol) + '%'
	#print(cmd) #Debug
	subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	#speakSpeechFromText("Το ραδιόφωνο του Σταύρου.", "el", "ONLINE")
	play_radio() #Αναπαραγωγή σταθμού
	#Φτιάχνει στιγμιότυπο του HTTPServer
	webServer = HTTPServer((hostName, serverPort), MyServer)
	print("Server started http://%s:%s" % (hostName, serverPort))

	#Δημιουργία του Thread και ξεκίνημα
	t = Thread(target = start_httpserver)
	t.start()

	#Για πάντα μέχρι να πατηθεί Ctrl+c
	print("Press Ctrl C to STOP")

	try:
		while True:
			
			#time.sleep(.05) #Delay
			#========= Έλεγχος των κουμπιών από το τηλεκοντρόλ υπερύθρων ==================================
			keyname, keytimes  = next_key()
			#Αύξηση της έντασης φωνής στον Mixer - Επιτρέπει autorepeat
			if keyname == b'KEY_VOLUMEUP':
				vol = Get_Volume()
				print ("UP")
				if vol < 100:
					vol += 1
					Set_Volume(vol)
					subprocess.run("amixer set PCM 100+", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
					print ("Volume: " + str(vol) + "%")
					write_config_file()
			#Μείωση της έντασης φωνής στον Mixer - Επιτρέπει autorepeat
			elif keyname == b'KEY_VOLUMEDOWN':
				vol = Get_Volume()
				print ("DOWN")
				if vol > 30:
					vol -= 1
					Set_Volume(vol)
					subprocess.run('amixer set PCM 100-', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
					print ("Volume: " + str(vol) + "%")
					write_config_file()
			#Έλεγχος αν πατήθηκε το προηγούμενο - Δεν επιτρέπει autorepeat
			elif keyname == b'KEY_PREVIOUS' and int(keytimes, 16) == 0: #Αν κάνει επανάληψη κατά το πάτημα αυξάνει το keytimes
				Prev_Station()
			#Έλεγχος αν πατήθηκε το επόμενο - Δεν επιτρέπει autorepeat
			elif keyname == b'KEY_NEXT' and int(keytimes, 16) == 0:
				Next_Station()
			#Έλεγχος αν πατήθκε το μπλε Option - Δεν επιτρέπει autorepeat
			elif keyname == b'KEY_OPTION' and int(keytimes, 16) == 0:
				print(local_ip)
				stop_radio()
				speakSpeechFromText(str(local_ip), "el", "OFFLINE")
				play_radio()
			#Έλεγχος αν πατήθηκε το Power - Δεν επιτρέπει autorepeat
			elif keyname == b'KEY_POWER' and int(keytimes, 16) == 0:
				print("Power Off")
				stop_radio()
				speakSpeechFromText("Γειά σας, και καλή συνέχεια", "el", "OFFLINE")
				os.system('sudo shutdown now')
			elif keyname == b'KEY_YELLOW' and int(keytimes, 16) == 0:
				now = datetime.datetime.now()
				tmp1 = str(now.time()).split(':')
				#tmp1[0] = "01"; tmp1[1] = "01"
				if tmp1[1] == "01":
					mins = "λεπτό"
				else:
					mins = "λεπτά"
				hours = ['Μηδέν', 'Μία', 'Δύο', 'Τρείς', 'Τέσσερις', 'Πέντε', 'Έξι', 'Επτά', 'Οκτώ', 'Εννέα', 'Δέκα', 'Έντεκα', 'Δώδεκα', 'Δεκατρείς',
			             'Δεκατέσσερις', 'Δεκαπέντε', 'Δεκαέξι', 'Δεκαεπτά', 'Δεκαοκτώ', 'Δεκαεννέα', 'Είκοσι', 'Εικοσιμία', 'Εικοσιδύο', 'Εικοσιτρείς']
				tmp2 = "Η ώρα είναι, " + hours[int(tmp1[0])] + ", και, " + tmp1[1].strip("0") + ", " + mins
				print(tmp2)
				speakSpeechFromText(tmp2, "el", "ONLINE")
			#Έλεγχος αν πατήθηκε το Mute - Δεν επιτρέπει autorepeat
			elif keyname == b'KEY_MUTE' and int(keytimes, 16) == 0:
				if mute == False:
					mute = True
					subprocess.run("amixer set PCM 0%", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
					print("Mute")
				else:
					mute = False
					subprocess.run("amixer set PCM 90%", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
					print("Unmute")
			#Έλεγχος αν πατήθηκε το Info - Δεν επιτρέπει autorepeat
			elif keyname == b'KEY_INFO' and int(keytimes, 16) == 0:
				if info == False:
					info = True
					print("Info pressed")
					msg = str(len(radios_names)) + " Αποθηκευμένοι ραδιοφωνικοί σταθμοί."
					msg += " Τώρα παίζει το ραδιόφωνο," + radios_names[Get_StationIdx()] + "."
					msg += " Διαχειριστείτε μέσω web στην διεύθυνση, http: "
					tmp = local_ip.split(".")
					msg1 = ""
					for i in range(len(tmp) - 1):
						msg1 += tmp[i] + " τελεία "
					msg1 += tmp[i+1]
					msg += msg1 + ", άνω κάτω τελεία 80 80."
					print(msg)
					stop_radio()
					speakSpeechFromText(msg, "el", "ONLINE")
					play_radio()
				else:
					info = False
			#Έλεγχος αν πατήθηκαν τα πλήκτρα 0 έως 9 - Δεν επιτρέπει autorepeat
			elif keyname in num_Buttons and int(keytimes, 16) == 0:	
				for i in range(len(num_Buttons)):
					if keyname == num_Buttons[i]:
						#print(i)
						Set_StationIdx(i-1)
						stop_radio()
						play_radio()
		
	#Αν πατήθηκε Ctrl+C
	except KeyboardInterrupt:
		os.system("killall -9 mplayer") #Σταμάτα όποια υπόσταση του mplayer
		webServer.server_close()
		print("Server stopped.")
