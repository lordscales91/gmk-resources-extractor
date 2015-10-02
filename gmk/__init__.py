from .util import FileReadStream, bytes_to_hex
import xml.etree.ElementTree as tree
from xml.dom import minidom
import os
import logging
import math

class Data:
    
    GMK_SIGN = b'FORM'
    
    def __init__(self):
        self.sign = self.GMK_SIGN
        self.size = 0
        self.sections = []
        self.filenames = {} # A dictionary to map resources to their corresponding filenames
    
    def load(self, fs):
        self.sign = fs.readBytes(4)
        if self.sign != self.GMK_SIGN:
            logging.error('Unknown signature')
            raise Exception('Invalid file')
        self.size = fs.readInt()
        cont = True
        while cont:
            sec = Section.create(fs)
            if sec.tag == 'EOF':
                cont = False
            else:
                if sec.resources_tag is not None:
                    self.filenames[sec.resources_tag] = sec.filenames
                self.sections.append(sec)
        logging.info('### File processed ###')
            
    def saveResources(self, base_path, fs):
        if not os.path.exists(base_path):
            os.mkdir(base_path)            
        for sect in self.sections:
            if sect.tag in self.filenames.keys():
                sect.saveResources(base_path, filenames=self.filenames[sect.tag], data_file=fs)
            else:
                sect.saveResources(base_path, data_file=fs)
            
        logging.info('### Resources saved ###')
                        
            
class Section:    
    IGNORES = []
    def __init__(self, tag, size, start_off):
        self.tag=tag
        self.size=size
        self.start_off=start_off
        self.resources_tag=None
    
    @staticmethod
    def create(fs):
        _CLASSES = {
            'GEN8':IgnoreSection,
            'SOND':SoundSection,
            'AUDO':AudioSection,
            'TXTR':TextureSection,
            'SPRT':SpriteSection,
            }
        section_tag = fs.readTag()
        if section_tag == 'EOF':
            return IgnoreSection('EOF', 0, 0)
        section_size = fs.readInt()
        if section_tag in Section.IGNORES:
            ignore = IgnoreSection(section_tag, section_size, fs.currOffset())
            ignore.load(fs)
            return ignore
        clazz = _CLASSES.get(section_tag, IgnoreSection)
        ret = clazz(section_tag, section_size, fs.currOffset())
        ret.load(fs)
        return ret
    
    def load(self, fs):
        raise Exception("Not implemented! Implement in subclasses")
    
    def saveResources(self, base_dir, subdir=None, filenames=None, data_file=None):
        raise Exception("Not implemented! Implement in subclasses")
            
class IgnoreSection(Section):
    
    def __init__(self, *args):
        Section.__init__(self, *args)
         
    def load(self, fs):                
        # skip section
        logging.info('Ignoring section '+self.tag)
        fs.skipBytes(self.size)
            
    def saveResources(self, base_dir, subdir=None, filenames=None, data_file=None):
        logging.info('Ignoring resources for '+self.tag +" section")
        
class SoundSection(Section):
    
    def __init__(self, *args):
        Section.__init__(self, *args)
        self.soundentries = []
        self.soundoffsets = [] 
        self.resources_tag = 'AUDO' #This section store resource filenames for the AUDO Section  
        self.filenames = []  
        
    def load(self, fs):
        logging.info('### Processing Sound section ###')
        count = fs.readInt()
        logging.info('Reading {0} offset entries'.format(count))        
        for i in range(count): #Read Offsets
            self.soundoffsets.append(fs.readInt())
        logging.info('Loading {0} sound entries'.format(count))
        for off in self.soundoffsets: #Load Entries
            fs.moveToOffset(off)
            entry = SoundEntry()
            entry.load(fs)
            self.filenames.append(entry.filename)
            self.soundentries.append(entry)
        """
        The man behind the design of this format must have a really twisted mind.
        Why do you think it's indicated the size of each section if we could 
        technically calculate it knowing the data structure?
        That's because the REAL size of the section doesn't correspond with the
        calculated size, in fact it's less than what it should be, that's probably
        because there are some pieces of data scattered over the file (which also
        explains the abusive use of the file offsets)... Jesus!
        """ 
        fs.moveToOffset(self.start_off) #So we move to the beginning of the section...
        fs.skipBytes(self.size)#...and then skip to the next section.
        ### THIS IS VERY INEFFICIENT ### 
            
    def saveResources(self, base_dir, subdir=None, filenames=None, data_file=None):
        logging.info('no resources for Sound section only metadata')
            
            
