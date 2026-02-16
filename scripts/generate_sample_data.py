#!/usr/bin/env python3
"""
Generate sample UK train data for Pulse visualisation.
Creates realistic-looking train movements across the UK rail network.
"""

import json
import math
import random
import os

random.seed(42)

# ── Station Coordinates (CRS: name, lat, lng) ──────────────────

STATIONS = {
    # London terminals
    'PAD': ('London Paddington',     51.5154, -0.1755),
    'KGX': ('London King\'s Cross',  51.5320, -0.1240),
    'EUS': ('London Euston',         51.5282, -0.1337),
    'WAT': ('London Waterloo',       51.5032, -0.1134),
    'VIC': ('London Victoria',       51.4952, -0.1441),
    'LST': ('London Liverpool St',   51.5178, -0.0825),
    'STP': ('London St Pancras',     51.5322, -0.1259),
    'LBG': ('London Bridge',         51.5052, -0.0864),
    'CHX': ('London Charing Cross',  51.5082, -0.1244),
    'MOG': ('London Moorgate',       51.5186, -0.0886),
    'FST': ('London Fenchurch St',   51.5114, -0.0795),

    # Major cities
    'BHM': ('Birmingham New St',     52.4778, -1.9000),
    'MAN': ('Manchester Piccadilly', 53.4774, -2.2309),
    'LDS': ('Leeds',                 53.7954, -1.5484),
    'LIV': ('Liverpool Lime St',     53.4076, -2.9774),
    'SHF': ('Sheffield',             53.3783, -1.4622),
    'BRI': ('Bristol Temple Meads',  51.4499, -2.5813),
    'NCL': ('Newcastle',             54.9688, -1.6170),
    'EDB': ('Edinburgh Waverley',    55.9522, -3.1891),
    'GLC': ('Glasgow Central',       55.8590, -4.2578),
    'CDF': ('Cardiff Central',       51.4750, -3.1787),
    'NRW': ('Norwich',               52.6270,  1.3073),

    # Intermediate stations
    'RDG': ('Reading',               51.4589, -0.9717),
    'OXF': ('Oxford',                51.7533, -1.2698),
    'SWI': ('Swindon',               51.5654, -1.7854),
    'BTH': ('Bath Spa',              51.3776, -2.3571),
    'EXD': ('Exeter St Davids',      50.7236, -3.5275),
    'PLY': ('Plymouth',              50.3717, -4.1427),
    'PNZ': ('Penzance',              50.1223, -5.5321),
    'CBG': ('Cambridge',             52.1943,  0.1372),
    'PBO': ('Peterborough',          52.5749, -0.2503),
    'DON': ('Doncaster',             53.5225, -1.1391),
    'YRK': ('York',                  53.9577, -1.0929),
    'DLM': ('Darlington',            54.5204, -1.5477),
    'MKC': ('Milton Keynes Central', 52.0344, -0.7747),
    'COV': ('Coventry',              52.4000, -1.5136),
    'WVH': ('Wolverhampton',         52.5862, -2.1180),
    'CRE': ('Crewe',                 53.0887, -2.4316),
    'PRE': ('Preston',               53.7561, -2.7082),
    'LAN': ('Lancaster',             54.0489, -2.8075),
    'CAR': ('Carlisle',              54.8906, -2.9328),
    'NOT': ('Nottingham',            52.9470, -1.1468),
    'LEI': ('Leicester',             52.6313, -1.1253),
    'DBY': ('Derby',                 52.9167, -1.4625),
    'STK': ('Stoke-on-Trent',        52.9998, -2.1842),
    'IPW': ('Ipswich',               52.0548,  1.1557),
    'CHM': ('Chelmsford',            51.7363,  0.4692),
    'CLJ': ('Clapham Junction',      51.4640, -0.1703),
    'SOU': ('Southampton Central',   50.9073, -1.4133),
    'BMH': ('Bournemouth',           50.7275, -1.8645),
    'WEY': ('Weymouth',              50.6144, -2.4548),
    'BTN': ('Brighton',              50.8296, -0.1410),
    'GTW': ('Gatwick Airport',       51.1564, -0.1611),
    'HAS': ('Hastings',              50.8586,  0.5873),
    'DVP': ('Dover Priory',          51.1241,  1.3048),
    'ASI': ('Ashford International', 51.1434,  0.8765),
    'CTB': ('Canterbury East',       51.2757,  1.0762),
    'SVS': ('Severn Tunnel Jn',      51.5860, -2.7728),
    'NWP': ('Newport',               51.5893, -2.9987),
    'SVG': ('Swansea',               51.6256, -3.9415),
    'ABD': ('Aberdeen',              57.1437, -2.0985),
    'INV': ('Inverness',             57.4809, -4.2234),
    'STG': ('Stirling',              56.1202, -3.9368),
    'PKS': ('Perth',                 56.3927, -3.4381),
    'DDE': ('Dundee',                56.4565, -2.9716),
    'HFD': ('Hereford',              52.0612, -2.7086),
    'SHR': ('Shrewsbury',            52.7121, -2.7485),
    'AHD': ('Abergavenny',           51.8224, -3.0136),
    'WRX': ('Wrexham General',       53.0458, -2.9952),
    'HUL': ('Hull',                  53.7438, -0.3483),
    'SCR': ('Scarborough',           54.2812, -0.4029),
    'HRG': ('Harrogate',             53.9933, -1.5373),
    'SKI': ('Skipton',               53.9587, -2.0236),
    'WGN': ('Wigan North Western',   53.5396, -2.6320),
    'WBQ': ('Warrington Bank Quay',  53.3880, -2.6026),
    'CHE': ('Chester',               53.1964, -2.8787),
    'BNG': ('Bangor',                53.2225, -4.1334),
    'HOL': ('Holyhead',              53.3069, -4.6319),
    'GRY': ('Grimsby Town',          53.5657, -0.0916),
    'LCN': ('Lincoln',               53.2263, -0.5387),
    'CTR': ('Chester-le-Street',     54.8588, -1.5742),

    # London commuter belt
    'WOK': ('Woking',                51.3189, -0.5573),
    'GFD': ('Guildford',             51.2372, -0.5957),
    'BSK': ('Basingstoke',           51.2677, -1.0863),
    'STA': ('Stafford',              52.8042, -2.1200),
    'TWI': ('Twickenham',            51.4501, -0.3306),
    'RMF': ('Romford',               51.5752,  0.1832),
    'SVK': ('Seven Kings',           51.5641,  0.0975),
    'ILF': ('Ilford',                51.5595,  0.0702),
    'STF': ('Stratford',             51.5416, -0.0036),
    'LER': ('Lewisham',              51.4660, -0.0138),
    'WMW': ('West Ham',              51.5285,  0.0053),
}

