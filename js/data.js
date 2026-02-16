// ── Data Loading & Interpolation Engine ─────────────────────

export let trainData = [];
export let operators = {};
export let meta = {};

export async function loadTrainData(url = 'data/trains.json') {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to load train data: ${res.status}`);
  const json = await res.json();

  meta = json.meta || {};
  operators = json.operators || {};
  trainData = json.trains || [];

  // Pre-sort each train's path by time (should already be sorted, but ensure)
  for (const train of trainData) {
    train._startTime = train.path[0][2];
    train._endTime = train.path[train.path.length - 1][2];
  }

  // Sort trains by start time for efficient active-window scanning
  trainData.sort((a, b) => a._startTime - b._startTime);

  return { meta, operators, trains: trainData };
}

/**
 * Interpolate a train's position at a given time.
 * Returns {lng, lat} or null if train is not active at this time.
 * path format: [[lng, lat, timeSeconds], ...]
 */
export function interpolatePosition(train, time) {
  if (time < train._startTime || time > train._endTime) return null;

  const path = train.path;
  const len = path.length;

  // Binary search for the segment containing `time`
  let lo = 0, hi = len - 1;
  while (lo < hi - 1) {
    const mid = (lo + hi) >> 1;
    if (path[mid][2] <= time) lo = mid;
    else hi = mid;
  }

  const t0 = path[lo][2];
  const t1 = path[hi][2];

  // At exact stop
  if (t1 === t0) return { lng: path[lo][0], lat: path[lo][1] };

  const f = (time - t0) / (t1 - t0);

  return {
    lng: path[lo][0] + (path[hi][0] - path[lo][0]) * f,
    lat: path[lo][1] + (path[hi][1] - path[lo][1]) * f,
  };
}

/**
 * Compute progress fraction (0..1) for a train at a given time.
 */
export function trainProgress(train, time) {
  if (time <= train._startTime) return 0;
  if (time >= train._endTime) return 1;
  return (time - train._startTime) / (train._endTime - train._startTime);
}

/**
 * Get the number of active trains at a given time.
 */
export function countActive(time) {
  let count = 0;
  for (const train of trainData) {
    if (time >= train._startTime && time <= train._endTime) count++;
  }
  return count;
}

/**
 * Get all active trains at a given time, optionally filtered by operator.
 * Returns array of {train, lng, lat}.
 */
export function getActivePositions(time, operatorFilter = null) {
  const results = [];
  for (const train of trainData) {
    if (time < train._startTime || time > train._endTime) continue;
    if (operatorFilter && train.op !== operatorFilter) continue;
    const pos = interpolatePosition(train, time);
    if (pos) {
      results.push({ train, lng: pos.lng, lat: pos.lat });
    }
  }
  return results;
}
