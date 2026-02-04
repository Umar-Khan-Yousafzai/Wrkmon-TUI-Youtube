"""Theme and CSS for wrkmon TUI."""

# Main application CSS with enhanced UX
APP_CSS = """
/* ============================================
   WRKMON - Terminal Music Player Theme
   Enhanced UX with better colors and visuals
   ============================================ */

/* Base screen styling */
Screen {
    background: #0d1117;
}

/* ----------------------------------------
   HEADER BAR
   ---------------------------------------- */
HeaderBar {
    dock: top;
    height: 1;
    background: #161b22;
    color: #58a6ff;
}

#header-inner {
    width: 100%;
}

#app-title {
    width: auto;
    color: #58a6ff;
    text-style: bold;
    padding: 0 1;
}

#current-view {
    width: 1fr;
    color: #8b949e;
    padding: 0 1;
}

#sys-stats {
    width: auto;
    color: #6e7681;
    padding: 0 1;
}

#update-indicator {
    width: auto;
    color: #f0883e;
    text-style: bold;
    padding: 0 1;
}

#update-indicator.update-available {
    color: #f85149;
    text-style: bold blink;
}

/* ----------------------------------------
   PLAYER BAR (Bottom) - Enhanced
   ---------------------------------------- */
PlayerBar {
    dock: bottom;
    height: 5;
    background: #161b22;
    border-top: solid #30363d;
    padding: 0 1;
}

#player-bar-inner {
    height: 100%;
}

#now-playing-row {
    height: 1;
}

#now-label {
    width: 4;
    color: #8b949e;
}

#play-status {
    width: 3;
    color: #3fb950;
    text-style: bold;
}

#play-status.paused {
    color: #f0883e;
}

#play-status.stopped {
    color: #6e7681;
}

#track-title {
    width: 1fr;
    color: #f0f6fc;
}

#progress-row {
    height: 1;
    padding: 0 1;
}

#time-current {
    width: 8;
    color: #3fb950;
}

#time-total {
    width: 8;
    color: #8b949e;
}

#progress {
    width: 1fr;
    background: #21262d;
}

#progress > .bar--bar {
    color: #238636;
    background: #238636;
}

#progress > .bar--complete {
    color: #3fb950;
}

#volume-row {
    height: 1;
}

#vol-label {
    width: 4;
    color: #8b949e;
}

#volume {
    width: 20;
    background: #21262d;
}

#volume > .bar--bar {
    color: #1f6feb;
    background: #1f6feb;
}

#vol-value {
    width: 5;
    color: #58a6ff;
}

#repeat-indicator {
    width: auto;
    color: #a371f7;
    text-style: bold;
    padding: 0 1;
}

/* ----------------------------------------
   CONTENT SWITCHER / MAIN AREA
   ---------------------------------------- */
#content-area {
    height: 1fr;
}

ContentSwitcher {
    height: 1fr;
}

/* ----------------------------------------
   VIEW CONTAINERS
   ---------------------------------------- */
SearchView, QueueView, HistoryView, PlaylistsView {
    height: 1fr;
    padding: 0 1;
}

#view-title {
    height: 1;
    color: #58a6ff;
    text-style: bold;
    background: #161b22;
    padding: 0 1;
}

/* Search container */
#search-container {
    height: auto;
    padding: 1 0;
}

#search-input {
    width: 100%;
    background: #0d1117;
    border: tall #30363d;
    color: #f0f6fc;
}

#search-input:focus {
    border: tall #58a6ff;
}

#search-input.-invalid {
    border: tall #f85149;
}

/* List headers (column titles) */
#list-header {
    height: 1;
    color: #8b949e;
    background: #161b22;
    text-style: bold;
}

/* Result/Queue/History lists */
#results-list, #queue-list, #history-list, #playlist-list {
    height: 1fr;
    background: #0d1117;
    scrollbar-background: #161b22;
    scrollbar-color: #30363d;
    scrollbar-color-hover: #484f58;
    scrollbar-color-active: #6e7681;
}

ListView > ListItem {
    height: 1;
    padding: 0 1;
    color: #c9d1d9;
}

ListView > ListItem:hover {
    background: #161b22;
}

ListView > ListItem.-highlight, ListView > ListItem:focus {
    background: #1f6feb20;
    color: #58a6ff;
}

/* Track status colors */
.track-playing {
    color: #3fb950;
    text-style: bold;
}

.track-queued {
    color: #f0883e;
}

.track-paused {
    color: #f0883e;
}

.result-text, .queue-text, .history-text {
    width: 100%;
}

/* Status bar - Enhanced */
#status-bar {
    dock: bottom;
    height: 1;
    color: #8b949e;
    background: #161b22;
    padding: 0 1;
}

/* ----------------------------------------
   SEARCH CONTENT & THUMBNAIL
   ---------------------------------------- */
#search-content {
    height: 1fr;
}

#thumbnail-panel {
    width: 50;
    min-width: 50;
    max-width: 50;
    height: 100%;
    background: #0d1117;
    border-left: solid #30363d;
    padding: 0 1;
}

#thumbnail-panel.hidden {
    display: none;
}

#thumb-title {
    height: 1;
    color: #58a6ff;
    text-style: bold;
    background: #161b22;
    padding: 0 1;
}

#thumb-preview {
    height: 1fr;
    background: #0d1117;
    color: #3fb950;
}

#thumb-preview.loading {
    color: #6e7681;
}

#ascii-content {
    height: auto;
    width: 100%;
}

.load-more {
    color: #a371f7;
    text-style: bold;
}

/* ----------------------------------------
   QUEUE VIEW SPECIFICS
   ---------------------------------------- */
#now-playing-section {
    height: auto;
    background: #161b22;
    border: solid #30363d;
    padding: 1;
    margin-bottom: 1;
}

#section-header {
    color: #8b949e;
    text-style: bold;
}

#current-track {
    color: #3fb950;
    padding: 0 1;
}

#playback-progress {
    height: 1;
    padding: 0 1;
}

#track-progress {
    width: 1fr;
    background: #21262d;
}

#track-progress > .bar--bar {
    color: #238636;
    background: #238636;
}

#pos-time, #dur-time {
    width: 8;
    color: #8b949e;
}

#mode-indicators {
    height: 1;
    padding: 0 1;
}

#shuffle-indicator, #repeat-indicator {
    width: auto;
    color: #a371f7;
    padding: 0 1;
}

/* ----------------------------------------
   PLAYLIST INPUT
   ---------------------------------------- */
#new-playlist-input {
    width: 100%;
    background: #0d1117;
    border: tall #30363d;
    color: #f0f6fc;
    margin: 1 0;
}

#new-playlist-input:focus {
    border: tall #58a6ff;
}

/* ----------------------------------------
   HELP OVERLAY
   ---------------------------------------- */
HelpScreen {
    align: center middle;
}

#help-container {
    width: 70;
    height: auto;
    max-height: 80%;
    background: #161b22;
    border: thick #30363d;
    padding: 1 2;
}

#help-title {
    text-align: center;
    color: #58a6ff;
    text-style: bold;
    padding-bottom: 1;
}

#help-content {
    color: #c9d1d9;
}

.help-section {
    color: #f0883e;
    text-style: bold;
    padding-top: 1;
}

.help-key {
    color: #a371f7;
    text-style: bold;
}

.help-desc {
    color: #8b949e;
}

/* ----------------------------------------
   METADATA PANEL
   ---------------------------------------- */
#metadata-panel {
    height: auto;
    background: #161b22;
    border: solid #30363d;
    padding: 1;
    margin-top: 1;
}

#metadata-title {
    color: #f0f6fc;
    text-style: bold;
}

#metadata-channel {
    color: #8b949e;
}

#metadata-stats {
    color: #6e7681;
}

/* ----------------------------------------
   NOTIFICATIONS
   ---------------------------------------- */
Toast {
    background: #161b22;
    border: solid #30363d;
    color: #c9d1d9;
}

Toast.-information {
    border: solid #58a6ff;
}

Toast.-warning {
    border: solid #f0883e;
}

Toast.-error {
    border: solid #f85149;
}

/* ----------------------------------------
   FOOTER - Enhanced
   ---------------------------------------- */
Footer {
    background: #161b22;
    color: #8b949e;
}

Footer > .footer--key {
    color: #58a6ff;
    background: #21262d;
    text-style: bold;
}

Footer > .footer--description {
    color: #8b949e;
}

/* ----------------------------------------
   FOCUS INDICATORS
   ---------------------------------------- */
Input:focus {
    border: tall #58a6ff;
}

Button:focus {
    background: #1f6feb;
}

"""

