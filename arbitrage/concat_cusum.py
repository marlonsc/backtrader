#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量跑 CUSUM 策略 → 导出每日收益 → 汇总
使用方法：
    python run_pairs_cusum.py
"""

import subprocess, datetime, pathlib, pandas as pd, shutil, sys

# ---------- 固定参数 ----------
BASE_CMD = [
    sys.executable,                                # 调用当前 python 解释器
    "arbitrage/JM_J_strategy_CUSUM.py",
    "--window", "30",
    "--win", "20",
    "--k_coeff", "0.6",
    "--h_coeff", "3",
    "--setcash", "200000",
    "--plot", "true",
    "--setslippage", "0.0001",
    "--export_csv", "true"
]

# 要跑的配对 (df0_key, df1_key)   ← 根据需要增删
PAIRS = [
    ("/J",  "/JM"),     # 豆粕 / 菜粕
    ("/OI", "/Y"),      # 菜油 / 豆油
    ("/L",  "/MA"),     # 线性塑料 / 甲醇
    ("/P", "/Y")       # 螺纹钢 / PVC

]

OUT_DIR = pathlib.Path("outcome")
OUT_DIR.mkdir(exist_ok=True)

# ---------- 批量运行 ----------
csv_paths = []

for df0, df1 in PAIRS:
    print(f"\n>>> Running pair {df0} vs {df1}")
    cmd = BASE_CMD + ["--df0_key", df0, "--df1_key", df1]
    subprocess.run(cmd, check=True)

    # JM_J_strategy_CUSUM.py 会把 CSV 存到 outcome/ ，名字里含 df0df1
    # 找最新生成的那个文件
    pattern = f"CUSUM_backtest_{df0.replace('/', '')}{df1.replace('/', '')}_*.csv"
    latest = max(OUT_DIR.glob(pattern), key=lambda p: p.stat().st_mtime)
    csv_paths.append((f"{df0.strip('/')}-{df1.strip('/')}", latest))
    print(f"   → saved: {latest.name}")

# ---------- 汇总每日收益 ----------
print("\n>>> Combining daily returns …")
df_list = []
for label, path in csv_paths:
    df = pd.read_csv(path)
    if "daily_return" not in df.columns:
        raise ValueError(f"{path} 缺少 daily_return 列")
    df = df[["date", "daily_return"]].rename(columns={"daily_return": label})
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df_list.append(df)

combined = pd.concat(df_list, axis=1).fillna(0)        # 无交易日补 0
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
combo_file = OUT_DIR / f"combined_daily_returns_{ts}.csv"
combined.to_csv(combo_file)
print(f"组合文件已保存：{combo_file}")
