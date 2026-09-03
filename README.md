# LA Urban Environmental Risk Explorer

An interactive web mapping application for exploring environmental risk patterns across Los Angeles neighborhoods.

The LA Urban Environmental Risk Explorer was developed as my senior Computer Science capstone project at the University of Redlands. The goal was to bring multiple environmental datasets into one interactive interface and make complex spatial risk information easier to explore and understand.

### Live Application

[View the LA Urban Environmental Risk Explorer](https://chloewernher.github.io/la-risk-explorer/)

## Project Overview

Environmental risk is rarely defined by a single factor. This project brings together multiple environmental indicators and allows users to explore how risk varies across Los Angeles neighborhoods.

The interface was designed to let users move between a high-level view of neighborhood risk and more detailed environmental context without requiring GIS experience.

Users can change risk scenarios, interact directly with neighborhoods, view individual risk breakdowns, and overlay additional environmental datasets for further context.

## Features

- Interactive neighborhood-level risk map
- Dynamic risk scoring across Los Angeles neighborhoods
- Multiple risk-focused scenario presets
- Interactive neighborhood popups with scores and risk breakdowns
- Historical wildfire perimeter overlay
- FEMA flood hazard zone overlay
- Air pollution context layer
- Air pollution indicators for PM2.5, ozone, diesel particulate matter, traffic pollution, toxic releases, and pesticides
- Context filtering by wildfire year, FEMA flood zone, and air pollution indicator
- Dynamic map legend and visual risk classifications
- Light and dark basemap options
- Responsive interactive controls for exploring the data

## Environmental Context Layers

### Wildfire History

Historical wildfire perimeters provide geographic context for areas that have experienced wildfire activity. Fire geometries are clipped to the project's Los Angeles study area before being displayed on the map.

### FEMA Flood Zones

FEMA National Flood Hazard Layer data provides mapped flood hazard classifications. Users can display flood zones over the neighborhood risk map and filter the overlay by FEMA flood zone.

### Air Pollution

CalEnviroScreen environmental indicators provide additional air pollution and environmental exposure context.

Available indicators include:

- PM2.5
- Ozone
- Diesel particulate matter
- Traffic pollution
- Toxic releases
- Pesticides

Users can switch between indicators to explore how different environmental conditions vary geographically.

## Data Processing

The environmental datasets originate from different sources and geographic boundaries, so preprocessing is used to create a consistent study area.

Python and Shapely are used to validate and clip wildfire, flood, and air pollution geometries to the Los Angeles neighborhood study area. The processed datasets are exported as GeoJSON for use by the web application.

This approach keeps the deployed application lightweight while preserving the spatial relationships needed for interactive exploration.

## Architecture

The original capstone architecture included a FastAPI backend with PostgreSQL/PostGIS for spatial data storage, querying, and risk calculations.

For the public portfolio deployment, the application uses preprocessed static GeoJSON files and client-side JavaScript. This removes the dependency on a continuously running database while allowing the interactive mapping and visualization functionality to remain publicly accessible.

The portfolio version is hosted using GitHub Pages.

## Technologies

**Frontend**
- JavaScript
- HTML
- CSS
- Leaflet

**Geospatial & Data Processing**
- GeoJSON
- Python
- Shapely
- QGIS / ArcGIS

**Original Backend Architecture**
- FastAPI
- PostgreSQL
- PostGIS

**Deployment**
- GitHub Pages

## Data Sources

Environmental and geographic data used in the project includes:

- CAL FIRE historical fire perimeter data
- FEMA National Flood Hazard Layer
- CalEnviroScreen environmental indicators
- Los Angeles neighborhood boundary data

The datasets were processed and clipped to create a consistent geographic study area for the application.

## Design Approach

A major goal of the project was to make spatial risk information understandable without overwhelming the user with raw GIS data.

The interface uses color, progressive detail, contextual overlays, interactive filtering, and neighborhood-level popups to allow users to explore the information at their own pace.

Rather than displaying every dataset simultaneously, users can select the environmental context most relevant to what they are investigating. This keeps the primary neighborhood risk visualization readable while still providing access to more detailed geographic information.

## Development

This project was developed as a senior Computer Science capstone at the University of Redlands and combines software development, GIS, spatial data processing, and interactive visualization.

The project evolved from a database-backed prototype into a self-contained public web application designed to make the work easy to access and explore.

## Author

**Chloe Wernher**  
B.S. Computer Science, University of Redlands
