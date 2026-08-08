#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cqut-timetable-skill 环境依赖检查与自动安装。

用法:
    python check_deps.py            # 检查并打印结果
    python check_deps.py --install  # 检查,缺失的依赖自动下载安装

依赖说明:
    - 查询功能(today_classes.py): 仅标准库,零依赖
    - 抓取功能(fetch_schedule_browser.py): 需要 playwright + Chromium
"""
import subprocess
import sys

# Windows 控制台可能是 GBK,统一用 UTF-8 输出避免 emoji 报错
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def check_python():
    print(f'[1/3] Python 版本: {sys.version.split()[0]}')
    if sys.version_info < (3, 9):
        print('  ❌ 需要 Python 3.9+,请先升级 Python')
        return False
    print('  ✅ OK')
    return True


def check_playwright():
    print('[2/3] 检查 playwright 库...')
    try:
        import playwright  # noqa: F401
        print('  ✅ 已安装')
        return True
    except ImportError:
        print('  ❌ 未安装')
        return False


def install_playwright():
    print('  📦 正在安装 playwright (pip install playwright)...')
    r = subprocess.run([sys.executable, '-m', 'pip', 'install', 'playwright'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ❌ pip 安装失败:\n{r.stderr[-2000:]}')
        return False
    print('  ✅ playwright 安装完成')
    return True


def check_chromium():
    print('[3/3] 检查 Chromium 浏览器...')
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        print('  ✅ Chromium 可用')
        return True
    except Exception:
        print('  ❌ Chromium 未安装或不可用')
        return False


def install_chromium():
    print('  📦 正在下载 Chromium (playwright install chromium)...')
    r = subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  ❌ Chromium 下载失败:\n{r.stderr[-2000:]}')
        return False
    print('  ✅ Chromium 下载完成')
    return True


def main():
    do_install = '--install' in sys.argv
    ok = check_python()
    pw = check_playwright()
    ch = check_chromium()

    if do_install:
        if not pw:
            pw = install_playwright()
        if not ch:
            ch = install_chromium()
        print()
        if pw and ch:
            print('🎉 环境就绪: 抓取 + 查询功能都可用')
        else:
            print('⚠️ 仍有依赖未装好,请按上方提示手动处理')
    else:
        print()
        if pw and ch:
            print('🎉 环境完整: playwright + Chromium 均已就绪')
        else:
            print('提示: 运行 `python check_deps.py --install` 可自动安装缺失依赖')
            print('      (若只需查询课表,零依赖,可直接使用 today_classes.py)')

    # 查询功能零依赖,只要 Python 达标即可用
    if ok:
        print('📖 查询功能(today_classes.py): 零依赖,随时可用')


if __name__ == '__main__':
    main()
