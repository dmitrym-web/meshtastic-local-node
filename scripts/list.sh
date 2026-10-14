#!/bin/bash
echo "Задания проекта:"
crontab -l 2>/dev/null | grep "meshtastic-local:" | awk -F'# ' '{print "  " $2}' | sed 's/meshtastic-local://'