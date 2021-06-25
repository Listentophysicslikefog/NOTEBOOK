#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os


def help():
    print "Usage: " + sys.argv[0] + " <region> <set>"


def main():
    if len(sys.argv[1:]) < 2:
        help()
        sys.exit()

    region = sys.argv[1]
    set_id = sys.argv[2]

    p2p_file = os.path.join(os.environ['HOME'], "limax", "udisk",
                           "region", region, set_id, "p2p_info")
    if os.path.exists(p2p_file):
        print("p2p")
    else:
        print("non-p2p")

if __name__ == "__main__":
    main()

