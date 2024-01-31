from fastapi import FastAPI, HTTPException, Form, Depends, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import time
import datetime
from matplotlib.ticker import MaxNLocator
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from fastapi.templating import Jinja2Templates
from datetime import datetime  # Import the datetime module
import asyncio
import uvicorn
import certifi
from matplotlib.colors import LinearSegmentedColormap
import numpy
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
import pandas as pd


app = FastAPI()

alive_status = -1
is_status_saved = 0
loop = asyncio.get_event_loop()
interval_task = None  # Flag to indicate whether the interval should continue


# initially -1 which indicates the initial connection of nodemcu module is not established yet.


# Enable CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Replace the following with your MongoDB connection details
uri = "mongodb+srv://baris:baris@iot.mpbeoff.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi("1"),tlsCAFile=certifi.where())
db = client[
    "your_database_name"
]  # Replace 'your_database_name' with your actual database name
collection = db["sensor_data"]
is_alive = db["is_alive"]

templates = Jinja2Templates(directory="templates")


class SensorData(BaseModel):
    weight: float
    temperature: float


@app.post("/api/sensor")
async def receive_sensor_data(
    temperature=Query(0, description="Skip items"),
    weight=Query(0, description="Limit items"),
    unix=Query(0, description="data sended time"),
):
    # buraya bir veri daha eklendi unix adında. bu datanın arduinodan gönderildiği zamanı söylemekte
    # bu veriyi tarih zaman formatına dönüştürp mongoya kaydedebiliriz, current time yerine kullnadım.
    data_time = datetime.fromtimestamp(float(unix))
    print(temperature, weight, unix, data_time)
    print("d-------------------------data----------time-----> ", data_time)

    try:
        # Insert sensor data into the MongoDB collection
        result = collection.insert_one(
            {
                "temperature": temperature,
                "weight": weight,
                "timestamp": data_time,  # Add current time to the data
            }
        )
        print(f"Data saved to MongoDB with ID: {result.inserted_id}")
    except Exception as e:
        print(f"Error saving data to MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {"message": "Data received and saved successfully"}

# Function to insert zeros for missing timestamps
def insert_zeros_before_first_data(data):
    # Check if the first timestamp is more than 4 hours from the reference time
    reference_time = datetime.now() - timedelta(hours=1)
    if data[0]['timestamp'] > reference_time + timedelta(seconds=30):
        modified_data = []
        current_time = reference_time
        while current_time < data[0]['timestamp']:
            modified_data.append({'temperature': '0', 'weight': '0', 'timestamp': current_time})
            current_time += timedelta(seconds=30)
        modified_data.extend(data)
        return modified_data
    else:
        return data
    
def insert_missing_timestamps(data):
    modified_data = []
    for i in range(len(data) - 1):
        modified_data.append(data[i])
        time_diff = data[i + 1]['timestamp'] - data[i]['timestamp']
        if time_diff.total_seconds() > 30:
            next_time = data[i]['timestamp'] + timedelta(seconds=30)
            while next_time < data[i + 1]['timestamp']:
                modified_data.append({'temperature': '0', 'weight': '0', 'timestamp': next_time})
                next_time += timedelta(seconds=30)
    
    # Adding the last data point
    modified_data.append(data[-1])
    return modified_data

def insert_zeros_after_last_data(data):
    # Get the current time
    current_time = datetime.now()

    # Check if the last timestamp is less than the current time
    if data[-1]['timestamp'] < current_time - timedelta(seconds=30):
        modified_data = data.copy()
        next_time = data[-1]['timestamp'] + timedelta(seconds=30)
        while next_time < current_time:
            modified_data.append({'temperature': '0', 'weight': '0', 'timestamp': next_time})
            next_time += timedelta(seconds=30)
        return modified_data
    else:
        return data


@app.get("/dashboard")
async def dashboard(request: Request):
    try:
        # Fetch all sensor data from MongoDB and sort by timestamp
        cursor = collection.find(
            {}, {"_id": 0, "temperature": 1, "weight": 1, "timestamp": 1}
        ).sort("timestamp", 1)
        sensor_data = list(cursor)
        # Sort sensor data by timestamp
        sensor_data.sort(key=lambda x: x["timestamp"])

        # Filtering data for the last hour
        current_time = datetime.now()
        two_hour_ago = datetime.now() - timedelta(hours=1)
        sensor_data = [d for d in sensor_data if d['timestamp'] > two_hour_ago]
        if len(sensor_data) == 0:
            sensor_data.append({'temperature': '0', 'weight': '0', 'timestamp': datetime.now()})
        sensor_data2 = insert_zeros_before_first_data(sensor_data)
        sensor_data2 = insert_missing_timestamps(sensor_data2)
        sensor_data2 = insert_zeros_after_last_data(sensor_data2)
        # Fetch is_alive data from MongoDB and sort by timestamp
        cursor_is_alive = is_alive.find(
            {}, {"_id": 0, "isAlive": 1, "timestamp": 1}
        ).sort("timestamp", 1)
        alive_data = list(cursor_is_alive)

        # Sort alive data by timestamp
        alive_data.sort(key=lambda x: x["timestamp"])
        alive_data = [d for d in alive_data if d['timestamp'] > two_hour_ago]

        # Extract data for plots
        timestamps = [data["timestamp"] for data in sensor_data]
        temperatures = [
            float(data["temperature"]) for data in sensor_data
        ]  # Convert to float
        weights = [float(data["weight"]) for data in sensor_data]  # Convert to float

        timestamps2 = [data["timestamp"] for data in sensor_data2]
        temperatures2 = [
            float(data["temperature"]) for data in sensor_data2
        ]  # Convert to float
        weights2 = [float(data["weight"]) for data in sensor_data2]  # Convert to float


        timestamps_is_alive = [data["timestamp"] for data in alive_data]
        isAlive = [data["isAlive"] for data in alive_data]

        # Create a plot for time vs alive status
        n = 10  # Adjust this value to control the number of x-axis labels
        limited_timestamps_is_alive = timestamps_is_alive[::n]

        # Create a plot for time vs alive status
        max_ticks = 5  # Adjust this value based on your preference
        locator = MaxNLocator(nbins=max_ticks, prune="both")
        limited_timestamps_is_alive = timestamps_is_alive

        # Create a plot for time vs alive status
        plt.figure(figsize=(8, 4))
        plt.step(timestamps_is_alive, isAlive, where="post", color="blue")
        plt.xlabel("Time")
        plt.ylabel("Alive Status")
        plt.title("Time vs Alive Status")

        # Set the x-axis locator
        plt.gca().xaxis.set_major_locator(locator)

        # Save the alive status plot to a BytesIO object
        alive_stream = io.BytesIO()
        plt.savefig(alive_stream, format="png")
        alive_stream.seek(0)
        alive_stream64 = base64.b64encode(alive_stream.read()).decode("utf-8")

        # Create a plot for time vs weight

        plt.figure(figsize=(10, 6))
        plt.step(timestamps2, weights2,  color="blue")
        plt.plot(timestamps2, weights2, ".--", color="blue", alpha = 0.3)
        plt.xlabel("Time")
        plt.ylabel("Weight")
        plt.xticks(rotation=45)
        plt.title("Time vs Weight")
        plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)



        # Save the weight plot to a BytesIO object
        weight_stream = io.BytesIO()
        plt.savefig(weight_stream, format="png")
        weight_stream.seek(0)
        weight_base64 = base64.b64encode(weight_stream.read()).decode("utf-8")

        # Create a plot for time vs temperature
        time_seconds = [(t - timestamps2[0]).total_seconds() for t in timestamps2]
        X = np.array(time_seconds).reshape(-1, 1)
        y = np.array(temperatures2)
        degree = 10
        polyreg = make_pipeline(PolynomialFeatures(degree), LinearRegression())
        polyreg.fit(X, y)
        plt.figure(figsize=(10, 6))
        plt.plot(X, y, ".--",color='blue', label='Actual Data')
        plt.plot(X, polyreg.predict(X), color='red', label='Polynomial Regression')
        #plt.plot(timestamps, temperatures, marker=".", linestyle="-", color="red")
        plt.xlabel("Time (seconds since 2 hour before)")
        plt.ylabel("Temperature")
        plt.xticks(rotation=45)
        plt.title("Time vs Temperature")
        plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)
        plt.legend()

        # Save the temperature plot to a BytesIO object
        temperature_stream = io.BytesIO()
        plt.savefig(temperature_stream, format="png")
        temperature_stream.seek(0)
        temperature_base64 = base64.b64encode(temperature_stream.read()).decode("utf-8")

        # Create a plot for temperatures vs weight
        norm = plt.Normalize(min(temperatures), max(temperatures))
        colors = ["blue", "red"]
        n_bins = 100  # More bins will give us a finer gradient
        cmap = LinearSegmentedColormap.from_list("blue_to_red", colors, N=n_bins)
        plt.figure(figsize=(8, 4))
        plt.scatter(temperatures, weights, c=temperatures, cmap=cmap, norm=norm)
        plt.xlabel("Temperatures")
        plt.ylabel("Weight")
        plt.title("Temperatures vs Weight")
        plt.grid( linestyle = '--', linewidth = 0.5)
        plt.colorbar()

        # Save the temperature vs weight plot to a BytesIO object
        temp_weight_stream = io.BytesIO()
        plt.savefig(temp_weight_stream, format="png")
        temp_weight_stream.seek(0)
        temp_weight_base64 = base64.b64encode(temp_weight_stream.read()).decode("utf-8")

        # Render the HTML template with dynamic content
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "weight_base64": weight_base64,
                "temperature_base64": temperature_base64,
                "temp_weight_base64": temp_weight_base64,
                "sensor_data": sensor_data,
                "is_alive_base64": alive_stream64,
            },
        )
    except Exception as e:
        print(f"Error fetching data from MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def insert_zeros_for_gaps(data):
    modified_data = []
    for i in range(len(data) - 1):
        modified_data.append(data[i])
        if (data[i + 1]['timestamp'] - data[i]['timestamp']).total_seconds() > 30:
            zero_entry = {'temperature': '0', 'weight': '0', 'timestamp': data[i]['timestamp'] + timedelta(seconds=30)}
            modified_data.append(zero_entry)
    modified_data.append(data[-1])
    return modified_data


@app.get("/api/unix")
def read_unix_time():
    return {"unix": int(time.time())}


@app.get("/api/ping")
async def ping():
    global alive_status
    global is_status_saved
    print("ping received")

    # Reset the interval when a new ping is received
    cancel_interval()
    await startup()

    if alive_status == -1:
        print("sa")
        alive_status = 1
        try:
            # Insert sensor data into the MongoDB collection
            result = is_alive.insert_one(
                {"isAlive": alive_status, "timestamp": datetime.now()}
            )
            print(f"Data saved to MongoDB with ID: {result.inserted_id}")
            is_status_saved = 1
        except Exception as e:
            print(f"Error saving data to MongoDB: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    elif alive_status == 0:
        alive_status = 1
        try:
            # Insert sensor data into the MongoDB collection
            result = is_alive.insert_one(
                {"isAlive": alive_status, "timestamp": datetime.now()}
            )
            print(f"Data saved to MongoDB with ID: {result.inserted_id}")
            is_status_saved = 1

        except Exception as e:
            print(f"Error saving data to MongoDB: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    return Response(status_code=200)


async def start_interval():
    global alive_status
    global is_status_saved
    global interval_task

    try:
        while True:
            await asyncio.sleep(22)  # sleep for 10 seconds
            if alive_status == 1:
                alive_status = 0
                is_status_saved = 0

            if is_status_saved == 0:
                try:
                    # Insert sensor data into the MongoDB collection
                    result = is_alive.insert_one(
                        {"isAlive": alive_status, "timestamp": datetime.now()}
                    )
                    print(f"Data saved to MongoDB with ID: {result.inserted_id}")
                    is_status_saved = 1

                except Exception as e:
                    print(f"Error saving data to MongoDB: {e}")
                    raise HTTPException(status_code=500, detail="Internal Server Error")

            print("Alive status:", alive_status)

    except asyncio.CancelledError:
        pass  # Task was cancelled, ignore the exception


async def startup():
    global interval_task
    interval_task = asyncio.create_task(start_interval())


def cancel_interval():
    global interval_task
    if interval_task:
        interval_task.cancel()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="192.168.165.247", port=8000)