class SoundEntry:
    
    def __init__(self):
        self.name = 'aud'
        self.type = b'\x00\x00\x00\x00'
        self.ext = '.wav'
        self.filename = 'aud.wav'
        self.effects = b'\x00\x00\x00\x00'
        self.volume = b'\x00\x00\x00\x00'
        self.pan = b'\x00\x00\x00\x00'
        self.preload = b'\x00\x00\x00\x00'
        self.audo_index = -1
        
    def load(self, fs):
        self.name = fs.readOffsetStr() 
        self.type = fs.readBytes(4)
        self.ext = fs.readOffsetStr()   
        self.filename = fs.readOffsetStr()
        self.effects = fs.readBytes(4)
        self.volume = fs.readBytes(8)
        self.pan = fs.readBytes(8)
        self.preload = fs.readBytes(4)  
        self.audo_index = fs.readInt()
    
        
    def __repr__(self):
        return str.format('<SoundEntry name={name:}, type={type:}, ext={ext:}, filename={filename:}, '+
                    'effects={effects:}, volume={volume:}, pan={pan:}, preload={preload:}, '+
                    'audio_index={audo_index:d}>',
                    name=self.name, type=bytes_to_hex(self.type), ext=self.ext,
                    filename=self.filename, effects=bytes_to_hex(self.effects),
                    volume=bytes_to_hex(self.volume), pan=bytes_to_hex(self.pan),
                    preload=bytes_to_hex(self.preload), audo_index=self.audo_index)
    
    
           
class AudioSection(Section):  
    def __init__(self, *args):
        Section.__init__(self, *args)
        self.audio_offsets = []
        
    def load(self, fs):       
        logging.info('### Processing Audio section ###') 
        count = fs.readInt()
        logging.info('Reading {0} offset entries'.format(count))
        for i in range(count):
            self.audio_offsets.append(fs.readInt())
        # We will not load all the audio data on memory, so we will skip that data
        fs.moveToOffset(self.start_off)
        fs.skipBytes(self.size)
        
            
    def saveResources(self, base_dir, subdir='audio', filenames=[], data_file=None):
        logging.info('### Saving Resources for Audio section ###')
        if data_file is None:
            raise Exception('Cannot locate data file')
                
        audio_dir = os.path.join(base_dir, subdir)
        if not os.path.exists(audio_dir):
            os.mkdir(audio_dir)
        
        if len(filenames) == 0:
            base_aud = 'aud'
            for i in range(len(self.audio_offsets)):
                filenames.append(base_aud+str(i)+'.wav')   
                
        for name, off in zip(filenames, self.audio_offsets):
            fname = os.path.join(audio_dir, name)
            data_file.moveToOffset(off)
            audio_len = data_file.readInt()
            audio_data = data_file.readBytes(audio_len)# Now is when we load the audio data
            with open(fname, 'wb') as f:
                f.write(audio_data) # And we store it
                
        logging.info('Saved {0} audio files'.format(len(self.audio_offsets)))

class TextureSection(Section):    
    def __init__(self, *args):
        Section.__init__(self, *args)
        self.texture_offsets = []
        self.texture_entries = []
    
    def load(self, fs):
        logging.info('### Processing Texture Section ###')
        count = fs.readInt()
        logging.info('Reading {0} entry offsets'.format(count))
        for i in range(count):
            self.texture_offsets.append(fs.readInt())  
        logging.info('Loading {0} entries'.format(count))
        
        for off in self.texture_offsets:
            fs.moveToOffset(off)
            entry = TextureEntry()
            entry.load(fs)
            self.texture_entries.append(entry)
        #Calculate sizes
        for i in range(len(self.texture_entries)-1):
            entry = self.texture_entries[i]
            if entry.image_size == -1: # this entry was unable to determine the size, let's calculate it
                entry.image_size = self.texture_entries[i+1].image_offset - entry.image_offset
                
        last_entry = self.texture_entries[-1]
        last_off = self.start_off + self.size
        if last_entry.image_size == -1:            
            last_entry.image_size = last_off - last_entry.image_offset            
        fs.moveToOffset(last_off)
            
    def saveResources(self, base_dir, subdir='textures', filenames=[], data_file=None):
        logging.info('### Saving Resources for Texture section ###')
        if data_file is None:
            raise Exception('Cannot locate data file')
        
        tex_dir = os.path.join(base_dir, subdir)
        if not os.path.exists(tex_dir):
            os.mkdir(tex_dir)
        
        if len(filenames) == 0:
            base_tex = 'tex'
            for i in range(len(self.texture_offsets)):
                filenames.append(base_tex+str(i)+'.png')
        
        for name, entry in zip(filenames, self.texture_entries):
            fname = os.path.join(tex_dir, name)
            data_file.moveToOffset(entry.image_offset)
            tex_len = entry.image_size
            tex_data = data_file.readBytes(tex_len)
            with open(fname, 'wb') as f:
                f.write(tex_data) 
                
        logging.info('Saved {0} texture files'.format(len(self.texture_entries)))
        

