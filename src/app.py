from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse
from dotenv import load_dotenv
from requests import post, get
import base64, serial, json, math, webbrowser, requests, time, os

from PIL import Image
from dithering import ordered_dither
import urllib.request
import numpy as np

ser = serial.Serial("COM6", 115200)
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
    
    # print(result.json())
    return result.json()
    



# auth_code = get_auth_code()
# tokens = get_token(auth_code)

# access_token = tokens["access_token"]
# refresh_token = tokens["refresh_token"]



def read_tokens():
    
    """
    return access and refresh token from tokens file 
    """

    with open("token.txt", "r") as f:
        lines = f.readlines()
        access_token, refresh_token = lines
        
    return access_token.strip("\n"), refresh_token


def update_tokens(ref_token):
    
    """
    get new access token with the PERPETUAL refresh token
    """
    
    tokens = update_token(ref_token) # get json
    access_token = tokens["access_token"]
    
    # resave to file
    with open("token.txt", "w") as f:
        f.write(access_token+"\n")
        f.write(ref_token)
        print("new token written!")
    

last = {
    "type": None,
    "title": None,
    "artist": None,
    "cover": None,
    "timestamp": None,
    "duration": None,
    "completion": None,
    "is_playing": None,
    "id": None
} # save last recorded details

cooldown_counter = 3 # for refresh cooldown




def pack_image(big_img):
    
    """ 
    reduces load by compacting image into packed bytes
    """
    
    flat = big_img.flatten()
    
    packed = bytearray()
    for i in range(0, len(flat), 8): # group into bytes
        byte = 0
        for bit in range(8):
            if flat[i + bit] == 255:
                byte |= (1 << (7 - bit))
        
        packed.append(byte)
        
    return packed


def get_activity(token, refresh):
    
    global last
    global cooldown_counter
    
    """ 
    the actual Meat and Potaro of this program. outputs a json with contents dependent on activity
    """
    
    
    url = "https://api.spotify.com/v1/me/player/currently-playing"
    
    headers = {
        "Authorization": "Bearer " + token
    }
    
    result = get(url, headers = headers)
    
    if result.status_code == 401:
        print("updating token...")
        update_tokens(refresh)
        result = get(url, headers = headers)
        
        access_token, refresh_token = read_tokens()
        get_activity(access_token, refresh_token)
        result.status_code = 200
    
    if result.content == "b''" or result.status_code == 204:
        # no activity for a loooong time
        # use last saved data
        print("been a while since last activity")
        print(last)
        return last
        
    data = json.loads(result.content)
    # print(data)
    
    if not data.get("item"):
        return
    
    
    def ms_convert(ms):
        seconds = ms / 1000
        minutes = math.floor(seconds / 60)
        seconds = math.floor(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    title = data.get("item").get("name")
    artist_list = data.get("item").get("artists") # list
    if len(data.get("item").get("album").get("images")) > 0:
        cover = data.get("item").get("album").get("images")[0].get("url")
    # else:
    #     cover = "/assets/man.jpg" # placeholder
    timestamp = ms_convert(data.get("progress_ms"))
    duration = ms_convert(data.get("item").get("duration_ms"))
    timestamp = f"{timestamp} / {duration}" 
    is_playing = data.get("is_playing")
    
    id = data.get("item").get("id")
    
    
    # convert artists list to string
    artist_name_list = []
    for artist in artist_list:
        artist_name_list.append(artist.get("name"))
    artists = ", ".join(artist_name_list)
    
    
    # cover processing
    # urllib.request.urlretrieve(cover, "cover.jpeg") # get from spotify url
    # image = np.array(Image.open("cover.jpeg").resize((200,200), Image.LANCZOS))
    # # os.remove("cover.jpeg")
    
    # converted = ordered_dither(image, "Bayer2x2")
    
    # converted = np.where(converted > 127, 255, 0)
    # packed = pack_image(converted)
    
    # barray = []
    
    # for row in converted:
    #     for col in row:                
    #         if col[0] == 255:
    #             barray.append(0xFF)
    #             # print("appended black")
    #         else:
    #             barray.append(0x00)
    #             # print("appended white")
                
    # # print(barray)
    # data = bytes(barray)
    # ser.write(data)
    
    

    completion = round(data.get("progress_ms")/data.get("item").get("duration_ms"), 3) # get song playback percentage

    
    # decision split here based on time?
    
    print(f"playing: {is_playing}")
    
    if is_playing:
        
        if cooldown_counter < 4:
            cooldown_counter += 2
    
        if last.get("id") == id: # still listening to the same song
            
            print("currently on same song | partial refresh, red ON")
            
            # send only timestamp
            output = {
                "type": "S", # differentiate between partial and full refreshes
                "timestamp": timestamp,
                "completion": completion
            }
            
            string_output = f"S|{timestamp}|{completion}"
            
        else: # listening to different song
            
            if cooldown_counter > 2:
            
                print("song changed | full refresh, green ON")

                output = {
                    "type": "L",
                    "title": title,
                    "artist": artists,
                    "cover": None,
                    "timestamp": timestamp,
                    "completion": completion,
                    "is_playing": is_playing,
                    "id": id 
                }
                last = output # refresh last saved
                
                string_output = f"L|{title}|{artists}|{None}|{timestamp}|{completion}"
                
                cooldown_counter = 0
            
            else:
                print("tried full refreshing before cooldown is cleared")
                return
            
        
    
    else: # if no music is playing, dont return anything at all
        print("nothing changes")
        if cooldown_counter < 4:
            cooldown_counter += 2
        return
    
    
    output = json.dumps(output)
    
    # length = len(data)
    # print(length)
    # ser.write(f"{length}\n".encode())
    print(string_output)

    # ser.write(output.encode("ascii"))

    ser.write(string_output.encode())


    ser.flush() # wait to finish before proceeding
    
    # time.sleep(0.05)
    # ser.write(packed)
    # ser.flush
    


if __name__ == "__main__":
    access_token, refresh_token = read_tokens()
    # get_activity(access_token)
    # ser.close()
    
    
    # temp testing
    while True:
        # gurt = input()
        get_activity(access_token, refresh_token)
        print(f"c: {cooldown_counter}")
        # line = ser.readline().decode(errors="ignore").strip()
        # if line:
        #     print("esp: " + line)
        time.sleep(2)
    

        