# ── Operators (TOC codes and colours) ────────────────────────

OPERATORS = {
    'GR': {'name': 'LNER',                     'color': '#ce0e2d'},
    'VT': {'name': 'Avanti West Coast',        'color': '#ff4713'},
    'GW': {'name': 'Great Western Railway',    'color': '#0a493e'},
    'EM': {'name': 'East Midlands Railway',    'color': '#6b2c91'},
    'SW': {'name': 'South Western Railway',    'color': '#0079c1'},
    'LE': {'name': 'Greater Anglia',           'color': '#d70428'},
    'SE': {'name': 'Southeastern',             'color': '#00afe8'},
    'SN': {'name': 'Southern',                 'color': '#8cc63e'},
    'XC': {'name': 'CrossCountry',             'color': '#660f21'},
    'TP': {'name': 'TransPennine Express',     'color': '#0b1560'},
    'SR': {'name': 'ScotRail',                 'color': '#1a3f7d'},
    'NT': {'name': 'Northern Trains',          'color': '#521980'},
    'TL': {'name': 'Thameslink',               'color': '#e7457b'},
    'AW': {'name': 'Transport for Wales',      'color': '#ff4713'},
    'CH': {'name': 'Chiltern Railways',        'color': '#00bfff'},
    'CC': {'name': 'c2c',                      'color': '#b7007c'},
    'LO': {'name': 'London Overground',        'color': '#ee7c0e'},
    'EL': {'name': 'Elizabeth Line',           'color': '#6950a1'},
    'GN': {'name': 'Great Northern',           'color': '#481481'},
    'HT': {'name': 'Hull Trains',              'color': '#de005c'},
    'GC': {'name': 'Grand Central',            'color': '#1d1d1b'},
    'CS': {'name': 'Caledonian Sleeper',       'color': '#1d3557'},
}

