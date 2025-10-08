#!/usr/bin/env python3
"""
GitHub Actions compatible slot monitor
Runs for a limited time and logs results
"""
import asyncio
import httpx
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging for GitHub Actions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GitHubSlotMonitor:
    """GitHub Actions compatible slot monitor"""
    
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
        
        # All consulate mapping
        self.all_consulate_mapping = {
            'CHENNAI': 'Chennai',
            'CHENNAI VAC': 'Chennai VAC',
            'HYDERABAD': 'Hyderabad',
            'HYDERABAD VAC': 'Hyderabad VAC',
            'KOLKATA': 'Kolkata',
            'KOLKATA VAC': 'Kolkata VAC',
            'MUMBAI': 'Mumbai',
            'MUMBAI VAC': 'Mumbai VAC',
            'NEW DELHI': 'New Delhi',
            'NEW DELHI VAC': 'New Delhi VAC',
            'DELHI': 'Delhi',
            'DELHI VAC': 'Delhi VAC'
        }

    async def check_slots(self) -> Dict[str, List[Dict]]:
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
                    return {'all': [], 'main': []}
                    
        except Exception as e:
            logger.error(f"Error checking slots: {e}")
            return {'all': [], 'main': []}

    def parse_slots(self, data: Dict) -> Dict[str, List[Dict]]:
        """Parse API response and extract available slots"""
        all_slots = []
        main_slots = []
        
        try:
            if 'slotDetails' in data:
                for slot_info in data['slotDetails']:
                    location = slot_info.get('visa_location', 'Unknown')
                    slots_count = slot_info.get('slots', 0)
                    
                    if slots_count > 0:
                        consulate_name = self.all_consulate_mapping.get(location.upper(), location)
                        slot_data = {
                            'location': consulate_name,
                            'slots': slots_count,
                            'timestamp': slot_info.get('createdon', 'Unknown'),
                            'is_vac': 'VAC' in location.upper(),
                            'is_main': 'VAC' not in location.upper()  # Any consulate that's not VAC
                        }
                        
                        all_slots.append(slot_data)
                        
                        # Only add main consulates (no VAC) to main_slots for Telegram
                        if slot_data['is_main']:
                            main_slots.append(slot_data)
                        
        except Exception as e:
            logger.error(f"Error parsing slots: {e}")
            
        return {'all': all_slots, 'main': main_slots}

    def print_slots_summary(self, slots: List[Dict]):
        """Print slots summary for GitHub Actions"""
        if not slots:
            logger.info("⏳ No available slots found")
            return
            
        logger.info(f"🎯 Found {len(slots)} locations with available slots:")
        
        # Group slots by consulate
        consulate_groups = {}
        for slot in slots:
            base_name = slot['location'].replace(' VAC', '')
            if base_name not in consulate_groups:
                consulate_groups[base_name] = {'main': None, 'vac': None}
            
            if slot['is_vac']:
                consulate_groups[base_name]['vac'] = slot
            else:
                consulate_groups[base_name]['main'] = slot
        
        for consulate, slots_group in consulate_groups.items():
            main_text = f"{slots_group['main']['slots']} slots" if slots_group['main'] else "No slots"
            vac_text = f"{slots_group['vac']['slots']} slots" if slots_group['vac'] else "No slots"
            
            logger.info(f"📍 {consulate}: Main={main_text}, VAC={vac_text}")

    async def send_telegram_notification(self, slots: List[Dict]):
        """Send notification via Telegram (only main consulates)"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("Telegram credentials not configured")
            return
            
        try:
            message = self.format_telegram_message(slots)
            
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

    def format_telegram_message(self, slots: List[Dict]) -> str:
        """Format message for Telegram notifications (main consulates only)"""
        if not slots:
            return "No main consulate slots available"
            
        message = f"🎯 <b>MAIN CONSULATE SLOTS AVAILABLE!</b> ({len(slots)} locations)\n\n"
        
        for slot in slots:
            message += f"📍 <b>{slot['location']}</b>: {slot['slots']} slots\n"
            
        message += f"\n⏰ Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message += "\n\n⚡ Book now at: https://www.usvisascheduling.com/"
        
        return message

    async def run_monitoring(self, duration_minutes: int = 5):
        """Run monitoring for specified duration"""
        logger.info(f"🚀 Starting slot monitoring for {duration_minutes} minutes")
        logger.info(f"⏰ Check interval: {self.interval} seconds")
        
        if self.telegram_bot_token and self.telegram_chat_id:
            logger.info("📱 Telegram notifications enabled (main consulates only)")
        else:
            logger.info("⚠️ Telegram notifications disabled")
        
        start_time = datetime.now()
        from datetime import timedelta
        end_time = start_time + timedelta(minutes=duration_minutes)
        check_count = 0
        
        try:
            while datetime.now() < end_time:
                check_count += 1
                logger.info(f"\n🔍 Check #{check_count} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                slots_data = await self.check_slots()
                all_slots = slots_data['all']
                main_slots = slots_data['main']
                
                # Show all slots summary
                self.print_slots_summary(all_slots)
                
                # Send Telegram notification only for main consulates (not VAC)
                if main_slots:
                    await self.send_telegram_notification(main_slots)
                    logger.info("📱 Telegram notification sent for main consulates only")
                else:
                    logger.info("📱 No main consulate slots - no Telegram notification")
                
                # Wait for next check (unless it's the last check)
                if datetime.now() < end_time:
                    logger.info(f"⏰ Next check in {self.interval} seconds...")
                    await asyncio.sleep(self.interval)
                
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
        
        logger.info(f"✅ Monitoring completed after {check_count} checks")

async def main():
    """Main function for GitHub Actions"""
    # Get interval from environment (default: 30 seconds)
    interval = int(os.getenv('MONITOR_INTERVAL', '30'))
    
    # Create monitor
    monitor = GitHubSlotMonitor(interval=interval)
    
    # Run monitoring for 5 minutes
    await monitor.run_monitoring(duration_minutes=5)

if __name__ == "__main__":
    asyncio.run(main())
