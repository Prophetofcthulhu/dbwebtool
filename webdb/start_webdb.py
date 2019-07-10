#!/usr/bin/env python

import argparse

import sys
sys.path.append("../")


from server_start import go

parser = argparse.ArgumentParser(description="Web DB Tool")
parser.add_argument('--path')
parser.add_argument('--number')
parser.add_argument('--port')


if __name__ == '__main__':
    args = parser.parse_args()
    go(host=args.path or '0.0.0.0', port=args.port or "8886")
