# -*- coding: utf-8 -*-
"""把 unittest 的真实运行结果导出成结构化证据文件（Mn-results.json）。

设计对应 docs/development/M1-contracts.md 的 G3/G4：
  - totals.tests 必须等于本轮真实用例数；
  - buildResult 必须与实际退出码一致；
  - codeVersion 记录被测源码的 commit，脏工作区要显式标注。

用法：
    python scripts/export_test_results.py                       # 默认写 docs/testing/MN-results.json
    python scripts/export_test_results.py --milestone M2 --out docs/testing/M2-results.json
    python scripts/export_test_results.py --label "CI sample mode" --quiet
"""
import argparse
import io
import json
import platform
import subprocess
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class Recorder(unittest.TextTestResult):
    """记录每个用例的耗时与状态，供按 suite 汇总。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
        self._t0 = 0.0

    def startTest(self, test):
        self._t0 = time.time()
        super().startTest(test)

    def _record(self, test, status):
        self.records.append({
            'module': type(test).__module__,
            'suite': type(test).__name__,
            'case': getattr(test, '_testMethodName', str(test)),
            'status': status,
            'seconds': round(time.time() - self._t0, 4),
        })

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, 'passed')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record(test, 'failed')

    def addError(self, test, err):
        super().addError(test, err)
        self._record(test, 'error')

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, 'skipped')


def git_code_version():
    """记录被测源码的 commit；证据文件自身的改动不算脏（否则每次都必然是 dirty）。"""
    try:
        sha = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO, capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(
            ['git', 'status', '--porcelain', '--', '.', ':(exclude)docs/testing'],
            cwd=REPO, capture_output=True, text=True).stdout.strip())
        return sha + (' (dirty working tree)' if dirty else '')
    except Exception:                                  # noqa: BLE001
        return 'unavailable (not a git checkout)'


def package_versions(names=('pandas', 'numpy', 'statsmodels', 'scipy')):
    out = {}
    for name in names:
        try:
            out[name] = __import__(name).__version__
        except Exception:                              # noqa: BLE001
            out[name] = None
    return out


def build_suites(records):
    buckets = {}
    for rec in records:
        key = (rec['module'], rec['suite'])
        buckets.setdefault(key, []).append(rec)
    suites = []
    for (module, suite), items in sorted(buckets.items()):
        suites.append({
            'module': module,
            'suite': suite,
            'tests': len(items),
            'failures': sum(1 for i in items if i['status'] == 'failed'),
            'errors': sum(1 for i in items if i['status'] == 'error'),
            'skipped': sum(1 for i in items if i['status'] == 'skipped'),
            'cases': [
                {'name': i['case'], 'status': i['status'], 'seconds': i['seconds']}
                for i in sorted(items, key=lambda x: x['case'])
            ],
        })
    return suites


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--milestone', default='M1')
    parser.add_argument('--out', default=None, help='默认 docs/testing/<milestone>-results.json')
    parser.add_argument('--label', default='unit tests')
    parser.add_argument('--start-dir', default='tests')
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else Path('docs') / 'testing' / ('%s-results.json' % args.milestone)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    command = 'python -m unittest discover -s %s' % args.start_dir

    started = datetime.now(timezone.utc).astimezone()
    stream = io.StringIO()
    loader = unittest.TestLoader()
    try:
        suite = loader.discover(str(REPO / args.start_dir), top_level_dir=str(REPO / args.start_dir))
    except Exception as exc:                           # noqa: BLE001
        print('无法发现测试：%r' % (exc,), file=sys.stderr)
        return 2

    runner = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Recorder)
    result = runner.run(suite)
    captured = stream.getvalue()
    if not args.quiet:
        print(captured)

    records = getattr(result, 'records', [])
    totals = {
        'tests': len(records),
        'failures': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped),
        'seconds': round(time.time() - started.timestamp(), 3),
    }
    ok = totals['failures'] == 0 and totals['errors'] == 0 and totals['tests'] > 0

    payload = {
        'milestone': args.milestone,
        'label': args.label,
        'capturedAt': started.isoformat(),
        'command': command,
        'buildResult': 'SUCCESS' if ok else 'FAILED',
        'exitCode': 0 if ok else 1,
        'platform': platform.platform(),
        'pythonVersion': platform.python_version(),
        'packages': package_versions(),
        'codeVersion': git_code_version(),
        'log': '(console output of %s; 完整日志见 CI artifact 或本地终端)' % command,
        'totals': totals,
        'suites': build_suites(records),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print('')
    print('evidence -> %s' % out_path.relative_to(REPO).as_posix())
    print('totals: tests=%d failures=%d errors=%d skipped=%d -> %s'
          % (totals['tests'], totals['failures'], totals['errors'], totals['skipped'],
             payload['buildResult']))
    if not ok:
        print('证据已写出，但本轮不是 SUCCESS；请先修复再提交。', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
