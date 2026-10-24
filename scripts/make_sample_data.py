
# -*- coding: utf-8 -*-
"""生成仓库自带的合成样例数据（Sample Mode）。

这些 CSV **不是**真实 RESSET 数据，也不含任何真实股票信息：股票代码、价格、财务金额全部由
随机数生成器按固定种子生成，仅用于在无 RESSET 权限时验证读取、清洗、特征、错期、分组、
市值加权与回归代码能否正确跑通。列名、单位与列顺序对齐 RESSET 导出文件的真实格式。

用法：
    python scripts/make_sample_data.py                # 写到 data/sample
    python scripts/make_sample_data.py --stocks 60    # 改股票数
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]

DAILY_COLS = [
    'Stkcd', 'Lstknm', 'Stkcdotrd', 'Listedstate', 'Date', 'Clpr', 'Trdvol', 'Trdsum',
    'Fullshr', 'Dret', 'DRfRet', 'PE', 'PB', 'EPS', 'ROE', 'Infopubdt', 'Enddt', 'Reporttype',
]
MONTHLY_COLS = [
    'Stkcd', 'Listedstate', 'Lstknm', 'Stkcdotrd', 'Date', 'ClPr', 'Trdvol', 'Trdsum',
    'Fullshr', 'Montrds', 'Monret', 'Monrfret', 'PE', 'PB', 'EPS', 'ROE',
    'Infopubdt', 'Enddt', 'Reporttype',
]
BS_COLS = [
    'A_StkCd', 'ReportType', 'EndDt', 'InfoPubDt', 'TotAss', 'TotCurrAss', 'TotCurLia',
    'ShortLoan', 'LongLoan', 'TaxPay', 'CashEqv', 'TradAss', 'TotLiab',
]
CF_COLS = [
    'A_StkCd', 'ReportType', 'EndDt', 'InfoPubDt', 'CENetIncr', 'IntangAssAmort', 'DeferExpAmort',
]
FAS_COLS = ['A_StkCd', 'ReportType', 'EndDt', 'FixAssType', 'CurIncrAD']

DAILY_DIR = 'RESSET_SAMPLE_日股票综合数据'
MONTHLY_DIR = 'RESSET_SAMPLE_月股票综合数据'
BS_DIR = 'RESSET_SAMPLE_资产负债表'
CF_DIR = 'RESSET_SAMPLE_现金流量表'
FAS_DIR = 'RESSET_SAMPLE_固定资产及折旧'


def build_codes(n_stocks):
    half = n_stocks // 2
    shenzhen = ['%06d' % (1 + i) for i in range(half)]
    shanghai = ['6000%02d' % (1 + i) for i in range(n_stocks - half)]
    return shenzhen + shanghai


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=str(REPO / 'data' / 'sample'))
    parser.add_argument('--stocks', type=int, default=40)
    parser.add_argument('--start', default='2013-01-01')
    parser.add_argument('--end', default='2014-12-31')
    parser.add_argument('--seed', type=int, default=20240101)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    out = Path(args.out)
    raw = out / 'raw'
    for name in (DAILY_DIR, MONTHLY_DIR, BS_DIR, CF_DIR, FAS_DIR):
        (raw / name).mkdir(parents=True, exist_ok=True)

    codes = build_codes(args.stocks)
    n = len(codes)
    dates = pd.bdate_range(args.start, args.end)
    t = len(dates)

    # 横截面特征：规模与账面市值比都带持久差异，保证分组不会退化成一组
    log_size = rng.uniform(20.0, 24.0, n)            # log(总市值，单位元)
    size_z = (log_size - log_size.mean()) / log_size.std()
    bm = rng.uniform(0.15, 1.20, n)                  # 账面市值比
    value_z = (bm - bm.mean()) / bm.std()
    shares = np.round(rng.uniform(0.6e8, 4.0e8, n) / 1e6) * 1e6
    price0 = np.exp(log_size) / shares
    price0 = np.clip(price0, 3.0, 80.0)
    market_value = price0 * shares

    # 共同市场因子 + 规模/价值倾斜 + 个股噪声
    market = rng.normal(0.0003, 0.010, t)
    drift = 0.00015 - 0.00012 * size_z + 0.00010 * value_z
    idio = rng.normal(0, 0.018, (t, n))
    daily_ret = drift[None, :] + market[:, None] + idio
    daily_ret[rng.random((t, n)) < 0.004] = 0.0       # 少量停牌日（收益记 0）

    prices = price0[None, :] * np.cumprod(1 + daily_ret, axis=0)
    prices = np.vstack([price0[None, :], prices[:-1]])  # 当日价格对应前一日收盘

    rf_daily = 0.035 / 252.0
    daily_rf = np.full((t, n), rf_daily)

    pe0 = rng.uniform(8.0, 40.0, n)
    eps = price0 / pe0
    roe = rng.uniform(4.0, 22.0, n)                    # 百分数
    pb = 1.0 / bm

    # 最新年报（Q4）→ 公告日 +4 个月，日表按公告日向后填充
    fiscal = [pd.Timestamp('2011-12-31'), pd.Timestamp('2012-12-31'), pd.Timestamp('2013-12-31')]
    pub = [d + pd.DateOffset(months=4) for d in fiscal]
    last_end = fiscal[0]
    last_pub = pub[0]
    end_arr, pub_arr = [], []
    for d in dates:
        idx = max([i for i, p in enumerate(pub) if p <= d], default=-1)
        if idx >= 0:
            last_end, last_pub = fiscal[idx], pub[idx]
        end_arr.append(last_end)
        pub_arr.append(last_pub)

    daily = pd.DataFrame({
        'Stkcd': np.repeat(codes, t),
        'Lstknm': np.repeat(['例股%02d' % (i + 1) for i in range(n)], t),
        'Stkcdotrd': np.repeat(codes, t),
        'Listedstate': 'Norm',
        'Date': np.tile(dates.values, n),
        'Clpr': np.round(prices.T.ravel(), 4),
        'Trdvol': np.round(
            np.repeat(shares, t) * rng.uniform(0.002, 0.020, t * n)).astype('int64'),
        'Trdsum': np.round(
            prices.T.ravel() * np.repeat(shares, t) * rng.uniform(0.002, 0.020, t * n), 2),
        'Fullshr': np.repeat(shares, t),
        'Dret': np.round(daily_ret.T.ravel(), 6),
        'DRfRet': np.round(daily_rf.T.ravel(), 8),
        'PE': np.round(np.repeat(pe0, t), 4),
        'PB': np.round(np.repeat(pb, t), 4),
        'EPS': np.round(np.repeat(eps, t), 4),
        'ROE': np.round(np.repeat(roe, t), 4),
        'Infopubdt': np.tile(np.array(pub_arr, dtype='datetime64[D]').astype(str), n),
        'Enddt': np.tile(np.array(end_arr, dtype='datetime64[D]').astype(str), n),
        'Reporttype': 'Q4',
    })[DAILY_COLS]
    daily.to_csv(raw / DAILY_DIR / 'RESSET_DRESSTK_SAMPLE.csv', index=False, encoding='utf-8')

    # 月表：按自然月最后交易日聚合
    d = daily.copy()
    d['Date'] = pd.to_datetime(d['Date'])
    d['ym'] = d['Date'].dt.to_period('M')
    rows = []
    for code, g in d.groupby('Stkcd', sort=True):
        g = g.sort_values('Date')
        for period, gm in g.groupby('ym', sort=True):
            gm = gm.sort_values('Date')
            rows.append({
                'Stkcd': code,
                'Listedstate': 'Norm',
                'Lstknm': gm['Lstknm'].iloc[-1],
                'Stkcdotrd': code,
                'Date': gm['Date'].iloc[-1].strftime('%Y-%m-%d'),
                'ClPr': round(float(gm['Clpr'].iloc[-1]), 4),
                'Trdvol': int(gm['Trdvol'].sum()),
                'Trdsum': round(float(gm['Trdsum'].sum()), 2),
                'Fullshr': float(gm['Fullshr'].iloc[-1]),
                'Montrds': int(gm['Trdvol'].sum()),
                'Monret': round(float(np.prod(1 + gm['Dret']) - 1), 6),
                'Monrfret': round(float(np.prod(1 + gm['DRfRet']) - 1), 8),
                'PE': float(gm['PE'].iloc[-1]),
                'PB': float(gm['PB'].iloc[-1]),
                'EPS': float(gm['EPS'].iloc[-1]),
                'ROE': float(gm['ROE'].iloc[-1]),
                'Infopubdt': gm['Infopubdt'].iloc[-1],
                'Enddt': gm['Enddt'].iloc[-1],
                'Reporttype': 'Q4',
            })
    pd.DataFrame(rows, columns=MONTHLY_COLS).to_csv(
        raw / MONTHLY_DIR / 'RESSET_MRESSTK_SAMPLE.csv', index=False, encoding='utf-8')

    # 年度财报表：每个股票 3 个财年
    bs_rows, cf_rows, fas_rows = [], [], []
    for i, code in enumerate(codes):
        base = float(np.exp(log_size[i]))
        growth = rng.uniform(0.03, 0.22)
        for k, end in enumerate(fiscal):
            ta = base * (1.0 + growth) ** k
            bs_rows.append({
                'A_StkCd': code, 'ReportType': 'Q4', 'EndDt': end.strftime('%Y-%m-%d'),
                'InfoPubDt': pub[k].strftime('%Y-%m-%d'),
                'TotAss': round(ta, 2), 'TotCurrAss': round(0.55 * ta, 2),
                'TotCurLia': round(0.35 * ta, 2), 'ShortLoan': round(0.08 * ta, 2),
                'LongLoan': round(0.05 * ta, 2), 'TaxPay': round(0.01 * ta, 2),
                'CashEqv': round(0.15 * ta, 2), 'TradAss': round(0.01 * ta, 2),
                'TotLiab': round(0.45 * ta, 2),
            })
            cf_rows.append({
                'A_StkCd': code, 'ReportType': 'Q4', 'EndDt': end.strftime('%Y-%m-%d'),
                'InfoPubDt': pub[k].strftime('%Y-%m-%d'),
                'CENetIncr': round(ta * rng.uniform(-0.03, 0.08), 2),
                'IntangAssAmort': round(0.004 * ta, 2),
                'DeferExpAmort': round(0.001 * ta, 2),
            })
            fas_rows.append({
                'A_StkCd': code, 'ReportType': 'Q4', 'EndDt': end.strftime('%Y-%m-%d'),
                'FixAssType': '99999', 'CurIncrAD': round(0.03 * ta, 2),
            })
    pd.DataFrame(bs_rows, columns=BS_COLS).to_csv(
        raw / BS_DIR / 'RESSET_BS_ALL_1.csv', index=False, encoding='utf-8')
    pd.DataFrame(cf_rows, columns=CF_COLS).to_csv(
        raw / CF_DIR / 'RESSET_SCF_ALL_1.csv', index=False, encoding='utf-8')
    pd.DataFrame(fas_rows, columns=FAS_COLS).to_csv(
        raw / FAS_DIR / 'RESSET_BSNOTE_FIXASSDEPR_SAMPLE.csv', index=False, encoding='utf-8')

    print('sample written to', raw)
    print('stocks=%d  trading days=%d  daily rows=%d  months=%d'
          % (n, t, len(daily), len(rows)))


if __name__ == '__main__':
    main()
