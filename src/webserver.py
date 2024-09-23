from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from threading import Thread

hostName = "0.0.0.0"
serverPort = 8080

p1='''<head>
 <title>Test</title>
</head>
<body>
</body>
<p>Hello!!!!</p>
This is a %s in %s
</body>
</html>'''

cnt = "Test"; st = "Stavros"

class MyServer(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(bytes(p1 %(cnt, st), "utf-8"))


webServer = HTTPServer((hostName, serverPort), MyServer)

def _create_httpserver():
    
	webServer.serve_forever()
 



if __name__ == "__main__":
	t = Thread(target=_create_httpserver)
	t.start()
	#webServer = HTTPServer((hostName, serverPort), MyServer)
	#print("Server started http://%s:%s" % (hostName, serverPort))

	try:
		while(True):
			print("OK") #webServer.serve_forever()
	except KeyboardInterrupt:
		pass

	webServer.server_close()
	print("Server stopped.")
