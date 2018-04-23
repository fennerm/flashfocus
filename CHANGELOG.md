# Changelog

## [Unreleased]

- Ability to exclude windows by ID or class
- Ability to apply different flash rules to tabs/new windows/closed windows
- More finetuned control over flash animation
- Better support for using flashfocus as a library to produce custom animation scripts.

## [0.3.0] - April 22nd, 2018

- Added a basic configuration file.
- Deprecate --opacity parameter, --flash-opacity should be used instead.

## [0.2.1] - April 14th, 2018

### Fixed
- Uncaught WindowError when window closed during flash.

## [0.2.0] - April 11th, 2018

### Added
- Ability to flash window on keybinding with flash_window command.

### Changed
- Window conflict behavior changed. Previously, if two flash requests were made for a single window within the flash interval, the second request would be ignored. Now the first request is just restarted, which makes the program feel more responsive.
- Removed tendo dependency.
- Added the default-opacity parameter.

### Fixed

- Division error in the python2 version which lead to 1ms flashes by default.

