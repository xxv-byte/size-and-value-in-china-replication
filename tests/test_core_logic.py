
# -*- coding: utf-8 -*-
"""行为测试：直接调用 Notebook 里的真实函数，在小型合成表上验证数据口径。

覆盖：股票代码规范化、清洗、股票池、日频特征、point-in-time 对齐、资产增长、
12-1 动量、月收益复利、形成月/持有月错期、2×3 因子构造、单变量十分位分组、
时间序列回归、单次截面回归、Fama-MacBeth。

注意：这些测试验证「函数在给定输入上的行为」，不验证真实数据下的论文数值。
"""
import contextlib
import io
import unittest

import numpy as np
import pandas as pd

from notebook_loader import SRC_JUP, load

NS = load(notebooks=[
    SRC_JUP / 'clean_and_universe_2.ipynb',
    SRC_JUP / 'features_3.ipynb',
    SRC_JUP / 'monthly_4.ipynb',
    SRC_JUP / 'portfolio_5.ipynb',
    SRC_JUP / 'time_series_regression_6.ipynb',
    SRC_JUP / 'cross_section_regression_7.ipynb',
    SRC_JUP / 'fama_macbeth_8.ipynb',
])


def quiet(func, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)


class CleaningTests(unittest.TestCase):
    def test_normalize_stock_code(self):
        codes = pd.Series([1, 1.0, '000001', ' 600001 ', 'ABC', None])
        out = NS['normalize_stock_code'](codes)
        self.assertEqual(out.tolist()[:4], ['000001', '000001', '000001', '600001'])
        self.assertTrue(out.iloc[4:].isna().all())

    def test_cleaning_drops_duplicates_and_missing(self):
        base = {
            'Stkcd': ['000001', '000001', '000002'],
            'Date': ['2013-01-04', '2013-01-04', '2013-01-07'],
            'Clpr': [10.0, 10.0, 20.0],
            'Fullshr': [1e8, 1e8, 2e8],
            'Dret': [0.01, 0.01, 0.02],
            'DRfRet': [0.0001, 0.0001, 0.0001],
            'PB': [2.0, 2.0, np.nan],
            'ROE': [10.0, 10.0, 12.0],
            'Trdvol': [1e6, 1e6, 2e6],
            'Trdsum': [1e7, 1e7, 4e7],
            'Listedstate': ['Norm', 'Norm', 'Norm'],
        }
        df = pd.DataFrame(base)
        out = NS['cleaning'](df)
        self.assertEqual(len(out), 1, '重复行与缺 PB 的行都应被去掉')
        self.assertEqual(out['Stkcd'].iloc[0], '000001')

    def test_universe_drops_st_and_thin_trading(self):
        # universe() 的 2/3 规则以「个股自身首末交易日」为区间：
        # 首日在第 1 天、末日在第 10 天，但只在其中 2 天成交 → 实际/可能 = 2/10，应被剔除。
        dates = pd.bdate_range('2013-01-01', periods=10)
        rows = []
        plans = [('000001', 'Norm', list(range(10))),
                 ('000002', 'Norm', [0, 9]),
                 ('000003', 'ST', list(range(10)))]
        for code, state, positions in plans:
            for i in positions:
                rows.append({'Stkcd': code, 'Date': dates[i], 'Listedstate': state,
                             'Clpr': 10.0, 'Fullshr': 1e8, 'Dret': 0.01, 'DRfRet': 0.0,
                             'PB': 2.0, 'ROE': 10.0, 'Trdvol': 1e6, 'Trdsum': 1e7})
        out = NS['universe'](pd.DataFrame(rows))
        self.assertEqual(sorted(out['Stkcd'].unique()), ['000001'],
                         'ST 与非正常上市、交易天数不足自身区间 2/3 的股票都应剔除')


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'Stkcd': ['000001', '000002'],
            'Date': pd.to_datetime(['2013-01-04', '2013-01-04']),
            'Clpr': [10.0, 25.0],
            'Fullshr': [1e8, 2e8],
            'PB': [2.0, 5.0],
            'EPS': [0.5, -1.0],
            'Dret': [0.01, -0.02],
            'DRfRet': [0.0, 0.0],
            'Trdvol': [1e6, 2e6],
            'Trdsum': [1e7, 5e7],
            'Listedstate': ['Norm', 'Norm'],
        })

    def test_market_value_bm_ep(self):
        df = NS['get_market_feature'](self.df.copy())
        self.assertAlmostEqual(df['daily_market_value'].iloc[0], 10.0 * 1e8)
        df = NS['get_bm'](df)
        self.assertAlmostEqual(df['daily_bm'].iloc[0], 0.5)
        df = NS['get_ep'](df)
        self.assertAlmostEqual(df['daily_ep'].iloc[0], 0.05)

    def test_point_in_time_alignment(self):
        annual = pd.DataFrame({
            'annual_stock_code': ['000001', '000001'],
            'annual_available_date': pd.to_datetime(['2013-04-30', '2014-04-30']),
            'annual_value': [100.0, 50.0],
        })
        daily = pd.DataFrame({
            'Stkcd': ['000001'] * 4,
            'Date': pd.to_datetime(['2013-04-29', '2013-04-30', '2014-04-29', '2014-04-30']),
        })
        aligned = NS['align_annual_value'](daily, annual)
        self.assertTrue(np.isnan(aligned[0]), '公告日前应无值')
        self.assertEqual(aligned[1], 100.0, '公告日当天即可用')
        self.assertEqual(aligned[2], 100.0, '沿用上一份年报')
        self.assertEqual(aligned[3], 50.0, '新公告日生效')

    def test_asset_growth_uses_adjacent_annual_reports(self):
        bs = pd.DataFrame({
            'A_StkCd': ['000001', '000001', '000001'],
            'EndDt': pd.to_datetime(['2011-12-31', '2012-12-31', '2013-12-31']),
            'InfoPubDt': pd.to_datetime(['2012-04-30', '2013-04-30', '2014-04-30']),
            'TotAss': [100.0, 100.0, 110.0],
        })
        annual = NS['prepare_annual_asset_growth'](bs)
        self.assertEqual(len(annual), 2)
        self.assertAlmostEqual(annual['annual_value'].iloc[1], 1.1)
        self.assertEqual(annual['annual_available_date'].iloc[1], pd.Timestamp('2014-04-30'))

    def test_momentum_skips_most_recent_month(self):
        months = pd.period_range('2011-01', periods=24, freq='M')
        rates = np.arange(24) / 1000.0
        df = pd.DataFrame({
            'Stkcd': '000001',
            'Date': [m.to_timestamp(how='end').normalize() for m in months],
            'Dret': rates,
        })
        out = NS['get_momentum'](df)
        mom = out['daily_mom']
        self.assertTrue(mom.iloc[:11].isna().all(), '前 11 个月没有 12-1 动量')
        expected = np.prod(1 + rates[12:23]) - 1
        self.assertAlmostEqual(mom.iloc[23], expected, places=10)


