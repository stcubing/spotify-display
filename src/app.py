import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import parse_qs, urlencode, urlparse
import webbrowser
from dotenv import load_dotenv
from requests import post, get
import requests
import serial
import time
import os

ser = serial.Serial("COM6", 9600, timeout = 1)
time.sleep(2)

print("connected")

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")






class auth_handler(BaseHTTPRequestHandler):
    
    """
    mini server thing (as opposed to matchify's flask framework).
    catch authorization code from a url.
    call this to get the code (or an error if there isnt one)
    """
    
    # wow custom get request
    def do_GET(self):
        parsed_url = urlparse(self.path) # split url into parts
        query = parse_qs(parsed_url.query) # parses parameters
        
        # api responses
        if "code" in query:
            self.server.auth_code = query["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"authorisation successful")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"no code found")


def get_auth_code():
    
    """
    gets auth code from spotify
    """
    
    params = urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": "user-read-currently-playing user-read-playback-state"
    })
    auth_url = f"https://accounts.spotify.com/authorize?{params}"
    
    webbrowser.open(auth_url)
    
    # start server with the url from app (d = daemon, background task)
    httpd = HTTPServer(("127.0.0.1",5000), auth_handler)
    httpd.handle_request()
    
    return httpd.auth_code



def get_token(auth_code):

    """
    turn auth code into usable tokens
    """

    # turn client id and secret codes into a base 64 string
    auth_string = f"{client_id}:{client_secret}"
    auth_base64 = base64.b64encode(auth_string.encode()).decode()

    # set the details of the request
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri
    }

    result = requests.post(url, headers = headers, data = data)

    return result.json() # instead of just a token, get a json which has both access and refresh tokens



def update_token(refresh_token):

    """
    refresh the token as needed (every hour)
    """


    auth_string = f"{client_id}:{client_secret}"
    auth_base64 = base64.b64encode(auth_string.encode()).decode()

    # set the details of the request
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    result = requests.post(url, headers = headers, data = data)
    return result.json()
    





# auth_code = get_auth_code()
# tokens = get_token(auth_code)

# access_token = tokens["access_token"]
# refresh_token = tokens["refresh_token"]



    



# every hour, call update_token(refresh_token)
# actually nvm just do a try catch or something and if it fails, update



# ser.write(b"gurt\n")

# while True:
#     # reading any incoming serial messages
#     line = ser.readline().decode(errors="ignore").strip()
#     if line:
#         print("esp: " + line)


def read_tokens():

    with open("token.txt", "r") as f:
        lines = f.readlines()
        access_token, refresh_token = lines
        
    return access_token.strip("\n"), refresh_token



def update_tokens():
    tokens = update_token(refresh_token)
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    
    # save to a file so i dont have to keep Freaking reopening the browser
    with open("token.txt", "w") as f:
        f.write(access_token+"\n")
        f.write(refresh_token)
    

def get_activity(token):
    url = "https://api.spotify.com/v1/me/player/currently-playing"
    
    headers = {
        "Authorization": "Bearer " + token
    }
    
    result = get(url, headers = headers)
    
    if result.status_code == 401:
        update_tokens()
        result = get(url, headers = headers)
        
    
    data = json.loads(result.content)
    
    
    # decision split here based on time
    
    
    
    # what info to get
    # - song name
    # - artists (comma separated)
    # - album cover url (figure out how to convert to eink)
    # - current timestamp
    # - playing status
    
    # do the time adaptivity thing later on idfk how to do that lmao
    
    # return what. a json file?
    
    type = "large" # use this to differentiate between small and large messages
    title = data["item"]["name"]
    artist_list = data["item"]["artists"] # list
    cover = data["item"]["album"]["images"][0]["url"]
    timestamp = data["progress_ms"]
    is_playing = data["is_playing"]
    
    artist_name_list = []
    for artist in artist_list:
        artist_name_list.append(artist["name"])
    artists = ", ".join(artist_name_list)
    
    
    output = {
        "type": type,
        "title": title,
        "artist": artists,
        "cover": cover,
        "timestamp": timestamp,
        "is_playing": is_playing
    }
    output = json.dumps(output)
    
    ser.write(output.encode("ascii"))
    ser.flush() # wait to finish before proceeding
    


if __name__ == "__main__":
    access_token, refresh_token = read_tokens()
    get_activity(access_token)


# while True:
    
#     message = input("enter (x/o): ")
    
#     if message == "x":
#         print("simulating full display refresh (led should be off)")
#         ser.write(b"asdf\n")
        
#     elif message == "o":
#         print("simulating partial display refresh (led should be on)")
#         ser.write(b"[time] asdf\n")
        
#     else:
#         print("invalid")
        

ser.close()