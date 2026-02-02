#!/bin/bash


SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd "$SCRIPT_DIR"

GUI_USER=$(who | awk '{print $1}' | head -n1)
GUI_HOME=$(getent passwd "$GUI_USER" | cut -d: -f6)

sudo DISPLAY=:0 XAUTHORITY="$GUI_HOME/.Xauthority" /usr/bin/python3 "$SCRIPT_DIR/synapse_deck.py"
