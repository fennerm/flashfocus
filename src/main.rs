#[macro_use]
extern crate clap;
extern crate i3ipc;
extern crate xcb;

use clap::{App, Arg};
use i3ipc::I3Connection;
use i3ipc::reply::Node;
use xcb::ffi::xproto::xcb_atom_t;
use xcb::xproto;

fn main() {
    let matches = App::new("i3flash")
        .author("Fenner Macrae <fmacrae.dev@gmail.com>")
        .arg(
            Arg::with_name("opacity")
            .short("o")
            .long("opacity")
            .value_name("FLOAT")
            .help("Opacity of window during flash")
            .takes_value(true)
            .validator(is_positive_decimal),
            )
        .arg(
            Arg::with_name("seconds")
            .short("s")
            .long("seconds")
            .value_name("FLOAT")
            .help("Length of the flash in seconds")
            .takes_value(true)
            .validator(is_positive_decimal),
            )
        .get_matches();

    let opacity = value_t!(matches, "opacity", f64);
    let seconds = value_t!(matches, "seconds", f64);

    for arg in vec![opacity, seconds] {
        assert!(arg.is_ok());
    }

    //let setup = x_connection.get_setup();
    //let screen = setup.roots().nth(screen_num as usize).unwrap();

    flash_current_window(&mut i3, x_connection, opacity, seconds);
}

fn get_focus_child(node: Node) -> Option<Node> {
    let target: i64 = node.focus[0];
    for child in node.nodes {
        if child.id == target {
            return Some(child);
        }
    }
    return None;
}

fn get_focused_window_id(i3: &mut I3Connection) -> i64 {
    let mut node: Node = i3.get_tree().unwrap();
    loop {
        node = get_focus_child(node).unwrap();
        if node.focused {
            return node.id;
        }
    }
}

fn get_window_opacity_atom(xorg: &xcb::Connection) -> xcb_atom_t {
    let opacity_cookie = xproto::intern_atom(
        &xorg,
        false,
        &"_NET_WM_WINDOW_OPACITY",
        );
    fdsf

        return opacity_cookie.get_reply().unwrap().atom();
}

fn flash_current_window(
    i3: &mut I3Connection,
    xorg: &xcb::Connection,
    opacity: f64,
    seconds: f64,
    ) {
    let opacity_atom: xcb_atom_t = get_window_opacity_atom(&xorg);
    let focused_window_id: i64 = get_focused_window_id(&mut i3);
    let window: xproto::Window = focused_window_id as u32;
    let long_offset: u32 = 1;
    let long_length: u32 = 2;

    // let property_cookie = xproto::get_property(
    //     &xorg,
    //     false,
    //     window,
    //     opacity_atom,
    //     ATOM_CARDINAL,
    //     long_offset,
    //     long_length
    // );

    xproto::change_property(
        &xorg,
        32,
        window,
        opacity_atom,
        xproto::ATOM_CARDINAL,
        32,
        &[opacity],
        );
}

fn is_positive_decimal(x: String) -> Result<(), String> {
    let decimal: f64 = x.parse().unwrap();
    if decimal < 1.0 && decimal > 0.0 {
        return Ok(());
    }
    Err(String::from("Input is not a valid decimal"))
}
