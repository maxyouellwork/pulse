// ── Pulse — Main App ────────────────────────────────────────

import { loadTrainData, trainData, operators, interpolatePosition } from './data.js';
import {
  initUI, updateClock, updateScrubber, updateCounter,
  setPlayState, showTrainInfo, hideLoading,
} from './ui.js';

// ── Constants ───────────────────────────────────────────────
const DAY_START = 4 * 3600;        // 04:00
const DAY_END = 25.5 * 3600;       // 01:30 next day
const PLAYBACK_DURATION = 90;      // seconds for full day at 1x
const BASE_SPEED = (DAY_END - DAY_START) / PLAYBACK_DURATION;

const UK_CENTER = [-1.8, 53.5];
const UK_ZOOM = 5.1;

const DEFAULT_DOT_COLOR = [255, 184, 48, 210];
const TRAIL_OPACITY = 140;

// ── State ───────────────────────────────────────────────────
let simulationTime = DAY_START;
let playbackSpeed = 1;
let isPlaying = true;
let operatorFilter = null;
let selectedTrain = null;
let map = null;
let deckOverlay = null;
let frameCount = 0;
let positionData = [];
let mapReady = false;

// ── Initialization ──────────────────────────────────────────
async function init() {
  // 1. Load data
  await loadTrainData();

  positionData = trainData.map((train) => ({
    train,
    position: [0, 0],
    color: DEFAULT_DOT_COLOR,
    radius: 0,
  }));

  // 2. Initialize UI immediately (doesn't need map)
  initUI({
    onPlayPause: () => { isPlaying = !isPlaying; setPlayState(isPlaying); },
    onSpeedChange: (speed) => { playbackSpeed = speed; },
    onScrub: (time) => { simulationTime = time; },
    onOperatorFilter: (op) => { operatorFilter = op; },
    onTrainClose: () => { selectedTrain = null; },
  });

  // 3. Start animation loop immediately (updates clock + counter even without map)
  startAnimation();
  hideLoading();

  // 4. Initialize map (async, non-blocking)
  initMap();
}

async function initMap() {
  // Fetch CARTO style and strip bounds/center/zoom so it can't override ours
  let style;
  try {
    const res = await fetch('https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json');
    style = await res.json();
    delete style.center;
    delete style.zoom;
    delete style.bounds;
  } catch {
    style = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';
  }

  map = new maplibregl.Map({
    container: 'map',
    style,
    center: UK_CENTER,
    zoom: UK_ZOOM,
    minZoom: 3.5,
    maxZoom: 12,
    maxBounds: undefined,
    pitch: 0,
    attributionControl: false,
    fadeDuration: 0,
  });

  // Aggressively clear any maxBounds that sources/style might set
  const forceView = () => {
    if (map.getMaxBounds()) {
      map.setMaxBounds(null);
      map.setMinZoom(3.5);
      map.setCenter(UK_CENTER);
      map.setZoom(UK_ZOOM);
    }
  };
  map.on('sourcedata', forceView);
  map.on('styledata', forceView);

  map.once('load', () => {
    forceView();
    // Stop listening after initial load settles
    setTimeout(() => {
      map.off('sourcedata', forceView);
      map.off('styledata', forceView);
    }, 2000);
    setupDeck();
  });

  // Fallback: if 'load' doesn't fire in 10s, try anyway
  setTimeout(() => {
    if (!mapReady) {
      forceView();
      setupDeck();
    }
  }, 10000);
}

function setupDeck() {
  if (mapReady) return; // already done
  mapReady = true;

  try {
    deckOverlay = new deck.MapboxOverlay({
      interleaved: false,
      layers: [],
      getTooltip: ({ object }) => {
        if (!object?.train) return null;
        const t = object.train;
        const opInfo = operators[t.op];
        return {
          html: `<b>${opInfo?.name || t.op}</b><br>${t.from} \u2192 ${t.to}<br><span style="opacity:0.6">${t.id}</span>`,
          style: {
            background: 'rgba(10,10,15,0.92)',
            color: '#e0ddd5',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '6px',
            padding: '8px 12px',
            fontFamily: 'SF Mono, Consolas, monospace',
            fontSize: '12px',
            lineHeight: '1.5',
          },
        };
      },
      onClick: ({ object }) => {
        if (object?.train) {
          selectedTrain = object.train;
          showTrainInfo(selectedTrain, simulationTime, operators[selectedTrain.op]);
        }
      },
    });

    map.addControl(deckOverlay);
  } catch (e) {
    console.error('deck.gl setup failed:', e);
    mapReady = false;
  }
}

