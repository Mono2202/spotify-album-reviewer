# Spotify Album Reviewer

A Python desktop app that tracks your currently playing Spotify song and lets you write per-track reviews directly into your Obsidian vault as structured markdown files.

Available as both a GUI (customtkinter) and a TUI (Textual).

---

## Features

- Polls Spotify every 5 seconds and auto-updates when the track changes
- 10-star rating widget with hover/click interaction
- Free-form notes with multi-line support
- Writes reviews to per-album `.md` files inside your Obsidian vault
- Auto-calculates the album's average rating from all reviewed tracks
- Downloads and embeds album cover art
- Loads existing review data when you return to a previously reviewed track
- Non-blocking UI — all network and file I/O runs off the main thread

---

## Prerequisites

- Python 3.11+
- A [Spotify Developer](https://developer.spotify.com/dashboard) app with `user-read-currently-playing` and `user-read-playback-state` scopes
- An Obsidian vault with a reviews folder and an assets/attachments folder

---

## Installation

```bash
git clone https://github.com/Mono2202/spotify-album-reviewer.git
cd spotify-album-reviewer
pip install -r requirements.txt
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback

OBSIDIAN_REVIEWS_PATH=C:\Users\You\Documents\Vault\Music Reviews
OBSIDIAN_ASSETS_PATH=C:\Users\You\Documents\Vault\Assets
```

On first run, a browser window will open for Spotify OAuth. The token is cached locally for subsequent runs.

---

## Usage

```bash
# GUI (default)
python main.py

# TUI
python main.py --tui
```

---

## Obsidian output format

Each album gets its own file at `{OBSIDIAN_REVIEWS_PATH}/{Album}.md`:

```markdown
---
artist: Radiohead
music_genre:
release: 2000
date: 2024-11-01
rating: 8.50
cover: KidA-1730412000000.png
---
![[KidA-1730412000000.png|135]]

### Tracks
| No. | Track | Rating | Symbol | Notes |
| --- | ----- | ------ | ------ | ----- |
| 1   | Everything in Its Right Place | 9/10 |  | Best opener ever |
| 2   | Kid A | 8/10 |  |  |
| 3   | The National Anthem |  |  |  |
```

- `rating` in the frontmatter is auto-calculated as the average of all reviewed tracks
- Unreviewed tracks have empty Rating and Notes cells
- The `Symbol` column is always left empty on submit — fill it manually in Obsidian
- `music_genre` is always left empty on submit — fill it manually in Obsidian

---

## Project structure

```
spotify-album-reviewer/
├── main.py              # Entry point — GUI or TUI via --tui flag
├── spotify_client.py    # Spotipy auth + track/album data fetching
├── obsidian_writer.py   # Create and update album markdown files
├── gui/
│   ├── app.py           # customtkinter main window
│   ├── star_rating.py   # 10-star rating widget
│   └── cover_art.py     # Async cover art fetch and display
├── tui/
│   └── app.py           # Textual terminal UI
├── .env                 # Never committed
├── .env.example
└── requirements.txt
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `spotipy` | Spotify Web API client |
| `python-dotenv` | `.env` loading |
| `customtkinter` | Modern tkinter GUI |
| `Pillow` | Cover art image handling |
| `requests` | Cover art download |
| `textual` | Terminal UI framework |
