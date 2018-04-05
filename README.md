# flashfocus

Simple focus animations for tiling window managers.

<video width="800" poster="demo/demo.jpg" height="450" controls preload>
  <source src="demo/demo.mp4"></source>
  <source src="demo/demo.webm"></source>
</video>

<br>

Compatible with all X based window managers (i3, bspwm, awesome-wm, xmonad).

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

## Configuration`

Flashfocus should be added to your startup programs. E.g for i3 put the
following in your config:

```
exec_always --no-startup-id flashfocus
```


See `flashfocus --help` for extra configuration options.
