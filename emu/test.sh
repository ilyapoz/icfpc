#!/bin/sh
for i in `seq 1000000`; do
    ./seed $i > cpp
    ./emu.py $i > py

    diff cpp py
done
