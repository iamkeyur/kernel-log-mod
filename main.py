#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import database
import c_detector
import detector
import config
import time


def initialize_repo_database():
    database.create_tables()


def main():
    initialize_repo_database()
    repo = "/home/keyur/Desktop/Kernel_Research_Git/linux/"
    c_detector.detect_project(repo, True, None)


if __name__ == '__main__':
    s = time.time()
    config.initialize()
    main()
    e = time.time()
    print("time : " + str(e-s))
