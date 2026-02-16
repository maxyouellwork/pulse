// ── UI Controls, Clock, Filters, Overlays ──────────────────

import { operators, trainData } from './data.js';

let onPlayPause = null;
let onSpeedChange = null;
let onScrub = null;
let onOperatorFilter = null;
let onTrainClose = null;

const $ = (sel) => document.querySelector(sel);

export function initUI(callbacks) {
  onPlayPause = callbacks.onPlayPause;
  onSpeedChange = callbacks.onSpeedChange;
  onScrub = callbacks.onScrub;
  onOperatorFilter = callbacks.onOperatorFilter;
  onTrainClose = callbacks.onTrainClose;

  // Play/Pause
  $('#play-btn').addEventListener('click', () => {
    onPlayPause?.();
  });

  // Speed buttons
  document.querySelectorAll('.speed-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.speed-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      onSpeedChange?.(Number(btn.dataset.speed));
    });
  });

  // Scrubber
  const scrubber = $('#scrubber');
  let scrubbing = false;

  scrubber.addEventListener('input', () => {
    scrubbing = true;
    onScrub?.(Number(scrubber.value), false);
  });
  scrubber.addEventListener('change', () => {
    onScrub?.(Number(scrubber.value), true);
    scrubbing = false;
  });
  scrubber.addEventListener('mousedown', () => { scrubbing = true; });
  scrubber.addEventListener('touchstart', () => { scrubbing = true; }, { passive: true });
  scrubber.addEventListener('mouseup', () => { scrubbing = false; });
  scrubber.addEventListener('touchend', () => { scrubbing = false; });

  // Store scrubbing state checker
  window._isScrubbing = () => scrubbing;

  // Operator panel toggle
  $('#operator-toggle').addEventListener('click', () => {
    $('#operator-list').classList.toggle('hidden');
  });

  // Close info panel
  $('#train-info-close').addEventListener('click', () => {
    $('#train-info').classList.add('hidden');
    onTrainClose?.();
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    switch (e.key) {
      case ' ':
        e.preventDefault();
        onPlayPause?.();
        break;
      case '1': onSpeedChange?.(1); setActiveSpeed(1); break;
      case '2': onSpeedChange?.(2); setActiveSpeed(2); break;
      case '3': onSpeedChange?.(5); setActiveSpeed(5); break;
      case '4': onSpeedChange?.(10); setActiveSpeed(10); break;
    }
  });

  buildOperatorList();
}

function setActiveSpeed(speed) {
  document.querySelectorAll('.speed-btn').forEach((btn) => {
    btn.classList.toggle('active', Number(btn.dataset.speed) === speed);
  });
}

function buildOperatorList() {
  const list = $('#operator-list');
  list.innerHTML = '';

  // "Show all" button
  const allBtn = document.createElement('button');
  allBtn.className = 'operator-item show-all active';
  allBtn.textContent = 'All operators';
  allBtn.addEventListener('click', () => {
    document.querySelectorAll('.operator-item').forEach((i) => i.classList.remove('active'));
    allBtn.classList.add('active');
    onOperatorFilter?.(null);
  });
  list.appendChild(allBtn);

  // Count trains per operator
  const counts = {};
  for (const t of trainData) {
    counts[t.op] = (counts[t.op] || 0) + 1;
  }

  // Sort operators by count descending
  const sorted = Object.entries(operators).sort((a, b) => (counts[b[0]] || 0) - (counts[a[0]] || 0));

  for (const [code, info] of sorted) {
    const btn = document.createElement('button');
    btn.className = 'operator-item';
    btn.innerHTML = `
      <span class="operator-dot" style="background:${info.color}"></span>
      <span>${info.name}</span>
      <span class="operator-count">${counts[code] || 0}</span>
    `;
    btn.addEventListener('click', () => {
      document.querySelectorAll('.operator-item').forEach((i) => i.classList.remove('active'));
      btn.classList.add('active');
      onOperatorFilter?.(code);
    });
    list.appendChild(btn);
  }
}

/**
 * Format seconds-since-midnight to HH:MM string.
 */
function formatTime(seconds) {
  const h = Math.floor(seconds / 3600) % 24;
  const m = Math.floor((seconds % 3600) / 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

export function updateClock(time) {
  $('#clock').textContent = formatTime(time);
}

export function updateScrubber(time) {
  if (window._isScrubbing?.()) return;
  $('#scrubber').value = time;
}

export function updateCounter(count) {
  const el = $('#active-count');
  el.textContent = count.toLocaleString();
}

export function setPlayState(playing) {
  const pauseIcon = $('.icon-pause');
  const playIcon = $('.icon-play');
  pauseIcon.style.display = playing ? '' : 'none';
  playIcon.style.display = playing ? 'none' : '';
}

export function showTrainInfo(train, time, operatorInfo) {
  const panel = $('#train-info');
  const content = $('#train-info-content');

  const progress = Math.min(1, Math.max(0,
    (time - train._startTime) / (train._endTime - train._startTime)
  ));

  const depTime = formatTime(train._startTime);
  const arrTime = formatTime(train._endTime);

  content.innerHTML = `
    <div class="info-operator" style="color:${operatorInfo?.color || '#ffb830'}">${operatorInfo?.name || train.op}</div>
    <div class="info-route">${train.from} &rarr; ${train.to}</div>
    <div class="info-id">${train.id} &middot; ${depTime} &ndash; ${arrTime}</div>
    <div class="info-progress"><div class="info-progress-bar" style="width:${(progress * 100).toFixed(1)}%"></div></div>
  `;
  panel.classList.remove('hidden');
}

export function hideTrainInfo() {
  $('#train-info').classList.add('hidden');
}

export function hideLoading() {
  const el = $('#loading');
  el.classList.add('fade-out');
  setTimeout(() => { el.style.display = 'none'; }, 700);
}
