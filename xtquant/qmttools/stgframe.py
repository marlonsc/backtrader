"""stgframe.py module.

Description of the module functionality."""


from xtquant import xtbson as _BSON_
from xtquant import xtdata


class StrategyLoader:
""""""
"""Args::
    this:"""
"""Args::
    this:"""
"""Args::
    this:"""
"""Args::
    this:"""
"""Args::
    this:"""
"""Args::
    this:"""
"""Args::
    this:"""
"""Args::
    this:"""
"""Args::
    data:"""
"""Args::
    this: 
    timetag:"""
    timetag:"""
        if not this.C.timelist or this.C.timelist[-1] < timetag:
            this.C.timelist.append(timetag)
        this.run_bar()
        return

    def run_bar(this):
"""Args::
    this:"""
"""Args::
    this: 
    callback: (Default value = None)"""
    callback: (Default value = None)"""
        C = this.C
        client = xtdata.get_client()

        data = {
            "formulaname": "",
            "stockcode": C.stock_code,
            "period": C.period,
            "starttime": C.start_time_str,
            "endtime": C.end_time_str,
            "count": 1,
            "dividendtype": C.dividend_type,
            "create": True,
            "pyrunmode": 1,
            "title": C.title,
            "historycallback": 1 if callback else 0,
            "realtimecallback": 1 if callback else 0,
        }

        client.subscribeFormula(C.request_id, _BSON_.BSON.encode(data), callback)

    def call_formula(this, func, data):
"""Args::
    this: 
    func: 
    data:"""
    data:"""
        C = this.C
        client = xtdata.get_client()
        bresult = client.callFormula(C.request_id, func, _BSON_.BSON.encode(data))
        return _BSON_.BSON.decode(bresult)

    def create_view(this, title):
"""Args::
    this: 
    title:"""
    title:"""
        C = this.C
        client = xtdata.get_client()
        data = {
            "viewtype": 0,
            "title": title,
            "groupid": -1,
            "stockcode": C.market + C.stockcode,
            "period": C.period,
            "dividendtype": C.dividend_type,
        }
        client.createView(C.request_id, _BSON_.BSON.encode(data))
        return


class BackTestResult:
""""""
"""Args::
    request_id:"""
""""""
"""Args::
    fields: (Default value = [])"""
""""""
"""Args::
    request_id:"""
    request_id:"""
        self.request_id = request_id
