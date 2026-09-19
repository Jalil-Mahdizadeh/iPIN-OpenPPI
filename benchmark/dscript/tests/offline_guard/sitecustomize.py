"""Qualification-only guard: deny Python TCP/IP networking, allow local IPC."""
import os
import socket

if os.environ.get("DSCRIPT_TEST_OFFLINE") == "1":
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise RuntimeError(f"Qualification forbids network access: {address!r}")
        return original_connect(sock, address)

    def connect_ex(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise RuntimeError(f"Qualification forbids network access: {address!r}")
        return original_connect_ex(sock, address)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
