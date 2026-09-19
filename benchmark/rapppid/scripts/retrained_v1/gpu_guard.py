"""Separately qualified network/process restrictions for single-GPU scoring.

Derived from the repository's restriction-only guard; historical code is not
modified. CUDA ioctls remain allowed. No network/PID namespace is claimed.
"""
import ctypes
import errno
import json
import os
from pathlib import Path
import resource
import runpy
import socket
import sys

DENIED=(
    'io_uring_setup','io_uring_enter','io_uring_register','ptrace',
    'process_vm_readv','process_vm_writev','pidfd_open','pidfd_getfd','pidfd_send_signal',
    'kill','tkill','tgkill','mount','umount2','pivot_root','setns','unshare',
    'open_by_handle_at','name_to_handle_at','bpf','perf_event_open','keyctl','shmget','shmat','shmctl')

def landlock(libc):
    """Permit CUDA's own /proc and driver views, deny other processes' trees.

    Native ARM64 syscall numbers are shared with asm-generic. Require ABI>=3
    (including truncate mediation), rather than silently weakening the guard.
    https://docs.kernel.org/userspace-api/landlock.html
    """
    abi=libc.syscall(444,0,0,1)
    if abi<6:
        raise RuntimeError('Landlock ABI >=6 is required for GPU scoring')
    class Ruleset(ctypes.Structure):
        _fields_=[('handled_access_fs',ctypes.c_uint64),('handled_access_net',ctypes.c_uint64),('scoped',ctypes.c_uint64)]
    class Beneath(ctypes.Structure):
        _pack_=1
        _fields_=[('allowed_access',ctypes.c_uint64),('parent_fd',ctypes.c_int32)]
    handled=(1<<15)-1  # ABI1 filesystem rights + REFER + TRUNCATE; allow GPU ioctls.
    rules=Ruleset(handled,0,3)  # Scope abstract AF_UNIX sockets and signals to this domain.
    fd=libc.syscall(444,ctypes.byref(rules),ctypes.sizeof(rules),0)
    if fd<0:
        raise OSError(ctypes.get_errno(),'Landlock create ruleset')
    allowed=[]
    try:
        for path in Path('/').iterdir():
            if path.name=='proc':
                continue
            allowed.append((path,handled if path.is_dir() else (1|2|4|(1<<14))))
        for path in [Path(f'/proc/{os.getpid()}'),Path('/proc/driver'),Path('/proc/sys'),
                     Path('/proc/cpuinfo'),Path('/proc/meminfo'),Path('/proc/stat'),
                     Path('/proc/uptime'),Path('/proc/filesystems'),Path('/proc/mounts'),Path('/proc/devices')]:
            if path.exists():
                rights=12 if path.is_dir() else 4
                if path==Path(f'/proc/{os.getpid()}'):
                    rights|=2|(1<<14)  # CUDA names its own helper threads through task/*/comm.
                allowed.append((path,rights))
        for path,rights in allowed:
            pfd=os.open(path,os.O_PATH|os.O_CLOEXEC)
            try:
                attr=Beneath(rights,pfd)
                if libc.syscall(445,fd,1,ctypes.byref(attr),0):
                    raise OSError(ctypes.get_errno(),f'Landlock allow {path}')
            finally:
                os.close(pfd)
        if libc.syscall(446,fd,0):
            raise OSError(ctypes.get_errno(),'Landlock restrict self')
    finally:
        os.close(fd)
    # A real existing other-process proc entry must become inaccessible.
    for target in [Path('/proc/1/maps'),Path(f'/proc/{os.getppid()}/maps')]:
        try:
            target.open('rb').close()
        except PermissionError:
            pass
        else:
            raise RuntimeError('Other-process proc access was not blocked')
    return abi

