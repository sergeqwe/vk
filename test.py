import sys
import time
import requests
from requests.auth import HTTPProxyAuth

proxies = {'http': 'http://lepinskiy.s.v:Subzero1010@proxy.neyvabank.ru:3128'}
auth = HTTPProxyAuth('lepinskiy.s.v', 'Subzero1010')

url = 'https://api.vk.com/method/photos.get?v=5.32&owner_id=-17655824&album_id=wall&count=1000&rev=1&photo_sizes=1'

def main() :
  start = time.clock()
  r = requests.get(url, stream=True, proxies=proxies, auth=auth)
  print(r.status_code)


  dl = 0
  total_length = r.headers.get('content-length')
  for chunk in r.iter_content(1024):
        dl += len(chunk)
        # f.write(chunk)
        done = int(50 * dl / int(total_length))
        sys.stdout.write("\r[%s%s] %s bps" % ('=' * done, ' ' * (50-done), dl//(time.clock() - start)))
        print ('')


  print('END')
  print(r.text)


if __name__ == "__main__" :
  main()