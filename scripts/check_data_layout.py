
# -*- coding: utf-8 -*-
"""运行前数据布局与口径检查（静态检查，不跑任何因子或回归）。

目的：在下载完 RESSET 数据、开始跑耗时很长的 Notebook 之前，先确认
  1) 目录与文件名能被代码的 glob 规则匹配到；
  2) 必需列存在、日期可解析、数值可转换、主键不重复（默认抽样，--deep 全量）；
  3) 研究样本期与预热窗口足够；
  4) 代码里没有残留的个人绝对路径。

输出三态：PASS / WARN / FAIL。存在 FAIL 时退出码为 1。

注意边界：本脚本只能验证「数据长什么样」，不能证明「实证计算没有前视偏差」。
错期、分组、加权是否正确，由 tests/ 下的行为测试负责。

用法：
    python scripts/check_data_layout.py                    # 检查 data/raw
    python scripts/check_data_layout.py --data-dir data/sample
    python scripts/check_data_layout.py --deep             # 主键唯一性做全量扫描
    python scripts/check_data_layout.py --max-scan-rows 200000
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CONFIG_NOTEBOOK = REPO / 'jupter_notebook_version' / 'src_jup' / 'config_0.ipynb'

# ---- 与 config_0.ipynb 保持一致的 6 个文件匹配规则（脚本会再回读 notebook 交叉核对） ----
PATTERNS = {
    'daily': 'RESSET_DRESSTK_*.csv',
    'monthly': 'RESSET_MRESSTK_*.csv',
    'bs': 'RESSET_BS_ALL_1.csv',
    'cf': 'RESSET_SCF_ALL_1.csv',
    'fas': 'RESSET_BSNOTE_FIXASSDEPR_*.csv',
    'lsdata': 'RESSET_THIMKTSTKINFO_1.csv',
    'merger': 'RESSET_MERG_1.csv',
}

TABLES = {
    'daily': {
        'desc': '日股票综合数据（日频行情 + 日频财务字段）',
        'required': ['Stkcd', 'Listedstate', 'Date', 'Clpr', 'Trdvol', 'Trdsum', 'Fullshr',
                     'Dret', 'DRfRet', 'PB', 'ROE', 'EPS', 'Infopubdt', 'Enddt'],
        'dates': ['Date', 'Infopubdt', 'Enddt'],
        'numeric': ['Clpr', 'Trdvol', 'Trdsum', 'Fullshr', 'Dret', 'DRfRet', 'PB'],
        'keys': ['Stkcd', 'Date'],
        'essential': True,
    },
    'monthly': {
        'desc': '月股票综合数据（月收益与月末财务字段，C 线使用）',
        'required': ['Stkcd', 'Date', 'ClPr', 'Monret', 'Monrfret', 'Montrds', 'Fullshr', 'PB', 'EPS'],
        'dates': ['Date'],
        'numeric': ['ClPr', 'Monret', 'Monrfret', 'Fullshr', 'PB'],
        'keys': ['Stkcd', 'Date'],
        'essential': True,
    },
    'bs': {
        'desc': '资产负债表（总资产、流动资产/负债、借款、货币资金）',
        'required': ['A_StkCd', 'ReportType', 'EndDt', 'InfoPubDt', 'TotAss', 'TotCurrAss',
                     'TotCurLia', 'ShortLoan', 'LongLoan', 'TaxPay', 'CashEqv', 'TradAss', 'TotLiab'],
        'dates': ['EndDt', 'InfoPubDt'],
        'numeric': ['TotAss', 'TotCurrAss', 'TotCurLia', 'ShortLoan', 'LongLoan', 'TaxPay',
                    'CashEqv', 'TradAss', 'TotLiab'],
        'keys': ['A_StkCd', 'ReportType', 'EndDt'],
        'essential': True,
    },
    'cf': {
        'desc': '现金流量表（净现金流、无形资产摊销、长期待摊费用摊销）',
        'required': ['A_StkCd', 'ReportType', 'EndDt', 'InfoPubDt', 'CENetIncr',
                     'IntangAssAmort', 'DeferExpAmort'],
        'dates': ['EndDt', 'InfoPubDt'],
        'numeric': ['CENetIncr', 'IntangAssAmort', 'DeferExpAmort'],
        'keys': ['A_StkCd', 'ReportType', 'EndDt'],
        'essential': True,
    },
    'fas': {
        'desc': '固定资产及折旧（仅 99999 合计行的本期折旧增加额）',
        'required': ['A_StkCd', 'ReportType', 'EndDt', 'FixAssType', 'CurIncrAD'],
        'dates': ['EndDt'],
        'numeric': ['CurIncrAD'],
        'keys': ['A_StkCd', 'ReportType', 'EndDt'],
        'essential': False,
    },
    'lsdata': {
        'desc': '三板/上市状态辅助表（仅扩展分析用，核心流程不读）',
        'required': [],
        'dates': [],
        'numeric': [],
        'keys': [],
        'essential': False,
    },
    'merger': {
        'desc': '吸收合并事件（仅壳价值扩展分析用，核心流程不读）',
        'required': [],
        'dates': [],
        'numeric': [],
        'keys': [],
        'essential': False,
    },
}

# 研究样本期（B 线）与论文复现期（C 线，含 1 年预热）
B_START = pd.Timestamp('2000-01-01')
B_END = pd.Timestamp('2016-12-31')
C_START = pd.Timestamp('1999-01-01')

PERSONAL_PATH = re.compile(r'([A-Za-z]:\\(?:Users|Desktop)\\|E:\\周子程|D:\\Desktop)', re.IGNORECASE)


class Report:
    def __init__(self):
        self.rows = []
        self.fails = 0
        self.warns = 0

    def add(self, level, where, msg, actual=None, expected=None, fix=None):
        if level == 'FAIL':
            self.fails += 1
        elif level == 'WARN':
            self.warns += 1
        self.rows.append((level, where, msg, actual, expected, fix))
        print('[%s] %s — %s' % (level, where, msg))
        if level != 'PASS':
            if actual is not None:
                print('        实际: %s' % actual)
            if expected is not None:
                print('        预期: %s' % expected)
            if fix is not None:
                print('        修复: %s' % fix)

    def ok(self, where, msg):
        self.add('PASS', where, msg)

    def summary(self):
        print('')
        print('=' * 72)
        print('汇总: FAIL=%d  WARN=%d  PASS=%d'
              % (self.fails, self.warns, sum(1 for r in self.rows if r[0] == 'PASS')))
        return 1 if self.fails else 0


def read_config_patterns():
    """从 config_0.ipynb 里回读 5 个 pattern，确保脚本与代码不会各说各话。"""
    notebook = json.loads(CONFIG_NOTEBOOK.read_text(encoding='utf-8'))
    text = '\n'.join(''.join(c.get('source', [])) for c in notebook['cells']
                     if c.get('cell_type') == 'code')
    found = dict(re.findall(r"(\w+_pattern)\s*=\s*'([^']+)'", text))
    return found


def check_config_consistency(rep):
    found = read_config_patterns()
    mapping = {
        'daily_stock_pattern': 'daily', 'month_pattern': 'monthly', 'bs_pattern': 'bs',
        'cf_pattern': 'cf', 'fas_pattern': 'fas', 'lsdata_pattern': 'lsdata',
        'merger_pattern': 'merger',
    }
    for key, table in mapping.items():
        value = found.get(key)
        if value is None:
            rep.add('FAIL', 'config_0.ipynb', '未找到 %s 定义' % key,
                    expected='notebook 中应有 %s' % key,
                    fix='检查 config_0.ipynb 是否被完整复制')
        elif value != PATTERNS[table]:
            rep.add('FAIL', 'config_0.ipynb', '%s 与检查脚本不一致' % key,
                    actual='%s = %r' % (key, value),
                    expected='%r' % PATTERNS[table],
                    fix='同步 scripts/check_data_layout.py 的 PATTERNS 与 config_0.ipynb')
        else:
            rep.ok('config_0.ipynb', '%s = %r' % (key, value))


def scan_personal_paths(rep):
    targets = list((REPO / 'jupter_notebook_version').rglob('*.ipynb'))
    targets += list((REPO / 'scripts').glob('*.py'))
    hits = []
    for path in targets:
        text = path.read_text(encoding='utf-8', errors='ignore')
        for match in PERSONAL_PATH.finditer(text):
            hits.append((path.relative_to(REPO).as_posix(), match.group(0)))
    if hits:
        for where, token in hits[:10]:
            rep.add('FAIL', where, '存在个人绝对路径', actual=token,
                    expected='使用 root / data_dir 相对路径',
                    fix='删除硬编码路径，改用 RESSET_PROJECT_ROOT / RESSET_DATA_DIR')
    else:
        rep.ok('仓库源码', '未发现个人绝对路径（%d 个文件）' % len(targets))


def find_files(raw, table):
    pattern = PATTERNS[table]
    return sorted(raw.rglob(pattern))


def check_layout(rep, raw):
    if not raw.exists():
        rep.add('FAIL', str(raw), '数据根目录不存在',
                actual='目录不存在',
                expected='%s 目录（内含各 RESSET 表目录）' % raw,
                fix='见 docs/DATA_DOWNLOAD_GUIDE.md，把 RESSET 导出文件放到 data/raw/ 下')
        return {}
    rep.ok(str(raw), '数据根目录存在')

    found = {}
    for table, spec in TABLES.items():
        files = find_files(raw, table)
        found[table] = files
        expected = '%s 个可匹配文件（glob: %s）' % ('>=1' if spec['essential'] else '0 或 >=1',
                                                  PATTERNS[table])
        if not files:
            if spec['essential']:
                rep.add('FAIL', table, '%s 缺失：没有匹配 %s 的文件' % (spec['desc'], PATTERNS[table]),
                        actual='0 个文件',
                        expected=expected,
                        fix='把该表导出为 %s 并放在 data/raw/ 下任意子目录；文件名必须符合该模式'
                            % PATTERNS[table])
            else:
                rep.add('WARN', table, '%s 缺失（仅补充实验需要）' % spec['desc'],
                        actual='0 个文件', expected=expected,
                        fix='如需运行扩展实验，补下载该表；否则可忽略')
        else:
            rep.ok(table, '%d 个文件（%s）' % (len(files), spec['desc']))

    # 重复下载目录 / 备份文件
    dirs = [p for p in raw.iterdir() if p.is_dir()]
    dup_dirs = [p for p in dirs if re.search(r'\(\d+\)\s*$', p.name)]
    if dup_dirs:
        rep.add('WARN', 'data/raw', '存在带 "(1)" 之类后缀的目录，容易重复匹配同一时段数据',
                actual=', '.join(sorted(p.name for p in dup_dirs)),
                expected='每个数据表只保留一个目录',
                fix='删除或移走重复下载的目录；同名股票-日期行会被 drop_duplicates 去掉，'
                    '但会白读一份数据并显著拖慢运行')
    backups = [p for p in raw.rglob('*') if p.is_file() and re.search(r'(备份|backup|副本|~\$)', p.name, re.I)]
    if backups:
        rep.add('WARN', 'data/raw', '存在疑似备份文件',
                actual=', '.join(p.name for p in backups[:5]),
                expected='目录中只留可直接读取的 CSV',
                fix='移走备份文件，避免 rglob 把备份也读进来')
    zips = [p for p in raw.glob('*.zip')]
    if zips:
        rep.add('WARN', 'data/raw', '存在未解压的 zip',
                actual=', '.join('%s (%.1f MB)' % (p.name, p.stat().st_size / 1e6) for p in zips),
                expected='CSV 已解压到子目录',
                fix='解压后再运行；zip 不会被读取函数匹配到')
    return found


def sample_read(path, nrows):
    return pd.read_csv(path, nrows=nrows, low_memory=False)


def check_schema(rep, table, files, nrows):
    spec = TABLES[table]
    if not files:
        return
    path = files[0]
    where = '%s :: %s' % (table, path.name)
    try:
        head = pd.read_csv(path, nrows=nrows, low_memory=False)
    except UnicodeDecodeError:
        rep.add('FAIL', where, 'UTF-8 解码失败',
                actual='读取异常', expected='UTF-8 编码的 CSV',
                fix='用 Excel/pandas 另存为 UTF-8 CSV（不要用 GBK）')
        return
    except Exception as exc:                       # noqa: BLE001
        rep.add('FAIL', where, '抽样读取失败', actual=repr(exc),
                expected='能被 pandas.read_csv 正常读取',
                fix='确认文件未被 Excel 独占打开、分隔符为逗号')
        return

    missing = [c for c in spec['required'] if c not in head.columns]
    if missing:
        hint = ''
        if table == 'monthly' and 'Clpr' in missing:
            hint = '（注意月表列名是 ClPr、日表是 Clpr，大小写不同）'
        rep.add('FAIL', where, '缺少必需列 %s%s' % (missing, hint),
                actual='实际列数 %d' % len(head.columns),
                expected='包含 %s' % spec['required'],
                fix='核对是否导出了正确的 RESSET 表；列名大小写必须一致')
    else:
        rep.ok(where, '必需列齐全（%d 列）' % len(spec['required']))

    for col in spec['dates']:
        if col in head.columns:
            parsed = pd.to_datetime(head[col], errors='coerce')
            bad = int(parsed.isna().sum())
            if bad:
                rep.add('FAIL', where, '%s 无法解析为日期' % col,
                        actual='%d/%d 行为空或非法' % (bad, len(head)),
                        expected='全部可解析（形如 2013-12-31）',
                        fix='检查该列是否被导出为文本或含中文日期')
    for col in spec['numeric']:
        if col in head.columns:
            parsed = pd.to_numeric(head[col], errors='coerce')
            bad = int(parsed.isna().sum() - head[col].isna().sum())
            if bad > 0:
                rep.add('WARN', where, '%s 有 %d 行无法转成数值' % (col, bad),
                        actual='存在非数值字符',
                        expected='纯数值（缺失留空）',
                        fix='检查该列是否含逗号千分位、百分号或中文单位')

    if 'Stkcd' in head.columns or 'A_StkCd' in head.columns:
        col = 'Stkcd' if 'Stkcd' in head.columns else 'A_StkCd'
        codes = head[col].astype('string').str.strip()
        blank = int(codes.isna().sum())
        bad_format = codes[codes.notna() & ~codes.str.fullmatch(r'\d{1,6}(\.0)?', na=False)]
        if blank:
            rep.add('WARN', where, '%s 有 %d 行为空代码（多为 B/H 股等非 A 股行）' % (col, blank),
                    actual='空值',
                    expected='A 股行为六位数字代码',
                    fix='无需处理：清洗函数 dropna 会丢弃这些行；若整表都为空则说明导错了列')
        if len(bad_format) > 0:
            rep.add('WARN', where, '%s 存在非六位数字代码（%d/%d）' % (col, len(bad_format), len(codes)),
                    actual=repr(bad_format.iloc[:5].tolist()),
                    expected="六位数字代码，如 '000001'",
                    fix='确认没有把港股/美股/指数混入；代码列应以字符串方式导出')

    # 日表：universe() 只保留 Listedstate == 'Norm'
    if table == 'daily' and 'Listedstate' in head.columns:
        states = sorted(head['Listedstate'].astype('string').str.strip().dropna().unique().tolist())
        if 'Norm' not in states:
            rep.add('FAIL', where, "Listedstate 中没有 'Norm'",
                    actual='抽样取值: %s' % states[:6],
                    expected="取值包含 'Norm'",
                    fix="universe() 只保留正常上市状态，缺 'Norm' 会让清洗后变成空表")
        else:
            rep.ok(where, "Listedstate 含 'Norm'（抽样取值 %s）" % states[:6])

    # 财务表：公告日不得早于报告期
    if 'InfoPubDt' in head.columns and 'EndDt' in head.columns:
        end = pd.to_datetime(head['EndDt'], errors='coerce')
        pub = pd.to_datetime(head['InfoPubDt'], errors='coerce')
        bad = int(((pub < end) & end.notna() & pub.notna()).sum())
        if bad:
            rep.add('FAIL', where, '有 %d 行公告日早于报告期（会破坏 point-in-time 对齐）' % bad,
                    actual='InfoPubDt < EndDt',
                    expected='公告日 >= 报告期',
                    fix='重新导出；或确认是否把"报告期"和"公告日"两列弄反了')
        else:
            rep.ok(where, '公告日不早于报告期')

    # 日表：收益率是否为小数
    if table == 'daily' and 'Dret' in head.columns:
        ret = pd.to_numeric(head['Dret'], errors='coerce').dropna()
        if len(ret):
            if ret.abs().max() > 1.0:
                rep.add('FAIL', where, 'Dret 疑似百分数（max|Dret|=%.3f）' % ret.abs().max(),
                        actual='max|Dret| = %.3f' % ret.abs().max(),
                        expected='小数，例如 0.0146 表示 1.46%',
                        fix='日收益必须导成小数；若是百分数，月度复利 (1+x).prod()-1 会全部放大 100 倍')
            else:
                rep.ok(where, 'Dret 为小数（max|Dret|=%.4f）' % ret.abs().max())


def check_period(rep, found, mode='auto'):
    daily = found.get('daily') or []
    if not daily:
        return
    if mode == 'skip':
        path = daily[0]
        dates = pd.read_csv(path, usecols=['Date'], low_memory=False)['Date']
        first = pd.to_datetime(dates, errors='coerce').min()
        last = pd.to_datetime(dates, errors='coerce').max()
        print('        （%s 日期范围 %s ~ %s；已跳过样本期判定）'
              % (path.name, first.date(), last.date()))
        return
    # 日表常被拆成多个年份分片：起点取第一个文件的 min，终点取最后一个文件的 max
    first_file, last_file = daily[0], daily[-1]
    first = pd.to_datetime(
        pd.read_csv(first_file, usecols=['Date'], low_memory=False)['Date'],
        errors='coerce').min()
    last = pd.to_datetime(
        pd.read_csv(last_file, usecols=['Date'], low_memory=False)['Date'],
        errors='coerce').max()
    where = '样本期 :: %d 个日表文件' % len(daily)
    print('        （起点取 %s，终点取 %s）' % (first_file.name, last_file.name))
    print('        （覆盖范围：%s ~ %s）' % (first.date(), last.date()))
    if pd.isna(first) or pd.isna(last):
        rep.add('FAIL', where, '日期范围无法识别', fix='检查 Date 列格式')
        return
    warmup_tolerance = pd.Timedelta(days=31)
    if first > C_START + warmup_tolerance:
        rep.add('WARN', where, '起始日期比 C 线预热起点 %s 晚超过 31 天' % C_START.date(),
                actual=first.date(), expected='<= %s' % C_START.date(),
                fix='C 线的 12 个月滚动指标需要早于 2000-01 的历史数据；B 线不受影响')
    else:
        rep.ok(where, '起始日期覆盖 C 线预热窗口')
    if last < B_END:
        rep.add('FAIL', where, '结束日期早于 B 线样本期末 %s' % B_END.date(),
                actual=last.date(), expected='>= %s' % B_END.date(),
                fix='补充下载 2016 年及以前的数据')
    else:
        rep.ok(where, '结束日期覆盖 B 线样本期')


def check_deep(rep, found, max_rows):
    """深度检查：逐文件统计主键重复，并判断文件之间是否真的重复（而不是正常分片）。

    RESSET 的日表是按行数切的**股票分片**：同一个分片内部覆盖整段日期，不同分片之间
    日期区间必然重叠。所以"日期区间重叠"本身不能说明重复下载——真正的重复是
    **同一批股票代码同时出现在两个文件里**。这里用「代码集合交集 + 日期区间重叠」判断，
    只有两者同时成立才报 WARN。
    """
    daily = found.get('daily') or []
    if daily:
        info = []
        total_rows = 0
        for path in daily:
            try:
                frame = pd.read_csv(path, usecols=['Stkcd', 'Date'], low_memory=False)
            except Exception as exc:               # noqa: BLE001
                rep.add('WARN', path.name, '深度检查跳过', actual=repr(exc))
                continue
            dates = pd.to_datetime(frame['Date'], errors='coerce')
            codes = set(frame['Stkcd'].astype('string').dropna().unique())
            dup = int(frame.duplicated(subset=['Stkcd', 'Date']).sum())
            info.append({'name': path.name, 'codes': codes, 'rows': len(frame), 'dup': dup,
                         'start': dates.min(), 'end': dates.max()})
            total_rows += len(frame)
            if dup:
                rep.add('WARN', 'daily :: %s' % path.name,
                        '文件内部主键重复 %d 行' % dup,
                        actual='重复 (Stkcd, Date) %d 行' % dup,
                        expected='文件内 (股票, 日期) 唯一',
                        fix='同一 (股票, 日期) 出现两次说明该文件本身被重复导出')
        if info:
            rep.ok('daily', '逐文件读取 %d 个文件、%d 行完成' % (len(info), total_rows))
            suspicious = []
            for i in range(len(info)):
                for j in range(i + 1, len(info)):
                    a, b = info[i], info[j]
                    if pd.isna(a['start']) or pd.isna(b['start']):
                        continue
                    if not (a['start'] <= b['end'] and b['start'] <= a['end']):
                        continue
                    shared = a['codes'] & b['codes']
                    # 按行数切分时，恰好跨片的股票可能同时出现在两个文件里（各占一部分行），
                    # 这属正常边界现象；共享 >= 2 个代码才视为可疑。
                    if len(shared) >= 2:
                        suspicious.append((a['name'], b['name'], len(shared)))
            if suspicious:
                detail = '\n                '.join(
                    '%s 与 %s 共享 %d 个股票代码且日期区间重叠' % item for item in suspicious[:5])
                rep.add('WARN', 'daily 分片',
                        '%d 对文件疑似重复（共享 >=2 个股票代码且日期区间重叠）' % len(suspicious),
                        actual=detail,
                        expected='每个股票代码只出现在一个分片里',
                        fix='RESSET 按行数切分时同一只股票只应落在一个分片；若两个分片共享代码，'
                            '通常是同一段时间被下载了两次（例如 "(1)" 副本目录）。'
                            '重复行会被 drop_duplicates 去掉，但读取与计算量翻倍')
            else:
                rep.ok('daily 分片', '各分片之间没有"同代码 + 同区间"的重叠')
        if total_rows and total_rows <= max_rows:
            keys = pd.concat(
                [pd.read_csv(path, usecols=['Stkcd', 'Date'], low_memory=False) for path in daily],
                ignore_index=True)
            dup = int(keys.duplicated(subset=['Stkcd', 'Date']).sum())
            if dup:
                rep.add('FAIL', 'daily 跨文件主键', '跨文件重复 %d 行' % dup,
                        actual='重复 %d 行' % dup, expected='0',
                        fix='删除重复下载的目录或文件')
            else:
                rep.ok('daily 跨文件主键', '无重复（全量 %d 行）' % total_rows)
        else:
            print('        提示：日表共 %d 行，超过 --max-scan-rows=%d，'
                  '跳过跨文件全量主键比对（改用「代码集合 × 日期区间」判断）'
                  % (total_rows, max_rows))

    for table in ('monthly', 'bs', 'cf', 'fas'):
        files = found.get(table) or []
        if not files:
            continue
        key = TABLES[table]['keys']
        value_col = {'bs': 'TotAss', 'cf': 'CENetIncr', 'fas': 'CurIncrAD'}.get(table)
        columns = list(key) + ([value_col] if value_col else [])
        frames = []
        for path in files:
            try:
                frames.append(pd.read_csv(path, usecols=columns, low_memory=False))
            except Exception as exc:               # noqa: BLE001
                rep.add('WARN', table, '深度检查跳过 %s' % path.name, actual=repr(exc))
        if not frames:
            continue
        keys = pd.concat(frames, ignore_index=True)
        total = len(keys)
        if total > max_rows:
            keys = keys.sample(max_rows, random_state=0)
            note = '（抽样 %d / %d 行）' % (max_rows, total)
        else:
            note = '（全部 %d 行）' % total

        exact = int(keys.duplicated().sum())
        dup_key = int(keys.duplicated(subset=key).sum())
        where = '主键唯一性 :: %s%s' % (table, note)

        if value_col:
            # 资产负债表 / 现金流量表 / 固定资产表本身会按合并-母公司、重述、类别等给出多版本，
            # 因此"键重复"是常态；真正要担心的是**整行完全重复**（重复下载的典型症状）。
            if exact == 0:
                rep.ok(where, '无完全重复行（键重复 %d 行属多口径版本，清洗时按规则取一条）' % dup_key)
            else:
                rep.add('WARN', where, '存在 %d 行完全重复（%.1f%%）' % (exact, exact / total * 100),
                        actual='整行重复 %d / %d 行' % (exact, total),
                        expected='同一行只出现一次',
                        fix='整行完全重复通常是同一份数据被导出两次（例如 "(1)" 副本目录），'
                            '请核对文件来源；键重复本身是正常的多口径版本，不必处理')
        else:
            rate = dup_key / max(total, 1)
            if dup_key == 0:
                rep.ok(where, '无跨文件主键重复')
            elif rate < 0.01:
                rep.add('WARN', where, '主键重复 %d 行（%.2f%%），多为前后分片在衔接月份重叠'
                        % (dup_key, rate * 100),
                        actual='重复 %d / %d 行' % (dup_key, total),
                        expected='同一 %s 只出现一次' % (key,),
                        fix='清洗阶段的 drop_duplicates 会保留一行；比例很低时可忽略，'
                            '但要确认不是把同一段时间下载了两次')
            else:
                rep.add('WARN', where, '主键重复 %d 行（%.1f%%）' % (dup_key, rate * 100),
                        actual='重复 %d / %d 行' % (dup_key, total),
                        expected='同一 %s 只出现一次' % (key,),
                        fix='比例较高通常是重复下载，请核对是否把同一段时间导出了两次')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', default=None,
                        help='默认为 data/raw；也可传 data/sample')
    parser.add_argument('--deep', action='store_true', help='全量扫描主键唯一性')
    parser.add_argument('--max-scan-rows', type=int, default=200000)
    parser.add_argument('--nrows', type=int, default=2000, help='每张表抽样读取的行数')
    parser.add_argument('--period-check', choices=['auto', 'strict', 'skip'], default='auto',
                        help='样本期检查策略：auto=样例目录自动跳过，strict=强制检查')
    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else REPO / 'data' / 'raw'
    raw = data_dir if data_dir.name == 'raw' else data_dir / 'raw'
    if not raw.exists() and data_dir.exists():
        raw = data_dir

    rep = Report()
    print('仓库根目录 : %s' % REPO)
    print('数据根目录 : %s' % raw)
    print('-' * 72)
    print('【1/4】配置一致性')
    check_config_consistency(rep)
    print('')
    print('【2/4】源码中的个人绝对路径')
    scan_personal_paths(rep)
    print('')
    print('【3/4】目录与文件名')
    found = check_layout(rep, raw)
    print('')
    print('【4/4】表结构抽样检查')
    for table in ('daily', 'monthly', 'bs', 'cf', 'fas'):
        check_schema(rep, table, found.get(table) or [], args.nrows)
    period_mode = args.period_check
    if period_mode == 'auto':
        period_mode = 'skip' if 'sample' in [p.lower() for p in raw.parts] else 'strict'
    if period_mode == 'skip':
        print('')
        print('【样本期】样例数据不要求覆盖 B/C 线完整样本期，跳过严格判定')
    check_period(rep, found, period_mode)
    if args.deep:
        print('')
        print('【附加】主键唯一性全量检查')
        check_deep(rep, found, args.max_scan_rows)
    else:
        print('')
        print('提示：加 --deep 可对主键唯一性做跨文件全量检查（会读较多数据）。')

    return rep.summary()


if __name__ == '__main__':
    sys.exit(main())
