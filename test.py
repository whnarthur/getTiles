import StringIO
import tarfile

tar = tarfile.open("test.tar", "w")
string = StringIO.StringIO()
string.write("hello")
string.seek(0)
info = tarfile.TarInfo(name="10/1/2.png")
info.size = len(string.buf)
tar.addfile(tarinfo=info, fileobj=string)