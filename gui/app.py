from __future__ import annotations

import threading
from typing import Callable

import customtkinter as ctk

from spotify_client import SpotifyClient, TrackInfo
from gui.cover_art import CoverArtLabel
from gui.star_rating import StarRating

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

POLL_INTERVAL_MS = 5000
WINDOW_WIDTH = 440
WINDOW_HEIGHT = 660

_COLOR_SUCCESS = "#1DB954"
_COLOR_ERROR = "#FF6B6B"
_COLOR_MUTED = "#888888"


class App(ctk.CTk):
    def __init__(
        self,
        spotify: SpotifyClient,
        on_submit: Callable[[TrackInfo, int, str], None],
        get_existing_review: Callable[[TrackInfo], tuple[int, str] | None],
    ):
        super().__init__()

        self.title("Spotify Album Reviewer")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)

        self._spotify = spotify
        self._on_submit_cb = on_submit
        self._get_existing_review = get_existing_review
        self._current_track: TrackInfo | None = None

        self._build_ui()
        self._poll_spotify()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # Cover art
        self._cover = CoverArtLabel(self, size=200)
        self._cover.grid(row=0, column=0, pady=(28, 14))

        # Song title
        self._title_label = ctk.CTkLabel(
            self,
            text="Nothing playing",
            font=ctk.CTkFont(size=19, weight="bold"),
            wraplength=WINDOW_WIDTH - 48,
        )
        self._title_label.grid(row=1, column=0, padx=24)

        # Artist · Album
        self._meta_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=_COLOR_MUTED,
            wraplength=WINDOW_WIDTH - 48,
        )
        self._meta_label.grid(row=2, column=0, padx=24, pady=(6, 20))

        # Rating row: label + stars + "X/10"
        rating_row = ctk.CTkFrame(self, fg_color="transparent")
        rating_row.grid(row=3, column=0)

        ctk.CTkLabel(rating_row, text="Rating", font=ctk.CTkFont(size=13)).pack(
            side="left", padx=(0, 10)
        )
        self._stars = StarRating(rating_row, command=self._on_rating_change)
        self._stars.pack(side="left")
        self._rating_text = ctk.CTkLabel(
            rating_row,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=_COLOR_MUTED,
            width=44,
        )
        self._rating_text.pack(side="left", padx=(10, 0))

        # Notes label + textbox
        ctk.CTkLabel(
            self, text="Notes", font=ctk.CTkFont(size=13), anchor="w"
        ).grid(row=4, column=0, sticky="w", padx=24, pady=(20, 4))

        self._notes = ctk.CTkTextbox(
            self, height=150, font=ctk.CTkFont(size=13), wrap="word"
        )
        self._notes.grid(row=5, column=0, sticky="ew", padx=24)

        # Submit button
        self._submit_btn = ctk.CTkButton(
            self,
            text="Submit Review",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._handle_submit,
        )
        self._submit_btn.grid(row=6, column=0, pady=20)

        # Status line
        self._status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color=_COLOR_MUTED
        )
        self._status_label.grid(row=7, column=0, pady=(0, 12))

    # ------------------------------------------------------------------ #
    # Spotify polling
    # ------------------------------------------------------------------ #

    def _poll_spotify(self) -> None:
        def fetch():
            try:
                track = self._spotify.get_current_track()
                self.after(0, self._apply_poll_result, track, None)
            except Exception as exc:
                self.after(0, self._apply_poll_result, None, exc)

        threading.Thread(target=fetch, daemon=True).start()
        self.after(POLL_INTERVAL_MS, self._poll_spotify)

    def _apply_poll_result(self, track: TrackInfo | None, exc: Exception | None) -> None:
        if exc is not None:
            self._set_status(f"Spotify error: {exc}", error=True)
            return
        if track is None and self._current_track is not None:
            self._show_idle()
        elif track is not None and (
            self._current_track is None
            or track.track_id != self._current_track.track_id
        ):
            self._on_track_changed(track)

    def _on_track_changed(self, track: TrackInfo) -> None:
        self._current_track = track
        self._title_label.configure(text=track.track_name)
        self._meta_label.configure(text=f"{track.artist}  ·  {track.album_name}")
        self._cover.load_url(track.cover_url)
        self._reset_form()
        self._set_status("")

        existing = self._get_existing_review(track)
        if existing:
            rating, notes = existing
            self._stars.set(rating)
            self._rating_text.configure(text=f"{rating}/10")
            if notes:
                self._notes.insert("1.0", notes)

    def _show_idle(self) -> None:
        self._current_track = None
        self._title_label.configure(text="Nothing playing")
        self._meta_label.configure(text="")
        self._cover.show_placeholder()
        self._reset_form()
        self._set_status("")

    # ------------------------------------------------------------------ #
    # Form helpers
    # ------------------------------------------------------------------ #

    def _reset_form(self) -> None:
        self._stars.reset()
        self._rating_text.configure(text="")
        self._notes.delete("1.0", "end")

    def _on_rating_change(self, value: int) -> None:
        self._rating_text.configure(text=f"{value}/10" if value else "")

    def _handle_submit(self) -> None:
        if not self._current_track:
            self._set_status("Nothing is playing.", error=True)
            return

        rating = self._stars.get()
        if not rating:
            self._set_status("Please select a rating first.", error=True)
            return

        notes = self._notes.get("1.0", "end").strip()
        track = self._current_track

        self._submit_btn.configure(state="disabled")
        self._set_status("Saving…")

        def save():
            try:
                self._on_submit_cb(track, rating, notes)
                self.after(0, self._on_save_done, None)
            except Exception as exc:
                self.after(0, self._on_save_done, exc)

        threading.Thread(target=save, daemon=True).start()

    def _on_save_done(self, exc: Exception | None) -> None:
        self._submit_btn.configure(state="normal")
        if exc is not None:
            self._set_status(f"Error saving: {exc}", error=True)
        else:
            self._set_status("Review saved!")

    def _set_status(self, msg: str, *, error: bool = False) -> None:
        color = _COLOR_ERROR if error else _COLOR_SUCCESS
        self._status_label.configure(
            text=msg, text_color=color if msg else _COLOR_MUTED
        )
