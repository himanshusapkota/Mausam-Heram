import tkinter as tk
from tkinter import font as tkfont
import threading
import requests
from PIL import Image, ImageTk
from io import BytesIO
from datetime import datetime


API_KEY  = "e6298966eaf88fa69960de882b0c8fa0"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
ICON_URL = "https://openweathermap.org/img/wn/{}@2x.png"


PLACEHOLDER = "Enter city name…"

BG_DARK      = "#0D1B2A"
BG_CARD      = "#1B2A3B"
BG_INPUT     = "#243447"
ACCENT       = "#00C2CB"
ACCENT_HOVER = "#00E5F0"
TEXT_PRIMARY = "#E8F4FD"
TEXT_MUTED   = "#7A9BB5"
TEXT_WARN    = "#FF6B6B"
DIVIDER      = "#1E3448"


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("WeatherNow")
        self.geometry("480x700")
        self.minsize(420, 620)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 480) // 2
        y = (self.winfo_screenheight() - 700) // 2
        self.geometry(f"+{x}+{y}")

        self._load_fonts()

        self._icon_image = None
        self._after_id   = None

        self._build_ui()
        self._start_clock()

        self.bind("<Return>", lambda _: self._fetch_weather_threaded())

    # ------------------------------------------------------------------ fonts
    def _load_fonts(self):
        self.font_title     = tkfont.Font(family="Helvetica", size=22, weight="bold")
        self.font_temp      = tkfont.Font(family="Helvetica", size=64, weight="bold")
        self.font_city      = tkfont.Font(family="Helvetica", size=18, weight="bold")
        self.font_label     = tkfont.Font(family="Helvetica", size=11)
        self.font_value     = tkfont.Font(family="Helvetica", size=13, weight="bold")
        self.font_muted     = tkfont.Font(family="Helvetica", size=10)
        self.font_input     = tkfont.Font(family="Helvetica", size=13)
        self.font_btn       = tkfont.Font(family="Helvetica", size=12, weight="bold")
        self.font_condition = tkfont.Font(family="Helvetica", size=14)

    # ------------------------------------------------------------------- UI
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self._build_header()
        self._build_search()
        self._build_weather_card()
        self._build_detail_grid()
        self._build_status_bar()

    def _build_header(self):
        header = tk.Frame(self, bg=BG_DARK, pady=18)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        tk.Label(
            header, text="🌤  Mausam Heram",
            font=self.font_title,
            bg=BG_DARK, fg=ACCENT,
        ).grid(row=0, column=0)

        self.lbl_clock = tk.Label(
            header, text="",
            font=self.font_muted,
            bg=BG_DARK, fg=TEXT_MUTED,
        )
        self.lbl_clock.grid(row=1, column=0, pady=(2, 0))

    def _build_search(self):
        search_frame = tk.Frame(self, bg=BG_DARK, pady=6)
        search_frame.grid(row=1, column=0, sticky="ew", padx=24)
        search_frame.columnconfigure(0, weight=1)

        inner = tk.Frame(search_frame, bg=BG_INPUT, padx=4, pady=4)
        inner.grid(row=0, column=0, sticky="ew")
        inner.columnconfigure(0, weight=1)

        self.entry_city = tk.Entry(
            inner,
            font=self.font_input,
            bg=BG_INPUT, fg=TEXT_PRIMARY,
            insertbackground=ACCENT,
            relief="flat",
            bd=0,
        )
        self.entry_city.grid(row=0, column=0, sticky="ew", padx=(10, 4), ipady=10)

        
        self.entry_city.insert(0, PLACEHOLDER)
        self.entry_city.config(fg=TEXT_MUTED)

        self.entry_city.bind("<FocusIn>",  self._on_entry_focus_in)
        self.entry_city.bind("<FocusOut>", self._on_entry_focus_out)

        self.btn_search = tk.Button(
            inner,
            text="Search",
            font=self.font_btn,
            bg=ACCENT, fg=BG_DARK,
            activebackground=ACCENT_HOVER,
            activeforeground=BG_DARK,
            relief="flat", bd=0,
            padx=18, pady=8,
            cursor="hand2",
            command=self._fetch_weather_threaded,
        )
        self.btn_search.grid(row=0, column=1, padx=(0, 4))

        self.btn_search.bind("<Enter>", lambda _: self.btn_search.config(bg=ACCENT_HOVER))
        self.btn_search.bind("<Leave>", lambda _: self.btn_search.config(bg=ACCENT))

    def _build_weather_card(self):
        self.card = tk.Frame(self, bg=BG_CARD, padx=20, pady=24)
        self.card.grid(row=2, column=0, sticky="ew", padx=24, pady=(18, 0))
        self.card.columnconfigure(0, weight=1)

        self.lbl_icon = tk.Label(self.card, bg=BG_CARD, image="")
        self.lbl_icon.grid(row=0, column=0)

        self.lbl_temp = tk.Label(
            self.card, text="--°C",
            font=self.font_temp,
            bg=BG_CARD, fg=TEXT_PRIMARY,
        )
        self.lbl_temp.grid(row=1, column=0, pady=(0, 4))

        self.lbl_city = tk.Label(
            self.card, text="City, Country",
            font=self.font_city,
            bg=BG_CARD, fg=ACCENT,
        )
        self.lbl_city.grid(row=2, column=0)

        self.lbl_condition = tk.Label(
            self.card, text="—",
            font=self.font_condition,
            bg=BG_CARD, fg=TEXT_MUTED,
        )
        self.lbl_condition.grid(row=3, column=0, pady=(4, 0))

    def _build_detail_grid(self):
        details_outer = tk.Frame(self, bg=BG_DARK)
        details_outer.grid(row=3, column=0, sticky="ew", padx=24, pady=18)
        details_outer.columnconfigure(0, weight=1)
        details_outer.columnconfigure(1, weight=1)

        tiles = [
            ("💧", "Humidity",   "lbl_humidity"),
            ("💨", "Wind Speed", "lbl_wind"),
            ("🌡",  "Feels Like", "lbl_feels"),
            ("👁",  "Visibility", "lbl_visibility"),
        ]

        GAP = 8   # pixel gap between the two columns

        for i, (icon, label, attr) in enumerate(tiles):
            row, col = divmod(i, 2)

            # FIX 3 & 4: Correct padx/pady so the inter-column gap actually
            # appears.  Previous code had `0 if col else 0` (always 0) for the
            # left pad and applied the bottom pad on every row including the last.
            px = (0, GAP // 2) if col == 0 else (GAP // 2, 0)
            py = (0, GAP)      if row == 0 else (0, 0)

            tile = tk.Frame(details_outer, bg=BG_CARD, padx=16, pady=14)
            tile.grid(row=row, column=col, sticky="nsew", padx=px, pady=py)

            lbl_header = tk.Frame(tile, bg=BG_CARD)
            lbl_header.pack(anchor="w")

            tk.Label(
                lbl_header, text=icon,
                font=self.font_label,
                bg=BG_CARD, fg=ACCENT,
            ).pack(side="left")
            tk.Label(
                lbl_header, text=f"  {label}",
                font=self.font_muted,
                bg=BG_CARD, fg=TEXT_MUTED,
            ).pack(side="left")

            value_lbl = tk.Label(
                tile, text="—",
                font=self.font_value,
                bg=BG_CARD, fg=TEXT_PRIMARY,
            )
            value_lbl.pack(anchor="w", pady=(6, 0))
            setattr(self, attr, value_lbl)

    def _build_status_bar(self):
        self.lbl_status = tk.Label(
            self,
            text="Type a city name and press Search or Enter.",
            font=self.font_muted,
            bg=BG_DARK, fg=TEXT_MUTED,
            wraplength=400,
        )
        self.lbl_status.grid(row=4, column=0, pady=(0, 18))

    # --------------------------------------------------------- entry helpers
    def _on_entry_focus_in(self, _event):
        # FIX 2: Compare against PLACEHOLDER (previously compared "Enter city
        # name..." with three ASCII dots while the inserted text used the
        # Unicode ellipsis "…", so this branch never executed).
        if self.entry_city.get() == PLACEHOLDER:
            self.entry_city.delete(0, "end")
            self.entry_city.config(fg=TEXT_PRIMARY)

    def _on_entry_focus_out(self, _event):
        if not self.entry_city.get().strip():
            # FIX 1 (continued): Use PLACEHOLDER constant.
            self.entry_city.insert(0, PLACEHOLDER)
            self.entry_city.config(fg=TEXT_MUTED)

    # ----------------------------------------------------------------- clock
    def _start_clock(self):
        self._tick()

    def _tick(self):
        now = datetime.now().strftime("%A, %d %B %Y  •  %I:%M:%S %p")
        self.lbl_clock.config(text=now)
        self._after_id = self.after(1000, self._tick)

    # --------------------------------------------------------------- network
    def _fetch_weather_threaded(self):
        city = self.entry_city.get().strip()

        # FIX 1 (continued): Guard uses PLACEHOLDER constant.
        if not city or city == PLACEHOLDER:
            self._set_status("Please enter a city name.", error=True)
            return

        self.btn_search.config(state="disabled", text="…")
        self._set_status("Fetching weather data…", error=False)

        thread = threading.Thread(
            target=self._fetch_weather, args=(city,), daemon=True
        )
        thread.start()

    def _fetch_weather(self, city: str):
        try:
            params = {
                "q":     city,
                "appid": API_KEY,
                "units": "metric",
            }
            response = requests.get(BASE_URL, params=params, timeout=10)

            if response.status_code == 401:
                self.after(0, self._show_error, "Invalid API key. Check your OpenWeatherMap key.")
                return
            if response.status_code == 404:
                self.after(0, self._show_error, f'City "{city}" not found. Try again.')
                return
            if response.status_code != 200:
                self.after(0, self._show_error, f"API error {response.status_code}. Please try again.")
                return

            data = response.json()

            icon_code  = data["weather"][0]["icon"]
            icon_image = self._download_icon(icon_code)

            self.after(0, self._update_ui, data, icon_image)

        except requests.exceptions.ConnectionError:
            self.after(0, self._show_error, "No internet connection. Check your network.")
        except requests.exceptions.Timeout:
            self.after(0, self._show_error, "Request timed out. Try again.")
        except Exception as exc:
            self.after(0, self._show_error, f"Unexpected error: {exc}")

    def _download_icon(self, icon_code: str):
        try:
            url  = ICON_URL.format(icon_code)
            resp = requests.get(url, timeout=8)
            img  = Image.open(BytesIO(resp.content)).resize((100, 100), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    # ----------------------------------------------------------- UI updates
    def _update_ui(self, data: dict, icon_image):
        temp      = round(data["main"]["temp"])
        feels     = round(data["main"]["feels_like"])
        humidity  = data["main"]["humidity"]
        condition = data["weather"][0]["description"].title()
        wind_kmh  = round(data["wind"]["speed"] * 3.6, 1)
        city_name = data["name"]
        country   = data["sys"]["country"]
        vis_m     = data.get("visibility", None)
        vis_km    = f"{vis_m / 1000:.1f} km" if vis_m is not None else "N/A"

        self.lbl_temp.config(text=f"{temp}°C")
        self.lbl_city.config(text=f"{city_name}, {country}")
        self.lbl_condition.config(text=condition)

        if icon_image:
            self._icon_image = icon_image           # prevent GC
            self.lbl_icon.config(image=self._icon_image)
        else:
            # FIX 5: Passing image="" raises a tkinter warning; only clear it
            # when there is actually something to clear.
            if self._icon_image is not None:
                self.lbl_icon.config(image="")
                self._icon_image = None

        self.lbl_humidity.config(text=f"{humidity}%")
        self.lbl_wind.config(text=f"{wind_kmh} km/h")
        self.lbl_feels.config(text=f"{feels}°C")
        self.lbl_visibility.config(text=vis_km)

        updated_at = datetime.now().strftime("%I:%M %p")
        self._set_status(f"Last updated at {updated_at}.", error=False)

      
        self._restore_button()

    def _show_error(self, message: str):
        self._set_status(message, error=True)
        self._restore_button()

    def _restore_button(self):
        
        self.btn_search.config(state="normal", text="Search")

    def _set_status(self, message: str, *, error: bool):
        colour = TEXT_WARN if error else TEXT_MUTED
        self.lbl_status.config(text=message, fg=colour)

    # ---------------------------------------------------------------- close
    def destroy(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        super().destroy()


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()