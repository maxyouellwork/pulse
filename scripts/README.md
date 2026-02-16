# Pulse — Data Pipeline

## Sample Data (for development)

```bash
python3 scripts/generate_sample_data.py
```

Generates ~2,000 sample trains with realistic UK routes and timing patterns.
Output: `data/trains.json`

## Real Data (Network Rail)

### Prerequisites

1. Register (free) at https://publicdatafeeds.networkrail.co.uk
2. Download three files:
   - **SCHEDULE** feed (JSON, ~100MB gzipped) — all timetabled services
   - **CORPUS** reference data (JSON) — TIPLOC to CRS code mapping
   - **Station locations** CSV from [ellcom/UK-Train-Station-Locations](https://github.com/ellcom/UK-Train-Station-Locations)

### Processing

```bash
python3 scripts/process_timetable.py \
  --schedule /path/to/SCHEDULE.json.gz \
  --corpus /path/to/CORPUS.json \
  --stations /path/to/stations.csv
```

Output: `data/trains.json` (~5-8MB raw, ~1-2MB gzipped)

### Data format

```json
{
  "meta": { "date": "...", "total_trains": 20000, "source": "..." },
  "operators": {
    "GR": { "name": "LNER", "color": "#ce0e2d" }
  },
  "trains": [
    {
      "id": "GR0001",
      "op": "GR",
      "from": "London King's Cross",
      "to": "Edinburgh Waverley",
      "path": [[lng, lat, time_seconds], ...]
    }
  ]
}
```

- `path`: Array of `[longitude, latitude, seconds_since_midnight]` waypoints
- Times are in seconds from midnight (e.g. 06:00 = 21600)
- Trains are sorted by departure time after loading
