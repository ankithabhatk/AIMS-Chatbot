from playwright.sync_api import sync_playwright
import time
import subprocess
import sys

# Start backend in background
print("Starting backend...")
backend_proc = subprocess.Popen(
    ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd="backend",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Wait for backend to start
time.sleep(3)

queries = [
    "Fees structure",
    "Courses offered",
    "Tell me about BCA"
]

results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.goto('http://localhost:3000')
    time.sleep(2)
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Testing: {query}")
        print('='*60)
        
        # Click robot
        robot = page.query_selector('.floating-robot-trigger')
        if robot:
            robot.click()
            time.sleep(1)
        
        # Type message
        input_field = page.query_selector('textarea')
        if input_field:
            input_field.fill(query)
            time.sleep(0.5)
        
        # Click send
        send_btn = page.query_selector('button.send-btn')
        if send_btn:
            send_btn.click()
            time.sleep(3)
        
        results[query] = "Sent"
    
    browser.close()

# Kill backend
backend_proc.terminate()
backend_proc.wait()

print("\n" + "="*60)
print("BACKEND TRACE RESULTS")
print("="*60)
print("\nCheck backend output above for:")
print("[QUERY] ...")
print("[INTENT] ...")
print("[COURSE] ...")
print("[FALLBACK] ...")
print("[RESPONSE TYPE] ...")
