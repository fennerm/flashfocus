# flashfocus

Simple focus animations for tiling window managers.

![Demo gif](demo/demo.gif)

<br>

When the focused window changes, flashfocus briefly decreases the window
opacity then slowly fades the window back to full opacity to create a flash
effect.

Compatible with all X based window managers (i3, bspwm, awesome-wm, xmonad...).

## Installation

An active window compositor is required for the effects of flashfocus to be
noticeable. If you don't have one setup already, I recommend
[compton](https://github.com/chjj/compton).

### Arch

Install from the Arch User Repository: `flashfocus-git`

### Ubuntu/Debian

```
sudo apt-get install libxcb-render0-dev;
pip install flashfocus
```

## Configuration

Flashfocus should be added to your startup programs. E.g for i3 put the
following in your config:

```
exec_always --no-startup-id flashfocus
```

Flashfocus also includes the `flash_window` script for flashing the current window in response to a keybinding. E.g if you'd like to bind to mod+n in i3:

```
bindsym $mod+n exec --no-startup-id flash_window
```

See `flashfocus --help` for extra configuration options.

### Tabbed containers in i3

The animations don't work well out of the box for i3 tabs. You'll need to add
the following to your compton config:

```
opacity-rule = [
    "0:_NET_WM_STATE@:32a *= '_NET_WM_STATE_HIDDEN'"
];
```

