"""浏览器端到端测试 — 从前端页面到后端 API 的完整流程。

使用 Playwright 模拟用户操作：
  1. 打开前端页面（file:// 协议）
  2. 验证登录页面渲染
  3. 验证主界面元素（后端不可用时使用回退数据）
  4. 验证 Canvas 图谱渲染
  5. 验证 JS 模块加载（auth.js, api_client.js, data_adapter.js）
  6. 截图留证

运行: python3 tests/test_e2e_browser.py
"""
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HTML_FILE = PROJECT_ROOT / "央企数字资产监管平台_prototype.html"
SCREENSHOT_DIR = PROJECT_ROOT / "tests" / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

results = []

def log(test_name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append((test_name, passed, detail))
    print(f"  {status}: {test_name}" + (f" — {detail}" if detail else ""))


def run_tests():
    print(f"\n{'='*60}")
    print("浏览器端到端测试 — Playwright")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 捕获控制台日志
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        # ── T1: 打开前端页面 ──
        file_url = f"file://{HTML_FILE}"
        page.goto(file_url)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1000)  # 等待 JS 执行
        log("T1: 页面加载", page.title() != "", f"title='{page.title()}'")
        page.screenshot(path=str(SCREENSHOT_DIR / "01_page_loaded.png"), full_page=True)

        # ── T2: 登录页面渲染 ──
        login_page = page.locator("#login-page")
        login_visible = login_page.is_visible()
        log("T2: 登录页面显示", login_visible, "无token时应显示登录页")

        # 验证登录表单元素
        email_input = page.locator("#login-email")
        pwd_input = page.locator("#login-password")
        login_btn = page.locator("#login-btn")
        log("T2a: 邮箱输入框", email_input.count() > 0)
        log("T2b: 密码输入框", pwd_input.count() > 0)
        log("T2c: 登录按钮", login_btn.count() > 0)
        page.screenshot(path=str(SCREENSHOT_DIR / "02_login_page.png"), full_page=True)

        # ── T3: JS 模块加载验证 ──
        auth_exists = page.evaluate("typeof Auth !== 'undefined'")
        api_exists = page.evaluate("typeof ApiClient !== 'undefined'")
        adapter_exists = page.evaluate("typeof DataAdapter !== 'undefined'")
        log("T3a: auth.js 加载", auth_exists, f"Auth={auth_exists}")
        log("T3b: api_client.js 加载", api_exists, f"ApiClient={api_exists}")
        log("T3c: data_adapter.js 加载", adapter_exists, f"DataAdapter={adapter_exists}")

        # ── T4: Auth 模块功能验证 ──
        no_token = page.evaluate("Auth.getToken() === null")
        is_expired = page.evaluate("Auth.isTokenExpired() === true")
        log("T4a: 无token时getToken()返回null", no_token)
        log("T4b: 无token时isTokenExpired()返回true", is_expired)

        # ── T5: DataAdapter.computeStatus 验证 ──
        status_up_danger = page.evaluate("DataAdapter.computeStatus(50, [80, 100], 'up')")
        status_up_warn = page.evaluate("DataAdapter.computeStatus(85, [80, 100], 'up')")
        status_up_normal = page.evaluate("DataAdapter.computeStatus(95, [80, 100], 'up')")
        status_down_danger = page.evaluate("DataAdapter.computeStatus(75, [null, 65], 'down')")
        log("T5a: computeStatus up danger", status_up_danger == "danger", f"got={status_up_danger}")
        log("T5b: computeStatus up warn", status_up_warn == "warn", f"got={status_up_warn}")
        log("T5c: computeStatus up normal", status_up_normal == "normal", f"got={status_up_normal}")
        log("T5d: computeStatus down danger", status_down_danger == "danger", f"got={status_down_danger}")

        # ── T6: 模拟登录后查看主界面（注入 fake token） ──
        # 构造一个 fake JWT（base64 编码的 payload）
        fake_payload = '{"sub":"test","tenant_id":"tenant-test","email":"t@t.com","permissions":[],"exp":9999999999}'
        page.evaluate(f"""
            // 手动构造 fake JWT（header.payload.signature）
            var header = btoa(JSON.stringify({{"alg":"HS256","typ":"JWT"}}));
            var payload = btoa('{fake_payload}');
            var fakeToken = header + '.' + payload + '.fake-signature';
            localStorage.setItem('drp_access_token', fakeToken);
            localStorage.setItem('drp_tenant_id', 'tenant-test');
        """)

        # 重新加载页面
        page.reload()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # 验证主界面显示（登录页应隐藏）
        login_hidden = not page.locator("#login-page").is_visible()
        app_visible = page.locator("#app").is_visible()
        log("T6a: 有token时登录页隐藏", login_hidden)
        log("T6b: 主界面显示", app_visible)
        page.screenshot(path=str(SCREENSHOT_DIR / "03_main_interface.png"), full_page=True)

        # ── T7: 主界面核心元素验证 ──
        kpi_bar = page.locator("#kpi-bar")
        breadcrumb = page.locator("#breadcrumb")
        graph_canvas = page.locator("#graph-canvas")
        tree = page.locator("#tree")
        rs_panel = page.locator("#rs")

        log("T7a: KPI栏存在", kpi_bar.count() > 0)
        log("T7b: 面包屑导航存在", breadcrumb.count() > 0)
        log("T7c: 图谱Canvas存在", graph_canvas.count() > 0)
        log("T7d: 左侧组织架构树存在", tree.count() > 0)
        log("T7e: 右侧作战室面板存在", rs_panel.count() > 0)

        # ── T8: Canvas 图谱渲染验证 ──
        canvas_width = page.evaluate("document.getElementById('graph-canvas')?.width || 0")
        canvas_height = page.evaluate("document.getElementById('graph-canvas')?.height || 0")
        log("T8a: Canvas 宽度 > 0", canvas_width > 0, f"width={canvas_width}")
        log("T8b: Canvas 高度 > 0", canvas_height > 0, f"height={canvas_height}")

        # 检查是否有图谱节点数据
        has_nodes = page.evaluate("typeof graphNodes !== 'undefined' && graphNodes.length > 0")
        log("T8c: 图谱节点数据存在", has_nodes)

        # ── T9: 状态栏验证 ──
        sb = page.locator("#sb")
        log("T9: 状态栏存在", sb.count() > 0)

        # ── T10: Ticker 验证 ──
        ticker = page.locator("#ticker")
        ticker_html = ticker.inner_html() if ticker.count() > 0 else ""
        log("T10: Ticker 行情数据存在", len(ticker_html) > 50, f"html_len={len(ticker_html)}")

        # ── T11: 控制台错误检查（排除预期错误：fake token的401、tenant格式的422） ──
        errors = [l for l in console_logs if l.startswith("[error]")
                  and "401" not in l and "令牌无效" not in l
                  and "422" not in l and "tenant" not in l.lower()
                  and "Failed to load resource" not in l]
        log("T11: 无非预期JS控制台错误", len(errors) == 0, f"errors={errors[:3]}" if errors else "")

        page.screenshot(path=str(SCREENSHOT_DIR / "04_final_state.png"), full_page=True)

        # 清理
        page.evaluate("localStorage.clear()")
        browser.close()

    # ── 汇总 ──
    print(f"\n{'='*60}")
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    print(f"总计: {len(results)} 项 | ✅ {passed} 通过 | ❌ {failed} 失败")
    print(f"截图保存在: {SCREENSHOT_DIR}/")
    print(f"{'='*60}\n")

    if failed > 0:
        print("失败项:")
        for name, p, detail in results:
            if not p:
                print(f"  ❌ {name}: {detail}")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
