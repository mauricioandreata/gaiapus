#!/usr/bin/env python3
"""Copy the bench firmware into the Wokwi project (single source of truth: firmware/)."""
import os, shutil
R = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
W = os.path.join(R, "sim", "wokwi")
shutil.copyfile(os.path.join(R, "firmware", "src", "main.cpp"), os.path.join(W, "sketch.ino"))
for h in ("gaiapus_protocol.h", "pinos.h"):
    shutil.copyfile(os.path.join(R, "firmware", "include", h), os.path.join(W, h))
print("sim/wokwi updated from firmware/")
