
# -*- coding: utf-8 -*-
"""从 Notebook 里抽取函数定义，供测试直接调用。

设计：Notebook 的代码单元常常「一段函数定义 + 一段内联流水线」混在同一个 cell 里，
不能整段 exec（会立刻去读几十 GB 的 CSV）。这里用 ast 只截取顶层 FunctionDef 的
源码行，加上 import 行，拼成一个小模块执行——等价于 %run 只借函数定义的做法。
"""
import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
SRC_JUP = REPO / 'jupter_notebook_version' / 'src_jup'
CH3_JUP = REPO / 'jupter_notebook_version' / 'CH3_jup'


def code_cells(path):
    notebook = json.loads(Path(path).read_text(encoding='utf-8'))
    for cell in notebook['cells']:
        if cell.get('cell_type') != 'code':
            continue
        source = cell.get('source', [])
        yield ''.join(source) if isinstance(source, list) else source


def strip_magics(text):
    """去掉 IPython 魔法命令行（%run、%matplotlib 等）与 get_ipython() 调用。"""
    kept = []
    for line in text.split('\n'):
        stripped = line.lstrip()
        if stripped.startswith('%') or 'get_ipython()' in line:
            continue
        kept.append(line)
    return '\n'.join(kept)


def notebook_text(path):
    return '\n'.join(code_cells(path))


def function_source(path):
    """返回 {函数名: 源码}，只含顶层 def。"""
    found = {}
    for raw in code_cells(path):
        text = strip_magics(raw)
        if not text.strip():
            continue
        tree = ast.parse(text)
        lines = text.splitlines()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno - 1
                end = node.end_lineno
                found[node.name] = '\n'.join(lines[start:end])
    return found


def literal_assignments(path):
    """返回「纯字面量/常量表」的赋值源码，例如 portfolio_5 的 direction_dict。"""
    chunks = []
    for raw in code_cells(path):
        text = strip_magics(raw)
        if not text.strip():
            continue
        tree = ast.parse(text)
        lines = text.splitlines()
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if any(isinstance(child, ast.Call) for child in ast.walk(node.value)):
                continue
            chunks.append('\n'.join(lines[node.lineno - 1:node.end_lineno]))
    return chunks


def import_lines(path):
    kept = []
    for text in code_cells(path):
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')) and 'get_ipython' not in stripped:
                kept.append(line)
    return kept


def load(namespace=None, notebooks=(), module_constants=True):
    """把若干 Notebook 的顶层函数定义装进一个命名空间并返回。"""
    ns = {
        'pd': pd,
        'np': np,
        'sm': sm,
        'Path': Path,
        'os': __import__('os'),
        '__name__': 'notebook_loader',
    }
    if namespace:
        ns.update(namespace)

    if module_constants:
        config = SRC_JUP / 'config_0.ipynb'
        for raw in code_cells(config):
            text = strip_magics(raw)
            # config_0 只有常量与 root 探测，没有数据读取，可以整段执行
            if not text.strip() or 'root' in text or 'import' in text:
                continue
            exec(compile(text, str(config), 'exec'), ns)
        # 手工提供 root/data_dir，避免触发目录探测
        ns.setdefault('root', REPO)
        ns.setdefault('data_dir', REPO / 'data')
        ns.setdefault('rawdata_dir', REPO / 'data' / 'raw')

    for path in notebooks:
        for source in literal_assignments(path):
            exec(compile(source, str(path), 'exec'), ns)
        for name, source in function_source(path).items():
            exec(compile(source, str(path), 'exec'), ns)
    return ns


def constants():
    """只取 config_0 的常量（不含路径探测）。"""
    return load()
