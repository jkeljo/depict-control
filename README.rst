====================
``depict-control``
====================

Control your `Depict Frame <https://www.depict.com>` from Python 3.5 with ``asyncio``!

This initial release is mainly targeting the functionality needed for basic integrations
with home automation systems:

* Sleep/wake
* Brightness + contrast
* Setting current image

*************
Usage example
*************

Finding frames on your network
==============================
To find the IP addresses of all tables on your local network. This is a very naive search; it assumes your subnet
mask is ``255.255.255.0``::

  from depict_control import Frame

  ip_addrs = await Frame.find_frame_ips()

Once you know the IP address, connect to the table (``session`` is an ``aiohttp Session`` object)::

  async with await Frame.connect(session, ip_addr) as frame:
    # Do stuff here

Basic controls
==============
In addition to a bunch of properties for querying the current state of the frame, ``Frame`` has several methods that
allow simple control::

  await frame.set_brightness(100)  # Set backlight brightness
  await frame.set_contrast(50)     # Set image contrast
  await frame.set_image_url(url)   # Display an image

