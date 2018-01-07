#!/usr/bin/env python
#-*- coding: utf-8 -*-
#从tar包读取key信息  或者使用命令：tar tf hunan_yingxiang_18_1.tar > 1.txt
#当tar包不完整时，该脚本读不出来

import datetime
import tarfile

if __name__ == "__main__":
    starttime = datetime.datetime.now()
    tarPath = "./hunan_yingxiang_10.tar"
    output = "./tiles.txt"

    fp = open(output,"w")
    tar = tarfile.open(tarPath )
    file_names = tar.getnames()
    for file_name in file_names:
        fp.write(file_name+"\n")
        fp.flush()
    tar.close()
    fp.close()