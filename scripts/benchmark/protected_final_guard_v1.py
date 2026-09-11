"""Restriction-only CPU launcher; no protected access before qualification.

Run inside the pinned Apptainer image with proc/sys/home/cwd/hostfs and
administrator bind paths disabled. This does not claim PID/network namespaces.
"""
from __future__ import annotations

import ctypes
import errno
import json
import os
from pathlib import Path
import resource
import runpy
import socket
import sys


DENIED = (
    "socket", "socketpair", "connect", "accept", "accept4", "bind", "listen",
    "sendto", "sendmsg", "sendmmsg", "recvfrom", "recvmsg", "recvmmsg",
    "io_uring_setup", "io_uring_enter", "io_uring_register", "ptrace",
    "process_vm_readv", "process_vm_writev", "pidfd_open", "pidfd_getfd",
    "pidfd_send_signal", "kill", "tkill", "tgkill", "mount", "umount2",
    "pivot_root", "setns", "unshare", "open_by_handle_at", "name_to_handle_at",
    "bpf", "perf_event_open", "keyctl", "shmget", "shmat", "shmctl",
)


def restrict() -> dict:
    if os.uname().machine != "aarch64":
        raise RuntimeError("Only the qualified native ARM64 ABI is permitted")
    for hidden in ("/proc", "/sys"):
        if list(Path(hidden).iterdir()):
            raise RuntimeError("Host process/device filesystem remains mounted")
    if Path("/nobackup").exists() or Path("/home/jalil").exists():
        raise RuntimeError("Model-development filesystem is visible")
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    # No inherited socket, directory, namespace, or host-process descriptor.
    os.closerange(3, resource.getrlimit(resource.RLIMIT_NOFILE)[0])
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    seccomp = ctypes.CDLL("libseccomp.so.2", use_errno=True)
    seccomp.seccomp_init.argtypes = [ctypes.c_uint32]
    seccomp.seccomp_init.restype = ctypes.c_void_p
    seccomp.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    seccomp.seccomp_syscall_resolve_name.restype = ctypes.c_int
    seccomp.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    seccomp.seccomp_load.argtypes = [ctypes.c_void_p]
    seccomp.seccomp_release.argtypes = [ctypes.c_void_p]
    if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
        raise RuntimeError("Cannot set no_new_privs")
    context = seccomp.seccomp_init(0x7FFF0000)  # native-ABI allow, bad ABI kills
    if not context:
        raise RuntimeError("Cannot initialize seccomp")
    try:
        for name in DENIED:
            number = seccomp.seccomp_syscall_resolve_name(name.encode("ascii"))
            if number < 0 or seccomp.seccomp_rule_add(context, 0x50000 | errno.EPERM, number, 0):
                raise RuntimeError("Cannot install complete syscall restrictions")
        if seccomp.seccomp_load(context):
            raise RuntimeError("Cannot enforce syscall restrictions")
    finally:
        seccomp.seccomp_release(context)
    for family in (socket.AF_INET, socket.AF_INET6, socket.AF_UNIX):
        try:
            socket.socket(family, socket.SOCK_STREAM)
        except PermissionError:
            pass
        else:
            raise RuntimeError("Socket restriction failed")
    # Probe the networking alternative and cross-process descriptor channel.
    for name in ("io_uring_setup", "pidfd_open"):
        number = seccomp.seccomp_syscall_resolve_name(name.encode("ascii"))
        ctypes.set_errno(0)
        if libc.syscall(number, 0, 0, 0) != -1 or ctypes.get_errno() != errno.EPERM:
            raise RuntimeError("Alternative channel restriction failed")
    os.environ["IPIN_EVALUATOR_NETWORK_ISOLATED"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    return {"network_syscall_filter_enforced": True, "proc_sys_hidden": True,
            "no_inherited_descriptors_above_stderr": True, "cpu_only": True,
            "network_namespace_claimed": False, "pid_namespace_claimed": False,
            "denied_syscalls": list(DENIED)}


if __name__ == "__main__":
    attestation = restrict()
    if sys.argv[1:] == ["--probe"]:
        import subprocess
        child = subprocess.run([sys.executable, "-c", "import socket; socket.socket()"],
                               capture_output=True, check=False)
        assert child.returncode != 0 and b"PermissionError" in child.stderr
        import numpy as np
        import pyarrow as pa
        import torch
        assert float(torch.arange(10).double().sum()) == 45.0
        attestation.update(child_inherits_filter=True, numpy=np.__version__,
                           pyarrow=pa.__version__, torch=torch.__version__)
        print(json.dumps(attestation, sort_keys=True))
    else:
        target = Path(sys.argv[1]).resolve(strict=True)
        if target.parent != Path("/bundle/code"):
            raise RuntimeError("Only frozen bundle entrypoints may execute")
        sys.argv = sys.argv[1:]
        sys.path.insert(0, "/bundle/code")
        runpy.run_path(str(target), run_name="__main__")
