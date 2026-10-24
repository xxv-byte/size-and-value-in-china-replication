
# -*- coding: utf-8 -*-
"""静态检查：Notebook 结构、%run 依赖、函数清单、个人绝对路径。"""
import json
import re
import unittest
from pathlib import Path

from notebook_loader import CH3_JUP, REPO, SRC_JUP, function_source, notebook_text

NOTEBOOKS = sorted(SRC_JUP.glob('*.ipynb')) + sorted(CH3_JUP.rglob('*.ipynb'))
RUN_PATTERN = re.compile(r'%run\s+([^\s]+)')

EXPECTED_FUNCTIONS = {
    'data_io_1.ipynb': ['read_daily_data', 'read_bs_data', 'read_cf_data', 'read_fas_data'],
    'clean_and_universe_2.ipynb': ['cleaning', 'universe', 'bs_cleaning', 'cf_cleaning',
                                   'prepare_annual_cash_flow', 'prepare_annual_asset_growth',
                                   'align_annual_value', 'prepare_annual_accruals',
                                   'prepare_annual_noa'],
    'features_3.ipynb': ['get_market_feature', 'get_momentum', 'get_bm', 'get_ep', 'get_cp',
                         'get_asset_growth', 'get_one_month_volatility', 'get_max_return',
                         'get_illiquidity', 'get_turnover_12m', 'get_abn_turnover_1m'],
    'monthly_4.ipynb': ['get_ym_monthly_excessret', 'get_form_signal', 'get_monthly_panel'],
    'portfolio_5.ipynb': ['get_groups_uncon', 'get_groups_neutral', 'get_groups_ch3'],
    'time_series_regression_6.ipynb': ['get_R', 'time_series_regression'],
    'cross_section_regression_7.ipynb': ['get_E_R', 'cross_section_regression'],
    'fama_macbeth_8.ipynb': ['fama_macbeth'],
}


class NotebookIntegrityTests(unittest.TestCase):
    def test_notebook_count(self):
        self.assertGreaterEqual(len(NOTEBOOKS), 30, '保留的 Notebook 数量少于预期')

    def test_every_notebook_is_valid_json_without_outputs(self):
        for path in NOTEBOOKS:
            with self.subTest(notebook=path.name):
                notebook = json.loads(path.read_text(encoding='utf-8'))
                self.assertIn('cells', notebook)
                for cell in notebook['cells']:
                    if cell.get('cell_type') == 'code':
                        self.assertEqual(cell.get('outputs'), [],
                                         '发布副本不应保留执行输出：%s' % path.name)
                        self.assertIsNone(cell.get('execution_count'))

    def test_run_targets_exist(self):
        for path in NOTEBOOKS:
            for target in RUN_PATTERN.findall(notebook_text(path)):
                if not target.endswith('.ipynb'):
                    continue
                with self.subTest(notebook=path.name, target=target):
                    resolved = (path.parent / target).resolve()
                    self.assertTrue(resolved.exists(), '%s 的 %%run 目标不存在: %s'
                                    % (path.name, resolved))

    def test_expected_functions_are_defined(self):
        for name, functions in EXPECTED_FUNCTIONS.items():
            path = SRC_JUP / name
            defined = function_source(path)
            for function in functions:
                with self.subTest(notebook=name, function=function):
                    self.assertIn(function, defined)

    def test_no_personal_absolute_paths(self):
        pattern = re.compile(r'([A-Za-z]:\\(?:Users|Desktop)\\|E:\\周子程|D:\\Desktop)', re.IGNORECASE)
        offenders = []
        for path in list(NOTEBOOKS) + list((REPO / 'scripts').glob('*.py')):
            text = path.read_text(encoding='utf-8', errors='ignore')
            for match in pattern.finditer(text):
                offenders.append((path.name, match.group(0)))
        self.assertEqual(offenders, [], '不应出现个人绝对路径: %s' % offenders[:5])

    def test_config_patterns_match_documentation(self):
        text = notebook_text(SRC_JUP / 'config_0.ipynb')
        for expected in ['RESSET_DRESSTK_*.csv', 'RESSET_MRESSTK_*.csv', 'RESSET_BS_ALL_1.csv',
                         'RESSET_SCF_ALL_1.csv', 'RESSET_BSNOTE_FIXASSDEPR_*.csv']:
            self.assertIn(expected, text, 'config_0 中的匹配规则与文档不一致')

    def test_config_has_no_hardcoded_root(self):
        text = notebook_text(SRC_JUP / 'config_0.ipynb')
        self.assertIn('RESSET_PROJECT_ROOT', text)
        self.assertIn('RESSET_DATA_DIR', text)
        self.assertNotIn("Path(r'", text)

    def test_momentum_call_present_in_downstream_pipelines(self):
        # 发布副本修复了 time_series_regression_6 / cross_section_regression_7 /
        # fama_macbeth_8 内联流程漏掉 get_momentum 的问题，见 docs/CHANGES.md
        for name in ('time_series_regression_6.ipynb', 'cross_section_regression_7.ipynb',
                     'fama_macbeth_8.ipynb'):
            text = notebook_text(SRC_JUP / name)
            self.assertIn('df = get_momentum(df)', text, '%s 缺少 get_momentum' % name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
