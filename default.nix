{pkgs ? import <nixpkgs> {}}: let
  python = pkgs.python313;
in
  python.pkgs.buildPythonPackage rec {
    pname = "flashfocus";
    version = "2.4.1";

    src = ./src; # your repo source

    propagatedBuildInputs = with python.pkgs; [
      cffi # latest version (2.0+)
      setuptools
      xcffib # X11 bindings
    ];

    meta = with pkgs.lib; {
      description = "Focus animation daemon for X11/Sway/i3/tiling WMs";
      license = licenses.mit;
      maintainers = with maintainers; [];
    };
  }
