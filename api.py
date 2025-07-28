import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver

# Load environment variables
load_dotenv()

def get_account_balance(account_id: int) -> dict:
    """Get balance for a specific account"""
    try:
        phone = os.getenv(f"ACCOUNT{account_id}_PHONE")
        password = os.getenv(f"ACCOUNT{account_id}_PASSWORD")
        
        if not phone or not password:
            raise ValueError(f"Credentials not found for account {account_id}")

        # Create new driver instance
        driver = webdriver.Chrome()
        wait = WebDriverWait(driver, 60)
        driver.maximize_window()

        try:
            print(f"[Account {account_id}] 🚀 Browser launched")
            
            # Navigate and login
            print(f"[Account {account_id}] 🌐 Navigating to login page...")
            driver.get("https://erspartner.mtnonline.com:8444/agentportal/agentportal/Application.html")
            time.sleep(3)

            # Login process
            print(f"[Account {account_id}] 📱 Entering credentials...")
            phone_input = wait.until(EC.presence_of_element_located((By.ID, "gwt-debug-Phone_Number")))
            type_like_human(phone_input, phone)
            time.sleep(0.5)

            password_input = wait.until(EC.presence_of_element_located((By.ID, "gwt-debug-PIN/Password")))
            type_like_human(password_input, password)
            time.sleep(0.5)

            submit_button = wait.until(EC.element_to_be_clickable((By.ID, "gwt-debug-submit_button")))
            ActionChains(driver).move_to_element(submit_button).click().perform()
            time.sleep(3)

            print(f"[Account {account_id}] ✅ Login successful")
            
            # Get balance
            print(f"[Account {account_id}] 🔄 Checking balance...")
            balance_element = wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "input#gwt-debug-Balance.gwt-TextBox-readonly"
                ))
            )
            
            balance = balance_element.get_attribute("value")
            if balance and balance.strip():
                print(f"[Account {account_id}] 💰 Balance: {balance}")
                return {
                    "account_id": account_id,
                    "balance": balance,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                print(f"[Account {account_id}] ⚠️ Empty balance value")
                return {
                    "account_id": account_id,
                    "error": "Empty balance",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }

        finally:
            driver.quit()

    except Exception as e:
        print(f"[Account {account_id}] ❌ Error: {str(e)}")
        return {
            "account_id": account_id,
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

app = FastAPI()

# API Key authentication
API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=401,
        detail="Invalid API Key"
    )

def type_like_human(element, text):
    """Type text with random delays between keystrokes"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))

@app.get("/balances")
async def read_balances(api_key: str = Depends(get_api_key)):
    """Get current balances for all accounts concurrently"""
    account_ids = [1, 2]  # List of account IDs to check
    results = []
    
    # Use ThreadPoolExecutor to run balance checks concurrently
    with ThreadPoolExecutor(max_workers=len(account_ids)) as executor:
        # Submit all balance check tasks
        future_to_account = {
            executor.submit(get_account_balance, account_id): account_id
            for account_id in account_ids
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_account):
            result = future.result()
            results.append(result)
    
    return {
        "accounts": sorted(results, key=lambda x: x.get('account_id', 0)),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/balance/{account_id}")
async def read_balance(account_id: int, api_key: str = Depends(get_api_key)):
    """Get current balance for a specific account"""
    result = get_account_balance(account_id)
    if "error" in result:
        raise HTTPException(
            status_code=500,
            detail=result["error"]
        )
    return {"balance": result["balance"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    