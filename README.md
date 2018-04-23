# flashfocus

Simple focus animations for tiling window managers.

![Demo gif](demo/demo.gif)

<br>

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

## Quickstart

#### Compton setup

The following must be present in your compton config file:

```
detect-client-opacity = true;
```

If you use i3, the following is also required for flashfocus to work with tabbed containers:

```
opacity-rule = [
    "0:_NET_WM_STATE@:32a *= '_NET_WM_STATE_HIDDEN'"
];
```

#### Running flashfocus

Flashfocus should be added to your startup programs. E.g for i3 place the
following in your config:

```
exec_always --no-startup-id flashfocus
```

The `flash_window` script can be used to flash the current window on key-press. E.g if you'd like to bind to mod+n in i3:

```
bindsym $mod+n exec --no-startup-id flash_window
```


## Configuration

Flashfocus can be configured via its config file or with command line parameters.

The config file is searched for in the following locations:
1. $XDG_CONFIG_HOME/flashfocus/flashfocus.yml
2. ~/.config/flashfocus/flashfocus.yml
3. ~/.flashfocus.yml

When flashfocus is first run it creates a default config file in 1. or 2. Documentation of all configuration options is present in the config file. More configuration options coming soon!
