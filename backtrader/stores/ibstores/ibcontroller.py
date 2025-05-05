"""Programmatic control over the TWS/gateway client software."""

import asyncio
import logging
import sys
from contextlib import suppress
from dataclasses import dataclass
from typing import ClassVar

import ib_insync.util as util
from eventkit import Event
from ib_insync.contract import Contract, Forex
from ib_insync.ib import IB


@dataclass
class IBC:
    r"""Programmatic control over starting and stopping TWS/Gateway
    using IBC (https://github.com/IbcAlpha/IBC).


    """

    IbcLogLevel: ClassVar = logging.DEBUG

    twsVersion: int = 0
    gateway: bool = False
    tradingMode: str = ""
    twsPath: str = ""
    twsSettingsPath: str = ""
    ibcPath: str = ""
    ibcIni: str = ""
    javaPath: str = ""
    userid: str = ""
    password: str = ""
    fixuserid: str = ""
    fixpassword: str = ""
    on2fatimeout: str = ""

    def __post_init__(self):
        """ """
        self._isWindows = sys.platform == "win32"
        if not self.ibcPath:
            self.ibcPath = "/opt/ibc" if not self._isWindows else "C:\\IBC"
        self._proc = None
        self._monitor = None
        self._logger = logging.getLogger("ib_insync.IBC")

    def __enter__(self):
        """ """
        self.start()
        return self

    def __exit__(self, *_exc):
        """

        :param *_exc:

        """
        self.terminate()

    def start(self):
        r"""Launch TWS/IBG."""
        util.run(self.startAsync())

    def terminate(self):
        r"""Terminate TWS/IBG."""
        util.run(self.terminateAsync())

    async def startAsync(self):
        """ """
        if self._proc:
            return
        self._logger.info("Starting")

        # map from field names to cmd arguments; key=(UnixArg, WindowsArg)
        args = dict(
            twsVersion=("", ""),
            gateway=("--gateway", "/Gateway"),
            tradingMode=("--mode=", "/Mode:"),
            twsPath=("--tws-path=", "/TwsPath:"),
            twsSettingsPath=("--tws-settings-path=", ""),
            ibcPath=("--ibc-path=", "/IbcPath:"),
            ibcIni=("--ibc-ini=", "/Config:"),
            javaPath=("--java-path=", "/JavaPath:"),
            userid=("--user=", "/User:"),
            password=("--pw=", "/PW:"),
            fixuserid=("--fix-user=", "/FIXUser:"),
            fixpassword=("--fix-pw=", "/FIXPW:"),
            on2fatimeout=("--on2fatimeout=", "/On2FATimeout:"),
        )

        # create shell command
        cmd = [
            (
                f"{self.ibcPath}\\scripts\\StartIBC.bat"
                if self._isWindows
                else f"{self.ibcPath}/scripts/ibcstart.sh"
            )
        ]
        for k, v in util.dataclassAsDict(self).items():
            arg = args[k][self._isWindows]
            if v:
                if arg.endswith("=") or arg.endswith(":"):
                    cmd.append(f"{arg}{v}")
                elif arg:
                    cmd.append(arg)
                else:
                    cmd.append(str(v))

        # run shell command
        self._proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE
        )
        self._monitor = asyncio.ensure_future(self.monitorAsync())

    async def terminateAsync(self):
        """ """
        if not self._proc:
            return
        self._logger.info("Terminating")
        if self._monitor:
            self._monitor.cancel()
            self._monitor = None
        if self._isWindows:
            import subprocess

            subprocess.call(["taskkill", "/F", "/T", "/PID", str(self._proc.pid)])
        else:
            with suppress(ProcessLookupError):
                self._proc.terminate()
                await self._proc.wait()
        self._proc = None

    async def monitorAsync(self):
        """ """
        while self._proc:
            line = await self._proc.stdout.readline()
            if not line:
                break
            self._logger.log(IBC.IbcLogLevel, line.strip().decode())


