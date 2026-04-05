from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    errors = []
    page.on('console', lambda msg: errors.append(f"[{msg.type}] {msg.text}"))
    page.on('pageerror', lambda err: errors.append(f"[pageerror] {err}"))
    
    page.goto('http://localhost:5174', wait_until='networkidle', timeout=15000)
    
    # 尝试登录
    page.fill('input[type="email"], input[placeholder*="@"]', 'admin@drp.local')
    page.fill('input[type="password"]', 'admin123')
    page.click('button:has-text("登录")')
    
    # 等待登录后的页面
    page.wait_for_timeout(3000)
    page.screenshot(path='dashboard_after_login.png', full_page=True)
    
    root = page.locator('#root')
    inner = root.inner_html()
    
    print(f"=== 登录后 #root 内容长度: {len(inner)} ===")
    print(f"=== 登录后 #root 前500字符: ===")
    print(inner[:500])
    print(f"=== 控制台消息 ({len(errors)}): ===")
    for e in errors[:30]:
        print(f"  {e}")
    
    browser.close()
