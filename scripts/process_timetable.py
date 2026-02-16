#!/usr/bin/env python3
"""
Process Network Rail timetable data into compact JSON for Pulse.

Prerequisites:
  1. Register at https://publicdatafeeds.networkrail.co.uk
  2. Download SCHEDULE (CIF/JSON) feed
  3. Download CORPUS reference data (for TIPLOC → CRS mapping)
  4. Download station locations CSV (from ellcom/UK-Train-Station-Locations on GitHub)

Usage:
  python3 process_timetable.py --schedule SCHEDULE.json.gz --corpus CORPUS.json --stations stations.csv

Output:
  data/trains.json — compact JSON ready for the frontend
"""

import argparse
import gzip
import json
import csv
import os
import sys
from datetime import datetime
from collections import defaultdict

# STP indicator priority: C(ancel) > N(ew) > O(verlay) > P(ermanent)
STP_PRIORITY = {'C': 4, 'N': 3, 'O': 2, 'P': 1}


def load_corpus(corpus_path):
    """Load CORPUS reference data for TIPLOC → CRS mapping."""
    with open(corpus_path) as f:
        data = json.load(f)

    tiploc_to_crs = {}
    for entry in data.get('TIPLOCDATA', []):
        tiploc = entry.get('TIPLOC', '').strip()
        crs = entry.get('3ALPHA', '').strip()
        if tiploc and crs:
            tiploc_to_crs[tiploc] = crs

    print(f"Loaded {len(tiploc_to_crs)} TIPLOC→CRS mappings from CORPUS")
    return tiploc_to_crs


