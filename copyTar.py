#!/usr/bin/env python
#-*- coding: utf-8 -*-
#将未写完的tar包里面的内容拷贝到一个新的tar包
import StringIO
import tarfile

tar = tarfile.open("hunan_yingxiang_11.tar", "r:")
files = tar.getnames()
for file in files:
    print file