def restrict():
    if os.uname().machine!='aarch64':
        raise RuntimeError('Only qualified ARM64 ABI permitted')
    if Path('/nobackup').exists() or Path('/home/jalil').exists():
        raise RuntimeError('Host workspace remains visible')
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    os.closerange(3,resource.getrlimit(resource.RLIMIT_NOFILE)[0])
    libc=ctypes.CDLL('libc.so.6',use_errno=True)
    lib=ctypes.CDLL('libseccomp.so.2',use_errno=True)
    lib.seccomp_init.argtypes=[ctypes.c_uint32]; lib.seccomp_init.restype=ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p]; lib.seccomp_syscall_resolve_name.restype=ctypes.c_int
    lib.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
    class Comparison(ctypes.Structure):
        _fields_=[('arg',ctypes.c_uint),('op',ctypes.c_int),('datum_a',ctypes.c_uint64),('datum_b',ctypes.c_uint64)]
    lib.seccomp_rule_add_array.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint,ctypes.POINTER(Comparison)]
    lib.seccomp_load.argtypes=[ctypes.c_void_p]; lib.seccomp_release.argtypes=[ctypes.c_void_p]
    if libc.prctl(38,1,0,0,0):
        raise RuntimeError('Cannot enforce no_new_privs')
    abi=landlock(libc)
    context=lib.seccomp_init(0x7fff0000)
    if not context:
        raise RuntimeError('Cannot initialize seccomp')
    try:
        for name in DENIED:
            number=lib.seccomp_syscall_resolve_name(name.encode())
            if number<0 or lib.seccomp_rule_add(context,0x50000|errno.EPERM,number,0):
                raise RuntimeError('Cannot enforce complete syscall restrictions')
        # CUDA uses local AF_UNIX helper IPC. All other socket families are
        # denied before threads start; inherited FDs are closed above. Scoped
        # Landlock blocks abstract-socket communication outside this domain.
        compare=Comparison(0,1,socket.AF_UNIX,0)  # SCMP_CMP_NE
        for name in ('socket','socketpair'):
            number=lib.seccomp_syscall_resolve_name(name.encode())
            if lib.seccomp_rule_add_array(context,0x50000|errno.EPERM,number,1,ctypes.byref(compare)):
                raise RuntimeError('Cannot restrict nonlocal socket families')
        if lib.seccomp_load(context):
            raise RuntimeError('Cannot activate syscall restrictions')
    finally:
        lib.seccomp_release(context)
    for family in (socket.AF_INET,socket.AF_INET6,socket.AF_NETLINK):
        try:
            socket.socket(family,socket.SOCK_STREAM)
        except PermissionError:
            pass
        else:
            raise RuntimeError('Socket restriction failed')
    for name in ('io_uring_setup','pidfd_open'):
        number=lib.seccomp_syscall_resolve_name(name.encode())
        ctypes.set_errno(0)
        if libc.syscall(number,0,0,0)!=-1 or ctypes.get_errno()!=errno.EPERM:
            raise RuntimeError('Alternative-channel restriction failed')
    return {'network_syscall_filter_enforced':True,'landlock_abi':abi,
        'other_process_proc_file_access_denied':True,'proc_sys_hidden':False,
        'own_proc_and_driver_sys_allowed_for_cuda':True,'local_AF_UNIX_IPC_allowed':True,
        'abstract_AF_UNIX_and_signals_scoped_to_landlock_domain':True,
        'inherited_fds_closed':True,'cpu_only':False,'cuda_ioctls_allowed':True,
        'network_namespace_claimed':False,'pid_namespace_claimed':False,
        'denied_syscalls':list(DENIED)}

if __name__=='__main__':
    attestation=restrict()
    if sys.argv[1:]==['--probe']:
        import subprocess
        child=subprocess.run([sys.executable,'-c','import socket; socket.socket()'],capture_output=True)
        if child.returncode==0 or b'PermissionError' not in child.stderr:
            raise RuntimeError('Child restriction inheritance failed')
        import torch
        from common import cuda
        device=cuda()
        x=torch.arange(256,device=device,dtype=torch.float32).reshape(16,16).requires_grad_()
        y=(x@x.T).square().mean(); y.backward(); torch.cuda.synchronize()
        if not torch.isfinite(x.grad).all():
            raise RuntimeError('GPU backward probe failed')
        attestation.update(gpu=torch.cuda.get_device_name(),torch=torch.__version__,
            cuda=torch.version.cuda,gpu_forward_backward_passed=True,child_inherits_filter=True)
        print(json.dumps(attestation,sort_keys=True))
    else:
        target=Path(sys.argv[1]).resolve(strict=True)
        if target.parent!=Path('/code'):
            raise RuntimeError('Only benchmark entrypoints may run')
        sys.argv=sys.argv[1:]
        runpy.run_path(str(target),run_name='__main__')


