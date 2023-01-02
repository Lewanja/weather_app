from flask import Flask, render_template, request
import requests
import os
import sqlite3

app = Flask(__name__)


@app.route("/")
def index():
    return "<h1> Welcome to the Home Page</h1>"


@app.route("/get_weather", methods=["GET"])
def get_weather():
    return render_template("weather_form.html")


def check_weather_db(latitude, longitude):
    """
    should not return data longer than 6 hrs
    :param latitude:
    :param longitude:
    :return: if data is found return as tuple of description, wind, temperature else return None"""
    conne_ct = sqlite3.connect('weatherdb.sqlite')
    conne_ct.row_factory = sqlite3.Row
    cursor = conne_ct.cursor()
    cursor.execute(
        f"select * from weather_app where latitude = {latitude} and longitude={longitude};")

    fetch = cursor.fetchall()
    conne_ct.close()
    if len(fetch) != 0:
        return dict(fetch[0])

    else:
        return None


def get_data_from_open_weather(latitude, longitude):
    API_key = os.environ.get("API_key")

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={API_key}"
    print(url)
    weather_response = requests.get(url)

    if weather_response.status_code == 200:
        success_weather_response_json = weather_response.json()
        description = success_weather_response_json["weather"][0]["description"]
        wind = success_weather_response_json["wind"]["speed"]
        temperature = success_weather_response_json["main"]["temp"]
        return dict(description=description, wind=wind, temperature=temperature)
    else:
        failed_weather_response_json = weather_response.json()
        error_message = failed_weather_response_json["message"]
        return dict(error_message=error_message)


@app.route("/post_weather", methods=["POST"])
def post_weather():
    # given lat and long provided by the user through a form
    lat = request.form["Latitude"]
    lon = request.form["Longitude"]

    # first check the sqlite db if it has records
    db_result = check_weather_db(lat, lon)
    # if it has records return those
    if db_result is not None:
        description = db_result["description"]
        wind = db_result["wind"]
        temperature = db_result["temperature"]
        return render_template("base.html", description=description, wind=wind, temperature=temperature)

    #
    # if it doesnt have, then get from open weather api
    else:
        api_weather_data = get_data_from_open_weather(lat, lon)
    # api weather data can either be success or failed dictionary
        if "error_message" in api_weather_data:
            return api_weather_data["error_message"]
        else:
            connection = sqlite3.connect("weatherdb.sqlite")
            cursor = connection.cursor()
            # then insert to sqlite
            db_query = f"""insert into weather_app 
(latitude, longitude, description, wind, temperature , local_time) 
values ({lat},{lon}, '{api_weather_data["description"]}', {api_weather_data["wind"]}, {api_weather_data["temperature"]}, 
time('now') ); """
            cursor.execute(db_query)
            connection.commit()
 # return value
            return render_template("base.html", description=api_weather_data["description"],
                                   wind=api_weather_data["wind"], temperature=api_weather_data["temperature"])


if __name__ == "__main__":
    app.run(debug=True)
