import customtkinter as ctk


class StarRating(ctk.CTkFrame):
    _FILLED = "★"
    _EMPTY = "☆"
    _COLOR_FILLED = "#FFD700"
    _COLOR_HOVER = "#FFA500"
    _COLOR_EMPTY = "#4a4a4a"

    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._rating = 0
        self._hover = 0
        self._command = command
        self._stars: list[ctk.CTkLabel] = []

        for i in range(1, 11):
            lbl = ctk.CTkLabel(
                self,
                text=self._EMPTY,
                font=ctk.CTkFont(size=24),
                text_color=self._COLOR_EMPTY,
                cursor="hand2",
            )
            lbl.grid(row=0, column=i - 1, padx=1)
            lbl.bind("<Enter>", lambda e, n=i: self._on_hover(n))
            lbl.bind("<Leave>", lambda e: self._on_leave())
            lbl.bind("<Button-1>", lambda e, n=i: self._on_click(n))
            self._stars.append(lbl)

        self._label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#aaaaaa",
            width=40,
        )
        self._label.grid(row=0, column=10, padx=(6, 0))

    def _on_hover(self, n: int) -> None:
        self._hover = n
        self._refresh()

    def _on_leave(self) -> None:
        self._hover = 0
        self._refresh()

    def _on_click(self, n: int) -> None:
        self._rating = n
        self._refresh()
        if self._command:
            self._command(self._rating)

    def _refresh(self) -> None:
        active = self._hover if self._hover else self._rating
        for i, lbl in enumerate(self._stars, 1):
            if i <= active:
                color = self._COLOR_HOVER if self._hover else self._COLOR_FILLED
                lbl.configure(text=self._FILLED, text_color=color)
            else:
                lbl.configure(text=self._EMPTY, text_color=self._COLOR_EMPTY)

        if self._hover:
            self._label.configure(text=f"{self._hover}/10")
        elif self._rating:
            self._label.configure(text=f"{self._rating}/10")
        else:
            self._label.configure(text="")

    def get(self) -> int:
        return self._rating

    def set(self, value: int) -> None:
        self._rating = max(0, min(10, value))
        self._hover = 0
        self._refresh()

    def reset(self) -> None:
        self._rating = 0
        self._hover = 0
        self._refresh()
