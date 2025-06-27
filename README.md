# DXF Floor Plan Processing Web Application

This project provides a web-based interface and backend API for uploading, processing, and viewing DXF files to extract floor plan images. It supports filtering layers by keywords, excluding unwanted data, and exporting floor images.

---

## Features

- Upload one or multiple DXF files linked to specific projects.
- Automatically process DXF files to extract categorized floor plan images.
- Filter and exclude layers or blocks based on keywords, blacklist, and excluded layers.
- View a list of processed DXF files for each project.
- View detailed floor plan images and export selected views.
- Backend API built with FastAPI.
- Frontend built with React.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

  
### Running the Application

To get the project up and running locally, please follow these steps:

## 1. Start the Backend Server
- Navigate to the backend directory in your terminal.
- Activate your Python environment (e.g., using `venv` or `conda`).
- Run the FastAPI server with the following command:
  
  ```bash
  uvicorn app.main:app --reload


## 2. Start the Frontend Application
- Navigate to the frontend directory in your terminal.
- Install project dependencies by running:

  ```bash
  npm install



