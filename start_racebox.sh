#!/bin/bash
# RaceBox Startup Script

echo '========================================'
echo '       RACEBOX GPS TRACKER'
echo '========================================'
echo ''
echo 'Waiting for GPS device...'

# Wait for GPS device to appear (up to 60 seconds)
for i in {1..60}; do
    if [ -e /dev/ttyUSB0 ]; then
        echo 'GPS device found!'
        sleep 2
        break
    fi
    echo -n '.'
    sleep 1
done

if [ ! -e /dev/ttyUSB0 ]; then
    echo ''
    echo 'ERROR: GPS device not found!'
    echo 'Please plug in the BU-353N GPS'
    echo ''
    echo 'Press Enter to retry...'
    read
    exec $0
fi

# Ensure we have permission
sudo chmod 666 /dev/ttyUSB0

# Run the tracker
cd /home/r4wm/github/racebox
python3 gps_performance.py

# If it exits, wait and restart
echo ''
echo 'Tracker stopped. Restarting in 5 seconds...'
sleep 5
exec $0
