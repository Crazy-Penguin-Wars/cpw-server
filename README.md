## Prerequisites
Make sure you have Python installed.

## Setup
To get started with this server, do the following:

1. Create a Virtual Python Environment using `python -m venv .venv`
2. Activate the venv (virtual environment) by running `source .venv/bin/activate` on Linux/MacOS or by running `.venv/Scripts/activate.bat` on Windows.
3. Install the necessary requirements `pip install -r requirements.txt` inside the venv.
4. You can now run the app with `python app.py`.

At any point you can exit the venv by running `deactivate`, to re-enter again run `python -m venv venv`

## Config
Copy the `.env.example` and rename it to `.env`, in here you will set all the necessary environment variables.  
For a development setup, the defaults should work.
