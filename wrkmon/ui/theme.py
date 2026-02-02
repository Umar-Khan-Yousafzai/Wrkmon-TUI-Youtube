"""Theme and CSS for wrkmon TUI."""

# Main application CSS
APP_CSS = """
/* ============================================
   WRKMON - Terminal Music Player Theme
   Designed to look like a system monitor
   ============================================ */

/* Base screen styling */
Screen {
    background: #0a0a0a;
}

/* ----------------------------------------
   HEADER BAR
   ---------------------------------------- */
HeaderBar {
    dock: top;
    height: 1;
    background: #1a1a1a;
    color: #00ff00;
}

#header-inner {
    width: 100%;
}

#app-title {
    width: auto;
    color: #00ff00;
    text-style: bold;
    padding: 0 1;
}

#current-view {
    width: 1fr;
    color: #008800;
    padding: 0 1;
}

#sys-stats {
    width: auto;
    color: #888888;
    padding: 0 1;
}

#update-indicator {
    width: auto;
    color: #ffff00;
    text-style: bold;
    padding: 0 1;
}

#update-indicator.update-available {
    color: #ff8800;
    text-style: bold blink;
}

/* ----------------------------------------
   PLAYER BAR (Bottom)
   ---------------------------------------- */
PlayerBar {
    dock: bottom;
    height: 5;
    background: #1a1a1a;
    border-top: solid #333333;
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
    color: #888888;
}

#play-status {
    width: 2;
    color: #00ff00;
}

#track-title {
    width: 1fr;
    color: #ffffff;
}

#progress-row {
    height: 1;
    padding: 0 1;
}

#time-current, #time-total {
    width: 8;
    color: #888888;
}

#progress {
    width: 1fr;
    background: #333333;
}

#progress > .bar--bar {
    color: #00ff00;
}

#volume-row {
    height: 1;
}

#vol-label {
    width: 4;
    color: #888888;
}

#volume {
    width: 20;
    background: #333333;
}

#volume > .bar--bar {
    color: #00ffff;
}

#vol-value {
    width: 5;
    color: #888888;
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
    color: #00ff00;
    text-style: bold;
    background: #111111;
    padding: 0 1;
}

/* Search container */
#search-container {
    height: auto;
    padding: 1 0;
}

#search-input {
    width: 100%;
    background: #1a1a1a;
    border: tall #333333;
    color: #ffffff;
}

#search-input:focus {
    border: tall #00ff00;
}

/* List headers (column titles) */
#list-header {
    height: 1;
    color: #888888;
    background: #111111;
    text-style: bold;
}

/* Result/Queue/History lists */
#results-list, #queue-list, #history-list, #playlist-list {
    height: 1fr;
    background: #0a0a0a;
    scrollbar-background: #1a1a1a;
    scrollbar-color: #333333;
}

ListView > ListItem {
    height: 1;
    padding: 0 1;
    color: #cccccc;
}

ListView > ListItem:hover {
    background: #1a1a1a;
}

ListView > ListItem.-highlight {
    background: #222222;
    color: #00ff00;
}

.result-text, .queue-text, .history-text {
    width: 100%;
}

/* Status bar */
#status-bar {
    dock: bottom;
    height: 1;
    color: #888888;
    background: #111111;
    padding: 0 1;
}

/* ----------------------------------------
   QUEUE VIEW SPECIFICS
   ---------------------------------------- */
#now-playing-section {
    height: auto;
    background: #111111;
    padding: 1;
    margin-bottom: 1;
}

#section-header {
    color: #888888;
    text-style: bold;
}

#current-track {
    color: #00ff00;
    padding: 0 1;
}

#playback-progress {
    height: 1;
    padding: 0 1;
}

#track-progress {
    width: 1fr;
    background: #333333;
}

#track-progress > .bar--bar {
    color: #00ff00;
}

#pos-time, #dur-time {
    width: 8;
    color: #888888;
}

#mode-indicators {
    height: 1;
    padding: 0 1;
}

#shuffle-indicator, #repeat-indicator {
    width: auto;
    color: #00ffff;
    padding: 0 1;
}

/* ----------------------------------------
   PLAYLIST INPUT
   ---------------------------------------- */
#new-playlist-input {
    width: 100%;
    background: #1a1a1a;
    border: tall #333333;
    color: #ffffff;
    margin: 1 0;
}

#new-playlist-input:focus {
    border: tall #00ff00;
}

/* ----------------------------------------
   FOOTER
   ---------------------------------------- */
Footer {
    background: #111111;
    color: #888888;
}

Footer > .footer--key {
    color: #00ff00;
    background: #1a1a1a;
}

Footer > .footer--description {
    color: #888888;
}

/* ----------------------------------------
   LABELS (General)
   ---------------------------------------- */
.label {
    color: #888888;
}

"""

# Alternative themes (can be switched via config)
THEMES = {
    "matrix": {
        "primary": "#00ff00",
        "secondary": "#008800",
        "accent": "#00ffff",
        "background": "#0a0a0a",
        "surface": "#1a1a1a",
    },
    "hacker": {
        "primary": "#00ffff",
        "secondary": "#008888",
        "accent": "#ff00ff",
        "background": "#0a0a0a",
        "surface": "#1a1a1a",
    },
    "minimal": {
        "primary": "#ffffff",
        "secondary": "#888888",
        "accent": "#4444ff",
        "background": "#000000",
        "surface": "#111111",
    },
}
