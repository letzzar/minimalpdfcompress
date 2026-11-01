# styles.py
import tkinter as tk
from tkinter import ttk
import logging
import sys

if sys.platform == "win32":
    FONT_FAMILY = "Segoe UI"
elif sys.platform == "darwin":
    FONT_FAMILY = "Helvetica"
else:
    FONT_FAMILY = "DejaVu Sans"

# Three background levels instead of outlines. Depth comes from the step
# between them, which is how current desktop interfaces separate regions; a
# 1px rectangle around every card is what made this look dated.
PALETTES = {
    'light': {
        "BG": "#f4f5f7", "WIDGET_BG": "#ffffff", "ELEVATED": "#eceef1",
        "WIDGET_HOVER": "#e3e6ea",
        "ACCENT": "#2563eb", "ACCENT_HOVER": "#1d4ed8", "ACCENT_SOFT": "#dbe6fe",
        "TEXT": "#15171a", "MUTED": "#5f6672",
        "DISABLED": "#b2b8c0", "DISABLED_BG": "#e6e8eb",
        "SCROLL_THUMB": "#c6cad0", "SCROLL_THUMB_HOVER": "#aab0b8",
        "BORDER": "#dfe2e6", "SUCCESS": "#1a9b50", "ERROR": "#d93b3b"
    },
    'dark': {
        "BG": "#141518", "WIDGET_BG": "#1d1f23", "ELEVATED": "#26292e",
        "WIDGET_HOVER": "#303439",
        "ACCENT": "#3b82f6", "ACCENT_HOVER": "#60a5fa", "ACCENT_SOFT": "#1e3356",
        "TEXT": "#e8eaed", "MUTED": "#9aa0a6",
        "DISABLED": "#6b7076", "DISABLED_BG": "#2a2d31",
        "SCROLL_THUMB": "#3d4248", "SCROLL_THUMB_HOVER": "#4e545b",
        "BORDER": "#2c2f34", "SUCCESS": "#3ec46d", "ERROR": "#ff5a5a"
    }
}

# One type scale, so headings stop being whatever size each tab felt like.
FONT_TITLE = 15
FONT_HEADING = 13
FONT_BODY = 10
FONT_SMALL = 9


