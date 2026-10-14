#!/usr/bin/env python3
"""
Space Explorer - An Interactive Galaxy Simulator
=================================================

How this project works (short version):

1. Python holds the whole web page (HTML + CSS + JavaScript) in one big string.
2. Python writes that string to a temporary .html file.
3. Python asks the default web browser to open that file.
4. The browser runs the animation using JavaScript and the HTML5 Canvas.

Only Python's standard library is used. No internet connection is needed.

Run it with:
    macOS:    python3 space_explorer.py
    Windows:  py space_explorer.py
"""

# ---------------------------------------------------------------------------
# SECTION 1: Python imports
# ---------------------------------------------------------------------------
import sys           # sys.exit() lets us end the program with a status code
import tempfile      # creates temporary files in a safe, system-chosen place
import webbrowser    # opens a web page in the user's default browser
from pathlib import Path  # modern, cross-platform way to work with file paths


# ---------------------------------------------------------------------------
# The web page.
#
# We use a RAW triple-quoted string (r""" ... """) and NOT an f-string.
#   - "raw" means backslashes are kept exactly as written.
#   - no "f" prefix means Python will NOT treat { } as placeholders, so the
#     CSS braces and JavaScript braces / template literals are completely safe.
# Rule for editing: never type three double quotes in a row inside the page.
# ---------------------------------------------------------------------------
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>Space Explorer - Interactive Galaxy Simulator</title>

<!-- ===================================================================
     SECTION 3: CSS variables and layout styles
     =================================================================== -->