# ── Route Definitions ────────────────────────────────────────
# Each route: (stations, operator, avg_speed_mph, services_per_day, bidirectional)

ROUTES = [
    # ── East Coast Main Line ──
    (['KGX', 'PBO', 'DON', 'YRK', 'DLM', 'NCL', 'EDB'], 'GR', 100, 34, True),
    (['KGX', 'PBO', 'DON', 'YRK'], 'GR', 100, 20, True),
    (['KGX', 'PBO', 'DON', 'YRK', 'DLM', 'NCL', 'EDB', 'ABD'], 'GR', 90, 10, True),

    # ── West Coast Main Line ──
    (['EUS', 'MKC', 'COV', 'BHM'], 'VT', 100, 48, True),
    (['EUS', 'MKC', 'CRE', 'MAN'], 'VT', 100, 36, True),
    (['EUS', 'MKC', 'CRE', 'PRE', 'LAN', 'CAR', 'GLC'], 'VT', 95, 18, True),
    (['EUS', 'MKC', 'CRE', 'LIV'], 'VT', 95, 18, True),

    # ── Great Western ──
    (['PAD', 'RDG', 'SWI', 'BTH', 'BRI'], 'GW', 90, 36, True),
    (['PAD', 'RDG', 'SWI', 'BTH', 'BRI', 'NWP', 'CDF'], 'GW', 85, 24, True),
    (['PAD', 'RDG', 'SWI', 'BTH', 'BRI', 'NWP', 'CDF', 'SVG'], 'GW', 80, 12, True),
    (['PAD', 'RDG', 'EXD', 'PLY', 'PNZ'], 'GW', 75, 12, True),
    (['PAD', 'RDG', 'EXD', 'PLY'], 'GW', 80, 16, True),
    (['PAD', 'RDG', 'OXF'], 'GW', 80, 36, True),
    (['PAD', 'RDG'], 'GW', 85, 40, True),

    # ── East Midlands ──
    (['STP', 'LEI', 'NOT'], 'EM', 85, 30, True),
    (['STP', 'LEI', 'DBY', 'SHF'], 'EM', 80, 20, True),

    # ── South Western ──
    (['WAT', 'WOK', 'BSK', 'SOU'], 'SW', 70, 48, True),
    (['WAT', 'WOK', 'BSK', 'SOU', 'BMH'], 'SW', 65, 24, True),
    (['WAT', 'WOK', 'BSK', 'SOU', 'BMH', 'WEY'], 'SW', 60, 10, True),
    (['WAT', 'WOK', 'GFD'], 'SW', 55, 36, True),
    (['WAT', 'WOK'], 'SW', 50, 40, True),

    # ── Greater Anglia ──
    (['LST', 'CHM', 'IPW', 'NRW'], 'LE', 75, 24, True),
    (['LST', 'CHM', 'IPW'], 'LE', 70, 24, True),
    (['LST', 'CBG'], 'LE', 65, 36, True),

    # ── Southeastern ──
    (['VIC', 'ASI', 'DVP'], 'SE', 60, 24, True),
    (['STP', 'ASI'], 'SE', 100, 18, True),
    (['CHX', 'LER', 'HAS'], 'SE', 50, 18, True),
    (['VIC', 'CTB', 'DVP'], 'SE', 55, 16, True),

    # ── Southern ──
    (['VIC', 'GTW', 'BTN'], 'SN', 55, 42, True),
    (['LBG', 'GTW', 'BTN'], 'SN', 55, 24, True),
    (['LBG', 'GTW'], 'SN', 50, 30, True),

    # ── CrossCountry ──
    (['BRI', 'BHM', 'DBY', 'SHF', 'LDS', 'YRK', 'NCL', 'EDB'], 'XC', 80, 14, True),
    (['BRI', 'BHM', 'DBY', 'SHF', 'LDS'], 'XC', 75, 12, True),
    (['BHM', 'DBY', 'SHF', 'LDS', 'YRK'], 'XC', 80, 12, True),
    (['CDF', 'BRI', 'BHM', 'MAN'], 'XC', 70, 10, True),

    # ── TransPennine ──
    (['MAN', 'LDS', 'YRK', 'NCL'], 'TP', 70, 20, True),
    (['MAN', 'LDS', 'HUL'], 'TP', 60, 12, True),
    (['MAN', 'LDS', 'YRK', 'SCR'], 'TP', 55, 8, True),

    # ── ScotRail ──
    (['EDB', 'STG', 'PKS', 'DDE', 'ABD'], 'SR', 70, 20, True),
    (['EDB', 'STG', 'PKS', 'DDE', 'ABD', 'INV'], 'SR', 60, 6, True),
    (['GLC', 'STG', 'PKS', 'DDE'], 'SR', 65, 16, True),
    (['EDB', 'GLC'], 'SR', 70, 42, True),
    (['GLC', 'STG'], 'SR', 55, 30, True),

    # ── Northern ──
    (['MAN', 'LDS'], 'NT', 55, 40, True),
    (['MAN', 'SHF'], 'NT', 50, 30, True),
    (['LDS', 'YRK'], 'NT', 50, 30, True),
    (['LDS', 'HRG', 'SKI'], 'NT', 40, 18, True),
    (['MAN', 'WGN', 'PRE'], 'NT', 45, 24, True),
    (['LIV', 'WBQ', 'MAN'], 'NT', 50, 26, True),
    (['LDS', 'HUL'], 'NT', 45, 20, True),
    (['SHF', 'DON', 'HUL'], 'NT', 40, 12, True),
    (['MAN', 'WGN', 'LIV'], 'NT', 50, 20, True),
    (['LDS', 'DON', 'LCN'], 'NT', 40, 10, True),

    # ── Thameslink ──
    (['LBG', 'GTW', 'BTN'], 'TL', 50, 30, True),
    (['STP', 'LBG', 'GTW'], 'TL', 45, 24, True),
    (['STP', 'CBG'], 'TL', 55, 28, True),

    # ── Transport for Wales ──
    (['CDF', 'NWP', 'BRI'], 'AW', 50, 20, True),
    (['CDF', 'SVG'], 'AW', 50, 22, True),
    (['CDF', 'NWP', 'AHD', 'HFD', 'SHR'], 'AW', 45, 12, True),
    (['SHR', 'WRX', 'CHE'], 'AW', 40, 12, True),
    (['CHE', 'BNG', 'HOL'], 'AW', 40, 10, True),

    # ── Chiltern ──
    (['MOG', 'BHM'], 'CH', 65, 28, True),

    # ── c2c ──
    (['FST', 'RMF'], 'CC', 40, 36, True),

    # ── Great Northern ──
    (['KGX', 'PBO', 'CBG'], 'GN', 65, 30, True),
    (['KGX', 'PBO'], 'GN', 70, 36, True),

    # ── Elizabeth Line ──
    (['PAD', 'STF', 'LST'], 'EL', 35, 72, True),

    # ── London Overground ──
    (['LST', 'STF'], 'LO', 30, 60, True),

    # ── Hull Trains ──
    (['KGX', 'DON', 'HUL'], 'HT', 85, 8, True),

    # ── Grand Central ──
    (['KGX', 'DON', 'YRK'], 'GC', 85, 8, True),

    # ── Caledonian Sleeper ──
    (['EUS', 'CRE', 'PRE', 'CAR', 'GLC'], 'CS', 60, 1, True),
    (['EUS', 'CRE', 'PRE', 'CAR', 'EDB', 'STG', 'PKS', 'INV'], 'CS', 55, 1, True),
]


