# coding:utf-8

from . import xtbson as _BSON_

# connection

__client = None
__client_last_spec = ("", None)


def connect(ip="", port=None, remember_if_success=True):
    """Args:
    ip: (Default value = "")
    port: (Default value = None)
    remember_if_success: (Default value = True)"""
    global __client

    if __client:
        if __client.is_connected():
            return __client

        __client.shutdown()
        __client = None

    from . import xtconn

    if not ip:
        ip = "localhost"

    if port:
        server_list = [f"{ip}:{port}"]
        __client = xtconn.connect_any(server_list)
    else:
        server_list = xtconn.scan_available_server_addr()

        default_addr = "localhost:58610"
        if default_addr not in server_list:
            server_list.append(default_addr)

        __client = xtconn.connect_any(server_list)

    if not __client or not __client.is_connected():
        raise Exception("无法连接xtquant服务，请检查QMT-投研版或QMT-极简版是否开启")

    if remember_if_success:
        global __client_last_spec
        __client_last_spec = (ip, port)

    return __client


def reconnect(ip="", port=None, remember_if_success=True):
    """Args:
    ip: (Default value = "")
    port: (Default value = None)
    remember_if_success: (Default value = True)"""
    global __client

    if __client:
        __client.shutdown()
        __client = None

    return connect(ip, port, remember_if_success)


def get_client():
    """ """
    global __client

    if not __client or not __client.is_connected():
        global __client_last_spec

        ip, port = __client_last_spec
        __client = connect(ip, port, False)

    return __client


# utils
def try_except(func):
    """Args:
    func:"""
    import sys
    import traceback

    def wrapper(*args, **kwargs):
        """"""
        try:
            return func(*args, **kwargs)
        except Exception:
            exc_type, exc_instance, exc_traceback = sys.exc_info()
            formatted_traceback = "".join(traceback.format_tb(exc_traceback))
            message = "\n{0} raise {1}:{2}".format(
                formatted_traceback, exc_type.__name__, exc_instance
            )
            # raise exc_type(message)
            print(message)
            return None

    return wrapper


def _BSON_call_common(interface, func, param):
    """Args:
    interface: 
    func: 
    param:"""
    return _BSON_.BSON.decode(interface(func, _BSON_.BSON.encode(param)))


def create_view(viewID, view_type, title, group_id):
    """Args:
    viewID: 
    view_type: 
    title: 
    group_id:"""
    client = get_client()
    return client.createView(viewID, view_type, title, group_id)


# def reset_view(viewID):
#    return


def close_view(viewID):
    """Args:
    viewID:"""
    client = get_client()
    return client.closeView(viewID)


# def set_view_index(viewID, datas):
#    '''
#    设置模型指标属性
#    index: { "output1": { "datatype": se::OutputDataType } }
#    '''
#    client = get_client()
#    return client.setViewIndex(viewID, datas)


def push_view_data(viewID, datas):
    """推送模型结果数据
datas: { "timetags: [t1, t2, ...], "outputs": { "output1": [value1, value2, ...], ... }, "overwrite": "full/increase" }

Args:
    viewID: 
    datas:"""
    client = get_client()
    bresult = client.pushViewData(viewID, "index", _BSON_.BSON.encode(datas))
    return _BSON_.BSON.decode(bresult)


def switch_graph_view(stock_code=None, period=None, dividendtype=None, graphtype=None):
    """Args:
    stock_code: (Default value = None)
    period: (Default value = None)
    dividendtype: (Default value = None)
    graphtype: (Default value = None)"""
    cl = get_client()

    result = _BSON_call_common(
        cl.commonControl,
        "switchgraphview",
        {
            "stockcode": stock_code,
            "period": period,
            "dividendtype": dividendtype,
            "graphtype": graphtype,
        },
    )


