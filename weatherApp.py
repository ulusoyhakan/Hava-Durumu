from _API_ import API_KEY
import streamlit as st
import requests
import sqlite3

# URL = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}"
# URL = "https://api.openweathermap.org/data/2.5/weather?"


class WeatherApp:
    def __init__(self,_url,api_key,lat,lon):
        self.URL  = _url
        self.API_KEY  = api_key
        self.params = {
                "lat": lat,
                "lon": lon,
                "appid": self.API_KEY
        }


        



    

