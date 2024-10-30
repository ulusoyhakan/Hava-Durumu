from _API_ import API_KEY
from datetime import datetime, timedelta, timezone
import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
import sqlite3
import json
import os

DB_NAME = "weatherDB.db"
URL = "https://api.openweathermap.org/data/2.5/weather?"

class Database:
    def __init__(self, db_name):
        self.db_name = db_name

    def dbQuery(self,QUERY:str):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        query_response = self.cursor.execute(QUERY).fetchall()
        self.conn.close()
        return query_response
        
    def selectCountries(self):
        self.SQL_QUERY_CONUTRIES =  'SELECT * FROM COUNTRIES'
        self.countries = self.dbQuery(self.SQL_QUERY_CONUTRIES)
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
        self.states = self.dbQuery(self.SQL_QUERY_STATES)
        self.statesDict = {
            state[1]: {
                "ID": state[0], "COUNTRY": state[2], "COUNTRY_CODE": state[3],
                "STATE_CODE": state[4], "LATITUDE": state[5], "LONGITUDE": state[6]
            }
            for  state in self.states
        }

        
    def selectCities(self,  STATE_ID):
        self.SQL_QUERY_CITIES = f"""
        SELECT CIT.ID, CIT.NAME, STA.NAME, CIT.STATE_CODE, CT.NAME,CIT.COUNTRY_CODE, CIT.LATITUDE, CIT.LONGITUDE
        FROM CITIES AS CIT
        LEFT JOIN STATES AS STA ON CIT.STATE_ID=STA.ID
        LEFT JOIN COUNTRIES AS CT ON CIT.COUNTRY_ID=CT.ID
        WHERE STA.ID={STATE_ID}
        """
        self.cities = self.dbQuery(self.SQL_QUERY_CITIES)
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


    def fetch_weather(self,lat,lon):
        """
        lat:  latitude -> enlem
        lon:  longitude -> boylam
        """
        self.params_ = {
                "lat": lat,
                "lon": lon,
                "units": 'metric',
                "lang": "tr",
                "appid": self.API_KEY
        }
        self.response = requests.get(url=self.URL,params=self.params_)
        return self.response.json() if self.response.status_code == 200 else self.response.status_code

        
    def fetch_weather_icon(self,icon_code):
        image_url = F"https://openweathermap.org/img/wn/{icon_code}@2x.png"
        image_response =  requests.get(image_url)
        return image_response.content if image_response.status_code == 200 else None

 
    def time_calculation(self,sunrise_timestamp,sunset_timestamp,timezone_):
        self.SUNRISE = sunrise_timestamp
        self.SUNSET = sunset_timestamp
        self.TIMEZONE = timezone_

        # Zaman dilimi farkını timedelta olarak hesaplıyoruz
        timezone_ofset_delta = timedelta(seconds=self.TIMEZONE)
        local_timezone = timezone(timezone_ofset_delta)
        
        # UTC zamanını timestamp'ten alıyoruz ve yerel zaman dilimiyle datetime nesnesi oluşturuyoruz
        sunrise_local = datetime.fromtimestamp(self.SUNRISE,local_timezone)
        sunset_local = datetime.fromtimestamp(self.SUNSET,local_timezone)
        
        # Yerel zamana uygun formatlama
        sunrise_formatted = sunrise_local.strftime('%H:%M:%S %Z')
        sunset_formatted = sunset_local.strftime('%H:%M:%S %Z')

        return (sunrise_formatted,sunset_formatted)

    
    def get_wind_direction(self,deg):
        if deg >= 337.5 or deg < 22.5:
            return "Kuzey"
        elif 22.5 <= deg < 67.5:
            return "Kuzeydoğu"
        elif 67.5 <= deg < 112.5:
            return "Doğu"
        elif 112.5 <= deg < 157.5:
            return "Güneydoğu"
        elif 157.5 <= deg < 202.5:
            return "Güney"
        elif 202.5 <= deg < 247.5:
            return "Güneybatı"
        elif 247.5 <= deg < 292.5:
            return "Batı"
        elif 292.5 <= deg < 337.5:
            return "Kuzeybatı"


    def sidebar(self):
        self.selectCountries()
        # ülkeler listesi veritabanından çekiliyor & sidebar oluşturuluyor.
        with st.sidebar:
            # veritabanında çekilen ülkeler listesi açılır kutu şeklinde kullanıcıya listeleniyor
            self.countryChoice = st.selectbox('Ülke Seçimi',self.countriesDict.keys(),
                                              placeholder="bir ülke seçin",index=None)
    
            if self.countryChoice:
                # seçilen ülkenin id'si alınıyor selectStates metodu ile ülke id'sine göre (şehirler|eyaletler) listeleniyor
                # ülkenini eyalet|şehir verisi yok ise kullanıcıya bildiriliyor.
                self.selectStates(self.countriesDict.get(self.countryChoice).get('ID'))
                if self.statesDict:
                    self.statesChoice = st.selectbox("Eyalet Seçimi",self.statesDict.keys(),
                                                    placeholder="bir şehir veya eyalet seçin",index=None)
                    
                    if self.statesChoice:
                        # seçilen eyaletin|şehrin id'si alınıyor selectCities metodu
                        # ile seçilen eyaletin|şehrin id'sine göre ileçe|şehir listeleniyor
                        self.selectCities(self.statesDict.get(self.statesChoice).get('ID'))
                        self.citiesChoice = st.selectbox("Şehir S eçimi",self.citiesDict.keys(),
                                                        placeholder="bir şehir veya ilçe seçin",index=None)
                    else:
                        # şehir|eyalet seçimi yapılmazsa default olarak boş liste gösteriliyor
                        st.selectbox("Şehir Seçimi",[''],placeholder="bir şehir veya ilçe seçin",index=None)
    
                else:
                    st.selectbox("Eyalet-İl Seçimi",[''],placeholder="Şehir verisi yok", index=None)
                    st.selectbox("Şehir-İlçe Seçimi",[''],placeholder="İlçe verisi yok", index=None)
                    self.statesChoice = None
                    self.citiesChoice = True

            else:
                # uygulama ilk açıldığında bir ülke seçilmemiş ise selectbox'lar boş bir liste gösteriyor
                st.selectbox("Eyalet-İl Seçimi",[''],placeholder="bir şehir veya eyalet seçin",index=None)
                st.selectbox("Şehir-İlçe Seçimi",[''],placeholder="bir şehir veya ilçe seçin",index=None)
    
    
    def get_countries_geojson(self):
        try:
            country_code =  self.countriesDict.get(self.countryChoice).get("ISO3")
            file_path = Fr"{os.path.join(os.getcwd(),'geojson')}\{country_code}.geojson"
            with open(file=file_path, mode="r",encoding="utf-8") as file:
                geojson_data = json.load(file)
            
            geojson = pdk.Layer(
                type='GeoJsonLayer',
                data=geojson_data,
                stroked=True,
                filled=True,
                get_fill_color='[0, 51, 153, 30]',  # arka plan rengi
                get_line_color='[102, 51, 0]',      # kenarlık rengi
                line_width_min_pixels=1,
                pickable=True
            )
            return geojson
        except AttributeError as err:
            print(err)
            return ""
    

    def map(self):
        try:
            if (self.countryChoice) and (self.statesChoice == None):
                self.LATITUDE = float(self.countriesDict.get(self.countryChoice).get("LATITUDE"))
                self.LONGITUDE = float(self.countriesDict.get(self.countryChoice).get("LONGITUDE"))
                self.ZOOM = 5
                
            elif (self.countryChoice and self.statesChoice) and (self.citiesChoice == None):
                self.LATITUDE = float(self.statesDict.get(self.statesChoice).get("LATITUDE"))
                self.LONGITUDE = float(self.statesDict.get(self.statesChoice).get("LONGITUDE"))
                self.ZOOM = 6

            elif (self.countryChoice and self.statesChoice and self.citiesChoice):
                self.LATITUDE = float(self.citiesDict.get(self.citiesChoice).get('LATITUDE'))
                self.LONGITUDE = float(self.citiesDict.get(self.citiesChoice).get('LONGITUDE'))
                self.ZOOM = 10

            else:
                self.LATITUDE = 0
                self.LONGITUDE = 0
                self.ZOOM = 0.9
        except AttributeError as attr_err:
            st.warning(attr_err, icon="⚠️")

        # Harita için pydeck başlangıç görünümü
        view_state = pdk.ViewState(longitude=self.LONGITUDE,latitude=self.LATITUDE,
            zoom=self.ZOOM,  # Haritanın başlangıç zoom seviyesi
            pitch=0
        )
        
        map_data_point = pd.DataFrame({"longitude": [self.LONGITUDE], "latitude": [self.LATITUDE]})
        # Pydeck harita katmanı (örnek veri olmadan boş harita)
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_data_point,
            get_position="[longitude, latitude]",
            get_color="[0, 255, 255, 120]",
            get_radius=200,
            radius_scale=30,
            radius_min_pixels=6,
            radius_max_pixels=20
        )
                
        geojson = ""
        # Haritayı Streamlit üzerinde göster
        st.pydeck_chart(pdk.Deck(
            layers=[layer,self.get_countries_geojson()],
                initial_view_state=view_state,
                map_style='mapbox://styles/mapbox/outdoors-v12'  # Harita stili
                ),width=750,height=500) # Harita boyutu (px)

    
    def weatherForecast(self):
        wind_to_kmh = lambda wind: (wind * 3600)  / 1000
        try:
            if self.statesChoice or self.citiesChoice:
                response = self.fetch_weather(lat=self.LATITUDE,lon=self.LONGITUDE)
                if type(response) == dict:
                    time_list = self.time_calculation(response['sys']['sunrise'],
                                                      response['sys']['sunset'],response['timezone'])
                    try:
                        sudden_wind =  wind_to_kmh(response['wind']['gust'])
                    except KeyError:
                        sudden_wind  = '0'
                    weatherTable = {
                        "Gün Doğumu": time_list[0],
                        "Gün Batımı": time_list[1],
                        "Açıklama": response["weather"][0]["description"],
                        "Sıcaklık": f'{response["main"]["temp"]:1}°C',
                        "Hissedilen": f'{response["main"]["feels_like"]}°C',
                        "Nem": F'%{response["main"]["humidity"]}',
                        "Rüzgar": F"{wind_to_kmh(response["wind"]["speed"]):.3} km/h",
                        "Rüzgar Yönü": self.get_wind_direction(response["wind"]["deg"]),
                        "Ani Rüzgar": F"{sudden_wind:.3} km/h"
                    }
                    df = pd.DataFrame(weatherTable,index=[0]).transpose()
                    col1,col2 = st.columns(2)
                    col1.header("Hava Durumu")
                    col2.image(self.fetch_weather_icon(response["weather"][0]["icon"]),width=75)
                    st.table(df)
                else:
                    st.info("Hava Durumu Bilgisi Bulunamadı.")
        except AttributeError as err:
            st.info("Lütfen bir şehir seçin.")
            
    
    def appStart(self):
        self.sidebar()
        self.map()
        self.weatherForecast()
    
app = WeatherApp(URL,API_KEY,DB_NAME)
app.appStart()

