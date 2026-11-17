import asyncio
import json
import socket
import unittest
import urllib.request

import _path  # noqa: F401

from main import LLMBridgeServer


def request(method, url, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=3) as response:
        body = response.read()
        return response.status, json.loads(body.decode("utf-8"))


def raw_exchange(host, port, payload: bytes) -> bytes:
    with socket.create_connection((host, port), timeout=3) as sock:
        sock.sendall(payload)
        sock.shutdown(socket.SHUT_WR)
        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
    return b"".join(chunks)


class HttpBridgeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.server = LLMBridgeServer(host="127.0.0.1", port=0)
        self.task = asyncio.create_task(self.server.bridge.start_server())
        for _ in range(50):
            if self.server.bridge._tcp is not None:
                break
            await asyncio.sleep(0.02)
        self.base = f"http://127.0.0.1:{self.server.bridge.port}"

    async def asyncTearDown(self):
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

    async def test_request_is_queued_for_the_plugin(self):
        status, body = await asyncio.to_thread(
            request,
            "POST",
            self.base + "/request",
            {"request": "Add a C major chord at the beginning"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "queued")
        self.assertEqual(body["source"], "local")
        self.assertEqual(body["commands"][0]["pitches"], [60, 64, 67])
        self.assertIn("C4", body["preview"][0])

        _, polled = await asyncio.to_thread(request, "GET", self.base + "/poll")
        self.assertEqual(polled["commands"][0]["type"], "add_chord")
        self.assertEqual(polled["commands"][0]["duration"], 480)
        self.assertEqual(polled["commands"][0]["tick"], 0)
        self.assertIn("batch_id", polled["commands"][0])

        _, empty = await asyncio.to_thread(request, "GET", self.base + "/poll")
        self.assertEqual(empty["commands"], [])

    async def test_desk_page_and_unicode_status(self):
        page = await asyncio.to_thread(raw_exchange, "127.0.0.1", self.server.bridge.port, b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
        head, _, body = page.partition(b"\r\n\r\n")
        length = int(head.split(b"Content-Length: ")[1].split(b"\r\n")[0])
        self.assertEqual(length, len(body))
        self.assertIn(b"What should change?", body)

        await asyncio.to_thread(
            request,
            "POST",
            self.base + "/score_info",
            {"title": "Prélude", "measures": 8, "staves": 1, "keySignature": 1, "timeSignature": {"numerator": 3, "denominator": 4}},
        )
        raw = await asyncio.to_thread(
            raw_exchange,
            "127.0.0.1",
            self.server.bridge.port,
            b"GET /status HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n",
        )
        head, _, body = raw.partition(b"\r\n\r\n")
        length = int(head.split(b"Content-Length: ")[1].split(b"\r\n")[0])
        self.assertEqual(length, len(body))
        status = json.loads(body.decode("utf-8"))
        self.assertEqual(status["score"]["title"], "Prélude")
        self.assertEqual(status["score"]["key_name"], "G")
        self.assertTrue(status["plugin_connected"])
        self.assertFalse(status["llm"]["configured"])

    async def test_plugin_confirmation_unblocks_a_waiting_send(self):
        result_task = asyncio.create_task(
            self.server.process_request("Transpose up a perfect fifth", wait_for_plugin=True)
        )
        await asyncio.sleep(0.05)
        _, polled = await asyncio.to_thread(request, "GET", self.base + "/poll")
        batch_id = polled["commands"][0]["batch_id"]
        await asyncio.to_thread(
            request,
            "POST",
            self.base + "/results",
            {"batch_id": batch_id, "executed": 1, "failed": 0, "errors": []},
        )
        result = await result_task
        self.assertEqual(result["status"], "applied")
        self.assertEqual(result["commands"][0]["semitones"], 7)

    async def test_music_endpoint_writes_a_bass_line(self):
        _, body = await asyncio.to_thread(
            request,
            "POST",
            self.base + "/music",
            {"action": "walking_bass", "chords": ["Gmaj", "C"], "measures": 1, "track": 0},
        )
        self.assertEqual(body["status"], "queued")
        self.assertEqual(len(body["commands"]), 4)
        self.assertEqual(body["commands"][1]["pitch"], 47)


if __name__ == "__main__":
    unittest.main()
