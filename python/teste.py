import requests

url = 'http://54.90.186.23:5000/upload'
files = {'file': open('teste.csv', 'rb')}
r = requests.post(url, files=files)
print(r.text)
