import subprocess
import queue
import requests
import json
import urllib.parse as urlparse
import threading

filequeue = queue.Queue()
j = json.load(open("./datasource/download.update.json"))['response_data']


def unzipfile():
    q = filequeue.get()

    while q:
        p = subprocess.call(['unzip', '-o', '-d', q[1], q[0]])
        print(p)
        delemp = subprocess.call('find "' + q[1] + '" -name "*" -type f -size 0c | xargs -n 1 rm -f', shell=True)
        q = filequeue.get()
    subprocess.call('find "' + q[1] + '" -name "*" -type d -empty | xargs -n 1 rm -f', shell=True)

t = threading.Thread(target=unzipfile)
t.start()
for x in j:
    name = urlparse.urlsplit(x['url']).path.split('/')[-1]
    print("下载", name, end="\n\n")
    r = requests.get(x['url'])
    path = "/home/eh5/PycharmProjects/llproxy-api/update/zip/" + name
    unzippath = '/home/eh5/PycharmProjects/llproxy-api/update/files_auto'
    open(path, 'wb').write(r.content)
    filequeue.put((path, unzippath))
filequeue.put(False)
