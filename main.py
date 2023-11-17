import logging

from AUDI.API import API
import json

logging.basicConfig(level=logging.INFO)

cred = open("credentials.json")
login_data = json.load(cred)
logging.info("Read user credentials: " + login_data["email"])


myApi = API(login_data["email"], login_data["password"])
myApi.login()

myApi.get_stations()
myApi.get_sessions()





