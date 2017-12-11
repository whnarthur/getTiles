import lmdb
import os
img_lmdb = lmdb.open("./hunan")
txn= img_lmdb.begin()
cursor = txn.cursor()
for ( idx, (key, value) ) in enumerate(cursor):
    (z, x, y) = key.split('_')
    path = "./%s/%s/" % (z, x)
    desPath = "./%s/%s/%s.png" % (z, x, y)
    if not os.path.exists(path):
        os.makedirs(path)

    with open(desPath, "wb") as fp_w:
        fp_w.write(value)

