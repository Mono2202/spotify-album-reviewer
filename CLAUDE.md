# spotify-album-reviewer

A Python tkinter desktop app that reads the user's current Spotify playback and lets them write per-song reviews into Obsidian markdown files inside their vault.

---

## Project overview

- **Language / stack:** Python 3, tkinter (GUI), Spotipy (Spotify API), python-dotenv
- **GUI style:** Modern tkinter design (consider `customtkinter` for a polished look)
- **Data flow:**
  1. Poll Spotify for the currently playing track (song title, artist, album, cover art URL)
  2. Display that info in the GUI with a 10-star rating widget and a notes text area
  3. On submit, write/update the review into the album's Obsidian markdown file

---

## Environment variables (`.env`)

```
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=

OBSIDIAN_REVIEWS_PATH=   # Absolute path to the reviews folder inside the vault
                         # e.g. C:\Users\MonoPC\Documents\Vault\Music Reviews
```

---

## Obsidian markdown format

Each album gets its own `.md` file named `<Artist> - <Album>.md` inside `OBSIDIAN_REVIEWS_PATH`.

### Full file template

```markdown
---
artist: <Artist Name>
music_genre:
  - <genre>
release: <release year>
date: <date first reviewed, YYYY-MM-DD>
rating: <average of all rated tracks, float rounded to 2dp>
cover: <AlbumName>-<unix_timestamp_ms>.png
---
![[<AlbumName>-<unix_timestamp_ms>.png|135]]

### Tracks
| No. | Track | Rating | Symbol | Notes |
| --- | ----- | ------ | ------ | ----- |
| 1   | Track Name | 7/10 |  | Review notes here |
| 2   | Track Name | 5/10 |  | Review notes here |
```

### Key rules

**File naming:** `{Artist} - {Album}.md`  
- Sanitise names: replace characters invalid in filenames (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) with a dash or space

**Cover art image:**
- Filename pattern: `{AlbumName}-{unix_timestamp_ms}.png` (timestamp from when the file was first created)
- The image is downloaded from Spotify and saved into `OBSIDIAN_REVIEWS_PATH` (same folder as the `.md` file)
- Embedded in the note as `![[filename.png|135]]` (135px wide via Obsidian wikilink syntax)
- The `cover:` frontmatter field holds only the filename, not the full path

**Frontmatter:**
- `artist` — artist name string
- `music_genre` — YAML list; leave empty (`[]` or omit items) if unknown, user can fill manually
- `release` — album release year as integer
- `date` — date the note was first created (`YYYY-MM-DD`)
- `rating` — **auto-calculated** average of all track ratings that have been reviewed; float rounded to 2 decimal places; recalculated on every submit

**Tracks table columns:**
| Column | Content |
|--------|---------|
| `No.`  | Track number (integer, 1-based, from Spotify track list for the album) |
| `Track` | Track title exactly as returned by Spotify |
| `Rating` | `X/10` format (e.g. `7/10`); empty string if not yet reviewed |
| `Symbol` | Optional Obsidian icon string (e.g. `:LiStar:`, `:LiTrash:`); always empty on app submit — user fills manually |
| `Notes` | Free-form review text; newlines within a cell use `<br><br>` |

**On submit (upsert logic):**
1. File doesn't exist → create it: download cover art, write full frontmatter + `![[...]]` + all album tracks as table rows (unreviewed rows have empty Rating and Notes)
2. File exists, song row has no rating yet → fill in the `Rating` and `Notes` cells for that row
3. File exists, song row already has a rating → replace only that row's `Rating` and `Notes` cells in-place
4. After any write → recalculate `rating` frontmatter as the mean of all non-empty `X/10` values in the table and update it

**Row matching:** match table rows by track title (column 2) — exact string match against the Spotify track name.

---

## GUI layout

```
┌─────────────────────────────────────────┐
│  [Album cover art - 200×200px]          │
│  Song Title          (bold, large)      │
│  Artist · Album                         │
│                                         │
│  Rating:  ★ ★ ★ ★ ★ ★ ★ ☆ ☆ ☆  (7/10) │
│                                         │
│  Notes:                                 │
│  ┌───────────────────────────────────┐  │
│  │  (multiline text area)            │  │
│  └───────────────────────────────────┘  │
│                                         │
│           [ Submit Review ]             │
└─────────────────────────────────────────┘
```

- Cover art is fetched from the Spotify image URL and displayed inline
- Rating widget: 10 clickable stars that highlight on hover/click
- Notes: scrollable `Text` widget
- Submit button writes to the markdown file and shows a brief confirmation

---

## File structure (planned)

```
spotify-album-reviewer/
├── main.py              # Entry point — launches the tkinter window
├── spotify_client.py    # Spotipy auth + current-track polling
├── obsidian_writer.py   # Read/write/update album markdown files
├── gui/
│   ├── app.py           # Main window class
│   ├── star_rating.py   # Reusable 10-star rating widget
│   └── cover_art.py     # Async image fetch + display helper
├── .env                 # Never committed
├── .env.example         # Committed, no real values
├── requirements.txt
└── CLAUDE.md
```

---

## Key implementation notes

### Spotify polling
- Use `spotipy.Spotify.current_user_playing_track()` via the `user-read-currently-playing` scope
- Poll every ~5 seconds with `after()` (tkinter's safe timer) — **never** `time.sleep()` on the main thread
- When the track changes, reset the rating and notes fields automatically

### Markdown write logic (`obsidian_writer.py`)
- File path: `{OBSIDIAN_REVIEWS_PATH}/{Artist} - {Album}.md`
- On first submit for an album:
  1. Download cover art from Spotify image URL → save as `{AlbumName}-{timestamp_ms}.png` in `OBSIDIAN_REVIEWS_PATH`
  2. Fetch the full album track list from Spotify to build all table rows upfront
  3. Write the complete file: frontmatter → `![[cover|135]]` → `### Tracks` → table with all rows (unreviewed rows have empty Rating/Symbol/Notes)
- On subsequent submits:
  - Parse the existing table; find the matching row by track title
  - Replace that row's `Rating` and `Notes` cells
  - Recalculate the `rating` frontmatter field (average of all `X/10` values present)
- Parse the markdown table with a line-by-line approach — no heavy markdown parsing library needed; rows follow the `| col | col | ... |` pattern
- Notes containing newlines must be serialised as `<br><br>` within the cell

### Star rating widget
- Extend `tk.Frame`; render 10 `tk.Label` widgets with Unicode stars (`★` / `☆`)
- Bind `<Enter>` / `<Leave>` for hover preview and `<Button-1>` to set the rating
- Expose a `get()` method returning `int` 1–10

### Error handling
- No Spotify session / not playing → show a placeholder UI state, keep polling
- Missing `.env` values → raise a clear `EnvironmentError` at startup
- Obsidian path doesn't exist → warn the user in the GUI, don't crash

---

## Dependencies

```
spotipy
python-dotenv
customtkinter      # or plain tkinter if preferred
Pillow             # for fetching and displaying cover art
requests           # for downloading cover art image bytes
```

---

## Running the app

```bash
pip install -r requirements.txt
# Fill in .env with your credentials
python main.py
```

---

## Out of scope (for now)

- The `Symbol` column (`:LiStar:`, `:LiTrash:` etc.) — always written empty; user fills manually in Obsidian
- `music_genre` frontmatter — always written empty; user fills manually
- Album-level ratings (only per-song; overall `rating` is auto-calculated average)
- Offline / cached track history
- Syncing back from Obsidian into Spotify
- Windows installer / packaging
