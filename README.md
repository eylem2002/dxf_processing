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
To run the project locally, start by launching the backend server. Navigate to the backend folder, activate your Python environment, and run the FastAPI server using a command such as uvicorn app.main:app --reload. This will start the backend API, usually accessible at http://localhost:8000. Next, open a new terminal window, go to the frontend folder, and start the React development server by running npm start. The frontend will launch in your default browser at http://localhost:3000. Make sure both the backend and frontend servers are running simultaneously to use the full functionality of the application.
