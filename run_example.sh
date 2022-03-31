#!/usr/bin/env bash
set -e
# Example script to use a DLI WPS7 to turn on/off UV lamp

# I have these in my .bashrc
# export WPS7_HOST=ahost
# export WPS7_USER=admin
# export WPS7_PASS=password

echo "Arming lamp"
./wps7.py --switch 1 --on
read -p "Turn on timer/lamp and press enter"

# Most parameters change slowly
# However user should also give like: --device AM2764A@DIP28 --sn ee01
./collect.py \
        --user mcmaster --eraser pe140t-2 --bulb 4 \
        --passes 3 --write-init \        
        "$@" || true

# Will run even if above fails
./wps7.py --switch 1 --off
echo "Done"

