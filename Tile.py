import urllib,urllib2
class CTile:
    def __init__(self, baseUrl):
        self.baseUrl = baseUrl

    def getTile(self, x, y, z):
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        headers = {'User-Agent': user_agent}

        try:
            url = "http://1%s&x=%s&y=%s&z=%s" % (self.baseUrl, x, y, z)
            request = urllib2.Request(url, headers=headers);
            tile = urllib2.urlopen(request).read();
            return tile
        except Exception, e:
            with open("error.txt", "a+") as fp:
                fp.write(url+"\n")
            raise  e