def add_schedule(
    schedule_name,
    begin_time="",
    finish_time="",
    interval=60,
    run=False,
    only_work_date=False,
    always_run=False,
):
    """ToDo: 向客户端添加调度任务

Args:
    schedule_name: str
    begin_time: str (Default value = "")
    finish_time: (Default value = "")
    interval: int (Default value = 60)
    run: bool (Default value = False)
    only_work_date: bool (Default value = False)
    always_run: bool (Default value = False)

Returns:
    None"""

    cl = get_client()

    result = _BSON_call_common(
        cl.commonControl,
        "addschedule",
        {
            "name": schedule_name,
            "starttime": -1 if begin_time == "" else int(begin_time),
            "endtime": -1,
            "interval": interval * 1000,
            "run": run,
            "onlyworkdate": only_work_date,
            "alwaysrun": always_run,
        },
    )


def add_schedule_download_task(
    schedule_name,
    stock_code=[],
    period="",
    recentday=0,
    start_time="",
    end_time="",
    incrementally=False,
):
    """Args:
    schedule_name: 
    stock_code: list (Default value = [])
    period: str (Default value = "")
    recentday: int (Default value = 0)
    start_time: str (Default value = "")
    end_time: str (Default value = "")
    incrementally: bool (Default value = False)

Returns:
    None"""

    d_stockcode = {}
    for stock in stock_code:
        sp_stock = stock.split(".")
        if len(sp_stock) == 2:
            if sp_stock[1] not in d_stockcode:
                d_stockcode[sp_stock[1]] = []

            d_stockcode[sp_stock[1]].append(sp_stock[0])
        else:
            d_stockcode[stock] = []

    cl = get_client()

    result = _BSON_call_common(
        cl.commonControl,
        "addscheduledownloadtask",
        {
            "name": schedule_name,
            "market": list(d_stockcode.keys()),
            "stockcode": list(d_stockcode.values()),
            "period": period,
            "recentday": recentday,
            "starttime": start_time,
            "endtime": end_time,
            "incrementally": incrementally,
        },
    )
    return


def modify_schedule_task(
    schedule_name,
    begin_time="",
    finish_time="",
    interval=60,
    run=False,
    only_work_date=False,
    always_run=False,
):
    """Args:
    schedule_name: 
    begin_time: (Default value = "")
    finish_time: (Default value = "")
    interval: (Default value = 60)
    run: (Default value = False)
    only_work_date: (Default value = False)
    always_run: (Default value = False)"""
    cl = get_client()

    result = _BSON_call_common(
        cl.commonControl,
        "modifyschedule",
        {
            "name": schedule_name,
            "starttime": -1 if begin_time == "" else int(begin_time),
            "endtime": -1,
            "interval": interval * 1000,
            "run": run,
            "onlyworkdate": only_work_date,
            "alwaysrun": always_run,
        },
    )


def remove_schedule(schedule_name):
    """Args:
    schedule_name:"""
    cl = get_client()

    result = _BSON_call_common(
        cl.commonControl, "removeschedule", {"name": schedule_name}
    )
    return


def remove_schedule_download_task(schedule_name, task_id):
    """Args:
    schedule_name: 
    task_id:"""
    cl = get_client()

    result = _BSON_call_common(
        cl.commonControl,
        "removescheduledownloadtask",
        {"name": schedule_name, "taskids": task_id},
    )
    return


def query_schedule_task():
    """ """
    cl = get_client()

    inst = _BSON_call_common(cl.commonControl, "queryschedule", {})

    return inst.get("result", [])


def push_xtview_data(data_type, time, datas):
    """Args:
    data_type: 
    time: 
    datas:"""
    cl = get_client()
    timeData = 0
    types = []
    numericDatas = []
    stringDatas = []
    if isinstance(time, int):
        name_list = list(datas.keys())
        value_list = []
        for name in name_list:
            value_list.append([datas[name]])
        timeData = [time]
    if isinstance(time, list):
        time_list = time
        name_list = list(datas.keys())
        value_list = list(datas.values())
        timeData = time_list

    for value in value_list:
        if isinstance(value[0], str):
            stringDatas.append(value)
            types.append(3)
        else:
            numericDatas.append(value)
            types.append(0)

    result = _BSON_call_common(
        cl.custom_data_control,
        "pushxtviewdata",
        {
            "dataType": data_type,
            "timetags": timeData,
            "names": name_list,
            "types": types,
            "numericDatas": numericDatas,
            "stringDatas": stringDatas,
        },
    )
    return
