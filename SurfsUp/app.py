# Import the dependencies.
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import numpy as np
import pandas as pd
import datetime as dt
from datetime import datetime, timedelta


from flask import Flask, jsonify



#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")


# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
measures = Base.classes.measurement
stations_data = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def homepage():
    """List all available routes"""
    return (
        f"Available Routes: <br/>"
        f"----------------------------------------------------------------------------------------------------------------------------------------------------------------------<br/>"
        f" <br/>"
        f"This route provides information on the last 12 months of precipitation data in Hawaii from the most recent date recorded<br/>"
        f" <br/>"
        f"/api/v1.0/precipitation<br/>"
        f" <br/>"
        f"----------------------------------------------------------------------------------------------------------------------------------------------------------------------<br/>"
        f" <br/>"
        f"This route provides the full list of stations this dataset has recorded within Hawaii<br/>"
        f" <br/>"
        f"/api/v1.0/stations<br/>"
        f" <br/>"
        f"----------------------------------------------------------------------------------------------------------------------------------------------------------------------<br/>"
        f" <br/>"
        f" <br/>"
        f"This route provides the last 12 months of temperature observation from this dataset's recorded most active station within Hawaii<br/>"
        f" <br/>"
        f"/api/v1.0/tobs<br/>"
        f" <br/>"
        f"----------------------------------------------------------------------------------------------------------------------------------------------------------------------<br/>"
        f" <br/>"
        f"For the following two routes, input a start or start/end date in between '2010-01-01' and '2017-08-23' with a YYYY-MM-DD format. <br/>"
        f"For example: /api/v1.0/2012-12-27/2017-01-01 <br/>"
        f" <br/>"
        f"Start API route:<br/>"
        f"/api/v1.0/<start><br/>"
        f" <br/>"
        f"Start/End API route:<br/>"
        f"/api/v1.0/<start>/<end><br/>"
        f" <br/>"
    )
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return precipitation analysis dictionary"""
    # Find the most recent date in the data set.
    recent_date_data = session.query(func.max(measures.date)).first()
    print(f"The most recent date is: {recent_date_data}")
    
    recent_date_str = recent_date_data[0]
    recent_date = dt.datetime.strptime(recent_date_str, '%Y-%m-%d')

    # Calculate the date one year from the last date in data set.- I used 366 days in order to include 2016-08-23
    year_before = recent_date - dt.timedelta(days = 366)

    # Query 12 months of precipitation data
    results = session.query(measures.date, measures.prcp).filter(measures.date >= year_before).all()

    session.close()

    # Create dictionary with precipitation analysis results- date as key and prcp as value
    prcp_data = {}
    for date, prcp in results:
        prcp_data[date] = prcp

    return jsonify(prcp_data)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = session.query(stations_data.station).all()

    session.close()

    # Returning a list of the different stations
    station_names = []
    for name in results:
        station_names.append(name[0])

    return jsonify(station_names)    

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    # Finding the most active station
    most_active = session.query(measures.station, func.count(measures.station)).\
        group_by(measures.station).\
        order_by(func.count(measures.station).desc()).first()[0]

    # Finding the most recent date for the most active station
    most_tobs_recent_date = session.query(measures.date).\
    filter(measures.station == most_active).\
    order_by(measures.date.desc()).first()[0]
    print(f"The most recent date for the most active station is: {most_tobs_recent_date}")

    recent_tobs_date_str = most_tobs_recent_date

    recent_tobs_date = dt.datetime.strptime(recent_tobs_date_str, '%Y-%m-%d')

    # Calculate the date one year from the most recent date for the most active station.
    year_ago = recent_tobs_date - dt.timedelta(days = 366)

    # Perform a query to retrieve the data and tobs scores
    most_tobs_data = session.query(measures.date, measures.tobs).\
        filter(measures.station == most_active, measures.date >= year_ago).all()

    session.close()
    
    # Returning just a list of the tobs
    tobs_data = []
    for tobs in most_tobs_data:
        tobs_data.append(tobs[1])

    return jsonify(tobs_data)    

# Start and End Dynamic routes 
@app.route("/api/v1.0/<start>")
def start(start):
    """Give tobs information starting from the date supplied by the user"""
    session = Session(engine)
    
    # Parsing input data to a datetime object
    start_date = datetime.strptime(start, '%Y-%m-%d')
    print(start_date)
   
    # Setting the stats calculations and start date as the input given by the user in the url
    # Included - timedelta(days=1) to include start date as part of the results
    start_date_info = session.query(
        measures.date,
        func.min(measures.tobs),
        func.max(measures.tobs),
        func.avg(measures.tobs)).\
        filter(measures.date >= start_date - timedelta(days=1)).\
        group_by(measures.date).all()

    session.close()

    # Formatting returned information into a dictionary with the provided labels
    start_stats = {}
    for info in start_date_info:
        date = info[0]
        start_stats[date] = {
            "min_temp" : info[1],
            "max_temp" : info[2],
            "avg_temp" : info[3]
        }
              
    return jsonify(start_stats)

@app.route("/api/v1.0/<start>/<end>")
def end(start, end):
    """Give tobs information starting from and ending with the dates supplied by the user"""
    session = Session(engine)
    
    # Parsing start and end inputs into datetime objects 
    start_date = datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.strptime(end, '%Y-%m-%d')

    # Setting the stats, start, and end dates as the input given by the user in the url
    # Included - timedelta(days=1) to include start date as part of the results
    start_end_date_info = session.query(
        measures.date,
        func.min(measures.tobs),
        func.max(measures.tobs),
        func.avg(measures.tobs)).\
        filter(measures.date >= start_date - timedelta(days=1), measures.date <= end_date).\
        group_by(measures.date).all()

    session.close()

    # Formatting returned information into a dictionary with the provided labels
    start_end_stats = {}
    for info in start_end_date_info:
        date = info[0]
        start_end_stats[date] = {
            "min_temp" : info[1],
            "max_temp" : info[2],
            "avg_temp" : info[3]
        }
        
    return jsonify(start_end_stats)

if __name__ == '__main__':
    app.run(debug=True)