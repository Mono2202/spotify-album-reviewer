from __future__ import annotations

import asyncio
from typing import Callable

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Label, TextArea

from spotify_client import SpotifyClient, TrackInfo

POLL_INTERVAL = 5  # seconds

_FILLED = "★"
_EMPTY = "☆"


class StarRating(Widget):
    """Clickable 10-star rating widget."""

    DEFAULT_CSS = """
    StarRating {
        height: 1;
        width: auto;
    }
    """

    value: reactive[int] = reactive(0)

    def render(self) -> str:
        stars = _FILLED * self.value + _EMPTY * (10 - self.value)
        label = f"  {self.value}/10" if self.value else "  -/10"
        return stars + label

    def on_click(self, event) -> None:
        clicked = event.x + 1
        if 1 <= clicked <= 10:
            self.value = 0 if self.value == clicked else clicked

    def get(self) -> int:
        return self.value

    def set(self, value: int) -> None:
        self.value = value

    def reset(self) -> None:
        self.value = 0


class TUIApp(App[None]):
    """Terminal UI for Spotify Album Reviewer."""

    TITLE = "Spotify Album Reviewer"

    CSS = """
    Screen {
        align: center top;
    }

    #panel {
        width: 62;
        border: round $primary;
        padding: 1 2;
        margin-top: 1;
    }

    #track-title {
        text-style: bold;
        width: 100%;
    }

    #track-meta {
        color: $text-disabled;
        margin-bottom: 1;
    }

    #rating-row {
        height: 1;
        margin-bottom: 1;
    }

    #rating-label {
        width: 9;
    }

    TextArea {
        height: 8;
        margin-bottom: 1;
    }

    Button {
        width: 100%;
    }

    #status {
        color: $success;
        text-align: center;
        height: 1;
        margin-top: 1;
    }

    #status.error {
        color: $error;
    }
    """

    def __init__(
        self,
        spotify: SpotifyClient,
        on_submit: Callable[[TrackInfo, int, str], None],
        get_existing_review: Callable[[TrackInfo], tuple[int, str] | None],
        initial_track: TrackInfo | None = None,
    ):
        super().__init__()
        self._spotify = spotify
        self._on_submit_cb = on_submit
        self._get_existing_review = get_existing_review
        self._current_track = initial_track

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="panel"):
            yield Label("Nothing playing", id="track-title")
            yield Label("", id="track-meta")
            with Horizontal(id="rating-row"):
                yield Label("Rating  ", id="rating-label")
                yield StarRating(id="stars")
            yield Label("Notes", id="notes-label")
            yield TextArea(id="notes")
            yield Button("Submit Review", id="submit", variant="success")
            yield Label("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        if self._current_track is not None:
            self._on_track_changed(self._current_track)
        self.set_interval(POLL_INTERVAL, self._poll_spotify)

    async def _poll_spotify(self) -> None:
        try:
            track = await asyncio.to_thread(self._spotify.get_current_track)
            if track is None and self._current_track is not None:
                self._show_idle()
            elif track is not None and (
                self._current_track is None
                or track.track_id != self._current_track.track_id
            ):
                self._on_track_changed(track)
        except Exception as exc:
            self._set_status(f"Spotify error: {exc}", error=True)

    def _on_track_changed(self, track: TrackInfo) -> None:
        self._current_track = track
        self.query_one("#track-title", Label).update(track.track_name)
        self.query_one("#track-meta", Label).update(f"{track.artist}  ·  {track.album_name}")
        self._reset_form()
        self._set_status("")

        existing = self._get_existing_review(track)
        if existing:
            rating, notes = existing
            self.query_one("#stars", StarRating).set(rating)
            if notes:
                self.query_one("#notes", TextArea).load_text(notes)

    def _show_idle(self) -> None:
        self._current_track = None
        self.query_one("#track-title", Label).update("Nothing playing")
        self.query_one("#track-meta", Label).update("")
        self._reset_form()
        self._set_status("")

    def _reset_form(self) -> None:
        self.query_one("#stars", StarRating).reset()
        self.query_one("#notes", TextArea).load_text("")

    @on(Button.Pressed, "#submit")
    async def handle_submit(self) -> None:
        if not self._current_track:
            self._set_status("Nothing is playing.", error=True)
            return

        rating = self.query_one("#stars", StarRating).get()
        if not rating:
            self._set_status("Please select a rating first.", error=True)
            return

        notes = self.query_one("#notes", TextArea).text.strip()
        track = self._current_track

        btn = self.query_one("#submit", Button)
        btn.disabled = True
        self._set_status("Saving…")

        try:
            await asyncio.to_thread(self._on_submit_cb, track, rating, notes)
            self._set_status("Review saved!")
        except Exception as exc:
            self._set_status(f"Error saving: {exc}", error=True)
        finally:
            btn.disabled = False

    def _set_status(self, msg: str, *, error: bool = False) -> None:
        status = self.query_one("#status", Label)
        status.update(msg)
        if error:
            status.add_class("error")
        else:
            status.remove_class("error")
