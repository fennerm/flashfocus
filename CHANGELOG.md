# Changelog

## [Unreleased]

- Ability to apply different flash rules to tabs/new windows/closed windows
- More finetuned control over flash animation

## [1.1.1] - Oct 13, 2018 
- Added flash-lone-windows CLI option.

## [1.1.0] - Oct 13, 2018

- Implemented flash-lone-windows configuration option (see default config file
  for details).

## [1.0.9] - Aug 2nd, 2018

- Fixed bug which broke window flashing when transparent windows are also
  active **#18**

## [1.0.8] - Jul 17th, 2018
- Fixed uncaught AttributeError when switching workspaces **#17**

## [1.0.7] - May 27th, 2018
- Fixed incorrect method call in Flasher

## [1.0.6] - May 27th, 2018
- Improved exception handling with nonexistant windows **#15**

## [1.0.5] - May 24th, 2018
- Added MANIFEST file for package data due to bug which caused default config to not be created **#14**

## [1.0.3 - 1.0.4] - May 16th, 2018
- Fixed bug when Xutil function returns None

## [1.0.1] - May 12th, 2018
- Fixed bug in presetting opacity

## [1.0.0] - May 9th, 2018
- Flash parameters can now be set for specific window class/ids. Regexes are supported.
- A faster alternative to the flash_window script (`nc_flash_window`) was added which requires openbsd-netcat. This script is not fully supported yet, so don't be surprised if it disappears later.
- Added a new `flash-on-focus` parameter for windows which user does not want to flash on focus but still needs the ability to flash on request.


## [0.3.5] - April 24th, 2018
- Improved logging output


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

