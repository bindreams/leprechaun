import sys
import subprocess as sp
from functools import wraps

if sys.platform == "win32":
    import win32api
    import win32con
    import win32job

    # Create a Job Object - a container for running processes in Windows that ensures that child processes will die
    # Borrowed from https://stackoverflow.com/a/23587108
    hJob = win32job.CreateJobObject(None, "")
    extended_info = win32job.QueryInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation)
    extended_info['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(hJob, win32job.JobObjectExtendedLimitInformation, extended_info)

    perms = win32con.PROCESS_TERMINATE | win32con.PROCESS_SET_QUOTA

    @wraps(sp.Popen)
    def popen(proc_args, **kwargs):
        proc = sp.Popen(proc_args, **kwargs)

        # Assign new process to a Job, ensuring it will die if Leprechaun crashes
        hProcess = win32api.OpenProcess(perms, False, proc.pid)
        win32job.AssignProcessToJobObject(hJob, hProcess)

        return proc

elif sys.platform.startswith("linux"):
    import ctypes
    import signal

    libc = ctypes.CDLL("libc.so.6")

    @wraps(sp.Popen)
    def popen(proc_args, **kwargs):
        if "preexec_fn" in kwargs:
            fn = kwargs.pop("preexec_fn")

            def preexec_fn():
                libc.prctl(1, signal.SIGKILL)
                fn()
        else:
            def preexec_fn():
                libc.prctl(1, signal.SIGKILL)

        return sp.Popen(proc_args, preexec_fn=preexec_fn, **kwargs)

else:
    # On MacOS and others, there is no good way to ensure children die with their parents
    @wraps(sp.Popen)
    def popen(proc_args, **kwargs):
        return sp.Popen(proc_args, **kwargs)
