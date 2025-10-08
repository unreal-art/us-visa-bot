#!/usr/bin/env python3
"""
Lightweight Visa Slot Monitor
Simple script to monitor Indian US visa slots and send notifications
Shows all locations in terminal, but only main consulates in Telegram
"""
import asyncio
import httpx
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()

class LightweightSlotMonitor:
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
        
        # Only main consulates for Telegram
        self.main_consulates = {'CHENNAI', 'HYDERABAD', 'MUMBAI'}

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
                            'is_main': location.upper() in self.main_consulates and 'VAC' not in location.upper()
                        }
                        
                        all_slots.append(slot_data)
                        
                        # Only add main consulates (no VAC) to main_slots for Telegram
                        if slot_data['is_main']:
                            main_slots.append(slot_data)
                        
        except Exception as e:
            logger.error(f"Error parsing slots: {e}")
            
        return {'all': all_slots, 'main': main_slots}

    def print_slots_table(self, slots: List[Dict]):
        """Print slots in a nice table format"""
        if not slots:
            console.print("⏳ No available slots found", style="yellow")
            return
            
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
        
        # Create table
        table = Table(title="🎯 Available Visa Slots", show_header=True, header_style="bold blue")
        table.add_column("Consulate", style="cyan", width=15)
        table.add_column("Main Consulate", style="green", width=20)
        table.add_column("VAC", style="yellow", width=20)
        
        for consulate, slots_group in consulate_groups.items():
            main_text = f"{slots_group['main']['slots']} slots" if slots_group['main'] else "No slots"
            vac_text = f"{slots_group['vac']['slots']} slots" if slots_group['vac'] else "No slots"
            
            # Style based on availability
            main_style = "green" if slots_group['main'] and slots_group['main']['slots'] > 0 else "red"
            vac_style = "yellow" if slots_group['vac'] and slots_group['vac']['slots'] > 0 else "red"
            
            table.add_row(
                consulate,
                f"[{main_style}]{main_text}[/{main_style}]",
                f"[{vac_style}]{vac_text}[/{vac_style}]"
            )
        
        console.print(table)
        
        # Show timestamp
        if slots:
            latest_timestamp = max(slot['timestamp'] for slot in slots)
            console.print(f"\n⏰ Last updated: {latest_timestamp}", style="dim")

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

    async def monitor_continuously(self):
        """Monitor slots continuously"""
        logger.info(f"🚀 Starting slot monitoring (interval: {self.interval}s)")
        logger.info("Press Ctrl+C to stop")
        
        last_notification_time = None
        
        try:
            while True:
                console.print(f"\n🔍 Checking slots at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="blue")
                
                slots_data = await self.check_slots()
                all_slots = slots_data['all']
                main_slots = slots_data['main']
                
                # Show all slots in terminal table
                self.print_slots_table(all_slots)
                
                # Send Telegram notification only for main consulates (not VAC)
                if main_slots:
                    # Send notification (but not too frequently)
                    now = datetime.now()
                    if (last_notification_time is None or 
                        (now - last_notification_time).seconds > 300):  # 5 minutes cooldown
                        
                        await self.send_telegram_notification(main_slots)
                        last_notification_time = now
                        console.print("📱 Telegram notification sent for main consulates only", style="green")
                
                console.print(f"\n⏰ Next check in {self.interval} seconds...", style="dim")
                await asyncio.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")

async def main():
    """Main function"""
    console.print(Panel.fit(
        "🇮🇳 Indian US Visa Slot Monitor",
        style="bold blue"
    ))
    
    # Configurable interval (default: 30 seconds)
    interval = int(os.getenv('MONITOR_INTERVAL', '30'))
    
    monitor = LightweightSlotMonitor(interval=interval)
    
    # Check if Telegram is configured
    if monitor.telegram_bot_token and monitor.telegram_chat_id:
        console.print("✅ Telegram notifications enabled (main consulates only)", style="green")
    else:
        console.print("⚠️ Telegram notifications disabled (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)", style="yellow")
    
    console.print(f"📊 Terminal shows: All locations (main + VAC)", style="cyan")
    console.print(f"📱 Telegram sends: Only MAIN consulates (Chennai, Mumbai, Hyderabad) - NO VAC", style="cyan")
    console.print(f"⏰ Check interval: {interval} seconds", style="cyan")
    console.print("🚀 Starting monitoring...", style="green")
    
    await monitor.monitor_continuously()

if __name__ == "__main__":
    asyncio.run(main())