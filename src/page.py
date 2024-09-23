from http.server import BaseHTTPRequestHandler, HTTPServer
from playctrl import *

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
  <button type="button" id="NextBtn" onclick="nextStation()">Επόμενος &gt;&gt;</button>
  <br><br><br>
  (c)2023-24 <a href="https://sv6gmp.blogspot.com/" target="_blank">Stavros S. Fotoglou</a>
  </center>
 </body>
</html>'''

p2='''<!DOCTYPE html>
<html>
 <head>
 </head>
 <body>
  <H1>This is page 2</H1>
 </body>
</html>
'''

#Κλάση για τοπικό WebServer
class MyServer(BaseHTTPRequestHandler):
    def radiosList(self):
        colors = ['#40E0D0', '#F0F8FF', '#EE82EE', '#FFFACD', '#F0FFFF', '#F5F5DC', '#DEB887', '#5F9EA0', '#FF7F50', '#D2691E', '#BDB76B', '#00BFFF', '#228B22', 
                  '#9400D3', '#8FBC8F', '#7CFC00', '#FFA500', '#98FB98']
        Ncolors = len(colors)
        #s = ""
        s = '<table border="1" bgcolor="#191970">\n'
        #for i, radioname in enumerate(radios_names, 1):
            #s += '<a href="/ctrl:idx=' + str(i) + '">' + str(i) + ". " + radioname + "</a><br>\n  "
        j = 0
        colidx = 0
        cols = 5
        s += "   <tr>\n"
        for i, radioname in enumerate(radios_names, 1):
            if j >= cols:
                s += "   </tr>\n"
                j = 0
                s += "   <tr>\n"
            #s += '    <td bgcolor="'+colors[colidx]+'" align="center"><a href="/ctrl:idx=' + str(i) + '"><b>' + str(i) + "</b><br>" + radioname + "</a></td>\n"
            s += '    <td align="center"><a href="/ctrl:idx=' + str(i) + '"><span class="stationBox" style="background-color:'+colors[colidx]+'"><span class="stationNum">' + str(i) + "</span><br>" + radioname + "</span></a></td>\n"
            colidx += 1
            if colidx >= Ncolors:
                colidx = 0
            j += 1
        s += "   </tr>\n"
        s += "  </table>\n"
        return s
    
    def do_GET(self):
        vol = Get_Volume()
        if self.path == '/':
            idx = Get_StationIdx()
            headers(self)
            self.wfile.write(bytes(p1 %(radios_names[idx], str(vol), self.radiosList()), "utf-8"))
            
        elif '/ctrl' in self.path:
            cmd = self.path.split(":")
            if "next=1" in cmd[1]:
                idx = Next_Station()
                #self.end_headers()
                headers(self)
                self.wfile.write(bytes(p1 %(radios_names[idx], str(vol), self.radiosList()), "utf-8"))           
                
            elif "prev=1" in cmd[1]:
                idx = Prev_Station()
                headers(self)
                self.wfile.write(bytes(p1 %(radios_names[idx], str(vol), self.radiosList()), "utf-8"))

            elif "idx" in cmd[1]:
                tmp = cmd[1].split("=")
                idx = int(tmp[1]) - 1
                Goto_Station(idx)
                headers(self)
                self.wfile.write(bytes(p1 %(radios_names[idx], str(vol), self.radiosList()), "utf-8"))

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
    
def headers(obj):
    obj.send_response(200)
    obj.send_header("Content-type", "text/html")
    obj.end_headers()
    