class MonthlyTests(unittest.TestCase):
    def test_monthly_return_compounds_daily(self):
        df = pd.DataFrame({
            'Stkcd': ['000001'] * 3,
            'Date': pd.to_datetime(['2013-01-07', '2013-01-08', '2013-01-09']),
            'Dret': [0.1, 0.1, 0.1],
            'DRfRet': [0.001, 0.001, 0.001],
        })
        monthly = quiet(NS['get_ym_monthly_excessret'], df.copy())
        self.assertAlmostEqual(monthly['monthly_return'].iloc[0], 1.1 ** 3 - 1, places=10)
        self.assertAlmostEqual(monthly['monthly_rfreturn'].iloc[0], 1.001 ** 3 - 1, places=10)
        self.assertAlmostEqual(monthly['monthly_excess_return'].iloc[0],
                               (1.1 ** 3 - 1) - (1.001 ** 3 - 1), places=10)

    def test_form_signal_uses_last_trading_day_and_next_month(self):
        day_cols = ['daily_market_value', 'daily_bm', 'daily_mom', 'daily_ep', 'daily_cp',
                    'daily_asset_growth', 'daily_volatility', 'daily_max',
                    'daily_illiquidity', 'daily_turnover_12m', 'daily_abn_turnover_1m']
        df = pd.DataFrame({
            'Stkcd': ['000001'] * 3,
            'Date': pd.to_datetime(['2013-01-15', '2013-01-31', '2013-02-28']),
            'daily_market_value': [1.0, 2.0, 3.0],
        })
        for col in day_cols[1:]:
            df[col] = df['daily_market_value']
        snap = quiet(NS['get_form_signal'], df.copy())
        first = snap.iloc[0]
        self.assertEqual(str(first['formation_date']), '2013-01')
        self.assertEqual(str(first['yield_date']), '2013-02', '形成月 + 1 = 持有月')
        self.assertEqual(first['monthly_market_value'], 2.0, '应取该月最后一个交易日')

    def test_monthly_panel_is_left_join_on_returns(self):
        monthly = pd.DataFrame({
            'Stkcd': ['000001', '000002'],
            'yield_date': [pd.Period('2013-02', 'M')] * 2,
            'monthly_return': [0.01, 0.02],
            'monthly_rfreturn': [0.0, 0.0],
            'monthly_excess_return': [0.01, 0.02],
        })
        snap = pd.DataFrame({
            'Stkcd': ['000001'],
            'formation_date': [pd.Period('2013-01', 'M')],
            'yield_date': [pd.Period('2013-02', 'M')],
            'monthly_market_value': [100.0],
        })
        out = quiet(NS['get_monthly_panel'], monthly, snap)
        self.assertEqual(len(out), 2, '以收益表为左表，不因缺信号丢行')
        self.assertTrue(np.isnan(out['monthly_market_value'].iloc[1]))


