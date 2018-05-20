import aiohttp
from aiohttp import web
import asyncio
import binascii
import netifaces
import os


class Frame(object):
    @classmethod
    async def connect(cls, ip):
        session = aiohttp.ClientSession(
            auto_decompress=True,
            raise_for_status=True,
        )
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
        async with self._session.get(
                "http://{ip}:3002/settings".format(ip=self._ip)) as resp:
            settings = await resp.json(content_type=None)
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
    def brightness(self):
        return self._brightness

    async def set_brightness(self, brightness: float):
        await self._send_command("brightness", level=brightness)

    @property
    def contrast(self):
        return self._contrast

    async def set_contrast(self, contrast: float):
        await self._send_command("contrast", level=contrast)

    @property
    def is_on(self):
        return self._power == "up"

    async def sleep(self):
        await self._send_command("power", pwr="down")

    async def wakeup(self):
        await self._send_command("power", pwr="up")

    async def upload_image(self, file_path):
        localhost = _get_ip()
        port = 8080
        image_extension = os.path.splitext(file_path)[1]
        image_name = binascii.hexlify(os.urandom(64)).decode('utf8') + image_extension

        file_sent = asyncio.Future()

        class GetFileResponse(web.FileResponse):
            def write_eof(self, data=b''):
                try:
                    return super().write_eof(data)
                finally:
                    file_sent.set_result(True)

        async def get_file(request):
            return GetFileResponse(file_path)

        app = web.Application()
        app.add_routes([web.get('/' + image_name, get_file)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, localhost, port)
        await site.start()

        await self.set_image_url(
            "http://{localhost}:{port}/{image_name}".format(
                localhost=localhost,
                port=port,
                image_name=image_name))

        await file_sent
        await site.stop()

    async def set_image_url(self, url):
        async with self._session.post(
                "http://{ip}:56789/apps/DepictFramePlayer/load_media".format(
                    ip=self._ip),
                json={
                    "media": {
                        "contentId": url,
                    },
                    "cmd_id": 0,
                    "type": "LOAD",
                    "autoplay": True,
                }) as resp:
            await resp.text()

    async def _send_command(self, cmd, **kwargs):
        async with self._session.post(
                "http://{ip}:3002/command/{cmd}".format(ip=self._ip, cmd=cmd),
                params=kwargs,
        ) as resp:
            pass


def _get_ip():
    for iface in netifaces.interfaces():
        ifaddresses = netifaces.ifaddresses(iface)
        if netifaces.AF_INET not in ifaddresses:
            continue

        for ifaddress in ifaddresses[netifaces.AF_INET]:
            local_addr = ifaddress["addr"]
            if local_addr == '127.0.0.1':
                continue

            return local_addr