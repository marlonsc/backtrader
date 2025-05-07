"""xtextend.py module.

Description of the module functionality."""

""""""
"""Args::
    this: 
    path: 
    auto_lock: (Default value = False)"""
    auto_lock: (Default value = False)"""
        this.path = path
        this.fhandle = None
        if auto_lock:
            this.lock()
        return

    def is_lock(this):
"""Args::
    this:"""
"""Args::
    this:"""
"""Args::
    this:"""
"""Args::
    this:"""
""""""
"""Args::
    base_dir:"""
""""""
"""Args::
    data: 
    time_indexs: 
    stock_length:"""
    stock_length:"""
        from ctypes import POINTER, c_float, c_short, cast, sizeof

        res = {}
        num = (sizeof(self.value_type) + sizeof(self.rank_type)) * stock_length
        for time_index in time_indexs:
            index = num * time_index
            value_data = data[index : index + sizeof(self.value_type) * stock_length]
            values = cast(value_data, POINTER(c_float))
            rank_data = data[
                index + sizeof(self.value_type) * stock_length : index + num
            ]
            ranks = cast(rank_data, POINTER(c_short))
            res[self.timedatelist[time_index]] = [
                (round(values[i], 3), ranks[i]) for i in range(stock_length)
            ]

        return res

    def format_time(self, times):
"""Args::
    times:"""
"""Args::
    file: 
    times:"""
    times:"""
        import os
        import time

        self.file = os.path.join(self.base_dir, file + "_Xdat")
        if not os.path.isdir(self.file):
            return "No such file"

        fs = FileLock(os.path.join(self.file, "filelock"), False)

        while fs.is_lock():
            print("文件被占用")
            time.sleep(1)
        fs.lock()

        self.read_config()

        time_list = []

        if not times:
            time_list = self.timedatelist
        elif isinstance(times, list):
            time_list.extend([self.format_time(i) for i in times])
        else:
            time_list.append(self.format_time(times))

        time_index = [
            self.timedatelist.index(time)
            for time in time_list
            if self.timedatelist.count(time) != 0
        ]

        stock_length = len(self.stocklist)
        data = None
        with open(os.path.join(self.file, "data"), "rb") as f:
            data = f.read()
        fs.unlock()
        res = self.read_data(data, time_index, stock_length)
        return self.stocklist, res


def show_extend_data(file, times):
"""Args::
    file: 
    times:"""
    times:"""
    import os

    from . import xtdata as xd

    exd = Extender(os.path.join(xd.init_data_dir(), "..", "datadir"))

    return exd.show_extend_data(file, times)
