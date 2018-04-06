FLASHFOCUS


Simple focus animations for tiling window managers.

When the focused window changes, flashfocus briefly decreases the window
opacity then slowly fades the window back to full opacity to create a flash
effect.

Compatible with all X based window managers (i3, bspwm, awesome-wm, xmonad).

Installation

An active window compositor is required for the effects of flashfocus to be noticeable. If you don’t have one setup already, I recommend compton.

Arch

Install from the Arch User Repository: flashfocus-git

Ubuntu/Debian

    sudo apt-get install libxcb-render0-dev;
    pip install flashfocus


Configuration

Flashfocus should be added to your startup programs. E.g for i3 put the following in your config:

    exec_always --no-startup-id flashfocus

See flashfocus --help for extra configuration options.
