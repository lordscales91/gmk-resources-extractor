import gmk
import sys
import logging

def usage():
    print('launch.py <data.win> [output_dir]')

if __name__ == '__main__':
    
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        usage()
    else:
        # set up logger
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)
        
        path = sys.argv[1]
        output = 'data'
        try:
            output = sys.argv[2]
        except:
            pass
        gmk.load(path, output)
    