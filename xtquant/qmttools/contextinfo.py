"""contextinfo.py module.

Description of the module functionality."""


from . import functions as _FUNCS_


class ContextInfo:
""""""
"""Args::
    this:"""
"""Args::
    this:"""
"""Args::
    this: 
    value:"""
    value:"""
        this.start_time = value

    @property
    def end(this):
"""Args::
    this:"""
"""Args::
    this: 
    value:"""
    value:"""
        this.end_time = value

    @property
    def capital(this):
"""Args::
    this:"""
"""Args::
    this: 
    value:"""
    value:"""
        this.asset = value

    ### qmt strategy frame ###

    def init(this):
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
    this: 
    account_info:"""
    account_info:"""
        return

    def order_callback(this, order_info):
"""Args::
    this: 
    order_info:"""
    order_info:"""
        return

    def deal_callback(this, deal_info):
"""Args::
    this: 
    deal_info:"""
    deal_info:"""
        return

    def position_callback(this, position_info):
"""Args::
    this: 
    position_info:"""
    position_info:"""
        return

    def orderError_callback(this, passorder_info, msg):
"""Args::
    this: 
    passorder_info: 
    msg:"""
    msg:"""
        return

    ### qmt functions - bar ###

    def is_last_bar(this):
"""Args::
    this:"""
"""Args::
    this:"""
"""Args::
    this: 
    barpos: (Default value = None)"""
    barpos: (Default value = None)"""
        try:
            return (
                this.timelist[barpos]
                if barpos is not None
                else this.timelist[this.barpos]
            )
        except Exception:
            return None

    ### qmt functions - graph ###

    def paint(this, name, value, index=-1, drawstyle=0, color="", limit=""):
"""Args::
    this: 
    name: 
    value: 
    index: (Default value = -1)
    drawstyle: (Default value = 0)
    color: (Default value = "")
    limit: (Default value = "")"""
    limit: (Default value = "")"""
        vp = {str(this.get_bar_timetag()): value}

        if name not in this.result:
            this.result[name] = {}
        this.result[name].update(vp)

        if name not in this.push_result:
            this.push_result[name] = {}
        this.push_result[name].update(vp)
        return

    ### qmt functions - quote ###

    def subscribe_quote(
        this,
        stock_code="",
        period="",
        dividend_type="",
        result_type="",
        callback=None,
    ):
"""Args::
    this: 
    stock_code: (Default value = "")
    period: (Default value = "")
    dividend_type: (Default value = "")
    result_type: (Default value = "")
    callback: (Default value = None)"""
    callback: (Default value = None)"""
        if not stock_code:
            stock_code = this.stock_code
        if not period or period == "follow":
            period = this.period
        if not dividend_type or dividend_type == "follow":
            dividend_type = this.dividend_type
        return _FUNCS_.subscribe_quote(
            stock_code, period, dividend_type, 0, result_type, callback
        )

    def subscribe_whole_quote(this, code_list, callback=None):
"""Args::
    this: 
    code_list: 
    callback: (Default value = None)"""
    callback: (Default value = None)"""
        return _FUNCS_.subscribe_whole_quote(code_list, callback)

    def unsubscribe_quote(this, subscribe_id):
"""Args::
    this: 
    subscribe_id:"""
    subscribe_id:"""
        return _FUNCS_.unsubscribe_quote(subscribe_id)

    def get_market_data(
        this,
        fields=[],
        stock_code=[],
        start_time="",
        end_time="",
        skip_paused=True,
        period="",
        dividend_type="",
        count=-1,
    ):
