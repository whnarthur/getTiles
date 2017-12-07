#获取输入省份的边界，可以通过高德api获取
with open("/Users/weihainan/Documents/input.txt") as fp:
    input = fp.readline().split(",")
    minx = 200
    miny = 90
    maxx = 0
    maxy = 0
    index = 1
    for i in input:
        # print i
        value = float(i)
        if index%2:
            if value<minx:
                minx = value
            if value>maxx:
                maxx = value
        else:
            if value<miny:
                miny = value
            if value>maxy:
                maxy = value
        index += 1
    print minx, miny, maxx, maxy