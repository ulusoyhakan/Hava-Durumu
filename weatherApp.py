from _API_ import API_KEY
from datetime import datetime
import streamlit as st
import pydeck as pdk
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
        SELECT CIT.ID, CIT.NAME, STA.NAME, CIT.STATE_CODE, CT.NAME,CIT.COUNTRY_CODE, CIT.LATITUDE, CIT.LONGITUDE
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


    def request_(self,lat,lon):
        self.params_ = {
                "lat": lat,
                "lon": lon,
                "units": 'metric',
                "lang": "tr",
                "appid": self.API_KEY
        }
        self.response = requests.get(url=self.URL,params=self.params_)
        if self.response.status_code  == 200:
            return  self.response.json()
        else:
            return self.response.status_code
        

    def sidebar(self):
        self.selectCountries()
        # ülkeler listesi veritabanından çekiliyor
        
        # sidebar oluşturuluyor.
        with st.sidebar:
            # veritabanında çekilen ülkeler listesi açılır kutu şeklinde kullanıcıya listeleniyor
            self.countryChoice = st.selectbox('Choice Country',self.countriesDict.keys(),placeholder="bir ülke seçin",index=None)
         
            if self.countryChoice:
                # kullanıcı ülke seçimini yaptıktan sonra seçilen ülkenin id'si alınıyor 
                # ve veritabanından o ülkenin id'sine göre (şehirler|eyaletler) listeleniyor
                
                self.selectStates(self.countriesDict.get(self.countryChoice).get('ID'))
                self.statesChoice = st.selectbox("Choice State",self.statesDict.keys(),placeholder="bir şehir veya eyalet seçin",index=None)
                
                
                if self.statesChoice:
                    # şehir|eyalet seçimi yapıldıise  seçilen eyaletin|şehrin id'si alınıyor
                    # ve veritabanından o eyaletin|şehrin id'sine göre ileçe|şehir listeleniyor
                    
                   self.selectCities(self.statesDict.get(self.statesChoice).get('ID'))
                   self.citiesChoice = st.selectbox("Choice City",self.citiesDict.keys(),placeholder="bir şehir veya ilçe seçin",index=None)
                else:
                    # şehir|eyalet seçimi  yapılmazsa default olarak boş liste gösteriliyor
                    st.selectbox("Choice Cities",[''],placeholder="bir şehir veya ilçe seçin",index=None)
   
                
            else:
                # uygulama ilk açıldığında bir ülke seçilmemiş ise kullanıcıya boş şehir ve ilçe listesi gösteriliyor
                st.selectbox("Choice State",[''],placeholder="bir şehir veya eyalet seçin",index=None)
                st.selectbox("Choice Cities",[''],placeholder="bir şehir veya ilçe seçin",index=None)

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
    
    
    def map(self):
        
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
            print(self.LATITUDE)
            print(self.LONGITUDE)

        else:
            self.LATITUDE = 0
            self.LONGITUDE = 0
            self.ZOOM = 0.9

        # Harita için pydeck başlangıç görünümü
        view_state = pdk.ViewState(
            latitude=self.LATITUDE,
            longitude=self.LONGITUDE,
            zoom=self.ZOOM,  # Haritanın başlangıç zoom seviyesi
            pitch=0
        )

        # Pydeck harita katmanı (örnek veri olmadan boş harita)
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=[],  # Veri eklemek isterseniz buraya ekleyebilirsiniz
            get_position="[longitude, latitude]",
            get_color="[200, 30, 0, 160]",
            get_radius=200,
        )

        # Haritayı Streamlit üzerinde göster
        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style='mapbox://styles/mapbox/outdoors-v12'  # Harita stili, opsiyonel
        ),width=580,height=386) # Harita boyutu

    
    def weatherForecast(self):
        if self.statesChoice or self.citiesChoice:
            response = self.request_(lat=self.LATITUDE,lon=self.LONGITUDE)
            if type(response) == dict:
                sunrise = datetime.fromtimestamp(response['sys']['sunrise']).time().strftime("%H:%M:%S")
                sunset = datetime.fromtimestamp(response['sys']['sunset']).time().strftime("%H:%M:%S")
                description = response["weather"][0]["description"]
                temperature = response["main"]["temp"]
                sensedTemperature = response["main"]["feels_like"]
                humidity = response["main"]["humidity"]
                windSpeed = response["wind"]["speed"]
                windDeg = self.get_wind_direction(response["wind"]["deg"]) 
                winGust = response["wind"]["gust"]
                
                col1,col2,col3 = st.columns(3)
                col1.metric("Gün Doğumu",sunrise)
                

app = WeatherApp(URL,API_KEY,DB_NAME)
app.sidebar()
app.map()
app.weatherForecast()


