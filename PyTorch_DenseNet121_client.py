# PyTorch DenseNet121 client 
import requests

resp = requests.post("http://localhost:5000/predict",
                     files={"file": open('./images/cat.jpg','rb')})

print(resp.text)