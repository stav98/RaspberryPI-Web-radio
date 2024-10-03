from http.server import BaseHTTPRequestHandler, HTTPServer
from playctrl import *

#Κύρια σελίδα όταν λειτουργεί το ραδιόφωνο
p1='''<!DOCTYPE html>
<html>
 <head>
  <meta charset="UTF-8">
  <title>Python Web Radio</title>
   <style>
    a {
       text-decoration: none;
       color: black;
      }
    a:hover {
       color: red;
      }
    td {
       padding: 0px;
      }
    .stationBox {
       display: block; 
       width: 100%%;
      }

    .stationBox:hover span {
       background-color: white;
      }

    .stationNum {
       color:blue; 
       font-weight:bold;
       padding: 2px;
      }
   </style>
   <script type="text/javascript">
    function nextStation()
     {
      location.href = "/ctrl:next=1";
     }
    function prevStation()
     {
      location.href = "/ctrl:prev=1";
     }
    function powerOff()
     {
      location.href = "/ctrl:powerOFF";
     }
    document.addEventListener("DOMContentLoaded", () => 
     {
      const set_volume = document.getElementById("SetVolume");
      const volume_val = document.getElementById("VolumeVal");
      volume_val.innerHTML = set_volume.value;
      set_volume.addEventListener("input", (event) => { volume_val.innerHTML = set_volume.value; });
      set_volume.addEventListener("change", (event) => { location.href = "/ctrl:vol=" + set_volume.value; });
     });
   </script>
 </head>
 <body bgcolor="#bde8bc">
  <center>
  <H1>Stavros Radio</H1>
  <p>Το raspberry PI λειτουργεί ως ραδιόφωνο.</p>
  <H2>Παίζει τώρα: <span style="color: blue">%s</style></H2>
  Ένταση φωνής: <input type="range" min="40" max="100" value="%s" id="SetVolume" style="width:250px;vertical-align:middle">
  <span id="VolumeVal"></span>%%
  <br><br>
  %s
  <br>
  <button type="button" id="PrevBtn" onclick="prevStation()">&lt;&lt; Προηγούμενος</button>&nbsp;&nbsp;
  <button type="button" id="NextBtn" onclick="nextStation()">Επόμενος &gt;&gt;</button><br><br>
  <button type="button" id="PwrBtn" onclick="powerOff()">Απενεργοποίηση</button>
  <br><br><br>
  (c)2023-24 <a href="https://sv6gmp.blogspot.com/" target="_blank">Stavros S. Fotoglou</a>
  </center>
 </body>
</html>'''

#Εμφανίζεται όταν πατηθεί το button τερματισμού στο Web Interface
p2='''<!DOCTYPE html>
<html>
 <head>
  <meta charset="UTF-8">
  <title>Python Web Radio</title>
 </head>
 <body>
  <center>
   <H1>Το ραδιόφωνο του Σταύρου</H1>
   <H2><font color="red">Απενεργοποιήθηκε</font></H2>
  </center>
 </body>
</html>
'''

#Κλάση για τοπικό WebServer
class MyServer(BaseHTTPRequestHandler):
    def radiosList(self):
        colors = ['#40E0D0', '#F0F8FF', '#EE82EE', '#FFFACD', '#F0FFFF', '#F5F5DC', '#DEB887', '#5F9EA0', '#FF7F50', '#D2691E', '#BDB76B', '#00BFFF', '#228B22', 
                  '#9400D3', '#8FBC8F', '#7CFC00', '#FFA500', '#98FB98']
        Ncolors = len(colors)
        s = '<table border="1" bgcolor="#191970">\n'
        j = 0
        colidx = 0
        cols = 5
        s += "   <tr>\n"
        for i, radioname in enumerate(radios_names, 1):
            if j >= cols:
                s += "   </tr>\n"
                j = 0
                s += "   <tr>\n"
            s += '    <td align="center"><a href="/ctrl:idx=' + str(i) + '"><span class="stationBox" style="background-color:'+colors[colidx]+'" title="Πατήστε για να ακούσετε αυτόν τον σταθμό"><span class="stationNum">' + str(i) + "</span><br>" + radioname + "</span></a></td>\n"
            colidx += 1
            if colidx >= Ncolors:
                colidx = 0
            j += 1
        s += "   </tr>\n"
        s += "  </table>\n"
        return s
    
    #Απόκριση server αν ζητήται η σελίδα
    def do_GET(self):
        vol = Get_Volume()
        #Αν ζητήται η αρχική σελίδα χωρίς παραμέτρους
        if self.path == '/':
            idx = Get_StationIdx()
            headers(self)
            self.wfile.write(bytes(p1 %(radios_names[idx], str(vol), self.radiosList()), "utf-8"))

        #Αν ζητήται με την διεύθυνση /ctrl    
        elif '/ctrl' in self.path:
            cmd = self.path.split(":")
            #Αν υπάρχει το get /ctrl:next=1 θα παίξει τον επόμενο σταθμό
            if "next=1" in cmd[1]:
                idx = Next_Station()
                headers(self)
                self.wfile.write(bytes(p1 %(radios_names[idx], str(vol), self.radiosList()), "utf-8"))           
                
            #Αν υπάρχει το get /ctrl:prev=1 θα παίξει τον προηγούμενο σταθμό
            elif "prev=1" in cmd[1]:
                idx = Prev_Station()
                headers(self)
                self.wfile.write(bytes(p1 %(radios_names[idx], str(vol), self.radiosList()), "utf-8"))

            #Αν υπάρχει το get /ctrl:idx=ν θα παίξει τον σταθμό με αυτό το index όπως πατήθηκε από τον πίνακα σταθμών
            elif "idx" in cmd[1]:
                tmp = cmd[1].split("=")
                idx = int(tmp[1]) - 1
                Goto_Station(idx)
                headers(self)
                self.wfile.write(bytes(p1 %(radios_names[idx], str(vol), self.radiosList()), "utf-8"))

            #Αν υπάρχει το get /ctrl:vol=νν τότε θα βάλει την ένταση στην τιμή νν
            elif "vol=" in cmd[1]:
                tmp = cmd[1].split("=")
                vol = int(tmp[1])
                idx = Get_StationIdx()
                Set_Volume(vol)
                cmd = 'amixer set PCM ' + str(vol) + '%'
                subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                write_config_file()
                headers(self)
                self.wfile.write(bytes(p1 %(radios_names[idx], str(vol), self.radiosList()), "utf-8"))
            
            #Αν υπάρχει το get /powerOFF τότε τερματίζει την λειτουργία. Στέλνει την σελίδα p2
            elif "powerOFF" in cmd[1]:
                headers(self)
                stop_radio()
                speakSpeechFromText("Γειά σας, και καλή συνέχεια", "el", "OFFLINE")
                self.wfile.write(bytes(p2, "utf-8"))
                os.system('sudo shutdown now')

#Αποστολή headers http
def headers(obj):
    obj.send_response(200)
    obj.send_header("Content-type", "text/html")
    obj.end_headers()
