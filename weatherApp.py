from _API_ import API_KEY
import streamlit as st
import requests
import sqlite3


DB_NAME = "weatherDB.db"

# URL = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}"
URL = "https://api.openweathermap.org/data/2.5/weather?"


class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        
    def selectCountries(self):
        self.SQL_QUERY_CONUTRIES =  'SELECT * FROM COUNTRIES'
        self.countries = self.cursor.execute(self.SQL_QUERY_CONUTRIES).fetchall()
        self.countriesDict = {
            country[1]:{"ID": country[0], "ISO3": country[2], "PHONE_CODE": country[3], 
                        "CAPITAL":country[4], "LATITUDE": country[7], "LONGITUDE": country[8]}  
            for country in self.countries
            }

    
    def selectStates(self, COUNTRY_ID):
        self.SQL_QUERY_STATES = f"""
        SELECT ST.ID,ST.NAME,CT.NAME,ST.COUNTRY_CODE,ST.STATE_CODE,ST.LATITUDE,ST.LONGITUDE
        FROM STATES AS ST
        LEFT JOIN COUNTRIES AS CT ON CT.ID=ST.COUNTRY_ID 
        WHERE CT.ID = {COUNTRY_ID}"""
        self.states = self.cursor.execute(self.SQL_QUERY_STATES).fetchall()
        self.statesDict = {
            state[1]: {
                "ID": state[0], "COUNTRY": state[2], "COUNTRY_CODE": state[3],
                "STATE_CODE": state[4], "LATITUDE": state[5], "LONGITUDE": state[6]
            }
            for  state in self.states
        }

        
    def selectCities(self,  STATE_ID):
        self.SQL_QUERY_CITIES = f"""
        SELECT CIT.ID, CIT.NAME, STA.NAME, CIT.STATE_CODE,
        CT.NAME, CIT.COUNTRY_CODE, CIT.LATITUDE, CIT.LONGITUDE
        FROM CITIES AS CIT
        LEFT JOIN STATES AS STA ON CIT.STATE_ID=STA.ID
        LEFT JOIN COUNTRIES AS CT ON CIT.COUNTRY_ID=CT.ID
        WHERE STA.ID={STATE_ID}
        """
        self.cities = self.cursor.execute(self.SQL_QUERY_CITIES).fetchall()
        self.citiesDict = {city[1]: {
            "ID": city[0], "STATE_NAME": city[2], "STATE_CODE": city[3], "COUNTRY_NAME": city[4],
            "COUNTRY_CODE":  city[5], "LATITUDE": city[6], "LONGITUDE": city[7]
        }
            for city in self.cities
        }

        
    
class WeatherApp(Database):
    def __init__(self,_url,api_key,DB_NAME):
        super().__init__(DB_NAME)
        self.URL  = _url
        self.API_KEY  = api_key
        # self.params = {
        #         "lat": lat,
        #         "lon": lon,
        #         "appid": self.API_KEY
        # }



    def sidebar(self):
        self.selectCountries()
        
        with st.sidebar:
            self.countryChoice = st.selectbox('Choice Country',self.countriesDict.keys(),placeholder="choose a country",index=None)
            if self.countryChoice:
                self.selectStates(self.countriesDict.get(self.countryChoice).get('ID'))
                
                
        

    
app = WeatherApp(URL,API_KEY,DB_NAME)
app.sidebar()