def haversine_miles(lat1, lng1, lat2, lng2):
    """Calculate distance in miles between two points."""
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def generate_departure_times(n_services, operator):
    """Generate realistic departure times throughout the day."""
    times = []

    # Sleeper services depart late evening
    if operator == 'CS':
        return [21 * 3600 + random.randint(0, 3600)]

    # Define time windows with relative weights
    windows = [
        (4*3600,   5.5*3600,  0.02),   # Very early
        (5.5*3600, 6.5*3600,  0.06),   # Early morning
        (6.5*3600, 9.5*3600,  0.25),   # Morning rush
        (9.5*3600, 12*3600,   0.15),   # Late morning
        (12*3600,  14*3600,   0.12),   # Midday
        (14*3600,  16.5*3600, 0.12),   # Afternoon
        (16.5*3600,19.5*3600, 0.20),   # Evening rush
        (19.5*3600,21*3600,   0.06),   # Evening
        (21*3600,  23*3600,   0.02),   # Late
    ]

    for _ in range(n_services):
        # Weighted random window selection
        r = random.random()
        cumulative = 0
        for start, end, weight in windows:
            cumulative += weight
            if r <= cumulative:
                t = random.randint(int(start), int(end))
                # Round to nearest 5 minutes for realism
                t = round(t / 300) * 300
                times.append(t)
                break
        else:
            times.append(random.randint(6*3600, 22*3600))

    times.sort()
    return times


