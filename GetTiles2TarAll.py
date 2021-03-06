#!/usr/bin/env python
#-*- coding: utf-8 -*-
import StringIO
from math import pi, cos, sin, log, exp, atan
from subprocess import call
import sys, os
import multiprocessing
import Tile
import datetime
from multiprocessing import cpu_count
import tarfile



DEG_TO_RAD = pi / 180
RAD_TO_DEG = 180 / pi

# Default number of rendering threads to spawn, should be roughly equal to number of CPU cores available
NUM_THREADS = cpu_count()


def minmax(a, b, c):
    a = max(a, b)
    a = min(a, c)
    return a


class GoogleProjection:
    def __init__(self, levels=18):
        self.Bc = []
        self.Cc = []
        self.zc = []
        self.Ac = []
        c = 256
        for d in range(0, levels):
            e = c / 2;
            self.Bc.append(c / 360.0)
            self.Cc.append(c / (2 * pi))
            self.zc.append((e, e))
            self.Ac.append(c)
            c *= 2

    def fromLLtoPixel(self, ll, zoom):
        d = self.zc[zoom]
        e = round(d[0] + ll[0] * self.Bc[zoom])
        f = minmax(sin(DEG_TO_RAD * ll[1]), -0.9999, 0.9999)
        g = round(d[1] + 0.5 * log((1 + f) / (1 - f)) * -self.Cc[zoom])
        return (e, g)

    def fromPixelToLL(self, px, zoom):
        e = self.zc[zoom]
        f = (px[0] - e[0]) / self.Bc[zoom]
        g = (px[1] - e[1]) / -self.Cc[zoom]
        h = RAD_TO_DEG * (2 * atan(exp(g)) - 0.5 * pi)
        return (f, h)


class DownloadThread:
    def __init__(self, tile, tarPath, q, qWrite, printLock):
        self.tile = tile
        self.tarPath = tarPath
        self.q = q
        self.qWrite = qWrite
        self.printLock = printLock

    def download_tile(self, x, y, z):
        try:
            im = tile.getTile(x, y, z)
            key = "%s/%s/%s/%s_%s.png" % (z, x/10, y/10, x, y)
            # key = "%s/%s/%s.png" % (z, x, y)
            self.qWrite.put((key, im))
        except Exception, e:
            pass

    def loop(self):
        while True:
            if self.q.empty():
                continue
            r = self.q.get()
            if (r == None):
                self.q.task_done()

                break
            else:
                (name, tile_uri, x, y, z) = r

            self.download_tile(x, y, z)
            self.q.task_done()

class WriteThread:
    def __init__(self, tarPath, qWrite):
        self.tar = tarfile.open(tarPath, "w")
        self.qWrite = qWrite
        self.fp = open("./tiles.txt", "w")


    def write_tile(self, key, picContent):
        string = StringIO.StringIO()
        string.write(picContent)
        string.seek(0)
        info = tarfile.TarInfo(name=key)
        info.size = len(string.buf)
        self.tar.addfile(tarinfo=info, fileobj=string)


    def loop(self):
        try:
            while True:
                if self.qWrite.empty():
                    continue

                r = self.qWrite.get()
                if (r == None):
                    self.qWrite.task_done()
                    self.tar.close()
                    self.fp.close()
                    break
                else:
                    (key, im) = r

                self.write_tile(key, im)
                self.fp.write(str(key)+"\n")
                self.qWrite.task_done()
        except Exception,e:
            self.tar.close()
            self.qWrite.task_done
            self.fp.close()



def download_tiles(tile, bbox, tarPath, minZoom=1, maxZoom=18, name="unknown", num_threads=NUM_THREADS):
    print "render_tiles(", bbox, tarPath, minZoom, maxZoom, name, ")"

    # Launch rendering threads
    queue = multiprocessing.JoinableQueue(32)
    qWrite = multiprocessing.JoinableQueue(32)
    printLock = multiprocessing.Lock()


    downloaders = {}
    for i in range(num_threads):
        downloader = DownloadThread(tile, tarPath, queue, qWrite, printLock)
        downloader_thread = multiprocessing.Process(target=downloader.loop)
        downloader_thread.start()
        downloaders[i] = downloader_thread

    # 1个写tar包进程
    tarWriter = WriteThread(tarPath, qWrite)
    write_thread = multiprocessing.Process(target=tarWriter.loop)
    write_thread.start()

    gprj = GoogleProjection(maxZoom + 1)

    ll0 = (bbox[0], bbox[3])
    ll1 = (bbox[2], bbox[1])

    sum = 0
    for z in range(minZoom, maxZoom + 1):
        px0 = gprj.fromLLtoPixel(ll0, z)
        px1 = gprj.fromLLtoPixel(ll1, z)

        for x in range(int(px0[0] / 256.0), int(px1[0] / 256.0) + 1):
            if (x < 0) or (x >= 2 ** z):
                continue
            for y in range(int(px0[1] / 256.0), int(px1[1] / 256.0) + 1):
                if (y < 0) or (y >= 2 ** z):
                    continue
                sum+=1

    print sum

    sumOfProcessed = 0
    for z in range(minZoom, maxZoom + 1):
        px0 = gprj.fromLLtoPixel(ll0, z)
        px1 = gprj.fromLLtoPixel(ll1, z)

        # check if we have directories in place
        zoom = "%s" % z
        for x in range(int(px0[0] / 256.0), int(px1[0] / 256.0) + 1):
            if (x < 0) or (x >= 2 ** z):
                continue
            str_x = "%s" % x
            for y in range(int(px0[1] / 256.0), int(px1[1] / 256.0) + 1):
                if (y < 0) or (y >= 2 ** z):
                    continue
                str_y = "%s" % y
                tile_uri =  zoom + '/' + str_x + '/' + str_y
                t = (name, tile_uri, x, y, z)
                # print t
                try:
                    queue.put(t)
                except Exception, e:
                    pass
                sumOfProcessed+=1
                print "processed : %s%%, %d/%d" % ( str((sumOfProcessed*1.0)/sum*100), sumOfProcessed, sum)

    # Signal render threads to exit by sending empty request to queue
    for i in range(num_threads):
        queue.put(None)

    # wait for pending rendering jobs to complete
    queue.join()

    for i in range(num_threads):
        downloaders[i].join()

    qWrite.put(None)
    qWrite.join()
    write_thread.join()


if __name__ == "__main__":
    starttime = datetime.datetime.now()

    path = "./tmp/"
    if not os.path.exists(path):
        os.makedirs(path)

    minZoom = 10
    maxZoom = 17
    #湖南省
    bbox = (108.790841, 24.636323, 114.261265, 30.126363)
    # bbox = (108.790841, 24.636323, 111.526053, 30.126363)
    # bbox = (111.526053, 24.636323, 114.261265, 30.126363)
    #高德卫星影像
    #tile = Tile.CTile("webst04.is.autonavi.com/appmaptile?style=6")
    #高德栅格底图
    tile = Tile.CTile("webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8")
    #谷歌卫星影像
    # tile = Tile.CTile("mt0.google.cn/maps/vt?lyrs=s%40748&hl=zh-CN&gl=CN")

    download_tiles(tile, bbox, "./hunan_10_17.tar", minZoom, maxZoom)

    endtime = datetime.datetime.now()
    print str(endtime-starttime)