@dataclass
class Watchdog:
    r"""Start, connect and watch over the TWS or gateway app and try to keep it
    up and running. It is intended to be used in an event-driven
    application that properly initializes itself upon (re-)connect.

    It is not intended to be used in a notebook or in imperative-style code.
    Do not expect Watchdog to magically shield you from reality. Do not use
    Watchdog unless you understand what it does and doesn't do.


    """

    events = [
        "startingEvent",
        "startedEvent",
        "stoppingEvent",
        "stoppedEvent",
        "softTimeoutEvent",
        "hardTimeoutEvent",
    ]

    controller: IBC
    ib: IB
    host: str = "127.0.0.1"
    port: int = 7497
    clientId: int = 1
    connectTimeout: float = 2
    appStartupTime: float = 30
    appTimeout: float = 20
    retryDelay: float = 2
    readonly: bool = False
    account: str = ""
    raiseSyncErrors: bool = False
    probeContract: Contract = Forex("EURUSD")
    probeTimeout: float = 4

    def __post_init__(self):
        """ """
        self.startingEvent = Event("startingEvent")
        self.startedEvent = Event("startedEvent")
        self.stoppingEvent = Event("stoppingEvent")
        self.stoppedEvent = Event("stoppedEvent")
        self.softTimeoutEvent = Event("softTimeoutEvent")
        self.hardTimeoutEvent = Event("hardTimeoutEvent")
        if not self.controller:
            raise ValueError("No controller supplied")
        if not self.ib:
            raise ValueError("No IB instance supplied")
        if self.ib.isConnected():
            raise ValueError("IB instance must not be connected")
        self._runner = None
        self._logger = logging.getLogger("ib_insync.Watchdog")

    def start(self):
        """ """
        self._logger.info("Starting")
        self.startingEvent.emit(self)
        self._runner = asyncio.ensure_future(self.runAsync())
        return self._runner

    def stop(self):
        """ """
        self._logger.info("Stopping")
        self.stoppingEvent.emit(self)
        self.ib.disconnect()
        self._runner = None

    async def runAsync(self):
        """ """

        def onTimeout(idlePeriod):
            """

            :param idlePeriod:

            """
            if not waiter.done():
                waiter.set_result(None)

        def onError(reqId, errorCode, errorString, contract):
            """

            :param reqId:
            :param errorCode:
            :param errorString:
            :param contract:

            """
            if errorCode in {100, 1100} and not waiter.done():
                waiter.set_exception(Warning(f"Error {errorCode}"))

        def onDisconnected():
            """ """
            if not waiter.done():
                waiter.set_exception(Warning("Disconnected"))

        while self._runner:
            try:
                await self.controller.startAsync()
                await asyncio.sleep(self.appStartupTime)
                await self.ib.connectAsync(
                    self.host,
                    self.port,
                    self.clientId,
                    self.connectTimeout,
                    self.readonly,
                    self.account,
                    self.raiseSyncErrors,
                )
                self.startedEvent.emit(self)
                self.ib.setTimeout(self.appTimeout)
                self.ib.timeoutEvent += onTimeout
                self.ib.errorEvent += onError
                self.ib.disconnectedEvent += onDisconnected

                while self._runner:
                    waiter: asyncio.Future = asyncio.Future()
                    await waiter
                    # soft timeout, probe the app with a historical request
                    self._logger.debug("Soft timeout")
                    self.softTimeoutEvent.emit(self)
                    probe = self.ib.reqHistoricalDataAsync(
                        self.probeContract,
                        "",
                        "30 S",
                        "5 secs",
                        "MIDPOINT",
                        False,
                    )
                    bars = None
                    with suppress(asyncio.TimeoutError):
                        bars = await asyncio.wait_for(probe, self.probeTimeout)
                    if not bars:
                        self.hardTimeoutEvent.emit(self)
                        raise Warning("Hard timeout")
                    self.ib.setTimeout(self.appTimeout)

            except ConnectionRefusedError:
                pass
            except Warning as w:
                self._logger.warning(w)
            except Exception as e:
                self._logger.exception(e)
            finally:
                self.ib.timeoutEvent -= onTimeout
                self.ib.errorEvent -= onError
                self.ib.disconnectedEvent -= onDisconnected
                await self.controller.terminateAsync()
                self.stoppedEvent.emit(self)
                if self._runner:
                    await asyncio.sleep(self.retryDelay)


if __name__ == "__main__":
    ibc = IBC(1012, gateway=True, tradingMode="paper")
    ib = IB()
    app = Watchdog(ibc, ib, appStartupTime=15)
    app.start()
    IB.run()