class TextureEntry:
    def __init__(self):
        self.magic = 0
        self.image_offset = 0 #In case of magic 1 the next 4 bytes indicate a offset to an image
        self.image_size = -1
        
    #Little trick to simulate a switch block    
    def __case0(self, fs):
        pass
        
    def __case1(self, fs):
        self.image_offset = fs.readInt()        
    
    def load(self, fs):
        self.magic = fs.readInt()
        __CASES = {
            0:self.__case0,
            1:self.__case1,
            }
        func = __CASES.get(self.magic, self.__case0)
        func(fs)
    
    def __repr__(self):
        return str.format('<TextureEntry magic={magic:d}, image_offset={image_offset:d}, '+
                          'image_size={image_size:d}>',
                          magic=self.magic, image_offset=self.image_offset,
                          image_size=self.image_size)

class SpriteSection(Section):
    def __init__(self, *args):
        Section.__init__(self, *args)
        self.sprite_offsets = []
        self.sprite_entries = []        
        
    def load(self, fs):
        logging.info('### Processing Sprite Section ###')
        count = fs.readInt()
        logging.info('Reading {0} offset entries'.format(count))
        for i in range(count):
            self.sprite_offsets.append(fs.readInt())
        logging.info('Loading {0} entries'.format(count))
        for off in self.sprite_offsets:
            fs.moveToOffset(off)
            entry = SpriteEntry()
            entry.load(fs)
            self.sprite_entries.append(entry)
            
    def saveResources(self, base_dir, subdir=None, filenames=None, data_file=None):
        logging.info('### Saving Resources for Sprite section ###')
        root = tree.Element('sprites')
        for entry in self.sprite_entries:
            attrib={'name':entry.name,
                    'width':str(entry.width),
                    'height':str(entry.height),
                    'leftPad':str(entry.leftPad),
                    'rightPad':str(entry.rightPad),
                    'bottomPad':str(entry.bottomPad),
                    'originX':str(entry.originX),
                    'originY':str(entry.originY),
                    'collision_mask':str(entry.collision_mask),}
            e = tree.SubElement(root, 'sprite', attrib)
            # e.text = 'Mask = '+bytes_to_hex(entry.mask)
            subimages = tree.SubElement(e, 'subimages')
            for off in entry.subimages_offsets:
                tree.SubElement(subimages, 'offset', {'value':str(off)})
                
        ugly = tree.tostring(root, 'utf-8')
        reparsed = minidom.parseString(ugly)
        pretty = reparsed.toprettyxml(indent='  ', newl=os.linesep, encoding='utf-8')
        xml = os.path.join(base_dir, 'sprites.xml')
        with open(xml, 'wb') as f:
            f.write(pretty)
        logging.info('Saved {0} sprite entries metadata into an XML'.format(len(self.sprite_entries)))
        

class SpriteEntry:
    def __init__(self):
        self.name = ''
        self.width = 0
        self.height = 0
        self.leftPad = 0
        self.rightPad = 0
        self.bottomPad = 0
        self.topPad = 0
        self.originX = 0
        self.originY = 0
        self.subimages_offsets = []
        self.collision_mask = 0
        self.mask = b''
    
    def load(self, fs):
        self.name = fs.readOffsetStr()
        self.width = fs.readInt()
        self.height = fs.readInt()
        self.leftPad = fs.readInt()
        self.rightPad = fs.readInt()
        self.bottomPad = fs.readInt()
        self.topPad = fs.readInt()
        fs.skipBytes(5*4) #Unknown bytes
        self.originX = fs.readInt()
        self.originY = fs.readInt()
        count = fs.readInt() #Number of sub-images
        for i in range(count):
            self.subimages_offsets.append(fs.readInt())
        self.collision_mask = fs.readInt()
        for i in range(math.ceil(self.width/8) * self.height):
            self.mask += fs.readBytes(1)
            
    def __repr__(self):
        return str.format('<SpriteEntry name={name:}, width={width:d}, height={height:d}, '+
                          'originX={originX:d}, originY={originY:d}>',
                          name=self.name, width=self.width, height=self.height, originX=self.originX,
                          originY=self.originY)
        

    
        
        
def setIgnores(ignore):
    __IGNORES = []
    _IGNOREMAP = {
        'sound':('SOND', 'AUDO'),
        'textures':('TXTR', ),
        'sprites':('SPRT', ),
        }
    for i in ignore:
        __IGNORES += _IGNOREMAP.get(i)
        
    Section.IGNORES = __IGNORES
    

def load(path, output_dir='.'):
    with FileReadStream(path) as fs:
        d = Data()
        d.load(fs)
        d.saveResources(output_dir, fs)
        
    