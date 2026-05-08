import os
from dataclasses import dataclass

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

SCOPES = "user-read-currently-playing user-read-playback-state"


@dataclass
class TrackInfo:
    track_id: str
    track_name: str
    track_number: int
    artist: str
    album_name: str
    album_id: str
    cover_url: str
    release_year: int


@dataclass
class AlbumTrack:
    track_number: int
    track_name: str
    track_id: str


class SpotifyClient:
    def __init__(self):
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

        if not all([client_id, client_secret, redirect_uri]):
            raise EnvironmentError(
                "Missing Spotify credentials. Set SPOTIFY_CLIENT_ID, "
                "SPOTIFY_CLIENT_SECRET, and SPOTIFY_REDIRECT_URI in .env"
            )

        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=SCOPES,
            open_browser=True,
        )
        self._sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_current_track(self) -> TrackInfo | None:
        """Return info about the currently playing track, or None if nothing is playing."""
        result = self._sp.current_user_playing_track()

        if not result or not result.get("is_playing"):
            return None

        item = result.get("item")
        if not item or item.get("type") != "track":
            return None

        album = item["album"]
        artists = item["artists"]
        images = album.get("images", [])

        cover_url = images[0]["url"] if images else ""
        release_year = self._parse_year(album.get("release_date", ""))
        artist = ", ".join(a["name"] for a in artists)

        return TrackInfo(
            track_id=item["id"],
            track_name=item["name"],
            track_number=item["track_number"],
            artist=artist,
            album_name=album["name"],
            album_id=album["id"],
            cover_url=cover_url,
            release_year=release_year,
        )

    def get_album_tracks(self, album_id: str) -> list[AlbumTrack]:
        """Return all tracks for an album in order."""
        tracks: list[AlbumTrack] = []
        results = self._sp.album_tracks(album_id, limit=50)

        while results:
            for item in results["items"]:
                tracks.append(AlbumTrack(
                    track_number=item["track_number"],
                    track_name=item["name"],
                    track_id=item["id"],
                ))
            results = self._sp.next(results) if results.get("next") else None

        tracks.sort(key=lambda t: t.track_number)
        return tracks

    def get_album_info(self, album_id: str) -> dict:
        """Return album-level metadata (artist, release year, cover url)."""
        album = self._sp.album(album_id)
        images = album.get("images", [])
        artists = album.get("artists", [])

        return {
            "album_name": album["name"],
            "artist": ", ".join(a["name"] for a in artists),
            "release_year": self._parse_year(album.get("release_date", "")),
            "cover_url": images[0]["url"] if images else "",
        }

    @staticmethod
    def _parse_year(release_date: str) -> int:
        """Extract the year from a Spotify release_date string (YYYY, YYYY-MM, or YYYY-MM-DD)."""
        try:
            return int(release_date.split("-")[0])
        except (ValueError, IndexError, AttributeError):
            return 0
