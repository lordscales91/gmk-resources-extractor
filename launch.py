import gmk
import sys
import logging
import argparse


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Utility to recover lost resources from GameMaker data.win files')
    parser.add_argument('input', metavar='<data.win>', 
                        help='refers to the main resource file usually called with this name.')
    parser.add_argument('output', metavar='output_dir', nargs='?', default='data',
                        help='optional base directory for the recovered resources, it defaults to "data"')
    parser.add_argument('-ignore', nargs='+', choices=['sound', 'textures', 'sprites'],
                        help='specifies which resources should be ignored, therefore not saved to disk')
    parser.add_argument('--convert', action='store_true',
                        help='Specifies if the metadata should be processed to get the final resources'+
                        ' (Ex. get the sprites)')    
    args=parser.parse_args()    
    # set up logger
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)
    
    path = args.input
    output = args.output
    if args.ignore is not None:
        gmk.setIgnores(args.ignore)
    if args.convert:
        gmk.CONVERT_RESOURCES = True
    gmk.load(path, output)
    