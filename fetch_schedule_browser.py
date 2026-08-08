# -*- coding: utf-8 -*-
"""
重庆理工大学课表抓取 - 统一身份认证(UIS SSO)方案

流程(不依赖个人收藏,任何用户可用):
  1. Playwright 打开 uis.cqut.edu.cn 统一认证,用学号密码登录
  2. 从 ehall cookie 取 ump_token,调 getApplicationUrl 接口拿 oauth ticket
     (applicationCode=UIVx60 是教务系统在 ehall 平台的固定应用 code)
  3. 用 ticket 访问 jwxt.cqut.edu.cn/sso/yhiotlogin 完成 SSO 换票
  4. 访问学生主页(index_initMenu.html)确认登录
  5. 调用课表接口 xskbcx_cxXsKb.html 抓取整学期课表
  6. 解析保存为 schedule_<学年>_<学期>.json

用法: python fetch_schedule_browser.py --year 2026 --term 1 [--config config.json]
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
JWXT = 'https://jwxt.cqut.edu.cn'
EHALL = 'https://ehall.cqut.edu.cn'
UIS = 'https://uis.cqut.edu.cn'
APP_CODE = 'UIVx60'  # 教务系统在 ehall 平台的应用 code(平台级配置,非个人收藏)


def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def login_uis(page, sid, pwd):
    """登录统一身份认证,进入 ehall"""
    page.goto(UIS + '/', timeout=60000, wait_until='networkidle')
    page.wait_for_timeout(2000)
    inputs = page.query_selector_all('input.el-input__inner')
    if len(inputs) < 2:
        raise RuntimeError('UIS 登录页结构异常')
    inputs[0].fill(sid)
    inputs[1].fill(pwd)
    page.wait_for_timeout(500)
    btn = page.query_selector('button.el-button--primary')
    if not btn:
        raise RuntimeError('UIS 找不到登录按钮')
    btn.click()
    page.wait_for_timeout(10000)
    if 'ehall' not in page.url:
        page.wait_for_timeout(5000)
    if 'ehall' not in page.url:
        tip = page.query_selector('.el-message, .el-form-item__error')
        raise RuntimeError('UIS 登录失败,当前 URL: ' + page.url
                           + ('; 提示: ' + tip.inner_text() if tip else ''))


def get_sso_ticket(ctx, page):
    """从 ehall cookie 取 ump_token,调 getApplicationUrl 拿教务 oauth ticket"""
    cks = ctx.cookies(EHALL)
    ump = next((c['value'] for c in cks if c['name'] == 'ump_token_pc-officeHall'), None)
    if not ump:
        raise RuntimeError('未找到 ump_token cookie,可能登录未成功')
    ticket = page.evaluate("""async ({token, appCode}) => {
        const ts = Date.now();
        const nonce = Math.floor(Math.random() * 1e14);
        const url = '/ump/' + 'officeHall/' + 'getApplicationUrl'
                  + '?applicationCode=' + appCode
                  + '&universityId=100005&appKey=pc-officeHall'
                  + '&timestamp=' + ts + '&nonce=' + nonce + '&clientCategory=PC';
        const r = await fetch(url, {headers: {'token': token}});
        const j = await r.json();
        if (!j || j.code !== '40001' || !j.content) {
            throw new Error('getApplicationUrl 失败: ' + JSON.stringify(j).slice(0, 200));
        }
        return j.content.ticket;
    }""", {'token': ump, 'appCode': APP_CODE})
    if not ticket:
        raise RuntimeError('getApplicationUrl 未返回 ticket')
    return ticket


def open_jwglxt(ctx, page):
    """用 ticket 走教务 SSO 换票,建立教务会话,返回已登录的教务页面"""
    ticket = get_sso_ticket(ctx, page)
    print(f'  已获取 SSO ticket,正在进入教务系统...')
    page.goto(f'{JWXT}/sso/yhiotlogin?ticket={ticket}',
              timeout=30000, wait_until='networkidle')
    page.wait_for_timeout(5000)
    # 打开学生主页确认登录态
    page.goto(JWXT + '/jwglxt/xtgl/index_initMenu.html?jsdm=xs',
              timeout=30000, wait_until='networkidle')
    page.wait_for_timeout(3000)
    if 'index_initMenu' not in page.url:
        raise RuntimeError('未进入教务学生主页,当前 URL: ' + page.url)
    return page


def fetch_schedule_json(page, year, xqm):
    """在教务上下文内抓取课表原始 JSON"""
    result = page.evaluate("""async ({year, xqm}) => {
        const url = '/jwglxt/kbcx/xskbcx_cxXsKb.html?gnmkdm=N2151';
        const params = new URLSearchParams();
        params.set('xnm', year);
        params.set('xqm', xqm);
        params.set('kzlx', 'ck');
        const resp = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            },
            body: params.toString()
        });
        const text = await resp.text();
        return {status: resp.status, text: text};
    }""", {'year': str(year), 'xqm': xqm})
    if result['status'] != 200:
        raise RuntimeError(f'课表接口 HTTP {result["status"]}')
    return json.loads(result['text'])


def parse_schedule(jres):
    xs = jres.get('xsxx', {})
    courses = []
    for i in jres.get('kbList', []):
        courses.append({
            'courseTitle': i.get('kcmc'),
            'teacher': i.get('xm'),
            'courseId': i.get('kch_id'),
            'courseSection': i.get('jc'),
            'courseWeek': i.get('zcd'),
            'weekday': i.get('xqj'),
            'campus': i.get('xqmc'),
            'courseRoom': i.get('cdmc'),
            'className': i.get('jxbmc'),
            'credit': i.get('xf'),
            'weeklyHours': i.get('zhxs'),
        })
    return {
        'name': xs.get('XM'),
        'studentId': xs.get('XH'),
        'className': xs.get('BJMC'),
        'major': xs.get('ZYMC'),
        'schoolYear': xs.get('XNMC'),
        'schoolTerm': xs.get('XQMMC'),
        'courseCount': len(courses),
        'courses': courses,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=os.path.join(BASE_DIR, 'config.json'))
    ap.add_argument('--year', required=True, help='学年,如 2026')
    ap.add_argument('--term', required=True, choices=['1', '2'],
                    help='学期: 1=秋季(2026-2027), 2=春季')
    args = ap.parse_args()

    cfg = load_config(args.config)
    if not cfg.get('sid') or not cfg.get('pwd'):
        print('错误: config.json 未填学号/密码')
        sys.exit(1)
    xqm = '3' if args.term == '1' else '12'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA)
        page = ctx.new_page()
        try:
            print(f'① 登录统一身份认证 (学号 {cfg["sid"]})...')
            login_uis(page, cfg['sid'], cfg['pwd'])
            print('② 获取 SSO ticket,进入教务系统...')
            open_jwglxt(ctx, page)
            print(f'③ 抓取 {args.year} 学年第{args.term}学期课表...')
            jres = fetch_schedule_json(page, args.year, xqm)
            result = parse_schedule(jres)
        finally:
            ctx.close()
            browser.close()

    fname = os.path.join(BASE_DIR, f'schedule_{args.year}_{args.term}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'✅ 抓取成功: {result["name"]} ({result["className"]} {result["major"]})')
    print(f'   学期: {result["schoolYear"]} {result["schoolTerm"]}')
    print(f'   课程数: {result["courseCount"]}')
    print(f'   已保存: {fname}')
    for c in result['courses'][:8]:
        print(f'   - {c["courseTitle"]} | {c["teacher"]} | 周{c["weekday"]} | '
              f'{c["courseSection"]} | {c["courseWeek"]} | {c["courseRoom"]}')


if __name__ == '__main__':
    main()