"""Args::
    this: 
    fields: (Default value = [])
    stock_code: (Default value = [])
    start_time: (Default value = "")
    end_time: (Default value = "")
    skip_paused: (Default value = True)
    period: (Default value = "")
    dividend_type: (Default value = "")
    count: (Default value = -1)"""
    count: (Default value = -1)"""
        if not stock_code:
            stock_code = [this.stock_code]
        if not period or period == "follow":
            period = this.period
        if not dividend_type or dividend_type == "follow":
            dividend_type = this.dividend_type
        if period != "tick" and count == -1 and len(fields) == 1:
            if not end_time or end_time == "follow":
                if this.barpos >= 0:
                    end_time = _FUNCS_.timetag_to_datetime(
                        this.get_bar_timetag(this.barpos)
                    )
                    count = -2
        if (
            period == "tick"
            and count == -1
            and len(fields) == 1
            and start_time == ""
            and end_time == ""
        ):
            count = -2

        return _FUNCS_.get_market_data(
            fields,
            stock_code,
            start_time,
            end_time,
            skip_paused,
            period,
            dividend_type,
            count,
        )

    def get_market_data_ex(
        this,
        fields=[],
        stock_code=[],
        period="",
        start_time="",
        end_time="",
        count=-1,
        dividend_type="",
        fill_data=True,
        subscribe=True,
    ):
"""Args::
    this: 
    fields: (Default value = [])
    stock_code: (Default value = [])
    period: (Default value = "")
    start_time: (Default value = "")
    end_time: (Default value = "")
    count: (Default value = -1)
    dividend_type: (Default value = "")
    fill_data: (Default value = True)
    subscribe: (Default value = True)"""
    subscribe: (Default value = True)"""
        if not stock_code:
            stock_code = [this.stock_code]
        if not period or period == "follow":
            period = this.period
        if not dividend_type or dividend_type == "follow":
            dividend_type = this.dividend_type

        if not this.subscribe_once and subscribe:
            this.subscribe_once = True
            if period != "tick":
                for stk in stock_code:
                    _FUNCS_.subscribe_quote(stk, period, dividend_type, -1)
            else:
                for stk in stock_code:
                    this.subscribe_whole_quote(stk)

        return _FUNCS_.get_market_data_ex(
            fields,
            stock_code,
            period,
            start_time,
            end_time,
            count,
            dividend_type,
            fill_data,
            subscribe,
        )

    def get_full_tick(this, stock_code=[]):
"""Args::
    this: 
    stock_code: (Default value = [])"""
    stock_code: (Default value = [])"""
        if not stock_code:
            stock_code = [this.stock_code]
        return _FUNCS_.get_full_tick(stock_code)

    def get_divid_factors(this, stock_code="", date=None):
"""Args::
    this: 
    stock_code: (Default value = "")
    date: (Default value = None)"""
    date: (Default value = None)"""
        if not stock_code:
            stock_code = this.stock_code
        return _FUNCS_.get_divid_factors(stock_code, date)

    ### qmt functions - finance ###

    def get_financial_data(
        this,
        field_list,
        stock_list,
        start_date,
        end_date,
        report_type="announce_time",
    ):
"""Args::
    this: 
    field_list: 
    stock_list: 
    start_date: 
    end_date: 
    report_type: (Default value = "announce_time")"""
    report_type: (Default value = "announce_time")"""
        raise "not implemented, use get_raw_financial_data instead"
        return

    def get_raw_financial_data(
        this,
        field_list,
        stock_list,
        start_date,
        end_date,
        report_type="announce_time",
    ):
"""Args::
    this: 
    field_list: 
    stock_list: 
    start_date: 
    end_date: 
    report_type: (Default value = "announce_time")"""
    report_type: (Default value = "announce_time")"""
        return _FUNCS_.get_raw_financial_data(
            field_list, stock_list, start_date, end_date, report_type
        )

    ### qmt functions - option ###

    def get_option_detail_data(this, optioncode):
"""Args::
    this: 
    optioncode:"""
    optioncode:"""
        return _FUNCS_.get_option_detail_data(optioncode)

    def get_option_undl_data(this, undl_code_ref):
"""Args::
    this: 
    undl_code_ref:"""
    undl_code_ref:"""
        return _FUNCS_.get_option_undl_data(undl_code_ref)

    def get_option_list(this, undl_code, dedate, opttype="", isavailavle=False):
"""Args::
    this: 
    undl_code: 
    dedate: 
    opttype: (Default value = "")
    isavailavle: (Default value = False)"""
    isavailavle: (Default value = False)"""
        return _FUNCS_.get_option_list(undl_code, dedate, opttype, isavailavle)

    def get_option_iv(this, opt_code):
"""Args::
    this: 
    opt_code:"""
    opt_code:"""
        return _FUNCS_.get_opt_iv(opt_code, this.request_id)

    def bsm_price(
        this,
        optType,
        targetPrice,
        strikePrice,
        riskFree,
        sigma,
        days,
        dividend=0,
    ):
"""Args::
    this: 
    optType: 
    targetPrice: 
    strikePrice: 
    riskFree: 
    sigma: 
    days: 
    dividend: (Default value = 0)"""
    dividend: (Default value = 0)"""
        optionType = ""
        if optType.upper() == "C":
            optionType = "CALL"
        if optType.upper() == "P":
            optionType = "PUT"
        if isinstance(targetPrice, list):
            result = []
            for price in targetPrice:
                bsmPrice = _FUNCS_.calc_bsm_price(
                    optionType,
                    strikePrice,
                    float(price),
                    riskFree,
                    sigma,
                    days,
                    dividend,
                    this.request_id,
                )
                bsmPrice = round(bsmPrice, 4)
                result.append(bsmPrice)
            return result
        else:
            bsmPrice = _FUNCS_.calc_bsm_price(
                optionType,
                strikePrice,
                targetPrice,
                riskFree,
                sigma,
                days,
                dividend,
                this.request_id,
            )
            result = round(bsmPrice, 4)
            return result

    def bsm_iv(
        this,
        optType,
        targetPrice,
        strikePrice,
        optionPrice,
        riskFree,
        days,
        dividend=0,
    ):
"""Args::
    this: 
    optType: 
    targetPrice: 
    strikePrice: 
    optionPrice: 
    riskFree: 
    days: 
    dividend: (Default value = 0)"""
    dividend: (Default value = 0)"""
        if optType.upper() == "C":
            optionType = "CALL"
        if optType.upper() == "P":
            optionType = "PUT"
        result = _FUNCS_.calc_bsm_iv(
            optionType,
            strikePrice,
            targetPrice,
            optionPrice,
            riskFree,
            days,
            dividend,
            this.request_id,
        )
        result = round(result, 4)
        return result

    ### qmt functions - static ###

    def get_instrument_detail(this, stock_code="", iscomplete=False):
