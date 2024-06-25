This repository contains various miscellaneous tools and utilities I have written to make my life easier.

These include:

- `ping.py`, a Python wrapper for *ping* that handles calculating *mdev*. Written for use in [Home Assistant](https://www.home-assistant.io/) when I reimplemented [Netprobe Lite](https://www.youtube.com/watch?v=Wn31husi6tc),
  as it turns out the [Raspberry Pi](https://www.raspberrypi.com/) version of *Home Assistant* uses the [Busybox](https://www.busybox.net/) ping, which doesn't calculate *mdev*. It also checks if it's using the Linux
  version and, if so, simply captures the *mdev* calculated by the tool instead.
  