class PortfolioTests(unittest.TestCase):
    """CH-3 的 2×3 排序用「已知分组」构造收益，再检验因子合成是否精确。

    分组标签按 get_groups_ch3 的做法复算：先按市值 rank(pct) 剔除最小 30%，
    再在剩余样本内用 qcut 分 S/B（中位数）与 G/M/V（30/70 分位）。
    """

    @staticmethod
    def _panel(label_rule):
        codes = ['%06d' % (i + 1) for i in range(40)]
        mv = np.linspace(1e8, 4e9, 40)
        ep = np.random.default_rng(5).permutation(np.linspace(-0.02, 0.10, 40))
        frame = pd.DataFrame({
            'Stkcd': codes,
            'yield_date': [pd.Period('2013-02', 'M')] * 40,
            'monthly_market_value': mv,
            'monthly_ep': ep,
        })

        keep = frame['monthly_market_value'].rank(pct=True) > 0.30
        kept = frame.loc[keep]
        size_label = pd.Series(index=frame.index, dtype=object)
        ep_label = pd.Series(index=frame.index, dtype=object)
        size_label.loc[kept.index] = pd.qcut(
            kept['monthly_market_value'].rank(method='first'),
            q=[0, 0.5, 1.0], labels=['S', 'B']).astype(str)
        ep_label.loc[kept.index] = pd.qcut(
            kept['monthly_ep'].rank(method='first'),
            q=[0, 0.3, 0.7, 1.0], labels=['G', 'M', 'V']).astype(str)

        frame['monthly_excess_return'] = label_rule(size_label, ep_label).astype(float)
        return frame, keep

    def test_ch3_smb_equals_small_minus_big(self):
        frame, _ = self._panel(lambda size, ep: (size == 'S').astype(float) * 0.01)
        factors = quiet(NS['get_groups_ch3'], frame)
        self.assertEqual(list(factors.columns),
                         ['market_factor', 'size_factor_smb', 'value_factor_vmg'])
        self.assertAlmostEqual(factors['size_factor_smb'].iloc[0], 0.01, places=10,
                               msg='小市值组多 1%，SMB 应为 1%')

    def test_ch3_vmg_equals_value_minus_growth(self):
        frame, _ = self._panel(lambda size, ep: (ep == 'V').astype(float) * 0.005)
        factors = quiet(NS['get_groups_ch3'], frame)
        self.assertAlmostEqual(factors['value_factor_vmg'].iloc[0], 0.005, places=10,
                               msg='高 EP 组多 0.5%，VMG 应为 0.5%')

    def test_ch3_market_factor_uses_top_seventy_percent(self):
        frame, keep = self._panel(lambda size, ep: (size == 'S').astype(float) * 0.01)
        factors = quiet(NS['get_groups_ch3'], frame)
        kept = frame.loc[keep]
        weights = kept['monthly_market_value'] / kept['monthly_market_value'].sum()
        expected = float((weights * kept['monthly_excess_return']).sum())
        self.assertAlmostEqual(factors['market_factor'].iloc[0], expected, places=10,
                               msg='MKT 应为剔除最小 30% 后剩余股票池的市值加权收益')

    def test_unconditional_sort_produces_ten_groups(self):
        n = 30
        frames = []
        for month in ['2013-02', '2013-03']:
            for i in range(n):
                row = {
                    'Stkcd': '%06d' % (i + 1),
                    'yield_date': pd.Period(month, 'M'),
                    'monthly_market_value': 1e8 * (i + 1),
                    'monthly_bm': 0.1 + i * 0.01,
                    'monthly_mom': 0.0,
                    'monthly_ep': 0.01 + i * 0.001,
                    'monthly_cp': 0.02,
                    'monthly_asset_growth': 1.0 + i * 0.01,
                    'monthly_volatility': 0.01,
                    'monthly_max': 0.02,
                    'monthly_illiquidity': 1e-9,
                    'monthly_turnover_12m': 0.005,
                    'monthly_abn_turnover_1m': 1.0,
                    'monthly_excess_return': 0.001 * i,
                }
                frames.append(row)
        F = quiet(NS['get_groups_uncon'], pd.DataFrame(frames))
        self.assertEqual(F.shape, (2, 10), 'F 应为 持有月 × 10 个因子')
        self.assertTrue((F['value_factor_hml'] > 0).all(),
                        '收益随 BM 上升时 HML 应为正')


