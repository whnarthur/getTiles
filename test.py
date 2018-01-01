import StringIO
import tarfile

tar = tarfile.open("hunan_yingxiang_11.tar", "a")
print tar.getnames()
