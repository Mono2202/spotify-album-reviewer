from spotify_client import SpotifyClient
from obsidian_writer import ObsidianWriter
from gui.app import App


def main() -> None:
    spotify = SpotifyClient()
    writer = ObsidianWriter(spotify)

    app = App(
        spotify=spotify,
        on_submit=writer.upsert_review,
        get_existing_review=writer.get_existing_review,
    )
    app.mainloop()


if __name__ == "__main__":
    main()
