import requests
import time
import datetime

success_response = 0
fail_response = 0

print("Please enter the duration for the run (in seconds): ")
x = input()

for i in range(int(x)):
    response = requests.get("http://169.254.170.22/")
    # response = requests.get("http://google.com")
    print(response.status_code)
    if (response.status_code == 200):
        success_response = success_response + 1
    else:
        fail_response = fail_response + 1
    time.sleep(1)

f = open("demofile2.txt", "a")
f.write("\n")
f.write("\n")
f.write("time started: " + str(datetime.datetime.now()))
f.write("\n")
f.write("successful responses = " + str(success_response) + "\n")
f.write("failed responses = " + str(fail_response))
f.close()