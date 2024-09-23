import os, subprocess
from urllib.parse import urlencode

radios_names = []; radios_urls = []
radio_idx = 0 #Δείκτης στο αρχείο με τα URL
volS = 0 #Τιμή έντασης φωνής για αποθήκευση σε αρχείο conf.txt

#Online TTS από την Google
def getGoogleSpeechURL(phrase, lang = "el"):
	googleTranslateURL = "http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=" + lang + "&"
	parameters = {'q': phrase}
	data = urlencode(parameters)
	googleTranslateURL = "%s%s" % (googleTranslateURL,data)
	return googleTranslateURL

# Η βασική συνάρτηση η οποία δέχεται την πρόταση σε κείμενο και καλεί εξωτερικά
# προγράμματα για την αναπαραγωγή του ήχου.
def speakSpeechFromText(phrase, lang="el", v="ONLINE"):
	#Αν είναι ONLINE στέλνει ένα URL στην Google και αυτή επιστρέφει αρχείο ήχου, το οποίο παίζει με το Mplayer
	if v == 'ONLINE':
		googleSpeechURL = getGoogleSpeechURL(phrase, lang)
		#print(googleSpeechURL) #Debug
		subprocess.call(["mplayer", "-really-quiet", "-af", "volume=8", googleSpeechURL], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	#Αν είναι OFFLINE τότε καλεί το espeak
	elif v == 'OFFLINE':
		l = "-v" + lang
		#s ταχύτητα, p pich, a ένταση
		subprocess.call(["espeak", l, "-s 130", "-p 90", "-a 350", phrase], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def write_config_file():
	full_path = os.path.realpath(__file__)
	dir_path = os.path.dirname(full_path)
	filename = dir_path + "/conf.txt"
	file = open(filename, "w")
	file.write("#Config File\n") #Γράψε σχόλιο
	file.write("LastMem:" + str(radio_idx) + "\n") #Γράψε σταθμό μνήμης
	file.write("Volume:" + str(volS) + "\n") #Γράψε ένταση φωνής
	file.close()

def is_latin(text): 
	flag = True
	for c in text:
		if c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
			flag = False
	return flag 

#Αναπαραγωγή του σταθμού
def play_radio():
	global p
	print(radios_names[radio_idx])
	speakSpeechFromText(str(radio_idx + 1), "el", "ONLINE")
	speakSpeechFromText(radios_names[radio_idx], "el", "ONLINE")
	#speakSpeechFromText(radios_names[radio_idx], "en", "ONLINE")
	'''a = radios_names[radio_idx].split(" ")
	en = ''
	el = ''
	for word in a:
		if is_latin(word):
			#speakSpeechFromText(word, "en", "ONLINE")
			en += word + ','
		else:
			#speakSpeechFromText(word, "el", "ONLINE")
			el += word + ','
	en = en[:-1]
	el = el[:-1]
	print(en)
	print(el)'''
	#speakSpeechFromText(en, "en", "ONLINE")
	#speakSpeechFromText(el, "el", "ONLINE")
	with open(os.devnull, 'wb') as nul:
		p = subprocess.Popen(['mplayer', '-really-quiet', radios_urls[radio_idx]], stdin=nul, stdout=subprocess.PIPE)
		#print(int(p.pid)) #Debug εμφανίζει το PID της διεργασίας
	write_config_file()

#Σταμάτημα του σταθμού
def stop_radio():
	p.terminate()

#Να παίξει τον επόμενο σταθμό στη σειρά
def Next_Station():
	global radio_idx
	stop_radio()
	if radio_idx < len(radios_urls) - 1:
		radio_idx += 1
	else:
		radio_idx = 0
	play_radio()
	return radio_idx

#Να παίξει τον προηγούμενο σταθμό στη σειρά
def Prev_Station():
	global radio_idx
	stop_radio()
	if radio_idx > 0:
		radio_idx -= 1
	else:
		radio_idx = len(radios_urls) - 1
	play_radio()
	return radio_idx

#Επιστρέφει το index του τρέχοντος σταθμού
def Get_StationIdx():
	return radio_idx

#Αλλάζει την τιμή της μεταβλητής radio_idx
def Set_StationIdx(idx):
	global radio_idx
	radio_idx = idx

#Παίζει τον σταθμό με το συγκεκριμένο Index
def Goto_Station(idx):
	Set_StationIdx(idx) #Άλλαξε τιμή του radio_idx με την παραπάνω συνάρτηση
	stop_radio()
	play_radio()

#Βάζει την τρέχουσα ένταση για να αποθηκευτεί στο αρχείο
def Set_Volume(v):
	global volS
	volS = v

def Get_Volume():
	return volS
