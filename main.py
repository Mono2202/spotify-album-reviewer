import argparse

from spotify_client import SpotifyClient
from obsidian_writer import ObsidianWriter


def main() -> None:
    parser = argparse.ArgumentParser(description="Spotify Album Reviewer")
    parser.add_argument("--tui", action="store_true", help="Launch the terminal UI instead of the GUI")
    args = parser.parse_args()

    spotify = SpotifyClient()
    writer = ObsidianWriter(spotify)

    if args.tui:
        from tui.app import TUIApp
        TUIApp(
            spotify=spotify,
            on_submit=writer.upsert_review,
            get_existing_review=writer.get_existing_review,
            initial_track=spotify.get_current_track(),
        ).run()
    else:
        from gui.app import App
        App(
            spotify=spotify,
            on_submit=writer.upsert_review,
            get_existing_review=writer.get_existing_review,
        ).mainloop()


if __name__ == "__main__":
    main()
