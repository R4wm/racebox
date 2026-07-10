# RaceBox - GPS Performance Tracker

A Python-based GPS performance tracker for timing acceleration runs using a USB GPS receiver.

## Features

- Real-time speed display (MPH)
- 0-30 mph timing
- 0-60 mph timing
- 1/8 mile (660 ft) timing with trap speed
- Automatic best times tracking (saved to JSON)

## Hardware

- Tested with GlobalSat BU-353N USB GPS receiver
- Any NMEA-compatible GPS at 4800 baud should work

## Requirements

- Python 3
- pyserial (`pip install pyserial` or `apt install python3-serial`)

## Usage

```bash
# Run the tracker (with screen clearing)
python3 gps_performance.py

# Run without screen clearing (for SSH/logging)
python3 gps_performance.py --no-clear
```

## How It Works

1. Come to a stop (< 2 mph) to arm the timer
2. Accelerate - timing starts automatically when you exceed 2 mph
3. Times are recorded as you hit 30 mph, 60 mph, and 660 feet
4. Best times are saved automatically to `~/gps_best_times.json`

## Troubleshooting

If the GPS isn't detected:
```bash
# Check if device exists
ls /dev/ttyUSB*

# Set permissions
sudo chmod 666 /dev/ttyUSB0

# Add user to dialout group (then re-login)
sudo usermod -a -G dialout $USER
```
