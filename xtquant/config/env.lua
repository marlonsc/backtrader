g_minVersion = "2.0.1.600"
g_minMobileVersion = "1.0.0.0"
g_company = "����ڿ�"
g_is_address_from_daemon = false
g_use_proxy_whole_quoter = 1
g_use_future_whole_quoter = 0
g_server_deploy_type = 0

g_defaultPorts = {
    xtdaemon="127.0.0.1:55000",
    xtservice="127.0.0.1:56000",
    xtindex="127.0.0.1:56001",
    xtmonitor="127.0.0.1:56002",
    xtwebservice="127.0.0.1:56003",
    xttraderservice="127.0.0.1:57000",
    xtquoter="127.0.0.1:59000",
    xtriskcontrol="127.0.0.1:60000",
    proxy="210.14.136.66:55300",
    proxy_backup="203.156.205.182:55300",
    xtcounter="127.0.0.1:61100",
    xtgateway="127.0.0.1:62100",
    xtsource="127.0.0.1:63000",
    xtitsmservice="127.0.0.1:63500",
    xttask="127.0.0.1:61000",
    xtquerybroker="127.0.0.1:65000",
    xtotp="127.0.0.1:64200",
    xtlogcenter="127.0.0.1:65100",
    xtctpservice="127.0.0.1:65200",
    xtapiservice="127.0.0.1:65300",
    xtclearservice="127.0.0.1:64100",
    xtdelegateservice="127.0.0.1:64300",
    xtalgoadapterservice="127.0.0.1:64500",
    xtmarket = "127.0.0.1:60100",
    xtfairplayservice="127.0.0.1:64600",
    xtnonstandardservice="127.0.0.1:64703",
    xtantisharefinancingservice = "127.0.0.1:64800",
    xtmysqlservice="127.0.0.1:64704",
    xtmobileservice="127.0.0.1:65400",
    xtmarketinfo="210.14.136.69:59500",
}

g_allPlatforms = {}
g_allBrokers = {}
g_fairPlayUnits = {}

g_ttservice_global_config = {
    m_maxClientCount=1,
    m_logCfg="ttservice.log4cxx",
    m_listenIP="0.0.0.0",
    m_nListenPort=56100,
    m_proxyIP="210.14.136.66",
    m_nProxyPort=55808,
    m_nWorkFlowPort=63000,
    m_workFlowIP="127.0.0.1",
    m_redisHost="127.0.0.1",
    m_redisPort=6379,
    m_nPortalThread=5,
    m_addrsPath="",
    m_nProductMaxPortfilio=100,
    m_debugAccounts="",
    m_nUseMd5=0,
}

