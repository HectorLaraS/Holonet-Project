from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import servicemanager
import win32event
import win32service
import win32serviceutil

# 1. Configuración dinámica de rutas basadas en la ubicación del archivo actual
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ahora podemos importar de src con seguridad
from src.config.settings import settings

# 2. Forzar dinámicamente el ejecutable de Python de tu entorno virtual (.venv)
PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

LOG_DIR = PROJECT_ROOT / "logs"
STDOUT_LOG = LOG_DIR / "scheduler_stdout.log"
STDERR_LOG = LOG_DIR / "scheduler_stderr.log"

APP_ARGS = [
    str(PYTHON_EXE),
    "-m",
    "src.main_scheduler",
]


class HolonetSchedulerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "HolonetScheduler"
    _svc_display_name_ = "Holonet Scheduler"
    _svc_description_ = (
        "Runs Holonet scheduler for Starlink polling and report generation."
    )

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.proc = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                for _ in range(20):
                    if self.proc.poll() is not None:
                        break
                    time.sleep(0.25)

                if self.proc.poll() is None:
                    self.proc.kill()
            except Exception:
                pass

    def SvcDoRun(self):
        LOG_DIR.mkdir(exist_ok=True)
        os.chdir(PROJECT_ROOT)

        servicemanager.LogInfoMsg("Holonet Scheduler service starting...")
        
        # Reportar inmediatamente que está corriendo para que Windows no marque Timeout
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)

        out = open(STDOUT_LOG, "a", encoding="utf-8")
        err = open(STDERR_LOG, "a", encoding="utf-8")

        try:
            self.proc = subprocess.Popen(
                APP_ARGS,
                cwd=str(PROJECT_ROOT),
                stdout=out,
                stderr=err,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            servicemanager.LogInfoMsg("Holonet Scheduler child process started.")

            while True:
                rc = win32event.WaitForSingleObject(self.stop_event, 1000)

                if rc == win32event.WAIT_OBJECT_0:
                    break

                if self.proc.poll() is not None:
                    servicemanager.LogErrorMsg(
                        "Holonet Scheduler child process exited "
                        f"with code {self.proc.returncode}. "
                        "Restarting..."
                    )

                    time.sleep(settings.SERVICE_RESTART_DELAY_SECONDS)

                    self.proc = subprocess.Popen(
                        APP_ARGS,
                        cwd=str(PROJECT_ROOT),
                        stdout=out,
                        stderr=err,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
        finally:
            out.close()
            err.close()

        servicemanager.LogInfoMsg("Holonet Scheduler service stopped.")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(HolonetSchedulerService)