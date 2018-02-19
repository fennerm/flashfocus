#!/usr/bin/env python
'''Flash i3 windows on focus'''
import logging as log
import os
from subprocess import (
    call,
    PIPE,
    Popen,
)
import sys
from time import sleep

import click
from click_default_group import DefaultGroup
import i3ipc

# 0xffffffff
MAX_OPACITY = 4294967295

log.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

log.info('Establishing connection with i3...')
i3 = i3ipc.Connection()
log.info('Connection established')


@click.group(cls=DefaultGroup, default='flash_focus', default_if_no_args=True)
@click.option('--opacity', '-o', default=0.2,
              help='Opacity of the window during a flash')
@click.option('--time', '-t', default=200, help='Flash time interval (in ms)')
@click.pass_context
def cli(context, opacity, time):
    '''Click command line interface group'''
    context.obj['opacity'] = format_opacity(opacity)
    context.obj['time'] = time / 1000


@cli.command()
@click.pass_context
def flash(context):
    '''Flash the currently focused window'''
    focused_window_id = str(i3.get_tree().find_focused().window)
    flash_window(focused_window_id,
                 flash_opacity=context.obj['opacity'],
                 time=context.obj['time'])


@cli.command()
@click.pass_context
def flash_focus(context):
    '''Wait for changes in focus and flash windows'''

    def on_window_focus(_, event):
        '''Change in focus hook'''
        x_window_id = str(event.container.window)
        log.info('Flashing window')
        flash_window(x_window_id,
                     flash_opacity=context.obj['opacity'],
                     time=context.obj['time'])

        log.info('Waiting for focus event...')

    i3.on('window::focus', on_window_focus)

    log.info('Waiting for focus event...')
    i3.main()


def format_opacity(opacity):
    '''Convert the opacity paramater from decimal to int'''
    if opacity > 1 or opacity < 0:
        sys.exit("Invalid opacity argument, expected a decimal")

    return int(opacity * MAX_OPACITY)


def get_window_opacity(x_window_id):
    '''Get the opacity of a window from its Xorg window id'''
    p = Popen(['xprop', '-id', x_window_id], stdout=PIPE)

    for line in p.stdout:
        line = line.decode('utf-8').strip()
        if line.startswith('_NET_WM_WINDOW_OPACITY'):
            opacity = line.split(' ')[-1]
            log.info('Window %s has opacity = %s', x_window_id, opacity)
            return opacity

    log.info('No opacity defined for window %s', x_window_id)
    return None


def set_opacity(x_window_id, opacity):
    '''Set the opacity of a Xorg window'''
    call(['xprop', '-id', x_window_id, '-f', '_NET_WM_WINDOW_OPACITY', '32c',
          '-set', '_NET_WM_WINDOW_OPACITY', str(opacity)])


def delete_opacity_property(x_window_id):
    '''Delete the _NET_WM_WINDOW_OPACITY property of a Xorg window'''
    call(['xprop', '-id', x_window_id, '-remove', '_NET_WM_WINDOW_OPACITY'])


def flash_window(x_window_id, flash_opacity, time):
    '''Briefly decrease the opacity of a Xorg window'''
    log.info('Flashing window %s...', x_window_id)
    default_opacity = get_window_opacity(x_window_id)

    set_opacity(x_window_id, opacity=flash_opacity)

    log.info('Waiting %sms...', time)
    sleep(time)

    if default_opacity:
        set_opacity(x_window_id, opacity=default_opacity)
    else:
        # Setting opacity to the max wouldn't work if the window has the
        # _NET_WM_OPAQUE_REGION defined, so we just delete the
        # _NET_WM_WINDOW_OPACITY property to return to the default
        delete_opacity_property(x_window_id)


if __name__ == '__main__':
    cli(obj={})
