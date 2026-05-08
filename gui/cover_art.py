import io
import threading

import requests
from PIL import Image
import customtkinter as ctk

_PLACEHOLDER_COLOR = "#2a2a2a"


class CoverArtLabel(ctk.CTkLabel):
    def __init__(self, master, size: int = 200, **kwargs):
        self._size = size
        self._ctk_image: ctk.CTkImage | None = None
        super().__init__(master, text="", **kwargs)
        self.show_placeholder()

    def load_url(self, url: str) -> None:
        """Fetch and display cover art from a URL. Runs in a background thread."""
        threading.Thread(target=self._fetch, args=(url,), daemon=True).start()

    def show_placeholder(self) -> None:
        placeholder = Image.new("RGB", (self._size, self._size), color=_PLACEHOLDER_COLOR)
        self._apply(placeholder)

    def _fetch(self, url: str) -> None:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            self.after(0, lambda: self._apply(img))
        except Exception:
            pass  # keep current image on failure

    def _apply(self, img: Image.Image) -> None:
        img = img.resize((self._size, self._size), Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(self._size, self._size))
        self._ctk_image = ctk_img  # prevent garbage collection
        self.configure(image=ctk_img)
