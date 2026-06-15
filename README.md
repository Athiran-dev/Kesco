# KESCO Electricity Billing Data Analysis Dashboard

A modern, high-performance local dashboard for analyzing KESCO electricity billing data. 
Built with a Python (FastAPI) backend for heavy data crunching and a React (Vite) frontend for a beautiful, animated UI.

## Setup & Running Instructions

### Windows (Easiest Way)
You do not need to install anything manually! Just follow these steps:
1. Ensure you have Python and Node.js installed on your computer.
2. Double-click the **`run_windows.bat`** file.
3. The script will automatically install all Python dependencies, all React dependencies, and launch both servers. Your browser will automatically open the dashboard.

### Mac / Linux
1. Open Terminal and navigate to this folder.
2. Run the backend:
   ```bash
   cd backend
   pip3 install -r ../requirements.txt
   python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```
3. Open a second Terminal window and run the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Features
- **Modern UI:** Glassmorphism, smooth animations, and a responsive dark mode layout.
- **Smart Data Parsing:** Automatic smart meter classification using regex heuristics.
- **Dynamic Filtering:** Slice and dice your data across 4 core vectors.
- **Live Updating:** Instantly edit specific Account IDs and save directly back to the excel file.
