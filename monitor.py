#!/usr/bin/env python3
"""
Lightweight Visa Slot Monitor
Simple script to monitor Indian US visa slots and send notifications
"""
import asyncio
import httpx
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SlotMonitor:
    """Lightweight slot monitor using checkvisaslots.com API"""
    
    def __init__(self, interval: int = 30):
        self.api_url = 'https://app.checkvisaslots.com/slots/v3'
        self.api_key = 'HZK5KL'
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        self.interval = interval
        
        # Headers from your curl command
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9,ja;q=0.8,ar;q=0.7,es;q=0.6,zh-CN;q=0.5,zh;q=0.4,de;q=0.3',
            'extversion': '4.6.5.1',
            'origin': 'chrome-extension://beepaenfejnphdgnkmccjcfiieihhogl',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Opera GX";v="120", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 OPR/120.0.0.0',
            'x-api-key': self.api_key
        }
        
        # Consulate mapping - only main consulates (no VAC)
        self.consulate_mapping = {
            'CHENNAI': 'Chennai',
            'HYDERABAD': 'Hyderabad',
            'MUMBAI': 'Mumbai'
        }
        
        # Only monitor these consulates
        self.monitored_consulates = {'CHENNAI', 'HYDERABAD', 'MUMBAI'}

    async def check_slots(self) -> List[Dict]:
        """Check for available slots using the API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.api_url,
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self.parse_slots(data)
                else:
                    logger.error(f"API request failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error checking slots: {e}")
            return []

    def parse_slots(self, data: Dict) -> List[Dict]:
        """Parse API response and extract available slots"""
        available_slots = []
        
        try:
            if 'slotDetails' in data:
                for slot_info in data['slotDetails']:
                    location = slot_info.get('visa_location', 'Unknown')
                    slots_count = slot_info.get('slots', 0)
                    
                    # Only check main consulates (no VAC)
                    if (slots_count > 0 and 
                        location.upper() in self.monitored_consulates and 
                        'VAC' not in location.upper()):
                        
                        consulate_name = self.consulate_mapping.get(location.upper(), location)
                        available_slots.append({
                            'location': consulate_name,
                            'slots': slots_count,
                            'timestamp': slot_info.get('createdon', 'Unknown')
                        })
                        
        except Exception as e:
            logger.error(f"Error parsing slots: {e}")
            
        return available_slots

    async def send_telegram_notification(self, slots: List[Dict]):
        """Send notification via Telegram"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("Telegram credentials not configured")
            return
            
        try:
            message = self.format_message(slots)
            
            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                payload = {
                    'chat_id': self.telegram_chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                
                response = await client.post(url, json=payload, timeout=10.0)
                
                if response.status_code == 200:
                    logger.info("📱 Telegram notification sent successfully")
                else:
                    logger.error(f"Telegram notification failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Telegram notification error: {e}")

    def format_message(self, slots: List[Dict]) -> str:
        """Format message for notifications"""
        if not slots:
            return "No slots available"
            
        message = f"🎯 <b>VISA SLOTS AVAILABLE!</b> ({len(slots)} locations)\n\n"
        
        for slot in slots:
            message += f"📍 <b>{slot['location']}</b>: {slot['slots']} slots\n"
            
        message += f"\n⏰ Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message += "\n\n⚡ Book now at: https://www.usvisascheduling.com/"
        
        return message

    def print_slots(self, slots: List[Dict]):
        """Print slots to console"""
        if not slots:
            print("⏳ No available slots found")
            return
            
        print(f"\n🎯 Found {len(slots)} locations with available slots:")
        print("=" * 50)
        
        for slot in slots:
            print(f"📍 {slot['location']}: {slot['slots']} slots")
            print(f"   ⏰ Last updated: {slot['timestamp']}")
            
        print("=" * 50)

    async def monitor_continuously(self):
        """Monitor slots continuously"""
        logger.info(f"🚀 Starting slot monitoring (interval: {self.interval}s)")
        logger.info("Press Ctrl+C to stop")
        
        last_notification_time = None
        
        try:
            while True:
                print(f"\n🔍 Checking slots at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                slots = await self.check_slots()
                
                if slots:
                    self.print_slots(slots)
                    
                    # Send notification (but not too frequently)
                    now = datetime.now()
                    if (last_notification_time is None or 
                        (now - last_notification_time).seconds > 300):  # 5 minutes cooldown
                        
                        await self.send_telegram_notification(slots)
                        last_notification_time = now
                else:
                    print("⏳ No available slots found")
                
                print(f"⏰ Next check in {self.interval} seconds...")
                await asyncio.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")

async def main():
    """Main function"""
    print("🇮🇳 Indian US Visa Slot Monitor")
    print("=" * 40)
    
    # Configurable interval (default: 30 seconds)
    interval = int(os.getenv('MONITOR_INTERVAL', '30'))
    
    monitor = SlotMonitor(interval=interval)
    
    # Check if Telegram is configured
    if monitor.telegram_bot_token and monitor.telegram_chat_id:
        print("✅ Telegram notifications enabled")
    else:
        print("⚠️ Telegram notifications disabled (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")
    
    print(f"📊 Monitoring: Chennai, Mumbai, Hyderabad (main consulates only)")
    print(f"⏰ Check interval: {interval} seconds")
    print("🚀 Starting monitoring...")
    
    await monitor.monitor_continuously()

if __name__ == "__main__":
    asyncio.run(main())
