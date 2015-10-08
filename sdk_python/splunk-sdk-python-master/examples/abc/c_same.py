import splunklib.client as client

HOST = "localhost"
PORT = 8000
USERNAME = "admin"
PASSWORD = "Pg18december"

# Create a Service instance and log in 
service = client.connect(
    host=HOST,
    port=PORT,
    username=USERNAME,
    password=PASSWORD)

# Print installed apps to the console to verify login
for app in service.apps:
      print app.name