def load_stations(stations_path):
    """Load station coordinates from CSV."""
    stations = {}
    with open(stations_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            crs = row.get('CRS', row.get('crs', row.get('StationCode', row.get('3alpha', '')))).strip()
            lat = row.get('Latitude', row.get('lat', row.get('latitude', '')))
            lng = row.get('Longitude', row.get('lng', row.get('longitude', '')))
            name = row.get('StationName', row.get('name', row.get('Name', row.get('station_name', crs))))
            if crs and lat and lng:
                try:
                    stations[crs] = {
                        'name': name.strip(),
                        'lat': float(lat),
                        'lng': float(lng),
                    }
                except ValueError:
                    continue

    print(f"Loaded {len(stations)} station coordinates")
    return stations


def parse_time(time_str):
    """Parse working timetable time (HHMM or HHMMH) to seconds since midnight."""
    if not time_str or time_str.strip() == '':
        return None
    t = time_str.strip()
    try:
        h = int(t[:2])
        m = int(t[2:4])
        s = 30 if len(t) > 4 and t[4] == 'H' else 0
        return h * 3600 + m * 60 + s
    except (ValueError, IndexError):
        return None


def is_tuesday(days_run):
    """Check if a service runs on Tuesdays (representative weekday)."""
    if not days_run or len(days_run) < 7:
        return True  # assume yes if missing
    return days_run[1] == '1'


def process_schedule(schedule_path, tiploc_to_crs, stations):
    """Process SCHEDULE feed and extract train services."""
    print(f"Processing schedule: {schedule_path}")

    # Read schedule entries
    if schedule_path.endswith('.gz'):
        f = gzip.open(schedule_path, 'rt', encoding='utf-8')
    else:
        f = open(schedule_path, 'r', encoding='utf-8')

    # Group by CIF UID for STP overlay handling
    schedules_by_uid = defaultdict(list)

    for line in f:
        try:
            record = json.loads(line.strip())
        except json.JSONDecodeError:
            continue

        if 'JsonScheduleV1' not in record:
            continue

        sched = record['JsonScheduleV1']
        uid = sched.get('CIF_train_uid', '')
        stp = sched.get('CIF_stp_indicator', 'P')
        days_run = sched.get('schedule_days_runs', '')
        toc = sched.get('atoc_code', '')
        locations = sched.get('schedule_segment', {}).get('schedule_location', [])

        if not uid or not locations:
            continue

        if not is_tuesday(days_run):
            continue

        schedules_by_uid[uid].append({
            'uid': uid,
            'stp': stp,
            'toc': toc,
            'locations': locations,
        })

    f.close()

    # Apply STP overlay logic: for each UID, keep highest priority
    trains = []
    for uid, versions in schedules_by_uid.items():
        # Sort by STP priority descending
        versions.sort(key=lambda v: STP_PRIORITY.get(v['stp'], 0), reverse=True)
        best = versions[0]

        # Skip cancelled services
        if best['stp'] == 'C':
            continue

        # Extract path
        path = []
        for loc in best['locations']:
            tiploc = loc.get('tiploc_code', '').strip()
            crs = tiploc_to_crs.get(tiploc)
            if not crs or crs not in stations:
                continue

            # Use working times (departure > arrival > pass)
            time = (parse_time(loc.get('departure')) or
                    parse_time(loc.get('arrival')) or
                    parse_time(loc.get('pass')))
            if time is None:
                continue

            stn = stations[crs]
            path.append([round(stn['lng'], 5), round(stn['lat'], 5), time])

        if len(path) < 2:
            continue

        # Ensure path is time-sorted
        path.sort(key=lambda p: p[2])

        origin = stations.get(tiploc_to_crs.get(
            best['locations'][0].get('tiploc_code', '').strip(), ''), {})
        dest = stations.get(tiploc_to_crs.get(
            best['locations'][-1].get('tiploc_code', '').strip(), ''), {})

        trains.append({
            'id': uid,
            'op': best['toc'],
            'from': origin.get('name', '?'),
            'to': dest.get('name', '?'),
            'path': path,
        })

    print(f"Extracted {len(trains)} valid train services")
    return trains


def main():
    parser = argparse.ArgumentParser(description='Process Network Rail timetable for Pulse')
    parser.add_argument('--schedule', required=True, help='Path to SCHEDULE JSON(.gz) feed')
    parser.add_argument('--corpus', required=True, help='Path to CORPUS reference JSON')
    parser.add_argument('--stations', required=True, help='Path to station locations CSV')
    parser.add_argument('--output', default=None, help='Output path (default: data/trains.json)')
    args = parser.parse_args()

    tiploc_to_crs = load_corpus(args.corpus)
    stations = load_stations(args.stations)
    trains = process_schedule(args.schedule, tiploc_to_crs, stations)

    # Known UK passenger operators with brand colours
    KNOWN_OPERATORS = {
        'NT': {'name': 'Northern Trains', 'color': '#262262'},
        'SE': {'name': 'Southeastern', 'color': '#009ddc'},
        'SR': {'name': 'ScotRail', 'color': '#1a5ba5'},
        'SW': {'name': 'South Western Railway', 'color': '#e11837'},
        'GW': {'name': 'Great Western Railway', 'color': '#0a493e'},
        'SN': {'name': 'Southern', 'color': '#8cc63e'},
        'LO': {'name': 'London Overground', 'color': '#ef7b10'},
        'AW': {'name': 'Transport for Wales', 'color': '#e4131b'},
        'LE': {'name': 'Greater Anglia', 'color': '#d70428'},
        'LM': {'name': 'West Midlands Trains', 'color': '#ff8300'},
        'TL': {'name': 'Thameslink', 'color': '#e83673'},
        'ME': {'name': 'Merseyrail', 'color': '#ffd500'},
        'XR': {'name': 'Elizabeth Line', 'color': '#9364cc'},
        'TP': {'name': 'TransPennine Express', 'color': '#00a4e4'},
        'EM': {'name': 'East Midlands Railway', 'color': '#6b2c91'},
        'VT': {'name': 'Avanti West Coast', 'color': '#e4131b'},
        'CC': {'name': 'c2c', 'color': '#b71c8e'},
        'GN': {'name': 'Great Northern', 'color': '#e83673'},
        'CH': {'name': 'Chiltern Railways', 'color': '#00bfff'},
        'XC': {'name': 'CrossCountry', 'color': '#660f21'},
        'GR': {'name': 'LNER', 'color': '#ce0e2d'},
        'HX': {'name': 'Heathrow Express', 'color': '#532e63'},
        'GX': {'name': 'Gatwick Express', 'color': '#e11837'},
        'CS': {'name': 'Caledonian Sleeper', 'color': '#1e3264'},
        'GC': {'name': 'Grand Central', 'color': '#2d2926'},
        'IL': {'name': 'Island Line', 'color': '#1fa14a'},
        'TW': {'name': 'Tyne & Wear Metro', 'color': '#ffd500'},
        'LT': {'name': 'London Tramlink', 'color': '#6cc24a'},
    }

    # Filter to known passenger operators only
    trains = [t for t in trains if t['op'] in KNOWN_OPERATORS]
    print(f"After filtering to passenger operators: {len(trains)}")

    # Reduce coordinate precision and path verbosity for smaller JSON
    for t in trains:
        t['path'] = [[round(p[0], 4), round(p[1], 4), p[2]] for p in t['path']]

    # Collect unique operators
    operators = {}
    for t in trains:
        op = t['op']
        if op not in operators:
            info = KNOWN_OPERATORS.get(op, {'name': op, 'color': '#ffb830'})
            operators[op] = info

    data = {
        'meta': {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_trains': len(trains),
            'source': 'Network Rail SCHEDULE',
        },
        'operators': operators,
        'trains': trains,
    }

    out_path = args.output or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'trains.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, 'w') as f:
        json.dump(data, f, separators=(',', ':'))

    size_kb = os.path.getsize(out_path) / 1024
    print(f"\nOutput: {out_path} ({size_kb:.0f} KB)")
    print(f"Total trains: {len(trains)}")


if __name__ == '__main__':
    main()
