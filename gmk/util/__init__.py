import logging
import struct
import os

class FileStream:
    def __init__(self, path, file_obj):
        self.__path = path
        self.__file_obj = file_obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def path(self):
        return self.__path

    def close(self):
        if self.__file_obj is not None:
            logging.debug('close the file("%s")', self.__path)
            self.__file_obj.close()
            self.__file_obj = None
            
class FileReadStream(FileStream):
    def __init__(self, path):
        self.__fin = open(path, 'rb')
        FileStream.__init__(self, path, self.__fin)
        
    def moveToOffset(self, off):
        self.__fin.seek(off)
    
    def skipBytes(self, num):
        self.__fin.seek(num, os.SEEK_CUR)
    
    def currOffset(self):
        return self.__fin.tell()
        
    def readTag(self):
        buf = self.__fin.read(4)
        if len(buf) != 4:
            return 'EOF'
        tag ,= struct.unpack('4s', buf)
        return str(tag, 'cp437')
    
    def readOffsetStr(self):
        offset = self.readInt()
        curoff = self.__fin.tell() #Save the current offset
        self.__fin.seek(offset-4)
        s = self.readStr()
        self.__fin.seek(curoff) #Go back to the current offset before continue
        return s
    
    # READ methods for general types
    def readInt(self):
        v, = struct.unpack('<i', self.__fin.read(4))
        return v
    
    def readStr(self):
        length = self.readInt()
        fmt = '<' + str(length) + 's'
        buf, = struct.unpack(fmt, self.__fin.read(length))
        self.skipBytes(1) # Skip null byte at the end        
        return str(buf, 'cp437')
    
    def readByte(self):
        v, = struct.unpack('<B', self.__fin.read(1))
        return v

    def readBytes(self, length):
        return self.__fin.read(length)
    
def bytes_to_hex(buf):
    return '['+', '.join('{0:#04x}'.format(x) for x in buf)+']'
    