"""Args::
    this: 
    stock_code: (Default value = "")
    iscomplete: (Default value = False)"""
    iscomplete: (Default value = False)"""
        if not stock_code:
            stock_code = this.stock_code
        return _FUNCS_.get_instrument_detail(stock_code, iscomplete)

    get_instrumentdetail = get_instrument_detail  # compat

    def get_trading_dates(this, stock_code, start_date, end_date, count, period="1d"):
"""Args::
    this: 
    stock_code: 
    start_date: 
    end_date: 
    count: 
    period: (Default value = "1d")"""
    period: (Default value = "1d")"""
        return _FUNCS_.get_trading_dates(
            stock_code, start_date, end_date, count, period
        )

    def get_stock_list_in_sector(this, sector_name):
"""Args::
    this: 
    sector_name:"""
    sector_name:"""
        return _FUNCS_.get_stock_list_in_sector(sector_name)

    def passorder(
        this,
        opType,
        orderType,
        accountid,
        orderCode,
        prType,
        modelprice,
        volume,
        strategyName,
        quickTrade,
        userOrderId,
    ):
"""Args::
    this: 
    opType: 
    orderType: 
    accountid: 
    orderCode: 
    prType: 
    modelprice: 
    volume: 
    strategyName: 
    quickTrade: 
    userOrderId:"""
    userOrderId:"""
        return _FUNCS_._passorder_impl(
            opType,
            orderType,
            accountid,
            orderCode,
            prType,
            modelprice,
            volume,
            strategyName,
            quickTrade,
            userOrderId,
            this.barpos,
            this.get_bar_timetag(),
            "passorder",
            "",
            this.request_id,
        )

    def set_auto_trade_callback(this, enable):
"""Args::
    this: 
    enable:"""
    enable:"""
        return _FUNCS_._set_auto_trade_callback_impl(enable, this.request_id)

    def set_account(this, accountid):
"""Args::
    this: 
    accountid:"""
    accountid:"""
        return _FUNCS_.set_account(accountid, this.request_id)

    def get_his_st_data(this, stock_code):
"""Args::
    this: 
    stock_code:"""
    stock_code:"""
        return _FUNCS_.get_his_st_data(stock_code)

    ### private ###

    def trade_callback(this, type, result, error):
"""Args::
    this: 
    type: 
    result: 
    error:"""
    error:"""

        class DetailData(object):
""""""
"""Args::
    _obj:"""
"""Args::
    this: 
    reqid:"""
    reqid:"""
        _FUNCS_.register_external_resp_callback(reqid, this.trade_callback)
        return

    def get_callback_cache(this, type):
"""Args::
    this: 
    type:"""
    type:"""
        return _FUNCS_._get_callback_cache_impl(type, this.request_id)

    def get_ipo_info(this, start_time="", end_time=""):
"""Args::
    this: 
    start_time: (Default value = "")
    end_time: (Default value = "")"""
    end_time: (Default value = "")"""
        return _FUNCS_.get_ipo_info(start_time, end_time)

    def get_backtest_index(this, path):
"""Args::
    this: 
    path:"""
    path:"""
        _FUNCS_.get_backtest_index(this.request_id, path)

    def get_group_result(this, path, fields):
"""Args::
    this: 
    path: 
    fields:"""
    fields:"""
        _FUNCS_.get_group_result(this.request_id, path, fields)

    def is_suspended_stock(this, stock_code, type):
"""Args::
    this: 
    stock_code: 
    type:"""
    type:"""
        if this.barpos > len(this.timelist):
            return False

        if type == 1 or len(this.timelist) == 0:
            inst = this.get_instrument_detail(stock_code)
            return inst.get("InstrumentStatus", 0) >= 1

        return _FUNCS_.is_suspended_stock(
            stock_code, this.period, this.timelist[this.barpos]
        )
