import requests
import time
import datetime

success_response = 0
fail_response = 0

print("Please enter the duration for the run (in seconds): ")
x = input()

for i in range(int(x)):
    print(str(i))
    try:
        response = requests.get("http://169.254.170.22/", timeout=10)
        # response = requests.get("http://google.com")
        success_response = success_response + 1
        print(str(i) + " Success")
    except:
        fail_response = fail_response + 1
        print(str(i) + " Fail")
    time.sleep(1)

f = open("results.txt", "a")
f.write("\n")
f.write("\n")
f.write("time started: " + str(datetime.datetime.now()))
f.write("\n")
f.write("successful responses = " + str(success_response) + "\n")
f.write("failed responses = " + str(fail_response))
f.close()