def add_intermediate_points(path, n_intermediate=2):
    """Add intermediate points between stations for smoother animation."""
    if len(path) < 2:
        return path

    smooth_path = [path[0]]
    for i in range(len(path) - 1):
        lng0, lat0, t0 = path[i]
        lng1, lat1, t1 = path[i + 1]

        for j in range(1, n_intermediate + 1):
            f = j / (n_intermediate + 1)
            # Add slight random curve for visual interest
            offset = random.gauss(0, 0.02) * math.sin(f * math.pi)
            smooth_path.append([
                round(lng0 + (lng1 - lng0) * f + offset, 5),
                round(lat0 + (lat1 - lat0) * f + offset * 0.5, 5),
                round(t0 + (t1 - t0) * f),
            ])

        smooth_path.append(path[i + 1])

    return smooth_path


def generate_trains():
    """Generate all train services."""
    all_trains = []
    train_counter = {}

    for route_stations, operator, avg_speed, n_services, bidirectional in ROUTES:
        directions = [route_stations]
        if bidirectional:
            directions.append(list(reversed(route_stations)))

        for direction in directions:
            actual_services = max(1, n_services // (2 if bidirectional else 1))
            dep_times = generate_departure_times(actual_services, operator)

            for dep_time in dep_times:
                # Generate train ID
                train_counter[operator] = train_counter.get(operator, 0) + 1
                train_id = f"{operator}{train_counter[operator]:04d}"

                # Build path with times
                path = []
                current_time = dep_time

                for i, station_code in enumerate(direction):
                    stn = STATIONS[station_code]
                    lat, lng = stn[1], stn[2]

                    if i == 0:
                        # Departure station
                        path.append([round(lng, 5), round(lat, 5), current_time])
                    else:
                        # Calculate travel time based on distance
                        prev_stn = STATIONS[direction[i-1]]
                        dist = haversine_miles(prev_stn[1], prev_stn[2], lat, lng)
                        # Adjust speed with some randomness
                        speed = avg_speed * random.uniform(0.85, 1.1)
                        travel_time = (dist / speed) * 3600  # seconds

                        # Add dwell time at intermediate stations (30s-120s)
                        dwell = random.randint(30, 120) if i < len(direction) - 1 else 0

                        current_time += int(travel_time)
                        path.append([round(lng, 5), round(lat, 5), current_time])
                        current_time += dwell

                # Add intermediate points for smooth animation
                path = add_intermediate_points(path)

                origin_name = STATIONS[direction[0]][0]
                dest_name = STATIONS[direction[-1]][0]

                all_trains.append({
                    'id': train_id,
                    'op': operator,
                    'from': origin_name,
                    'to': dest_name,
                    'path': path,
                })

    return all_trains


def main():
    trains = generate_trains()

    # Shuffle to avoid rendering artifacts from sorted data
    random.shuffle(trains)

    data = {
        'meta': {
            'date': '2026-02-10',
            'total_trains': len(trains),
            'source': 'sample',
            'note': 'Generated sample data for development. Replace with real Network Rail data.',
        },
        'operators': OPERATORS,
        'trains': trains,
    }

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'trains.json')

    with open(out_path, 'w') as f:
        json.dump(data, f, separators=(',', ':'))

    # Also write a pretty version for inspection
    with open(out_path.replace('.json', '_pretty.json'), 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Generated {len(trains)} trains")
    print(f"Output: {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB)")

    # Print operator breakdown
    counts = {}
    for t in trains:
        counts[t['op']] = counts.get(t['op'], 0) + 1
    print("\nOperator breakdown:")
    for op, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {op:4s} {OPERATORS[op]['name']:30s} {count:4d}")


if __name__ == '__main__':
    main()
