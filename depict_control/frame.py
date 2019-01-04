import asyncio

_LANDSCAPE_RESOLUTION = (3840, 2160)


class Frame(object):
    """Represents one Depict Frame."""
    @classmethod
    async def find_frame_ips(self, session=None):
        import netifaces

        for iface in netifaces.interfaces():
            ifaddresses = netifaces.ifaddresses(iface)
            if netifaces.AF_INET not in ifaddresses:
                continue

            for ifaddress in ifaddresses[netifaces.AF_INET]:
                local_addr = ifaddress["addr"]
                if local_addr == '127.0.0.1':
                    continue

                broadcast = ifaddress["broadcast"]

                root = local_addr[:local_addr.rindex('.') + 1]
                pings = []
                for i in range(1, 256):
                    table_addr = root + str(i)
                    if table_addr != local_addr and table_addr != broadcast:
                        pings.append(
                            asyncio.Task(_ping_frame(session, table_addr)))

                return [ip for ip in await asyncio.gather(*pings) if ip]


    @classmethod
    async def connect(cls, session, ip):
        frame = Frame(session, ip)
        await frame.update()
        return frame

    def __init__(self, session, ip):
        self._session = session
        self._ip = ip
        self._brightness = None
        self._contrast = None
        self._name = None
        self._power = None
        self._orientation = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self._session.close()

    async def update(self):
        settings = await _get_frame_settings(self._session, self._ip)
        self._brightness = settings["brightness"]
        self._contrast = settings["contrast"]
        self._name = settings["friendly_name"]
        self._orientation = settings["orientation"]
        self._power = settings["power"]

    @property
    def name(self):
        return self._name

    @property
    def orientation(self):
        return self._orientation

    @property
    def resolution(self):
        if self.orientation == 'landscape':
            return _LANDSCAPE_RESOLUTION
        else:
            return tuple(reversed(_LANDSCAPE_RESOLUTION))

    @property
    def brightness(self):
        return self._brightness

    async def set_brightness(self, brightness: float):
        """Sets the brightness (range from 0 to 100)"""
        await self._send_command("brightness", level=int(brightness))

    @property
    def contrast(self):
        return self._contrast

    async def set_contrast(self, contrast: float):
        """Sets the contrast (range from 0 to 100)"""
        await self._send_command("contrast", level=int(contrast))

    @property
    def is_on(self):
        return self._power == "up"

    async def sleep(self):
        await self._send_command("power", pwr="down")

    async def wakeup(self):
        await self._send_command("power", pwr="up")

    async def set_image_url(self, url):
        async with self._session.post(
                "http://{ip}:56789/apps/DepictFramePlayer/load_media".format(
                    ip=self._ip,),
                json={
                    "media": {
                        "contentId": url,
                    },
                    "cmd_id": 0,
                    "type": "LOAD",
                    "autoplay": True,
                },
                raise_for_status=True) as resp:
            await resp.text()

    async def _send_command(self, cmd, **kwargs):
        async with self._session.post(
                "http://{ip}:3002/command/{cmd}".format(ip=self._ip, cmd=cmd),
                params=kwargs,
                raise_for_status=True,
        ) as resp:
            pass


# noinspection PyBroadException
async def _ping_frame(session, ip):
    try:
        await _get_frame_settings(session, ip)
        return ip
    except Exception:
        return None


async def _get_frame_settings(session, ip):
    async with session.get(
            "http://{ip}:3002/settings".format(ip=ip),
            timeout=1.25,
            raise_for_status=True) as resp:
        return await resp.json(content_type=None)
