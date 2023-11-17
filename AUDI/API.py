import re

import requests
import logging

from bs4 import BeautifulSoup

BASE_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "de,en-US;q=0.7,en;q=0.3"
                }

BASE_API_URL = "https://prod.emea.cbs.charging.cariad.digital/home-charging/"

login_page_url = "https://identity.vwgroup.io/oidc/v1/authorize?client_id=21a54939-7081-4f39-ba49-ceb3d6d95b1a@apps_vw-dilab_com&scope=openid&response_type=code&redirect_uri=https://mobile-audi.emea.home.charging.cariad.digital/auth"
email_login_url = "https://identity.vwgroup.io/signin-service/v1/21a54939-7081-4f39-ba49-ceb3d6d95b1a@apps_vw-dilab_com/login/identifier"
password_login_url = "https://identity.vwgroup.io/signin-service/v1/21a54939-7081-4f39-ba49-ceb3d6d95b1a@apps_vw-dilab_com/login/authenticate"
get_token_url = "https://prod.emea.cbs.charging.cariad.digital/user-identity/v2/identity/login"


class API:
    def __init__(self, email, password):
        self.session = requests.session()
        self.email = email
        self.password = password
        self.header = BASE_HEADERS

    def login(self):
        logging.info("Start Login procedure...")

        enter_mail_page = self.session.get(login_page_url, headers=BASE_HEADERS)
        # get login tokens from login page out of html
        html = BeautifulSoup(enter_mail_page.text, "html.parser")
        csrf = html.find("input", {"id": "csrf"}).attrs["value"]
        input_relayState = html.find("input", {"id": "input_relayState"}).attrs["value"]
        hmac = html.find("input", {"id": "hmac"}).attrs["value"]

        payload = {
            "hmac": hmac,
            "relayState": input_relayState,
            "_csrf": csrf,
            "email": self.email,
        }

        send_mail_req = self.session.post(email_login_url, data=payload, headers=BASE_HEADERS)

        # get new hmac and csrf token from js script
        csrf = re.findall(r"csrf_token: '.*',", send_mail_req.text)[0].split("'")[1]
        hmac = re.findall(r'"hmac":"(.*?)"', send_mail_req.text)[0].split('"')[0]

        payload = {
            "hmac": hmac,
            "relayState": input_relayState,
            "_csrf": csrf,
            "email": self.email,
            "password": self.password
        }

        # send password
        send_pw_req = self.session.post(password_login_url, data=payload, headers=BASE_HEADERS)

        payload = {
            "code": send_pw_req.url.split("?")[1].removeprefix("code="),
            "msp_login": True,
            "redirect_uri": "https://mobile-audi.emea.home.charging.cariad.digital/auth"
        }

        login_req = self.session.post(get_token_url, json=payload, headers=BASE_HEADERS)

        bearer_str = "Bearer " + login_req.json()["access_token"]
        self.header.update({"Authorization": bearer_str})

        wc_access_token_str = login_req.json()["msp_access_token"]
        self.header.update({"wc_access_token": wc_access_token_str})

        logging.info("Login successful")

    def get_sessions(self):
        logging.info("Get sessions")
        ret = self.session.get(BASE_API_URL + "v2/charging/sessions", headers=self.header)


        print(ret.json())

    def get_stations(self):
        logging.info("Get Stations")
        ret = self.session.get(BASE_API_URL + "v1/stations", headers=self.header)

        print(ret.json())

    def get_firmware(self, station_id):
        logging.info("Get Firmware from Station: " + str(station_id))
        ret = self.session.get(BASE_API_URL + "v1/stations/" + station_id + "/firmware", headers=self.header)

        print(ret.json())

    def stop_charging(self, session_id):
        logging.info("Stop charging session: " + str(session_id))
        ret = self.session.post(BASE_API_URL + "v1/charging/sessions/" + session_id + "/stop", headers=self.header)

        print(ret)

    def start_charging(self, station_id):
        logging.info("Start charging on station: " + str(station_id))
        ret = self.session.post("https://prod.emea.cbs.charging.cariad.digital/home-charging/v1/charging/sessions/start", json={"station_id": station_id}, headers=self.header)

        print(ret)