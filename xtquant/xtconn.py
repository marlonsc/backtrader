"""xtconn.py module.

Description of the module functionality."""


from .xtdatacenter import try_create_client

# config
localhost = "127.0.0.1"

# function
status_callback = None


def try_create_connection(addr):
"""addr: 'localhost:58610'

Args::
    addr:"""
    addr:"""
    ip, port = addr.split(":")
    if not ip:
        ip = localhost
    if not port:
        raise Exception("invalid port")

    cl = try_create_client()
    cl.set_config_addr(addr)

    global status_callback
    if status_callback:
        cl.registerCommonControlCallback("watchxtquantstatus", status_callback)

    ec, msg = cl.connect()
    if ec < 0:
        raise Exception((ec, msg))
    return cl


def create_connection(addr):
"""Args::
    addr:"""
"""扫描当前环境下所有XTQuant服务实例

Returns::
    [ config1, config2,... ]"""
    [ config1, config2,... ]"""

    import json
    import os

    result = []

    try:
        config_dir = os.path.abspath(
            os.path.join(os.environ["USERPROFILE"], ".xtquant")
        )

        for f in os.scandir(config_dir):
            full_path = f.path

            f_xtdata_cfg = os.path.join(full_path, "xtdata.cfg")
            if not os.path.exists(f_xtdata_cfg):
                continue

            try:
                config = json.load(open(f_xtdata_cfg, "r", encoding="utf-8"))

                ip = config.get("ip", None)
                if not ip:
                    config["ip"] = localhost

                port = config.get("port", None)
                if not port:
                    continue

            except Exception:
                continue

            is_running = False

            f_running_status = os.path.join(full_path, "running_status")
            if os.path.exists(f_running_status):
                try:
                    os.remove(f_running_status)
                except PermissionError:
                    is_running = True
                except Exception:
                    pass

            config["is_running"] = is_running

            result.append(config)

    except Exception:
        pass

    return result


def get_internal_server_addr():
"""获取内部XTQuant服务地址

Returns::
    '127.0.0.1:58610'"""
    '127.0.0.1:58610'"""
    try:
        from .xtdatacenter import get_local_server_port

        local_server_port = get_local_server_port()
        if local_server_port:
            return f"127.0.0.1:{local_server_port}"
    except BaseException:
        pass
    return None


def scan_available_server_addr():
"""扫描当前环境下可用的XTQuant服务实例

Returns::
    [ '0.0.0.0:58610', '0.0.0.0:58611', ... ]"""
    [ '0.0.0.0:58610', '0.0.0.0:58611', ... ]"""

    import os
    import sys

    result = []

    internal_server_addr = get_internal_server_addr()
    if internal_server_addr:
        result.append(internal_server_addr)

    try:
        result_scan = []

        inst_list = scan_all_server_instance()

        for config in inst_list:
            try:
                if not config.get("is_running", False):
                    continue

                ip = config.get("ip", None)
                port = config.get("port", None)
                if not ip or not port:
                    continue

                addr = f"{ip}:{port}"

                root_dir = os.path.normpath(config.get("root_dir", ""))
                if root_dir and os.path.normpath(sys.executable).find(root_dir) == 0:
                    result_scan.insert(0, addr)
                else:
                    result_scan.append(addr)

            except Exception:
                continue

    except Exception:
        pass

    result += result_scan

    result = list(dict.fromkeys(result))

    return result


def connect_any(addr_list, start_port, end_port):
"""addr_list: [ addr, ... ]
addr: 'localhost:58610'

Args::
    addr_list: 
    start_port: 
    end_port:"""
    end_port:"""
    for addr in addr_list:
        try:
            port = int(addr.split(":")[1])
            if start_port > port or port > end_port:
                continue

            cl = create_connection(addr)
            if cl:
                return cl
        except Exception:
            continue

    return None