g_future_quote_platforms = {
    {m_nId=20001, m_strName="CTPʵ��", m_strAbbrName="sqsp", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=20002, m_strName="����ʵ��", m_strAbbrName="hssp", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=21018, m_strName="v8tʵ��", m_strAbbrName="sqsp", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=21001, m_strName="CTPģ��", m_strAbbrName="gdmn", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=21002, m_strName="����ģ��", m_strAbbrName="hsmn", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=21003, m_strName="v8tģ��", m_strAbbrName="gdmn", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=20000, m_strName="ѸͶ�߼�����", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=21111, m_strName="�ʹ�ʵ��", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=21112, m_strName="�ʹ�ģ��", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=20013, m_strName="����ʵ��", m_strAbbrName="hshl", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=21013, m_strName="����ģ��", m_strAbbrName="hshl", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=21015, m_strName="������Խ", m_strAbbrName="hsdy", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=21014, m_strName="����Ӣ��", m_strAbbrName="hsyd", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=21017, m_strName="�������", m_strAbbrName="hsjg", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=21019, m_strName="������ԭ", m_strAbbrName="hszy", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=20015, m_strName="������Խʵ��", m_strAbbrName="hsdysp", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=20014, m_strName="����Ӣ��ʵ��", m_strAbbrName="hsydsp", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=20017, m_strName="�������ʵ��", m_strAbbrName="hsjgsp", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
    {m_nId=20019, m_strName="������ԭʵ��", m_strAbbrName="hszysp", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=1,},
}

g_futureoption_quote_platforms = {
    {m_nId=70001, m_strName="CTPʵ��", m_strAbbrName="sqsp", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=5,},
    {m_nId=71001, m_strName="CTPģ��", m_strAbbrName="gdmn", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=5,},
    {m_nId=71111, m_strName="�ʹ�ʵ��", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=5,},
    {m_nId=71112, m_strName="�ʹ�ģ��", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=5,},
}

g_stock_quote_platforms = {
    {m_nId=10000, m_strName="ѸͶ�߼�����", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=2,},
    {m_nId=1111, m_strName="�ʹ�ʵ��", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=2,},
    {m_nId=1112, m_strName="�ʹ�ģ��", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=2,},
}

g_credit_quote_platforms = {
    {m_nId=10000, m_strName="ѸͶ�߼�����", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=3,},
}

g_stockoption_quote_platforms = {
    {m_nId=10001, m_strName="ѸͶ�߼�����", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=6,},
    {m_nId=1211, m_strName="�ʹ�ʵ��", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=6,},
    {m_nId=1212, m_strName="�ʹ�ģ��", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=6,},
}

g_hgt_quote_platforms = {
    {m_nId=10003, m_strName="ѸͶ�߼�����", m_strAbbrName="hgtmn", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=7,},
    {m_nId=1411, m_strName="�ʹ�ʵ��", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=7,},
    {m_nId=1412, m_strName="�ʹ�ģ��", m_strAbbrName="xtgj", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=7,},
}

g_new3board_quote_platforms = {
    {m_nId=10002, m_strName="ѸͶ�߼�����", m_strAbbrName="neeq", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=10,},
    {m_nId=1311, m_strName="�ʹ�ʵ��", m_strAbbrName="neeq", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=10,},
    {m_nId=1312, m_strName="�ʹ�ģ��", m_strAbbrName="neeq", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=10,},
}

g_gold_quote_platforms = {
	{m_nId=31003, m_strName="ѸͶ�߼�����", m_strAbbrName="zxjtgold", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=4,},
    {m_nId=31111, m_strName="�ʹ�ʵ��", m_strAbbrName="zxjtgold", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=4,},
    {m_nId=31112, m_strName="�ʹ�ģ��", m_strAbbrName="zxjtgold", m_strLogo="broker_logo_1", m_strBrokerTag="xtbroker", m_strQuoterTag="xtquoter", m_nType=4,},
}

g_future_order_limits = {
    {m_strProductID="IF", m_nLimit=200},
    {m_strProductID="AU", m_nLimit=100},
}

g_banks = {
    {m_strLogo="bank_logo_1", m_strId="1", m_strName="��������",},
    {m_strLogo="bank_logo_2", m_strId="2", m_strName="ũҵ����",},
    {m_strLogo="bank_logo_3", m_strId="3", m_strName="�й�����",},
    {m_strLogo="bank_logo_4", m_strId="4", m_strName="��������",},
    {m_strLogo="bank_logo_5", m_strId="5", m_strName="��ͨ����",},
    {m_strLogo="bank_logo_6", m_strId="6", m_strName="���ڽ���",},
    {m_strLogo="bank_logo_Z", m_strId="Z", m_strName="��������",}
}

g_batchOrder_config = {
    -- Whether to enable batch ordinary order, 0 means disabled
    is_batch_ordinaryOrder = 1,
    -- After how many batch ordinary orders to send all at once
    buffer_clear_duration_milli_sec = 100,
    buffer_clear_max_order_num = 100,
    -- apiserver order upper limit per time window
    api_order_upper_limit = 1000,
    -- The upper limit of batch order per time window, after reaching the limit, send immediately
    api_order_duration_milli_sec = 1000,
    -- Minimum interval for algorithmic orders, 0.5s
    api_min_algorithm_order_duration_milli_sec = 500,
    -- Minimum interval for group orders, 10s
    api_min_group_order_duration_milli_sec = 10000,
    max_order_duration_milli_sec = -1,
    max_order_count = -1,
}
