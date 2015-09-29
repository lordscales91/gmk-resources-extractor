from .util import FileReadStream, bytes_to_hex
import os
import logging

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
            
        logging.info('### Resources saved ###')
                        
            
class Section:    
    
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
            }
        section_tag = fs.readTag()
        if section_tag == 'EOF':
            return IgnoreSection('EOF', 0, 0)
        section_size = fs.readInt()
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
            audio_data = data_file.readBytes(audio_len)#Now is when we load the audio data
            with open(fname, 'wb') as f:
                f.write(audio_data) # And we store it
                
        logging.info('Saved {0} audio files'.format(len(self.audio_offsets)))

        
        
        
def load(path, output_dir='.'):
    with FileReadStream(path) as fs:
        d = Data()
        d.load(fs)
        d.saveResources(output_dir, fs)
        
    