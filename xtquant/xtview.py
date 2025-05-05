# coding:utf-8

from . import xtbson as _BSON_

# connection

__client = None
__client_last_spec = ("", None)


def connect(ip="", port=None, remember_if_success=True):
    """

    :param ip:  (Default value = "")
    :param port:  (Default value = None)
    :param remember_if_success:  (Default value = True)

    """
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
    """

    :param ip:  (Default value = "")
    :param port:  (Default value = None)
    :param remember_if_success:  (Default value = True)

    """
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
    """

    :param func:

    """
    import sys
    import traceback

    def wrapper(*args, **kwargs):
        """

        :param *args:
        :param **kwargs:

        """
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
    """

    :param interface:
    :param func:
    :param param:

    """
    return _BSON_.BSON.decode(interface(func, _BSON_.BSON.encode(param)))


def create_view(viewID, view_type, title, group_id):
    """

    :param viewID:
    :param view_type:
    :param title:
    :param group_id:

    """
    client = get_client()
    return client.createView(viewID, view_type, title, group_id)


# def reset_view(viewID):
#    return


def close_view(viewID):
    """

    :param viewID:

    """
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

    :param viewID:
    :param datas:

    """
    client = get_client()
    bresult = client.pushViewData(viewID, "index", _BSON_.BSON.encode(datas))
    return _BSON_.BSON.decode(bresult)


def switch_graph_view(stock_code=None, period=None, dividendtype=None, graphtype=None):
    """

    :param stock_code:  (Default value = None)
    :param period:  (Default value = None)
    :param dividendtype:  (Default value = None)
    :param graphtype:  (Default value = None)

    """
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

    :param schedule_name: str
    :param begin_time: str (Default value = "")
    :param finish_time:  (Default value = "")
    :param interval: int (Default value = 60)
    :param run: bool (Default value = False)
    :param only_work_date: bool (Default value = False)
    :param always_run: bool (Default value = False)
    :returns: None
    Example::

        # 向客户端添加一个每日下载沪深A股市场的日K任务
        from xtquant import xtview, xtdata
        stock_list = xtdata.get_stock_list_in_sector("沪深A股")
        xtview.add_schedule(
            schedule_name = "test计划",
            begin_time ="150500",
            interval = 60*60*24,
            run = True,
            only_work_date = True,
            always_run = False)

    """

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
    """

    :param schedule_name:
    :param stock_code: list (Default value = [])
    :param period: str (Default value = "")
    :param recentday: int (Default value = 0)
    :param start_time: str (Default value = "")
    :param end_time: str (Default value = "")
    :param incrementally: bool (Default value = False)
    :returns: None
    Example::
        # 向客户端现存的调度方案中添加一个下载任务
        xtview.add_schedule_download_task(
            schedule_name = "test计划",
            stock_code = stock_list
            period = "1d" )
    """

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
    """

    :param schedule_name:
    :param begin_time:  (Default value = "")
    :param finish_time:  (Default value = "")
    :param interval:  (Default value = 60)
    :param run:  (Default value = False)
    :param only_work_date:  (Default value = False)
    :param always_run:  (Default value = False)

    """
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
    """

    :param schedule_name:

    """
    cl = get_client()

    result = _BSON_call_common(
        cl.commonControl, "removeschedule", {"name": schedule_name}
    )
    return


def remove_schedule_download_task(schedule_name, task_id):
    """

    :param schedule_name:
    :param task_id:

    """
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
    """

    :param data_type:
    :param time:
    :param datas:

    """
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
