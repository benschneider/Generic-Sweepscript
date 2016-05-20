#!/bin/bash

gcc -I /Users/benschneider/anaconda/pkgs/python-2.7.11-0/include/python2.7 -I /Users/benschneider/anaconda/pkgs/numpy-1.10.4-py27_2/lib/python2.7/site-packages/numpy/core/include/numpy-c $1 -o $1.o
gcc -L/usr/local/lib $1.o -lgsl -lgslcblas -lm -o $2