class RegressionTests(unittest.TestCase):
    def test_time_series_regression_recovers_betas(self):
        rng = np.random.default_rng(7)
        T, K, N = 400, 2, 6
        F = pd.DataFrame(rng.normal(0, 0.04, (T, K)), columns=['f1', 'f2'])
        true_beta = np.array([[1.2, 0.8, 1.0, 1.5, 0.5, 1.1],
                              [0.3, -0.2, 0.6, 0.1, -0.4, 0.9]])
        codes = ['s%d' % i for i in range(N)]
        noise = rng.normal(0, 0.004, (T, N))
        R = pd.DataFrame(F.to_numpy() @ true_beta + 0.005 + noise, columns=codes)
        B, alpha, alpha_t = quiet(NS['time_series_regression'], R, F)
        self.assertEqual(B.shape, (K, N))
        np.testing.assert_allclose(B.to_numpy(), true_beta, atol=0.02)
        np.testing.assert_allclose(alpha.to_numpy(), 0.005, atol=0.005)

    def test_cross_section_regression_recovers_premium(self):
        rng = np.random.default_rng(11)
        K, N = 2, 200
        beta = rng.normal(1, 0.3, (K, N))
        codes = ['s%d' % i for i in range(N)]
        B = pd.DataFrame(beta, index=['f1', 'f2'], columns=codes)
        lam = np.array([0.01, -0.004])
        E_R = pd.Series(beta.T @ lam + 0.002, index=codes, name='E_R')
        E_F, E_F_t, alpha, res = quiet(NS['cross_section_regression'], E_R, B)
        np.testing.assert_allclose(E_F.to_numpy(), lam, atol=1e-8)

    def test_fama_macbeth_recovers_average_premium(self):
        rng = np.random.default_rng(3)
        T, K, N = 120, 2, 100
        beta = rng.normal(1, 0.3, (K, N))
        codes = ['s%d' % i for i in range(N)]
        B = pd.DataFrame(beta, index=['f1', 'f2'], columns=codes)
        lam = np.array([0.008, 0.003])
        R = pd.DataFrame(
            rng.normal(0, 0.002, (T, N)) + 0.001 + beta.T @ lam,
            index=pd.period_range('2000-01', periods=T, freq='M'),
            columns=codes,
        )
        lam_t, Alpha, lambda_bar, t_stat = quiet(NS['fama_macbeth'], R, B)
        self.assertEqual(lam_t.shape, (T, K))
        np.testing.assert_allclose(lambda_bar.to_numpy(), lam, atol=0.001)
        self.assertTrue((t_stat.abs() > 2).all(), '给定常数溢价时 t 值应显著')


if __name__ == '__main__':
    unittest.main(verbosity=2)