<style>
  /* Theme colours live in CSS variables. JavaScript changes them when the
     user picks another theme, so every panel recolours at once. */
  :root {
    --bg0: #070914;
    --bg1: #0d1233;
    --accent: #7dd3fc;
    --accent2: #c084fc;
    --gold: #fbbf24;
    --pink: #f472b6;
    --text: #e8ecff;
    --muted: #a8b0d8;
    --panel: rgba(16, 20, 48, 0.74);
    --panel-border: rgba(160, 175, 255, 0.2);
    --focus: #fde68a;
  }

  * { box-sizing: border-box; }
  [hidden] { display: none !important; }

  html, body { margin: 0; min-height: 100%; }

  body {
    font-family: "Avenir Next", "Segoe UI Variable Text", "Segoe UI", system-ui,
                 -apple-system, sans-serif;
    color: var(--text);
    line-height: 1.5;
    background: radial-gradient(1300px 800px at 15% -10%, var(--bg1), var(--bg0));
    background-color: var(--bg0);
    background-attachment: fixed;
  }

  .skip-link {
    position: absolute; left: 12px; top: -60px; z-index: 10;
    background: var(--focus); color: #1a1405; padding: 8px 14px;
    border-radius: 999px; font-weight: 700; text-decoration: none;
  }
  .skip-link:focus { top: 12px; }

  /* Desktop layout: big canvas on the left, dashboard on the right. */
  .app {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 390px;
    grid-template-rows: auto minmax(0, 1fr);
    gap: 14px 18px;
    height: 100vh;
    padding: 16px 18px 18px;
  }

  .app-header { grid-column: 1 / -1; display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
  .app-header h1 { margin: 0; font-size: 1.7rem; letter-spacing: 0.01em; font-weight: 700; }
  .app-header p  { margin: 0; color: var(--muted); }

  /* The stage holds the canvas. user-select stops accidental text selection
     when the user clicks quickly on the canvas. */
  .stage {
    position: relative;
    overflow: hidden;
    min-height: 320px;
    border-radius: 30px;
    border: 1px solid var(--panel-border);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.55), inset 0 0 80px rgba(120, 140, 255, 0.07);
    -webkit-user-select: none; user-select: none;
    -webkit-tap-highlight-color: transparent;
  }

  /* touch-action: none stops the page scrolling or zooming while the user
     taps or drags on the canvas. */
  canvas {
    position: absolute; inset: 0;
    width: 100%; height: 100%;
    display: block;
    touch-action: none;
    cursor: crosshair;
  }

  /* pointer-events: none means this text can never block a canvas click. */
  .stage-hint {
    position: absolute; left: 18px; bottom: 14px; right: 18px; margin: 0;
    font-size: 0.85rem; color: var(--muted);
    pointer-events: none;
    text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9);
  }

  .error-banner {
    position: absolute; left: 14px; right: 14px; top: 14px;
    padding: 12px 16px; border-radius: 14px;
    background: rgba(127, 29, 29, 0.92); border: 1px solid #fca5a5; color: #fff;
  }

  .sidebar { display: flex; flex-direction: column; gap: 14px; overflow-y: auto; padding: 2px 4px 4px 2px; }

  .panel {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 22px;
    padding: 16px 18px;
    -webkit-backdrop-filter: blur(12px); backdrop-filter: blur(12px);
  }
  .panel h2 { margin: 0 0 12px; font-size: 1.05rem; font-weight: 650; }

  /* Statistics */
  .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 18px; margin: 0; }
  .stats dt { font-size: 0.8rem; color: var(--muted); }
  .stats dd { margin: 2px 0 0; font-size: 1.4rem; font-weight: 650; font-variant-numeric: tabular-nums; }
  .status-dot {
    display: inline-block; width: 10px; height: 10px; border-radius: 50%;
    margin-right: 8px; background: #4ade80; box-shadow: 0 0 10px #4ade80;
  }
  .status-dot.is-paused { background: var(--gold); box-shadow: 0 0 10px var(--gold); }

  /* Buttons */
  .btn-row { display: flex; flex-wrap: wrap; gap: 10px; }
  .btn {
    font: inherit; font-weight: 600; color: var(--text);
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid var(--panel-border);
    border-radius: 999px;
    padding: 10px 18px;
    cursor: pointer;
    transition: transform 0.12s ease, background 0.15s ease, box-shadow 0.15s ease;
  }
  .btn:hover { background: rgba(255, 255, 255, 0.15); box-shadow: 0 0 18px rgba(125, 211, 252, 0.2); }
  .btn:active { transform: translateY(1px) scale(0.96); background: rgba(255, 255, 255, 0.22); }
  .btn-primary { background: var(--accent); color: #06101f; border-color: transparent; }
  .btn-primary:hover { background: var(--accent); filter: brightness(1.1); }
  .btn:focus-visible, input[type="range"]:focus-visible, .skip-link:focus-visible {
    outline: 3px solid var(--focus); outline-offset: 3px;
  }

  .field { margin-top: 16px; }
  .field-label { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 0.92rem; }
  .field-label output { font-variant-numeric: tabular-nums; color: var(--accent); font-weight: 650; }
  input[type="range"] { width: 100%; accent-color: var(--accent); }

  .group-title { margin: 16px 0 8px; font-size: 0.92rem; }
  .theme-btn[aria-pressed="true"], .planet-btn[aria-pressed="true"] {
    border-color: var(--accent); background: rgba(125, 211, 252, 0.18); box-shadow: 0 0 0 1px var(--accent);
  }
  .planet-list { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
  .planet-btn { display: inline-flex; align-items: center; gap: 8px; padding: 7px 14px; font-size: 0.9rem; }
  .planet-dot { width: 12px; height: 12px; border-radius: 50%; flex: none; }

  .message { min-height: 1.4em; margin: 12px 0 0; font-size: 0.88rem; color: var(--gold); }

  .reset-note, .note, .shortcuts { margin: 10px 0 0; font-size: 0.82rem; color: var(--muted); }

  /* Information panel */
  .empty { padding: 14px; border-radius: 16px; border: 1px dashed var(--panel-border); color: var(--muted); }
  .empty strong { color: var(--text); }
  .info-name { margin: 0; font-size: 1.4rem; }
  .tag {
    display: inline-block; margin: 6px 0 10px; padding: 2px 12px; font-size: 0.8rem;
    border-radius: 999px; background: rgba(192, 132, 252, 0.2); color: #e9d5ff;
  }
  .info-desc { margin: 0 0 10px; }
  .info-facts { margin: 0; padding-left: 20px; }
  .info-facts li { margin-bottom: 6px; }

  /* Smaller screens: stack everything in one column. The page scrolls
     normally, but the canvas itself ignores touch scrolling. */
  @media (max-width: 880px) {
    .app { display: block; height: auto; padding: 12px; }
    .app-header { margin-bottom: 10px; }
    .app-header h1 { font-size: 1.45rem; }
    .stage { height: 62vh; min-height: 340px; margin-bottom: 14px; border-radius: 24px; }
    .sidebar { overflow: visible; }
    .sidebar > * + * { margin-top: 0; }
  }

  /* Respect people who ask their system for less motion. */
  @media (prefers-reduced-motion: reduce) {
    .btn { transition: none; }
  }
</style>
</head>

<!-- ===================================================================
     SECTION 2: HTML document structure
     =================================================================== -->
<body>
<a class="skip-link" href="#controls">Skip to controls</a>

<noscript>
  <p style="padding:16px;background:#7f1d1d;color:#fff;margin:0">
    Space Explorer needs JavaScript. Please enable JavaScript in your browser and reload this page.
  </p>
</noscript>

<div class="app">
  <header class="app-header">
    <h1>Space Explorer</h1>
    <p>An interactive galaxy simulator</p>
  </header>

  <main class="stage" id="stage">
    <canvas id="spaceCanvas" role="img"
            aria-label="Animated solar system with six planets orbiting a glowing sun. Keyboard users can pick planets from the planet list."></canvas>
    <p class="stage-hint">Click a planet to learn about it. Click empty space to send a meteor there.</p>
    <div id="errorBanner" class="error-banner" role="alert" hidden></div>
  </main>

  <aside class="sidebar" aria-label="Simulator dashboard">

    <section class="panel" aria-labelledby="statsTitle">
      <h2 id="statsTitle">Live statistics</h2>
      <dl class="stats">
        <div><dt>Planets</dt><dd id="statPlanets">0</dd></div>
        <div><dt>Status</dt><dd><span id="statusDot" class="status-dot" aria-hidden="true"></span><span id="statStatus">Running</span></dd></div>
        <div><dt>Speed</dt><dd id="statSpeed">1.0x</dd></div>
        <div><dt>Meteors launched</dt><dd id="statMeteors">0</dd></div>
      </dl>
    </section>

    <section class="panel" id="controls" aria-labelledby="controlsTitle">
      <h2 id="controlsTitle">Controls</h2>
      <div class="btn-row">
        <button type="button" class="btn btn-primary" id="meteorBtn">Launch Meteor</button>
        <button type="button" class="btn" id="pauseBtn">Pause</button>
        <button type="button" class="btn" id="resetBtn">Reset</button>
      </div>

      <div class="field">
        <label class="field-label" for="speedSlider">
          <span>Animation speed</span><output id="speedOutput" for="speedSlider">1.0x</output>
        </label>
        <input type="range" id="speedSlider" min="0.1" max="4" step="0.1" value="1">
      </div>

      <p class="group-title" id="themeLabel">Theme</p>
      <div class="btn-row" role="group" aria-labelledby="themeLabel" id="themeButtons"></div>

      <p class="message" id="message" role="status" aria-live="polite"></p>
      <p class="reset-note">Reset sets speed to default, resumes motion, clears meteors and the counter, clears the selected planet, and returns to the Deep Space theme.</p>
      <p class="shortcuts">Keyboard: Space pause or resume, M launch meteor, R reset, 1 to 6 pick a planet, Esc clear selection.</p>
    </section>

    <section class="panel" aria-labelledby="infoTitle">
      <h2 id="infoTitle">Planet information</h2>
      <div class="planet-list" id="planetList" role="group" aria-label="Choose a planet"></div>
      <div aria-live="polite">
        <div class="empty" id="infoEmpty">
          <strong>No planet selected.</strong> Click a planet in the simulation, or choose one from the list above, to see its description and facts.
        </div>
        <article id="infoCard" hidden>
          <h3 class="info-name" id="infoName"></h3>
          <p class="tag" id="infoType"></p>
          <p class="info-desc" id="infoDesc"></p>
          <ul class="info-facts" id="infoFacts"></ul>
        </article>
      </div>
      <p class="note">All facts shown are real and simplified for learning. Sizes and distances in the simulation are not to scale.</p>
    </section>

  </aside>
</div>

<!-- ===================================================================
     JavaScript. Wrapped in an IIFE (a function that runs immediately) so
     our variables stay private and do not become global variables.
     =================================================================== -->
<script>
(function () {
  'use strict'; // Makes JavaScript stricter, so common mistakes become errors.

  // =================================================================
  // SECTION 4 (part 1): Constants and shared application state
  // =================================================================
  var TAU = Math.PI * 2;            // A full circle in radians (2 * pi).
  var ORBIT_TILT = 0.48;            // Orbit height / width. < 1 gives a 3D look.
  var MAX_METEORS = 30;             // Safety limit for meteors in flight.
  var STAR_POOL = 420;              // How many stars are created in total.
  var DEFAULT_THEME = 'deep';

  var prefersReducedMotion = !!(window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var DEFAULT_SPEED = prefersReducedMotion ? 0.5 : 1;

  // All values that change while the app runs live in ONE object.
  // The drawing code reads this object; it never reads the DOM.
  var state = {
    width: 0, height: 0, dpr: 1,       // canvas size in CSS pixels, pixel ratio
    cx: 0, cy: 0,                      // centre of the solar system
    sunRadius: 30, planetScale: 1,
    simTime: 0,                        // seconds of "simulation time"
    speed: DEFAULT_SPEED,              // speed multiplier
    paused: false,
    meteorCount: 0,
    selectedId: null,
    themeId: DEFAULT_THEME,
    stars: [], planets: [], meteors: [], particles: [],
    lastFrameTime: 0,
    rafId: null                        // id of the ONE animation loop
  };

  // =================================================================
  // SECTION 5 (data): Themes. Each theme has canvas colours ("r,g,b"
  // strings) and CSS variable values for the dashboard.
  // =================================================================
  var THEMES = {
    deep: {
      name: 'Deep Space',
      bgTop: '#050712', bgBottom: '#0d1236',
      nebula: [
        { x: 0.2, y: 0.25, r: 0.55, color: '88,60,200', alpha: 0.28 },
        { x: 0.8, y: 0.7,  r: 0.5,  color: '30,120,220', alpha: 0.22 },
        { x: 0.55, y: 0.1, r: 0.35, color: '230,80,170', alpha: 0.12 }
      ],
      starTints: ['255,255,255', '190,220,255', '255,230,170'],
      sunInner: '255,250,215', sunMid: '255,196,70', sunOuter: '255,120,30',
      meteorHead: '255,255,255', meteorTail: '125,211,252',
      accentRgb: '125,211,252',
      vars: { '--bg0': '#070914', '--bg1': '#0d1233', '--accent': '#7dd3fc', '--accent2': '#c084fc' }
    },
    nebula: {
      name: 'Nebula',
      bgTop: '#14041f', bgBottom: '#34093f',
      nebula: [
        { x: 0.25, y: 0.3,  r: 0.55, color: '236,72,153', alpha: 0.28 },
        { x: 0.75, y: 0.65, r: 0.5,  color: '147,51,234', alpha: 0.3 },
        { x: 0.5, y: 0.95,  r: 0.4,  color: '251,146,60', alpha: 0.14 }
      ],
      starTints: ['255,255,255', '255,200,230', '255,225,170'],
      sunInner: '255,245,225', sunMid: '255,170,90', sunOuter: '244,80,120',
      meteorHead: '255,255,255', meteorTail: '244,114,182',
      accentRgb: '244,114,182',
      vars: { '--bg0': '#12041f', '--bg1': '#2a0a3d', '--accent': '#f472b6', '--accent2': '#fbbf24' }
    },
    aurora: {
      name: 'Aurora',
      bgTop: '#020e0f', bgBottom: '#06262a',
      nebula: [
        { x: 0.2, y: 0.75, r: 0.55, color: '20,184,166', alpha: 0.26 },
        { x: 0.8, y: 0.3,  r: 0.5,  color: '59,130,246', alpha: 0.24 },
        { x: 0.5, y: 0.5,  r: 0.35, color: '132,204,22', alpha: 0.08 }
      ],
      starTints: ['255,255,255', '190,255,240', '200,225,255'],
      sunInner: '255,252,220', sunMid: '253,224,71', sunOuter: '250,150,40',
      meteorHead: '255,255,255', meteorTail: '94,234,212',
      accentRgb: '94,234,212',
      vars: { '--bg0': '#02100f', '--bg1': '#06201f', '--accent': '#5eead4', '--accent2': '#60a5fa' }
    }
  };
  var theme = THEMES[DEFAULT_THEME]; // The theme currently in use.

  // =================================================================
  // SECTION 6: Planet data. Each planet is an object (key: value pairs).
  // speed = radians per second at 1x. startAngle = where it begins.
  // colors = [highlight, base, shadow] used for the sphere shading.
  // =================================================================
  var PLANET_DATA = [
    {
      id: 'mercury', name: 'Mercury', type: 'Rocky planet',
      size: 5.5, speed: 0.62, startAngle: 0.8, style: 'plain', ring: false,
      colors: ['#e5e7eb', '#a8a29e', '#3f3a36'], glow: '200,200,215',
      description: 'The smallest planet and the closest to the Sun. It has almost no atmosphere, so its temperatures swing wildly.',
      facts: [
        'One year on Mercury lasts about 88 Earth days.',
        'Daytime surface temperatures reach about 430 \u00B0C, while nights drop to about \u2212180 \u00B0C.',
        'Mercury has no moons.'
      ]
    },
    {
      id: 'venus', name: 'Venus', type: 'Rocky planet',
      size: 8.5, speed: 0.47, startAngle: 2.4, style: 'plain', ring: false,
      colors: ['#fff1c9', '#e9b872', '#6e4219'], glow: '250,200,120',
      description: 'About the same size as Earth, but wrapped in a thick atmosphere that traps heat like a blanket.',
      facts: [
        'Venus is the hottest planet, with a surface around 465 \u00B0C.',
        'It spins backward compared with most planets.',
        'A day on Venus (about 243 Earth days) is longer than its year (about 225 Earth days).'
      ]
    },
    {
      id: 'earth', name: 'Earth', type: 'Rocky planet',
      size: 9, speed: 0.38, startAngle: 4.1, style: 'earth', ring: false,
      colors: ['#c3e6ff', '#3b82f6', '#0a2560'], glow: '96,165,250',
      description: 'Our home. It is the only place we know of that supports life, and it has liquid water on its surface.',
      facts: [
        'About 71% of Earth\u2019s surface is covered by water.',
        'One year is about 365.25 days.',
        'Earth has one natural moon.'
      ]
    },
    {
      id: 'mars', name: 'Mars', type: 'Rocky planet',
      size: 7, speed: 0.30, startAngle: 5.5, style: 'plain', ring: false,
      colors: ['#fecaca', '#ef6a45', '#521a10'], glow: '248,113,113',
      description: 'A cold, dusty desert world. Its red colour comes from iron oxide (rust) in the soil.',
      facts: [
        'Olympus Mons, the tallest known volcano in the solar system, is about 22 km high.',
        'Mars has two small moons, Phobos and Deimos.',
        'A day on Mars lasts about 24 hours and 37 minutes.'
      ]
    },
    {
      id: 'jupiter', name: 'Jupiter', type: 'Gas giant',
      size: 17, speed: 0.17, startAngle: 1.3, style: 'bands', ring: false,
      colors: ['#fde7c4', '#d6a36a', '#53351b'], glow: '251,191,120',
      description: 'The largest planet. It is a huge ball of mostly hydrogen and helium with powerful storms.',
      facts: [
        'Jupiter is more than twice as massive as all the other planets combined.',
        'The Great Red Spot is a giant storm that people have observed for centuries.',
        'It has many dozens of known moons, including Ganymede, the largest moon in the solar system.'
      ]
    },
    {
      id: 'saturn', name: 'Saturn', type: 'Gas giant',
      size: 14, speed: 0.12, startAngle: 3.3, style: 'bands', ring: true,
      colors: ['#fff3c4', '#e6c27a', '#65501f'], glow: '250,220,140',
      description: 'Famous for its bright rings. It is a gas giant that is lighter than it looks.',
      facts: [
        'Saturn\u2019s average density is lower than the density of water.',
        'Its rings are made mostly of water ice, from tiny grains to boulders.',
        'It has well over 100 known moons, including Titan, which has a thick atmosphere.'
      ]
    }
  ];

  // =================================================================
  // Handles to HTML elements (looked up once, reused everywhere).
  // =================================================================
  var canvas = document.getElementById('spaceCanvas');
  var stage = document.getElementById('stage');
  var ui = {
    planets: document.getElementById('statPlanets'),
    status: document.getElementById('statStatus'),
    statusDot: document.getElementById('statusDot'),
    speed: document.getElementById('statSpeed'),
    meteors: document.getElementById('statMeteors'),
    meteorBtn: document.getElementById('meteorBtn'),
    pauseBtn: document.getElementById('pauseBtn'),
    resetBtn: document.getElementById('resetBtn'),
    slider: document.getElementById('speedSlider'),
    sliderOut: document.getElementById('speedOutput'),
    themeButtons: document.getElementById('themeButtons'),
    planetList: document.getElementById('planetList'),
    message: document.getElementById('message'),
    error: document.getElementById('errorBanner'),
    infoEmpty: document.getElementById('infoEmpty'),
    infoCard: document.getElementById('infoCard'),
    infoName: document.getElementById('infoName'),
    infoType: document.getElementById('infoType'),
    infoDesc: document.getElementById('infoDesc'),
    infoFacts: document.getElementById('infoFacts')
  };
  var ctx = null;        // The canvas "drawing context": our paintbrush.
  var messageTimer = null;

  // =================================================================
  // Small helper functions
  // =================================================================
  function rand(min, max) { return min + Math.random() * (max - min); }
  function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
  function rgba(rgb, alpha) { return 'rgba(' + rgb + ',' + alpha + ')'; }
  function fmtSpeed(value) { return value.toFixed(1) + 'x'; }

  function showError(text) {
    ui.error.textContent = text;
    ui.error.hidden = false;
  }

  // Shows a short note, then clears it after 3.5 seconds.
  function showMessage(text) {
    ui.message.textContent = text;
    window.clearTimeout(messageTimer);
    messageTimer = window.setTimeout(function () { ui.message.textContent = ''; }, 3500);
  }

  // =================================================================
  // SECTION 4 (part 2): Canvas initialisation and resizing (high-DPI)
  // =================================================================
  // A high-DPI ("retina") screen packs more physical pixels into each CSS
  // pixel. We make the canvas bitmap bigger (width * dpr) but keep its
  // displayed size the same, then scale the drawing so we can keep using
  // plain CSS-pixel coordinates everywhere.
  function resizeCanvas() {
    var rect = stage.getBoundingClientRect();
    var width = Math.max(1, Math.floor(rect.width));
    var height = Math.max(1, Math.floor(rect.height));
    state.dpr = Math.min(window.devicePixelRatio || 1, 2); // cap at 2 for speed
    state.width = width;
    state.height = height;
    canvas.width = Math.round(width * state.dpr);
    canvas.height = Math.round(height * state.dpr);
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);
    computeLayout();
    updatePlanetPositions();
  }

  // Works out sun size, orbit sizes and planet sizes from the canvas size,
  // so everything stays visible after the window is resized.
  function computeLayout() {
    var w = state.width, h = state.height;
    var minDim = Math.min(w, h);
    state.cx = w / 2;
    state.cy = h / 2;
    state.sunRadius = clamp(minDim * 0.065, 16, 44);
    state.planetScale = clamp(minDim / 720, 0.55, 1.15);

    var count = state.planets.length;
    var innerRx = state.sunRadius * 2.3;
    // The biggest orbit must fit inside the canvas both ways.
    var maxRx = Math.min(w * 0.43, (h * 0.45) / ORBIT_TILT);
    maxRx = Math.max(maxRx, innerRx + count * 8);
    var step = (maxRx - innerRx) / (count - 1);

    state.planets.forEach(function (planet, index) {
      planet.rx = innerRx + step * index;      // horizontal orbit radius
      planet.ry = planet.rx * ORBIT_TILT;      // vertical orbit radius
      planet.radius = planet.size * state.planetScale;
    });
  }

  // =================================================================
  // SECTION 5: Star generation and rendering
  // =================================================================
  // Stars store positions as fractions (0 to 1) of the canvas, so they
  // never need to be recreated when the window is resized.
  function createStars() {
    state.stars = [];
    for (var i = 0; i < STAR_POOL; i++) {
      var bright = Math.random() < 0.08;
      state.stars.push({
        nx: Math.random(), ny: Math.random(),
        size: bright ? rand(1.3, 2.2) : rand(0.3, 1.3),
        baseAlpha: rand(0.35, 1),
        twinkleSpeed: rand(0.8, 3),
        phase: rand(0, TAU),
        drift: rand(0.0004, 0.0016),
        tint: Math.floor(Math.random() * 3),
        bright: bright
      });
    }
  }

  function drawBackground() {
    var w = state.width, h = state.height;
    var sky = ctx.createLinearGradient(0, 0, 0, h);
    sky.addColorStop(0, theme.bgTop);
    sky.addColorStop(1, theme.bgBottom);
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, w, h);

    // Soft glowing clouds (nebulae) that drift very slowly.
    var drift = prefersReducedMotion ? 0 : state.simTime * 0.03;
    theme.nebula.forEach(function (cloud, i) {
      var nx = w * (cloud.x + Math.sin(drift + i * 2) * 0.04);
      var ny = h * (cloud.y + Math.cos(drift * 0.8 + i) * 0.04);
      var radius = Math.max(w, h) * cloud.r;
      var glow = ctx.createRadialGradient(nx, ny, 0, nx, ny, radius);
      glow.addColorStop(0, rgba(cloud.color, cloud.alpha));
      glow.addColorStop(1, rgba(cloud.color, 0));
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, w, h);
    });
  }

  function drawStars() {
    var w = state.width, h = state.height;
    // Smaller screens draw fewer stars so they are not crowded.
    var visible = Math.round(clamp((w * h) / 3600, 120, STAR_POOL));
    for (var i = 0; i < visible; i++) {
      var star = state.stars[i];
      // Slow sideways drift. The double modulo keeps the result between 0 and 1.
      var fx = (((star.nx - star.drift * state.simTime) % 1) + 1) % 1;
      var x = fx * w, y = star.ny * h;
      // Twinkle: brightness follows a sine wave that goes up and down.
      var twinkle = prefersReducedMotion ? 1 :
        0.65 + 0.35 * Math.sin(state.simTime * star.twinkleSpeed + star.phase);
      var alpha = star.baseAlpha * twinkle;
      var tint = theme.starTints[star.tint];
      if (star.bright) {
        ctx.fillStyle = rgba(tint, alpha * 0.16);
        ctx.beginPath(); ctx.arc(x, y, star.size * 4, 0, TAU); ctx.fill();
      }
      ctx.fillStyle = rgba(tint, alpha);
      ctx.beginPath(); ctx.arc(x, y, star.size, 0, TAU); ctx.fill();
    }
  }

  // =================================================================
  // SECTION 7: Orbital calculations, sun and planet drawing
  // =================================================================
  // Orbit maths: a point moving around an ellipse is
  //   x = centreX + cos(angle) * radiusX
  //   y = centreY + sin(angle) * radiusY
  // and the angle grows with time.
  function updatePlanetPositions() {
    state.planets.forEach(function (planet) {
      planet.angle = planet.startAngle + state.simTime * planet.speed;
      planet.x = state.cx + Math.cos(planet.angle) * planet.rx;
      planet.y = state.cy + Math.sin(planet.angle) * planet.ry;
    });
  }

  function drawOrbits() {
    state.planets.forEach(function (planet) {
      var selected = planet.id === state.selectedId;
      ctx.beginPath();
      ctx.ellipse(state.cx, state.cy, planet.rx, planet.ry, 0, 0, TAU);
      ctx.lineWidth = selected ? 1.6 : 1;
      ctx.strokeStyle = selected ? rgba(theme.accentRgb, 0.65) : 'rgba(255,255,255,0.11)';
      ctx.stroke();
    });
  }

  function drawSun() {
    var r = state.sunRadius;
    var pulse = prefersReducedMotion ? 1 : 1 + Math.sin(state.simTime * 1.4) * 0.03;

    var corona = ctx.createRadialGradient(state.cx, state.cy, r * 0.6, state.cx, state.cy, r * 3.6 * pulse);
    corona.addColorStop(0, rgba(theme.sunOuter, 0.55));
    corona.addColorStop(0.4, rgba(theme.sunOuter, 0.17));
    corona.addColorStop(1, rgba(theme.sunOuter, 0));
    ctx.fillStyle = corona;
    ctx.beginPath(); ctx.arc(state.cx, state.cy, r * 3.6 * pulse, 0, TAU); ctx.fill();

    var core = ctx.createRadialGradient(state.cx - r * 0.25, state.cy - r * 0.25, r * 0.1, state.cx, state.cy, r);
    core.addColorStop(0, rgba(theme.sunInner, 1));
    core.addColorStop(0.55, rgba(theme.sunMid, 1));
    core.addColorStop(1, rgba(theme.sunOuter, 1));
    ctx.fillStyle = core;
    ctx.beginPath(); ctx.arc(state.cx, state.cy, r, 0, TAU); ctx.fill();
  }

  // Saturn's ring is drawn in two halves: the back half before the planet
  // and the front half after it, so the planet appears to sit inside it.
  function drawRingHalf(planet, half) {
    var start = half === 'back' ? Math.PI : 0;
    var end = half === 'back' ? TAU : Math.PI;
    ctx.save();
    ctx.translate(planet.x, planet.y);
    ctx.rotate(-0.38);
    ctx.lineCap = 'butt';
    ctx.lineWidth = Math.max(1.5, planet.radius * 0.3);
    ctx.strokeStyle = 'rgba(233,213,170,0.6)';
    ctx.beginPath(); ctx.ellipse(0, 0, planet.radius * 2.1, planet.radius * 0.62, 0, start, end); ctx.stroke();
    ctx.lineWidth = Math.max(1, planet.radius * 0.14);
    ctx.strokeStyle = 'rgba(200,175,120,0.55)';
    ctx.beginPath(); ctx.ellipse(0, 0, planet.radius * 1.65, planet.radius * 0.49, 0, start, end); ctx.stroke();
    ctx.restore();
  }

  function drawPlanet(planet, now) {
    var x = planet.x, y = planet.y, r = planet.radius;
    var selected = planet.id === state.selectedId;

    // Soft glow around the planet.
    var glow = ctx.createRadialGradient(x, y, r * 0.8, x, y, r * 2.4);
    glow.addColorStop(0, rgba(planet.glow, 0.35));
    glow.addColorStop(1, rgba(planet.glow, 0));
    ctx.fillStyle = glow;
    ctx.beginPath(); ctx.arc(x, y, r * 2.4, 0, TAU); ctx.fill();

    if (planet.ring) { drawRingHalf(planet, 'back'); }

    // Sphere shading: the bright spot faces the sun.
    var dx = state.cx - x, dy = state.cy - y;
    var len = Math.hypot(dx, dy) || 1;
    var ux = dx / len, uy = dy / len;
    var shade = ctx.createRadialGradient(x + ux * r * 0.45, y + uy * r * 0.45, r * 0.1, x, y, r);
    shade.addColorStop(0, planet.colors[0]);
    shade.addColorStop(0.55, planet.colors[1]);
    shade.addColorStop(1, planet.colors[2]);
    ctx.fillStyle = shade;
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();

    // Surface details are clipped so they stay inside the sphere.
    if (planet.style === 'bands' || planet.style === 'earth') {
      ctx.save();
      ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.clip();
      if (planet.style === 'bands') {
        for (var i = -3; i <= 3; i++) {
          ctx.fillStyle = (i % 2 === 0) ? 'rgba(255,240,220,0.14)' : 'rgba(90,50,30,0.22)';
          ctx.fillRect(x - r, y + i * r * 0.28 - r * 0.07, r * 2, r * 0.14);
        }
      } else {
        var shift = Math.cos(state.simTime * 0.6) * r * 0.25;
        ctx.fillStyle = 'rgba(74,222,128,0.6)';
        ctx.beginPath(); ctx.ellipse(x - r * 0.3 + shift, y - r * 0.15, r * 0.38, r * 0.26, 0.5, 0, TAU); ctx.fill();
        ctx.beginPath(); ctx.ellipse(x + r * 0.35 + shift, y + r * 0.35, r * 0.28, r * 0.2, -0.4, 0, TAU); ctx.fill();
      }
      ctx.restore();
    }

    if (planet.ring) { drawRingHalf(planet, 'front'); }

    // Highlight ring for the selected planet (pulses unless reduced motion).
    if (selected) {
      var pulse = prefersReducedMotion ? 0 : Math.sin(now / 260) * 2;
      var ringR = Math.max(r * (planet.ring ? 2.5 : 1.7), 14) + pulse;
      ctx.lineWidth = 2;
      ctx.strokeStyle = rgba(theme.accentRgb, 0.95);
      ctx.beginPath(); ctx.arc(x, y, ringR, 0, TAU); ctx.stroke();
    }

    // Name labels are drawn only when there is enough room.
    if (state.width > 520 || selected) {
      ctx.font = (selected ? '600 13px ' : '12px ') + 'system-ui, "Segoe UI", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = selected ? '#ffffff' : 'rgba(232,236,255,0.62)';
      var labelOffset = Math.max(r * (planet.ring ? 2.5 : 1.7), 14) + 16;
      ctx.fillText(planet.name, x, y + labelOffset);
    }
  }

  // =================================================================
  // SECTION 8: Meteors and impact particles
  // =================================================================
  function launchMeteor(targetX, targetY) {
    if (state.meteors.length >= MAX_METEORS) {
      showMessage('Too many meteors in the sky. Wait a moment and try again.');
      return false;
    }
    // Meteors enter from above the top edge or beyond the right edge.
    var fromTop = Math.random() < 0.7;
    var startX = fromTop ? rand(state.width * 0.25, state.width * 1.1) : state.width + 30;
    var startY = fromTop ? -30 : rand(0, state.height * 0.5);
    var dx = targetX - startX, dy = targetY - startY;
    var distance = Math.hypot(dx, dy);
    if (distance < 40) { distance = 40; dx = -40; dy = 0; }

    state.meteors.push({
      startX: startX, startY: startY,
      dirX: dx / distance, dirY: dy / distance,   // unit direction (length 1)
      targetX: targetX, targetY: targetY,
      totalDistance: distance, travelled: 0,
      speed: rand(520, 820),                       // pixels per second at 1x
      size: rand(2.2, 3.6),
      x: startX, y: startY
    });
    state.meteorCount += 1;
    updateStats();
    return true;
  }

  // A button-launched meteor flies toward a random spot on the canvas.
  function launchRandomMeteor() {
    launchMeteor(rand(state.width * 0.1, state.width * 0.8), rand(state.height * 0.25, state.height * 0.9));
  }

  function spawnImpactBurst(x, y) {
    for (var i = 0; i < 18; i++) {
      var angle = rand(0, TAU), speed = rand(40, 190);
      var life = rand(0.35, 0.9);
      state.particles.push({
        x: x, y: y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
        life: life, maxLife: life, size: rand(1, 2.6)
      });
    }
  }

  // simDt = seconds of simulation time since the last frame
  // (real time * speed, or 0 when paused).
  function updateMeteors(simDt) {
    var alive = [];
    state.meteors.forEach(function (meteor) {
      meteor.travelled += meteor.speed * simDt;
      meteor.x = meteor.startX + meteor.dirX * meteor.travelled;
      meteor.y = meteor.startY + meteor.dirY * meteor.travelled;
      if (meteor.travelled >= meteor.totalDistance) {
        spawnImpactBurst(meteor.targetX, meteor.targetY); // finished: burst, then drop it
      } else {
        alive.push(meteor);
      }
    });
    state.meteors = alive; // finished meteors are no longer referenced
  }

  function updateParticles(simDt) {
    var alive = [];
    state.particles.forEach(function (p) {
      p.life -= simDt;
      if (p.life <= 0) { return; } // expired: skip it so it is removed
      p.x += p.vx * simDt;
      p.y += p.vy * simDt;
      var drag = Math.pow(0.15, simDt); // slows the particle smoothly
      p.vx *= drag; p.vy *= drag;
      alive.push(p);
    });
    state.particles = alive;
  }

  function drawMeteors() {
    var tailLength = 150 * clamp(state.planetScale, 0.7, 1.1);
    state.meteors.forEach(function (m) {
      var tailX = m.x - m.dirX * tailLength, tailY = m.y - m.dirY * tailLength;
      var tail = ctx.createLinearGradient(m.x, m.y, tailX, tailY);
      tail.addColorStop(0, rgba(theme.meteorTail, 0.95));
      tail.addColorStop(1, rgba(theme.meteorTail, 0));
      ctx.lineCap = 'round';
      ctx.lineWidth = m.size * 1.6;
      ctx.strokeStyle = tail;
      ctx.beginPath(); ctx.moveTo(m.x, m.y); ctx.lineTo(tailX, tailY); ctx.stroke();

      var head = ctx.createRadialGradient(m.x, m.y, 0, m.x, m.y, m.size * 5);
      head.addColorStop(0, rgba(theme.meteorHead, 1));
      head.addColorStop(0.35, rgba(theme.meteorTail, 0.6));
      head.addColorStop(1, rgba(theme.meteorTail, 0));
      ctx.fillStyle = head;
      ctx.beginPath(); ctx.arc(m.x, m.y, m.size * 5, 0, TAU); ctx.fill();
    });
  }

  function drawParticles() {
    state.particles.forEach(function (p) {
      ctx.fillStyle = rgba(theme.meteorTail, clamp(p.life / p.maxLife, 0, 1));
      ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, TAU); ctx.fill();
    });
  }

  // =================================================================
  // Main drawing function: paints one frame from the current state.
  // =================================================================
  function render(now) {
    drawBackground();
    drawStars();
    drawOrbits();
    // Planets "behind" the sun (upper half of their orbit) are drawn first.
    state.planets.filter(function (p) { return Math.sin(p.angle) < 0; })
      .forEach(function (p) { drawPlanet(p, now); });
    drawSun();
    state.planets.filter(function (p) { return Math.sin(p.angle) >= 0; })
      .forEach(function (p) { drawPlanet(p, now); });
    drawMeteors();
    drawParticles();
  }

  // =================================================================
  // SECTION 7 (loop): The single animation loop
  // =================================================================
  function update(simDt) {
    state.simTime += simDt;
    updatePlanetPositions();
    updateMeteors(simDt);
    updateParticles(simDt);
  }

  // requestAnimationFrame calls this before every screen repaint.
  // The loop is ALWAYS running once; pausing only sets simDt to 0.
  // That is why pause / resume / reset can never create a second loop.
  function frame(now) {
    state.rafId = window.requestAnimationFrame(frame);
    // Delta time = real seconds since the previous frame. It is capped so
    // a long pause (for example a hidden tab) does not cause a big jump.
    var realDt = clamp((now - state.lastFrameTime) / 1000, 0, 0.05);
    state.lastFrameTime = now;
    var simDt = state.paused ? 0 : realDt * state.speed;
    update(simDt);
    render(now);
  }

  function startLoop() {
    if (state.rafId !== null) { return; } // guard: never start a second loop
    state.lastFrameTime = performance.now();
    state.rafId = window.requestAnimationFrame(frame);
  }

  // =================================================================
  // SECTION 9: Planet selection and the information panel
  // =================================================================
  function findPlanet(id) {
    for (var i = 0; i < state.planets.length; i++) {
      if (state.planets[i].id === id) { return state.planets[i]; }
    }
    return null;
  }

  function planetAt(x, y) {
    var best = null, bestDistance = Infinity;
    state.planets.forEach(function (planet) {
      var hitRadius = Math.max(planet.radius * (planet.ring ? 1.9 : 1), 10) + 8; // generous for touch
      var distance = Math.hypot(x - planet.x, y - planet.y);
      if (distance <= hitRadius && distance < bestDistance) { best = planet; bestDistance = distance; }
    });
    return best;
  }

  function renderInfoPanel() {
    var planet = findPlanet(state.selectedId);
    if (!planet) {
      ui.infoEmpty.hidden = false;
      ui.infoCard.hidden = true;
      return;
    }
    ui.infoEmpty.hidden = true;
    ui.infoCard.hidden = false;
    ui.infoName.textContent = planet.name;   // textContent is safe: it never runs HTML
    ui.infoType.textContent = planet.type;
    ui.infoDesc.textContent = planet.description;
    while (ui.infoFacts.firstChild) { ui.infoFacts.removeChild(ui.infoFacts.firstChild); }
    planet.facts.forEach(function (fact) {
      var item = document.createElement('li');
      item.textContent = fact;
      ui.infoFacts.appendChild(item);
    });
  }

  function syncPlanetButtons() {
    var buttons = ui.planetList.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute('aria-pressed', String(buttons[i].getAttribute('data-id') === state.selectedId));
    }
  }

  function selectPlanet(id) {
    state.selectedId = id;
    renderInfoPanel();
    syncPlanetButtons();
  }

  // =================================================================
  // SECTION 10: Buttons, slider, themes and reset
  // =================================================================
  function updateStats() {
    ui.planets.textContent = String(state.planets.length);
    ui.status.textContent = state.paused ? 'Paused' : 'Running';
    ui.statusDot.classList.toggle('is-paused', state.paused);
    ui.speed.textContent = fmtSpeed(state.speed);
    ui.meteors.textContent = String(state.meteorCount);
  }

  function updatePauseButton() {
    ui.pauseBtn.textContent = state.paused ? 'Resume' : 'Pause';
  }

  function setPaused(paused) {
    state.paused = paused;
    updatePauseButton();
    updateStats();
  }

  function setSpeed(value) {
    state.speed = clamp(value, 0.1, 4);
    ui.slider.value = String(state.speed);
    ui.sliderOut.textContent = fmtSpeed(state.speed);
    ui.slider.setAttribute('aria-valuetext', fmtSpeed(state.speed) + ' speed');
    updateStats();
  }

  function applyTheme(id) {
    if (!THEMES[id]) { return; }
    state.themeId = id;
    theme = THEMES[id];
    Object.keys(theme.vars).forEach(function (name) {
      document.documentElement.style.setProperty(name, theme.vars[name]);
    });
    var buttons = ui.themeButtons.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute('aria-pressed', String(buttons[i].getAttribute('data-theme') === id));
    }
  }

  // Reset returns EVERYTHING to the starting state:
  // time, planet positions, speed, running state, meteors, particles,
  // meteor counter, selected planet, and theme.
  function resetSimulation() {
    state.simTime = 0;
    state.meteors = [];
    state.particles = [];
    state.meteorCount = 0;
    state.selectedId = null;
    updatePlanetPositions();
    setSpeed(DEFAULT_SPEED);
    setPaused(false);
    applyTheme(DEFAULT_THEME);
    renderInfoPanel();
    syncPlanetButtons();
    showMessage('Simulation reset.');
  }

  function buildPlanetButtons() {
    state.planets.forEach(function (planet, index) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'btn planet-btn';
      button.setAttribute('data-id', planet.id);
      button.setAttribute('aria-pressed', 'false');
      button.setAttribute('aria-label', 'Show information about ' + planet.name + ' (shortcut ' + (index + 1) + ')');
      var dot = document.createElement('span');
      dot.className = 'planet-dot';
      dot.style.background = planet.colors[1];
      dot.setAttribute('aria-hidden', 'true');
      button.appendChild(dot);
      button.appendChild(document.createTextNode(planet.name));
      button.addEventListener('click', function () { selectPlanet(planet.id); });
      ui.planetList.appendChild(button);
    });
  }

  function buildThemeButtons() {
    Object.keys(THEMES).forEach(function (id) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'btn theme-btn';
      button.setAttribute('data-theme', id);
      button.setAttribute('aria-pressed', 'false');
      button.textContent = THEMES[id].name;
      button.addEventListener('click', function () { applyTheme(id); });
      ui.themeButtons.appendChild(button);
    });
  }

  // Convert mouse position to canvas coordinates. The canvas may be
  // displayed at a different size than its internal size, so we scale.
  function getCanvasPoint(event) {
    var rect = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left) * (state.width / rect.width),
      y: (event.clientY - rect.top) * (state.height / rect.height)
    };
  }

  function onCanvasClick(event) {
    var point = getCanvasPoint(event);
    var planet = planetAt(point.x, point.y);
    if (planet) {
      selectPlanet(planet.id);
    } else {
      launchMeteor(point.x, point.y);
    }
  }

  function onCanvasMove(event) {
    var point = getCanvasPoint(event);
    canvas.style.cursor = planetAt(point.x, point.y) ? 'pointer' : 'crosshair';
  }

  function onKeyDown(event) {
    if (event.ctrlKey || event.metaKey || event.altKey) { return; }
    var key = event.key;
    var onButton = event.target && event.target.closest && event.target.closest('button');
    if (key === ' ' || key === 'Spacebar') {
      if (onButton) { return; }          // let a focused button use Space normally
      event.preventDefault();            // stops the page from scrolling
      setPaused(!state.paused);
    } else if (key === 'm' || key === 'M') {
      launchRandomMeteor();
    } else if (key === 'r' || key === 'R') {
      resetSimulation();
    } else if (key === 'Escape') {
      selectPlanet(null);
    } else if (key >= '1' && key <= String(state.planets.length)) {
      selectPlanet(state.planets[Number(key) - 1].id);
    }
  }

  // =================================================================
  // SECTION 11: Initialisation and error handling
  // =================================================================
  function init() {
    ctx = canvas.getContext ? canvas.getContext('2d') : null;
    if (!ctx) {
      showError('Your browser does not support the HTML5 canvas, so the simulation cannot run. Try a recent version of Chrome, Edge, Firefox, or Safari.');
      return;
    }

    // Copy the planet data into live objects that can hold positions.
    state.planets = PLANET_DATA.map(function (data) {
      var live = {};
      Object.keys(data).forEach(function (k) { live[k] = data[k]; });
      live.x = 0; live.y = 0; live.rx = 0; live.ry = 0; live.radius = 0; live.angle = data.startAngle;
      return live;
    });

    createStars();
    buildPlanetButtons();
    buildThemeButtons();
    applyTheme(DEFAULT_THEME);
    setSpeed(DEFAULT_SPEED);
    resizeCanvas();
    renderInfoPanel();
    updatePauseButton();
    updateStats();

    // Events
    ui.meteorBtn.addEventListener('click', launchRandomMeteor);
    ui.pauseBtn.addEventListener('click', function () { setPaused(!state.paused); });
    ui.resetBtn.addEventListener('click', resetSimulation);
    ui.slider.addEventListener('input', function () { setSpeed(parseFloat(ui.slider.value)); });
    canvas.addEventListener('click', onCanvasClick);
    canvas.addEventListener('pointermove', onCanvasMove);
    document.addEventListener('keydown', onKeyDown);

    if (window.ResizeObserver) {
      new ResizeObserver(resizeCanvas).observe(stage);
    } else {
      window.addEventListener('resize', resizeCanvas);
    }
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) { state.lastFrameTime = performance.now(); }
    });

    if (prefersReducedMotion) {
      showMessage('Reduced motion is on: speed starts at 0.5x and stars do not twinkle.');
    }
    startLoop();
  }

  // Any unexpected error is shown to the user instead of failing silently.
  window.addEventListener('error', function (event) {
    showError('Something went wrong: ' + event.message);
  });

  try {
    init();
  } catch (error) {
    console.error(error);
    showError('The simulator could not start: ' + error.message);
  }
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# SECTION 1 (continued): Python launcher logic
# ---------------------------------------------------------------------------
def write_temporary_page(html_text):
    """Write the page to a temporary .html file and return its Path.

    delete=False keeps the file after it is closed, so the browser can open it.
    encoding="utf-8" makes sure special characters (like the degree sign)
    are saved correctly on every operating system.
    """
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        prefix="space_explorer_",
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_file.write(html_text)
        return Path(temp_file.name)


