#![feature(plugin)]
#![cfg_attr(test, plugin(stainless))]
#![recursion_limit = "1024"]

#[macro_use]
extern crate error_chain;

#[macro_use]
extern crate structopt;

extern crate i3ipc;
extern crate xcb;

mod errors {
    error_chain!{}
}

use i3ipc::I3Connection;
use i3ipc::reply::Node;
use structopt::StructOpt;
use xcb::ffi::xproto::xcb_atom_t;
use xcb::xproto;

use errors::*;

#[derive(StructOpt, Debug)]
#[structopt(name = "i3flash")]
struct Opt {
    // The opacity during a flash
    #[structopt(short = "o", long = "opacity", default_value = "0.9")]
    opacity: f64,

    // Length of flash interval in seconds
    #[structopt(short = "s", long = "seconds", default_value = "0.2")]
    seconds: f64,
}

fn validate_opts(opts: &Opt) -> Result<()> {
    if opts.opacity > 1.0 || opts.opacity < 0.0 {
        bail!(format!("{} is not between 0.0 and 1.0", opts.opacity));
    }
    if opts.seconds < 0.0 {
        bail!(format!("{} can't be negative", opts.seconds));
    }
    Ok(())
}

fn main() {
    if let Err(ref e) = run() {
        use std::io::Write;
        let stderr = &mut ::std::io::stderr();
        let errmsg = "Error writing to stderr";

        writeln!(stderr, "error: {}", e).expect(errmsg);

        for e in e.iter().skip(1) {
            writeln!(stderr, "caused by: {}", e).expect(errmsg);
        }

        if let Some(backtrace) = e.backtrace() {
            writeln!(stderr, "backtrace: {:?}", backtrace).expect(errmsg);
        }

        ::std::process::exit(1);
    }
}

fn run() -> Result<()> {
    let opts = Opt::from_args();
    validate_opts(&opts).chain_err(|| "argument validation error")?;

    let mut i3 =
        I3Connection::connect().chain_err(|| "unable to connect to i3")?;
    let (xorg, _screen) = xcb::Connection::connect(None)
        .chain_err(|| "unable to connect to X session")?;

    flash_current_window(&mut i3, &xorg, opts.opacity, opts.seconds)
        .chain_err(|| "failed to flash window")?;
    return Ok(());
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

fn get_focused_window_id(i3: &mut I3Connection) -> Result<u32> {
    let mut node: Node = i3.get_tree()
        .chain_err(|| "failed to fetch the window tree from i3")?;
    loop {
        node =
            get_focus_child(node).ok_or("can't find a child node with focus")?;
        if node.focused {
            let window_id = node.window
                .chain_err(|| "failed to get window id from i3 node")?;
            return Ok(window_id as u32);
        }
    }
}

fn get_window_opacity_atom(xorg: &xcb::Connection) -> Result<xcb_atom_t> {
    let opacity_cookie =
        xproto::intern_atom(&xorg, false, &"_NET_WM_WINDOW_OPACITY");

    let xorg_reply = opacity_cookie
        .get_reply()
        .chain_err(|| "error in X server reply")?;

    return Ok(xorg_reply.atom());
}

fn flash_current_window(
    i3: &mut I3Connection,
    xorg: &xcb::Connection,
    opacity: f64,
    seconds: f64,
) -> Result<()> {
    let opacity_atom: xcb_atom_t = get_window_opacity_atom(&xorg)
        .chain_err(|| "failed to generate _NET_WM_WINDOW_OPACITY atom")?;
    let focused_window_id: u32 = get_focused_window_id(i3)
        .chain_err(|| "failed to find the current focused window")?;
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
    return Ok(());
}

#[cfg(test)]
mod tests {
    extern crate i3ipc;
    extern crate xcb;
    pub use i3ipc::I3Connection;
    pub use super::*;

    fn new_empty_window(
        xorg: &xcb::Connection,
        screen: &xcb::Screen,
    ) -> xcb::Window {
        let wid = xorg.generate_id();
        let values = [
            (xcb::CW_BACK_PIXEL, screen.white_pixel()),
            (
                xcb::CW_EVENT_MASK,
                xcb::EVENT_MASK_EXPOSURE | xcb::EVENT_MASK_KEY_PRESS,
            ),
        ];
        xcb::create_window(
            &xorg,
            xcb::COPY_FROM_PARENT as u8,
            wid,
            screen.root(),
            0,
            0,
            500,
            500,
            0,
            xcb::WINDOW_CLASS_INPUT_OUTPUT as u16,
            xcb::ffi::base::XCB_COPY_FROM_PARENT,
            &values,
        );
        xcb::map_window(&xorg, wid);
        return wid;
    }

    describe! stainless {
        before_each {
            let mut i3 = I3Connection::connect().unwrap();
            let (xorg, screen_number) = xcb::Connection::connect(None).unwrap();
            let setup = xorg.get_setup();
            let screen = setup.roots().nth(screen_number as usize).unwrap();
        }

        it "checks get_focused_window_id" {
            let wid1 = new_empty_window(&xorg, &screen);
            assert_eq!(get_focused_window_id(&mut i3).unwrap(), wid1);
            let wid2 = new_empty_window(&xorg, &screen);
            assert_eq!(get_focused_window_id(&mut i3).unwrap(), wid2);
            i3.run_command("focus left").unwrap();
            assert_eq!(get_focused_window_id(&mut i3).unwrap(), wid1);
        }
    }
}
