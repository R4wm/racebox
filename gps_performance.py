#!/usr/bin/env python3
"""
GPS Performance Tracker - Direct NMEA parsing
- Current speed display
- 0-30 mph timing
- 0-60 mph timing  
- 1/8 mile (660 ft) timing

Usage: python3 gps_performance.py [--no-clear]
"""

import serial
import json
import time
import os
import sys
from math import radians, sin, cos, sqrt, atan2

# Constants
KNOTS_TO_MPH = 1.15078
FEET_PER_METER = 3.28084
EIGHTH_MILE_FEET = 660.0

# Config
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 4800
BEST_TIMES_FILE = os.path.expanduser("~/gps_best_times.json")

# Check for --no-clear flag
NO_CLEAR = '--no-clear' in sys.argv

def load_best_times():
    try:
        with open(BEST_TIMES_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"0_30": None, "0_60": None, "eighth_mile": None, "eighth_mile_speed": None}

def save_best_times(times):
    with open(BEST_TIMES_FILE, 'w') as f:
        json.dump(times, f, indent=2)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in meters"""
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))

def parse_nmea_coord(coord_str, direction):
    """Parse NMEA coordinate to decimal degrees"""
    if not coord_str or not direction:
        return None
    try:
        if direction in ['N', 'S']:
            deg = float(coord_str[:2])
            mins = float(coord_str[2:])
        else:
            deg = float(coord_str[:3])
            mins = float(coord_str[3:])
        decimal = deg + mins / 60.0
        if direction in ['S', 'W']:
            decimal = -decimal
        return decimal
    except:
        return None

def parse_gprmc(sentence):
    """Parse GPRMC sentence for speed and position"""
    parts = sentence.split(',')
    if len(parts) < 10:
        return None
    try:
        status = parts[2]
        if status != 'A':
            return None
        lat = parse_nmea_coord(parts[3], parts[4])
        lon = parse_nmea_coord(parts[5], parts[6])
        speed_knots = float(parts[7]) if parts[7] else 0
        speed_mph = speed_knots * KNOTS_TO_MPH
        return {'lat': lat, 'lon': lon, 'speed_mph': speed_mph, 'valid': True}
    except:
        return None

def clear_screen():
    if not NO_CLEAR:
        print('\033[2J\033[H', end='', flush=True)

def main():
    best_times = load_best_times()
    
    # Run state
    run_active = False
    run_start_time = None
    run_start_lat = None
    run_start_lon = None
    time_0_30 = None
    time_0_60 = None
    time_eighth = None
    speed_at_eighth = None
    max_speed_in_run = 0
    
    START_SPEED_THRESHOLD = 2.0
    SPEED_30_MPH = 30.0
    SPEED_60_MPH = 60.0
    
    print("Opening GPS serial port...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    except Exception as e:
        print(f"Error opening serial port: {e}")
        print("Make sure GPS is plugged in and try: sudo chmod 666 /dev/ttyUSB0")
        return
    
    print("Connected! Waiting for GPS fix...\n")
    time.sleep(1)
    
    try:
        while True:
            try:
                line = ser.readline().decode('ascii', errors='ignore').strip()
            except:
                continue
            
            if not line.startswith('$GPRMC'):
                continue
            
            data = parse_gprmc(line)
            if not data or not data['valid']:
                continue
            
            speed_mph = data['speed_mph']
            lat = data['lat']
            lon = data['lon']
            
            clear_screen()
            
            print("=" * 55)
            print("         GPS PERFORMANCE TRACKER")
            print("=" * 55)
            print(f"  Position: {lat:.6f}, {lon:.6f}")
            print("-" * 55)
            print(f"        >>> SPEED: {speed_mph:5.1f} MPH <<<")
            print("-" * 55)
            
            # Run logic
            if not run_active:
                if speed_mph < START_SPEED_THRESHOLD:
                    print("  STATUS: READY - Accelerate to start timing!")
                else:
                    print(f"  STATUS: Slow to <2 mph to arm ({speed_mph:.1f} mph)")
            
            if not run_active and speed_mph >= START_SPEED_THRESHOLD and lat and lon:
                run_active = True
                run_start_time = time.time()
                run_start_lat = lat
                run_start_lon = lon
                time_0_30 = None
                time_0_60 = None
                time_eighth = None
                speed_at_eighth = None
                max_speed_in_run = 0
            
            if run_active and lat and lon:
                elapsed = time.time() - run_start_time
                distance_m = haversine_distance(run_start_lat, run_start_lon, lat, lon)
                distance_ft = distance_m * FEET_PER_METER
                max_speed_in_run = max(max_speed_in_run, speed_mph)
                
                if time_0_30 is None and speed_mph >= SPEED_30_MPH:
                    time_0_30 = elapsed
                    if best_times["0_30"] is None or time_0_30 < best_times["0_30"]:
                        best_times["0_30"] = time_0_30
                        save_best_times(best_times)
                
                if time_0_60 is None and speed_mph >= SPEED_60_MPH:
                    time_0_60 = elapsed
                    if best_times["0_60"] is None or time_0_60 < best_times["0_60"]:
                        best_times["0_60"] = time_0_60
                        save_best_times(best_times)
                
                if time_eighth is None and distance_ft >= EIGHTH_MILE_FEET:
                    time_eighth = elapsed
                    speed_at_eighth = speed_mph
                    if best_times["eighth_mile"] is None or time_eighth < best_times["eighth_mile"]:
                        best_times["eighth_mile"] = time_eighth
                        best_times["eighth_mile_speed"] = speed_at_eighth
                        save_best_times(best_times)
                
                print(f"\n  >> RUN ACTIVE: {elapsed:.2f}s | {distance_ft:.0f} ft | Max: {max_speed_in_run:.1f} mph")
                print(f"  0-30: {time_0_30:.2f}s" if time_0_30 else "  0-30: ---")
                print(f"  0-60: {time_0_60:.2f}s" if time_0_60 else "  0-60: ---")
                if time_eighth:
                    print(f"  1/8 mi: {time_eighth:.2f}s @ {speed_at_eighth:.1f} mph")
                else:
                    print(f"  1/8 mi: {distance_ft:.0f}/660 ft")
                
                if speed_mph < START_SPEED_THRESHOLD:
                    run_active = False
                    print("\n  >> RUN COMPLETE <<")
            
            print("\n" + "-" * 55)
            print("  BEST TIMES:")
            print(f"    0-30 mph:  {best_times['0_30']:.2f}s" if best_times['0_30'] else "    0-30 mph:  --")
            print(f"    0-60 mph:  {best_times['0_60']:.2f}s" if best_times['0_60'] else "    0-60 mph:  --")
            if best_times['eighth_mile']:
                print(f"    1/8 mile:  {best_times['eighth_mile']:.2f}s @ {best_times['eighth_mile_speed']:.1f} mph")
            else:
                print("    1/8 mile:  --")
            print("=" * 55)
            print("  Ctrl+C to exit")
            
    except KeyboardInterrupt:
        print("\n\nExiting...")
        ser.close()

if __name__ == "__main__":
    main()
