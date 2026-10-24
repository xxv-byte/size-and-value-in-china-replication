
# -*- coding: utf-8 -*-
"""Sample Mode 运行器：用仓库自带的小规模合成数据，把 B 线主流水线完整跑一遍。

它不复制任何计算逻辑：按 %run 顺序读取 9 个 Notebook 的代码单元并顺序执行（等价于在
Jupyter 里从 fama_macbeth_8.ipynb 一路运行），只做两件事：
  1. 跳过 %run / IPython 魔法命令行（顺序由本脚本的 CHAIN 决定，与 Notebook 一致）；
  2. 把 RESSET_DATA_DIR 指向 data/sample，让读取函数取到合成数据。

用法：
    python scripts/run_sample_pipeline.py                # 用 data/sample
    python scripts/run_sample_pipeline.py --verbose      # 同时打印 Notebook 的原始输出
    python scripts/run_sample_pipeline.py --data-dir data/raw   # 若已有真实数据也可这样跑
"""
import argparse
import contextlib
import io
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC_JUP = REPO / 'jupter_notebook_version' / 'src_jup'

CHAIN = [
    'config_0.ipynb',
    'data_io_1.ipynb',
    'clean_and_universe_2.ipynb',
    'features_3.ipynb',
    'monthly_4.ipynb',
    'portfolio_5.ipynb',
    'time_series_regression_6.ipynb',
    'cross_section_regression_7.ipynb',
    'fama_macbeth_8.ipynb',
]


def cell_sources(path):
    notebook = json.loads(path.read_text(encoding='utf-8'))
    for cell in notebook['cells']:
        if cell.get('cell_type') != 'code':
            continue
        source = cell.get('source', [])
        text = ''.join(source) if isinstance(source, list) else source
        kept = []
        for line in text.split('\n'):
            stripped = line.lstrip()
            if stripped.startswith('%') or 'get_ipython()' in line:
                continue
            kept.append(line)
        code = '\n'.join(kept).strip('\n')
        if code.strip():
            yield code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', default=str(REPO / 'data' / 'sample'))
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    os.environ['RESSET_DATA_DIR'] = str(Path(args.data_dir).resolve())
    os.environ.setdefault('RESSET_PROJECT_ROOT', str(REPO))

    namespace = {'__name__': '__main__', 'run_features_pipeline': False}
    started = time.time()
    factor_returns = None
    ch3_factors = None
    for name in CHAIN:
        path = SRC_JUP / name
        buffer = io.StringIO()
        t0 = time.time()
        with contextlib.redirect_stdout(buffer):
            for code in cell_sources(path):
                exec(compile(code, str(path), 'exec'), namespace)
        cost = time.time() - t0
        print('[%5.1fs] %s' % (cost, name))
        if args.verbose:
            print(buffer.getvalue())
        if name == 'portfolio_5.ipynb':
            # fame_macbeth_8 会把 F 重新赋值为「每期溢价矩阵」，因此在这里先留存因子收益矩阵
            factor_returns = namespace['F'].copy()
            ch3_factors = namespace.get('F_ch3').copy()

    F = factor_returns
    lambda_t = namespace['F']          # fame_macbeth 返回的「每期溢价」矩阵（与上面的 F 同名，已在此区分）
    lambda_bar = namespace['lambda_bar']
    tstat = namespace['t_stat']
    B = namespace['B']
    R = namespace['R']

    print('')
    print('--- Sample Mode 结果形状检查 ---')
    print('S2 日度特征表 df         : %d 行 × %d 列' % namespace['df'].shape)
    print('S5 月度面板 monthly_final: %d 行 × %d 列' % namespace['monthly_final'].shape)
    print('S7 因子收益矩阵 F        : %s' % (F.shape,))
    print('CH-3 三因子 F_ch3        : %s' % (None if ch3_factors is None else ch3_factors.shape,))
    print('S8 收益矩阵 R            : %s' % (R.shape,))
    print('S9 因子暴露 B            : %s' % (B.shape,))
    print('S9 每期因子溢价 lambda_t : %s' % (lambda_t.shape,))
    print('S9 Newey-West t          : %s' % (tstat.shape,))
    print('')
    print('CH-3 因子月均收益（合成数据，不能当作论文结果）:')
    print(ch3_factors.mean().round(6).to_string())
    print('')
    print('Fama-MacBeth 平均风险溢价 lambda_bar（合成数据）:')
    print(lambda_bar.round(6).to_string())
    print('')
    print('Newey-West(4) t 值（合成数据）:')
    print(tstat.round(3).to_string())
    print('总耗时 %.1fs' % (time.time() - started))

    checks = [
        (len(namespace['df']) > 0, 'S2 日度特征表非空'),
        (len(namespace['monthly_final']) > 0, 'S5 月度面板非空'),
        (F.shape[1] == 10, 'F 含 10 个因子列'),
        (ch3_factors is not None and list(ch3_factors.columns) ==
         ['market_factor', 'size_factor_smb', 'value_factor_vmg'], 'CH-3 三因子列名正确'),
        (B.shape[1] > 0 and R.shape[1] == B.shape[1], 'B 与 R 的股票轴一致'),
        (lambda_t.shape[1] == F.shape[1], 'lambda_t 的因子轴与 F 一致'),
        (lambda_bar.notna().sum() == F.shape[1], '每个因子都有平均风险溢价'),
    ]
    failed = [msg for ok, msg in checks if not ok]
    print('')
    for ok, msg in checks:
        print(('  PASS  ' if ok else '  FAIL  ') + msg)
    if failed:
        print('检查失败：%s' % failed)
        return 1
    print('Sample Mode 通过：主流水线在合成数据上跑通。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
