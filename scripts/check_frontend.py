from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    errors = []
    page.on('console', lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type in ('error', 'warning') else None)
    page.on('pageerror', lambda err: errors.append(f"[pageerror] {err}"))
    
    page.goto('http://localhost:5173', wait_until='networkidle', timeout=15000)
    page.screenshot(path='frontend_5173.png', full_page=True)
    
    root = page.locator('#root')
    inner = root.inner_html()
    
    print(f"=== 页面标题: {page.title()} ===")
    print(f"=== #root 内容长度: {len(inner)} ===")
    print(f"=== #root 前500字符: ===")
    print(inner[:500])
    print(f"=== 控制台错误/警告 ({len(errors)}): ===")
    for e in errors[:20]:
        print(f"  {e}")
    
    browser.close()
