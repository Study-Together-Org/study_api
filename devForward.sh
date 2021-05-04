#!/usr/bin/env bash

# sql/mariadb ports
ssh -fN -L 3306:localhost:3306 root@95.179.130.39

# redis ports
ssh -fN -L 6379:localhost:6379 root@95.179.130.39

# discord ext ipc ports
ssh -fN -L 20000:localhost:20000 root@95.179.130.39
ssh -fN -L 8765:localhost:8765 root@95.179.130.39