// ── Animation Loop ──────────────────────────────────────────
function startAnimation() {
  let lastTime = performance.now();

  function tick() {
    const now = performance.now();
    const delta = Math.min((now - lastTime) / 1000, 2.0);
    lastTime = now;

    if (isPlaying) {
      simulationTime += delta * playbackSpeed * BASE_SPEED;
      if (simulationTime >= DAY_END) simulationTime = DAY_START;
    }

    // Always update clock + counter
    frameCount++;
    updateClock(simulationTime);
    updateScrubber(simulationTime);

    // Count active trains
    let activeCount = 0;
    for (let i = 0; i < positionData.length; i++) {
      const train = positionData[i].train;
      if (simulationTime >= train._startTime && simulationTime <= train._endTime) {
        if (!operatorFilter || train.op === operatorFilter) {
          activeCount++;
        }
      }
    }
    if (frameCount % 5 === 0) updateCounter(activeCount);

    // Update deck.gl layers only if map is ready
    if (mapReady && deckOverlay) {
      try {
        updatePositions();
        updateLayers();
      } catch (e) {
        // Silently retry next frame
      }
    }

    // Update selected train info
    if (selectedTrain && frameCount % 15 === 0) {
      showTrainInfo(selectedTrain, simulationTime, operators[selectedTrain.op]);
    }
  }

  // setInterval is reliable even in background tabs (throttled to ~1s)
  setInterval(tick, 50);

  // Also use rAF for smooth 60fps when tab is focused
  function rafLoop() {
    tick();
    requestAnimationFrame(rafLoop);
  }
  requestAnimationFrame(rafLoop);
}

function updatePositions() {
  for (let i = 0; i < positionData.length; i++) {
    const item = positionData[i];
    const train = item.train;

    if (simulationTime < train._startTime || simulationTime > train._endTime) {
      item.radius = 0;
      continue;
    }
    if (operatorFilter && train.op !== operatorFilter) {
      item.radius = 0;
      continue;
    }

    const pos = interpolatePosition(train, simulationTime);
    if (pos) {
      item.position = [pos.lng, pos.lat];
      item.radius = 600;
      const opInfo = operators[train.op];
      if (opInfo) {
        const hex = opInfo.color;
        item.color = [
          parseInt(hex.slice(1, 3), 16),
          parseInt(hex.slice(3, 5), 16),
          parseInt(hex.slice(5, 7), 16),
          210,
        ];
      } else {
        item.color = DEFAULT_DOT_COLOR;
      }
    } else {
      item.radius = 0;
    }
  }
}

function updateLayers() {
  const visibleData = positionData.filter((d) => d.radius > 0);

  const trainLayer = new deck.ScatterplotLayer({
    id: 'trains',
    data: visibleData,
    getPosition: (d) => d.position,
    getRadius: (d) => d.radius,
    getFillColor: (d) => d.color,
    radiusMinPixels: 2.5,
    radiusMaxPixels: 7,
    opacity: 0.9,
    updateTriggers: {
      getPosition: frameCount,
      getRadius: frameCount,
      getFillColor: frameCount,
    },
    pickable: true,
    autoHighlight: true,
    highlightColor: [255, 255, 255, 80],
  });

  const glowLayer = new deck.ScatterplotLayer({
    id: 'glow',
    data: visibleData,
    getPosition: (d) => d.position,
    getRadius: (d) => d.radius * 2.5,
    getFillColor: (d) => [d.color[0], d.color[1], d.color[2], 40],
    radiusMinPixels: 5,
    radiusMaxPixels: 16,
    opacity: 0.6,
    updateTriggers: {
      getPosition: frameCount,
      getRadius: frameCount,
      getFillColor: frameCount,
    },
    pickable: false,
  });

  const trailLayer = new deck.TripsLayer({
    id: 'trails',
    data: operatorFilter
      ? trainData.filter((t) => t.op === operatorFilter)
      : trainData,
    getPath: (d) => d.path.map((p) => [p[0], p[1]]),
    getTimestamps: (d) => d.path.map((p) => p[2]),
    getColor: (d) => {
      const opInfo = operators[d.op];
      if (opInfo) {
        const hex = opInfo.color;
        return [
          parseInt(hex.slice(1, 3), 16),
          parseInt(hex.slice(3, 5), 16),
          parseInt(hex.slice(5, 7), 16),
          TRAIL_OPACITY,
        ];
      }
      return [255, 184, 48, TRAIL_OPACITY];
    },
    currentTime: simulationTime,
    trailLength: 600,
    widthMinPixels: 1.5,
    widthMaxPixels: 3,
    opacity: 0.7,
    jointRounded: true,
    capRounded: true,
    updateTriggers: { getColor: operatorFilter },
  });

  deckOverlay.setProps({
    layers: [trailLayer, glowLayer, trainLayer],
  });
}

// ── Start ───────────────────────────────────────────────────
init().catch((err) => {
  console.error('Pulse init failed:', err);
  const el = document.querySelector('.loading-text');
  if (el) el.textContent = 'Failed to load. Run from a local server.';
});
