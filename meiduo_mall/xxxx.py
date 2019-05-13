import requests

url = 'https://fanyi.baidu.com/?aldtype=16047'

head = {
'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
}

qurey_string = {

}
response = requests.get(url, data=qurey_string, headers= head)