def apply_theme(root, mode='dark'):
    style = ttk.Style(root)
    colors = PALETTES.get(mode, PALETTES['dark'])

    try:
        style.theme_use('clam')
    except tk.TclError:
        logging.warning("The 'clam' theme is not available.")
        return colors

    style.configure('.', background=colors["BG"], foreground=colors["TEXT"], borderwidth=0,
                    fieldbackground=colors["WIDGET_BG"], font=(FONT_FAMILY, FONT_BODY),
                    relief='flat', highlightthickness=0)
    style.map('.', foreground=[('disabled', colors["DISABLED"])],
              fieldbackground=[('disabled', colors["BG"])],
              background=[('disabled', colors["BG"])])

    # Buttons
    style.layout('TButton', [('Button.padding', {'sticky': 'nswe', 'children': [('Button.label', {'sticky': 'nswe'})]})])
    style.configure('TButton', padding=(14, 7), background=colors["ELEVATED"], foreground=colors["TEXT"],
                    font=(FONT_FAMILY, FONT_BODY), highlightthickness=0, borderwidth=0, relief='flat')
    style.map('TButton', background=[('pressed', colors["WIDGET_BG"]), ('active', colors["WIDGET_HOVER"])])

    style.configure('Accent.TButton', background=colors["ACCENT"], foreground="#ffffff",
                    font=(FONT_FAMILY, 12, 'bold'), padding=(16, 10))
    style.map('Accent.TButton',
              background=[('disabled', colors["DISABLED_BG"]), ('pressed', colors["ACCENT_HOVER"]),
                          ('active', colors["ACCENT_HOVER"])],
              foreground=[('disabled', colors["DISABLED"]), ('pressed', "#ffffff"), ('active', "#ffffff")])

    # Secondary buttons are filled rather than outlined: an outline next to a
    # borderless card reads as a stray rectangle.
    style.configure('Outline.TButton', background=colors["ELEVATED"], foreground=colors["ACCENT"],
                    borderwidth=0, highlightthickness=0, padding=(12, 6), font=(FONT_FAMILY, FONT_SMALL))
    style.map('Outline.TButton',
              background=[('active', colors["WIDGET_HOVER"]), ('disabled', colors["DISABLED_BG"])],
              foreground=[('active', colors["ACCENT_HOVER"]), ('disabled', colors["DISABLED"])])
    style.configure('Large.Outline.TButton', background=colors["ELEVATED"], foreground=colors["ACCENT"],
                    borderwidth=0, highlightthickness=0, padding=(16, 9), font=(FONT_FAMILY, 11))
    style.map('Large.Outline.TButton',
              background=[('active', colors["WIDGET_HOVER"]), ('disabled', colors["DISABLED_BG"])],
              foreground=[('active', colors["ACCENT_HOVER"]), ('disabled', colors["DISABLED"])])

    # Frames and labels
    style.configure('TFrame', background=colors["BG"])
    style.configure('Card.TFrame', background=colors["WIDGET_BG"], relief='flat', borderwidth=0)
    style.configure('Elevated.TFrame', background=colors["ELEVATED"], relief='flat', borderwidth=0)
    style.configure('AccentBG.TFrame', background=colors["ACCENT"])
    style.configure('TLabel', background=colors["BG"], foreground=colors["TEXT"])
    style.configure('Card.TLabel', background=colors["WIDGET_BG"])
    style.configure('Title.TLabel', background=colors["WIDGET_BG"], foreground=colors["TEXT"],
                    font=(FONT_FAMILY, FONT_TITLE, 'bold'))
    style.configure('Heading.TLabel', background=colors["WIDGET_BG"], foreground=colors["TEXT"],
                    font=(FONT_FAMILY, FONT_HEADING, 'bold'))
    style.configure('Muted.TLabel', background=colors["WIDGET_BG"], foreground=colors["MUTED"],
                    font=(FONT_FAMILY, FONT_SMALL))

    # Inputs: filled, no resting border, accent only on focus.
    style.configure('TEntry', relief='flat', borderwidth=0, padding=9,
                    insertcolor=colors["TEXT"], fieldbackground=colors["ELEVATED"],
                    bordercolor=colors["ELEVATED"], lightcolor=colors["ELEVATED"],
                    darkcolor=colors["ELEVATED"])
    style.map('TEntry',
              fieldbackground=[('readonly', colors["BG"]), ('focus', colors["ELEVATED"])],
              bordercolor=[('focus', colors["ACCENT"])],
              lightcolor=[('focus', colors["ACCENT"])],
              darkcolor=[('focus', colors["ACCENT"])])

    style.configure('TCombobox', relief='flat', borderwidth=0, padding=8,
                    arrowcolor=colors["MUTED"], arrowsize=16,
                    fieldbackground=colors["ELEVATED"], bordercolor=colors["ELEVATED"],
                    lightcolor=colors["ELEVATED"], darkcolor=colors["ELEVATED"])
    style.map('TCombobox',
              bordercolor=[('focus', colors["ACCENT"])],
              arrowcolor=[('active', colors["TEXT"])],
              fieldbackground=[('readonly', colors["ELEVATED"])],
              foreground=[('readonly', colors["TEXT"])])

    style.configure('TProgressbar', relief='flat', pbarrelief='flat', borderwidth=0, thickness=6,
                    troughcolor=colors["ELEVATED"], background=colors["ACCENT"])
    style.layout('TProgressbar', [('Progressbar.trough', {'children': [('Progressbar.pbar', {'sticky': 'nswe'})], 'sticky': 'nswe'})])

    # Tabs: no box around the selected one, just accent text.
    style.configure('TNotebook', background=colors["BG"], borderwidth=0, tabmargins=(2, 4, 2, 0))
    style.configure('TNotebook.Tab', background=colors["BG"], foreground=colors["MUTED"],
                    padding=[16, 9], borderwidth=0, font=(FONT_FAMILY, FONT_BODY, 'bold'))
    style.map('TNotebook.Tab',
              background=[('selected', colors["BG"]), ('active', colors["BG"])],
              foreground=[('selected', colors["ACCENT"]), ('active', colors["TEXT"])],
              expand=[('selected', [0, 0, 0, 0])])

    style.configure('Horizontal.TScale', background=colors["WIDGET_BG"], troughcolor=colors["ELEVATED"],
                    sliderrelief='flat', sliderlength=18, borderwidth=0)
    style.map('Horizontal.TScale', background=[('active', colors["ACCENT_HOVER"]), ('!active', colors["ACCENT"])])

    # Checkbuttons were raw clam squares next to custom toggles; at least make
    # them share the palette and the spacing.
    style.configure('TCheckbutton', background=colors["WIDGET_BG"], foreground=colors["TEXT"],
                    padding=(2, 5), focuscolor=colors["WIDGET_BG"],
                    indicatorcolor=colors["ELEVATED"], indicatorrelief='flat',
                    indicatormargin=(0, 0, 8, 0), font=(FONT_FAMILY, FONT_BODY))
    style.map('TCheckbutton',
              background=[('active', colors["WIDGET_BG"])],
              indicatorcolor=[('selected', colors["ACCENT"]), ('active', colors["WIDGET_HOVER"])],
              foreground=[('disabled', colors["DISABLED"])])

    style.configure('Card.TRadiobutton', background=colors["WIDGET_BG"], foreground=colors["TEXT"],
                    indicatorrelief='flat', indicatormargin=5, indicatordiameter=-1, padding=10,
                    focuscolor=colors["WIDGET_BG"], font=(FONT_FAMILY, FONT_BODY))
    style.map('Card.TRadiobutton',
              background=[('active', colors["ELEVATED"]), ('selected', colors["WIDGET_BG"])],
              foreground=[('selected', colors["ACCENT"])])

    style.layout('Segmented.TRadiobutton', [('Radiobutton.padding', {'sticky': 'nswe', 'children': [('Radiobutton.label', {'sticky': 'nswe'})]})])
    style.configure('Segmented.TRadiobutton', indicatoron=0, relief='flat', padding=(12, 9),
                    background=colors["ELEVATED"], foreground=colors["MUTED"], borderwidth=0,
                    focuscolor=colors["ELEVATED"], font=(FONT_FAMILY, FONT_BODY))
    style.map('Segmented.TRadiobutton',
              background=[('selected', colors["ACCENT"]), ('active', colors["WIDGET_HOVER"])],
              foreground=[('selected', "#ffffff"), ('active', colors["TEXT"])])

    style.layout('Position.TRadiobutton', [('Radiobutton.padding', {'sticky': 'nswe', 'children': [('Radiobutton.indicator', {'sticky': 'nswe'})]})])
    style.configure('Position.TRadiobutton', indicatoron=0, relief='flat', padding=15,
                    background=colors["ELEVATED"], borderwidth=0, focuscolor=colors["ELEVATED"])
    style.map('Position.TRadiobutton',
              background=[('selected', colors["ACCENT"]), ('active', colors["WIDGET_HOVER"])])

    # clam draws a sunken field around a Treeview that no amount of
    # borderwidth=0 removes; dropping it from the layout is the only way.
    style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
    style.configure('Treeview', rowheight=30, background=colors["WIDGET_BG"],
                    fieldbackground=colors["WIDGET_BG"], foreground=colors["TEXT"],
                    relief='flat', borderwidth=0)
    style.map('Treeview', background=[('selected', colors["ACCENT"])], foreground=[('selected', "#ffffff")])
    style.configure('Treeview.Heading', background=colors["WIDGET_BG"], foreground=colors["MUTED"],
                    font=(FONT_FAMILY, FONT_SMALL, 'bold'), relief='flat', borderwidth=0, padding=(6, 8))
    style.map('Treeview.Heading', background=[('active', colors["ELEVATED"])])

    style.configure('Vertical.TScrollbar', background=colors["SCROLL_THUMB"], troughcolor=colors["BG"],
                    borderwidth=0, arrowsize=12, arrowcolor=colors["MUTED"])
    style.map('Vertical.TScrollbar', background=[('active', colors["SCROLL_THUMB_HOVER"])])

    root.option_add('*TCombobox*Listbox.background', colors["ELEVATED"])
    root.option_add('*TCombobox*Listbox.foreground', colors["TEXT"])
    root.option_add('*TCombobox*Listbox.selectBackground', colors["ACCENT"])
    root.option_add('*TCombobox*Listbox.selectForeground', "#ffffff")
    root.option_add('*TCombobox*Listbox.relief', 'flat')
    root.option_add('*TCombobox*Listbox.highlightThickness', 0)
    root.option_add('*TCombobox*Listbox.borderwidth', 0)

    return colors