# Color palette for programmatic access
COLORS = {
    # Base colors (GitHub Dark theme inspired)
    "bg_primary": "#0d1117",
    "bg_secondary": "#161b22",
    "bg_tertiary": "#21262d",
    "border": "#30363d",
    "border_active": "#58a6ff",

    # Text colors
    "text_primary": "#f0f6fc",
    "text_secondary": "#c9d1d9",
    "text_muted": "#8b949e",
    "text_faint": "#6e7681",

    # Accent colors
    "blue": "#58a6ff",
    "green": "#3fb950",
    "green_dark": "#238636",
    "orange": "#f0883e",
    "red": "#f85149",
    "purple": "#a371f7",
    "cyan": "#39c5cf",
    "yellow": "#d29922",

    # Status colors
    "playing": "#3fb950",
    "paused": "#f0883e",
    "stopped": "#6e7681",
    "queued": "#f0883e",
    "error": "#f85149",
    "success": "#3fb950",
    "warning": "#f0883e",
    "info": "#58a6ff",
}

# Alternative themes
THEMES = {
    "github_dark": {
        "primary": "#58a6ff",
        "secondary": "#8b949e",
        "accent": "#a371f7",
        "success": "#3fb950",
        "warning": "#f0883e",
        "error": "#f85149",
        "background": "#0d1117",
        "surface": "#161b22",
    },
    "matrix": {
        "primary": "#00ff00",
        "secondary": "#008800",
        "accent": "#00ffff",
        "success": "#00ff00",
        "warning": "#ffff00",
        "error": "#ff0000",
        "background": "#0a0a0a",
        "surface": "#1a1a1a",
    },
    "dracula": {
        "primary": "#bd93f9",
        "secondary": "#6272a4",
        "accent": "#ff79c6",
        "success": "#50fa7b",
        "warning": "#ffb86c",
        "error": "#ff5555",
        "background": "#282a36",
        "surface": "#44475a",
    },
    "nord": {
        "primary": "#88c0d0",
        "secondary": "#81a1c1",
        "accent": "#b48ead",
        "success": "#a3be8c",
        "warning": "#ebcb8b",
        "error": "#bf616a",
        "background": "#2e3440",
        "surface": "#3b4252",
    },
}
