from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import csv
import aiohttp
import asyncio
import uvicorn


# Create an instance of the FastAPI application
# Connect the Jinja2 template to work with HTML templates (templates folder)
app = FastAPI()
templates = Jinja2Templates(directory='templates')


# Global Dictionary of Cities
cities = {}


# Function for loading a list of cities from a CSV file
# As a result, the cities will be saved to the global cities dictionary
def load_cities(filename):
    global cities
    with open(filename, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Use city name as the key to avoid confusion
            city_name = row['country']
            cities[city_name] = {'latitude': float(row['latitude']), 'longitude': float(row['longitude'])}


# Load a list of cities
load_cities('europe.csv')


# Handler for the initial page index.html
# We explicitly indicate that this is HTML
@app.get('/', response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


# Handler for path GET /update
# It should return the cities and their temperatures to the Javascript in the index.html file
# was able to read and display this list
@app.get('/update')
async def fetch_weather():
    global cities
    async with aiohttp.ClientSession() as session:
        # This nested function gets the temperature for a given city
        # using the open-meteo.com API
        async def fetch_city_weather(name):
            try:
                # Assuming the cities dictionary contains latitude and longitude information
                if name in cities:
                    lat = cities[name]['latitude']
                    lon = cities[name]['longitude']
                    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                    async with session.get(url) as response:
                        data = await response.json()
                        # Extract the temperature from the API response
                        temperature = data['current_weather']['temperature']
                        cities[name]['temperature'] = temperature
                else:
                    print(f"City {name} not found in cities dictionary.")
            except Exception as e:
                print(f"Error fetching weather for {name}: {e}")


        # Create tasks for each city
        # and wait until they are all executed asynchronously
        tasks = [fetch_city_weather(city) for city in cities]
        await asyncio.gather(*tasks)
    return cities


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="localhost", port=8080)