def open_in_browser(html_path):
    """Try to open the file in the default browser. Return True if it worked."""
    page_url = html_path.resolve().as_uri()  # turns a path into a file:// address
    try:
        return webbrowser.open(page_url)
    except webbrowser.Error as error:
        print(f"Browser error: {error}")
        return False


def main():
    """Create the page, open it, and clean up afterwards."""
    print("Space Explorer: preparing your galaxy...")

    # Step 1: write the page to disk (this can fail, e.g. disk full).
    try:
        html_path = write_temporary_page(HTML_PAGE)
    except OSError as error:
        print(f"Sorry, the temporary web page could not be written: {error}")
        print("Check that your disk has free space and that you may write to the temp folder.")
        return 1

    # Step 2: open the page in the browser.
    if open_in_browser(html_path):
        print("Space Explorer has opened in your default web browser.")
        print("To close it, simply close the browser tab or window.")
    else:
        print("Python could not open a browser automatically.")
        print("Open this file yourself (copy the path into your browser's address bar):")
        print(f"  {html_path}")

    print(f"Temporary page: {html_path}")

    # Step 3: wait, then delete the temporary file. The page is already
    # loaded in the browser, so deleting the file does not close it.
    try:
        input("Press Enter here when you are finished to delete the temporary file and exit... ")
    except (EOFError, KeyboardInterrupt):
        print()  # no keyboard input available, or Ctrl+C pressed
    finally:
        try:
            html_path.unlink()
            print("Temporary file deleted. Goodbye!")
        except OSError:
            print(f"Could not delete the temporary file. You can remove it manually: {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())