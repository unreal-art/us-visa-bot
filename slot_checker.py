"""
Visa slot checker that integrates with checkvisaslots.com API
and monitors real-time slot availability
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import httpx
from dataclasses import dataclass

@dataclass
class VisaSlot:
    """Represents a visa slot"""
    date: datetime
    consulate: str
    consulate_id: str
    available: bool
    slot_type: str = "regular"

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')} at {self.consulate} ({'Available' if self.available else 'Not Available'})"

class SlotChecker:
    """
    Advanced slot checker with multiple data sources
    """

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_urls = {
            'checkvisaslots': 'https://checkvisaslots.com',
            'api_endpoint': 'https://checkvisaslots.com/api/slots'
        }

    async def check_available_slots(self, target_date: Optional[datetime] = None) -> List[VisaSlot]:
        """
        Check for available visa slots from multiple sources
        """
        available_slots = []

        # Check checkvisaslots.com API
        api_slots = await self._check_api_slots(target_date)
        available_slots.extend(api_slots)

        # Check direct visa portal (as backup)
        portal_slots = await self._check_portal_directly(target_date)
        available_slots.extend(portal_slots)

        # Remove duplicates and sort by date
        unique_slots = self._remove_duplicate_slots(available_slots)
        return sorted(unique_slots, key=lambda x: x.date)

    async def _check_api_slots(self, target_date: Optional[datetime] = None) -> List[VisaSlot]:
        """
        Check slots using checkvisaslots.com API
        """
        slots = []
        try:
            async with httpx.AsyncClient() as client:
                # Construct API request
                params = {
                    'country': self.config.country_code,
                    'consulate': self.config.consular_id,
                }

                if target_date:
                    params['date_from'] = target_date.strftime('%Y-%m-%d')

                # Make API request with proper headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                    'Referer': 'https://checkvisaslots.com'
                }

                response = await client.get(
                    f"{self.base_urls['checkvisaslots']}/api/availability",
                    params=params,
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    slots = self._parse_api_response(data)
                    self.logger.info(f"📊 Found {len(slots)} slots via API")
                else:
                    self.logger.warning(f"API request failed with status {response.status_code}")

        except Exception as e:
            self.logger.error(f"❌ API slot check failed: {e}")

        return slots

    def _parse_api_response(self, data: Dict) -> List[VisaSlot]:
        """Parse API response into VisaSlot objects"""
        slots = []

        try:
            # Parse different API response formats
            if 'available_dates' in data:
                for date_info in data['available_dates']:
                    slot_date = datetime.strptime(date_info['date'], '%Y-%m-%d')
                    slots.append(VisaSlot(
                        date=slot_date,
                        consulate=date_info.get('consulate', 'Unknown'),
                        consulate_id=date_info.get('consulate_id', self.config.consular_id),
                        available=True
                    ))

            elif 'slots' in data:
                for slot_info in data['slots']:
                    slot_date = datetime.strptime(slot_info['date'], '%Y-%m-%d')
                    slots.append(VisaSlot(
                        date=slot_date,
                        consulate=slot_info.get('location', 'Unknown'),
                        consulate_id=str(slot_info.get('id', self.config.consular_id)),
                        available=slot_info.get('available', False)
                    ))

        except Exception as e:
            self.logger.error(f"Error parsing API response: {e}")

        return slots

    async def _check_portal_directly(self, target_date: Optional[datetime] = None) -> List[VisaSlot]:
        """
        Directly check the visa portal for available slots
        This serves as a backup to API checking
        """
        slots = []

        try:
            async with httpx.AsyncClient() as client:
                # Simulate checking the actual visa portal
                base_url = self.config.get_base_url()

                # This would need to be customized based on the actual portal structure
                # For now, returning empty list as this requires browser automation
                self.logger.info("🔍 Direct portal check would require browser automation")

        except Exception as e:
            self.logger.error(f"❌ Direct portal check failed: {e}")

        return slots

    def _remove_duplicate_slots(self, slots: List[VisaSlot]) -> List[VisaSlot]:
        """Remove duplicate slots based on date and consulate"""
        seen = set()
        unique_slots = []

        for slot in slots:
            slot_key = (slot.date.date(), slot.consulate_id)
            if slot_key not in seen:
                seen.add(slot_key)
                unique_slots.append(slot)

        return unique_slots

    async def monitor_slots_continuously(self, 
                                       target_date: Optional[datetime] = None,
                                       callback = None) -> None:
        """
        Continuously monitor for slot availability
        """
        self.logger.info(f"🔄 Starting continuous slot monitoring (interval: {self.config.retry_timeout}s)")

        last_available_count = 0

        while True:
            try:
                # Check for available slots
                slots = await self.check_available_slots(target_date)
                available_slots = [s for s in slots if s.available]

                # Log status
                if available_slots:
                    self.logger.info(f"🎯 Found {len(available_slots)} available slots!")
                    for slot in available_slots[:3]:  # Show first 3
                        self.logger.info(f"   📅 {slot}")

                    # Trigger callback if new slots found
                    if callback and len(available_slots) > last_available_count:
                        await callback(available_slots)
                else:
                    self.logger.info("⏳ No available slots found")

                last_available_count = len(available_slots)

                # Wait before next check
                await asyncio.sleep(self.config.retry_timeout)

            except KeyboardInterrupt:
                self.logger.info("🛑 Slot monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Error during slot monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

    def get_earliest_available_slot(self, slots: List[VisaSlot], 
                                  target_date: Optional[datetime] = None) -> Optional[VisaSlot]:
        """Get the earliest available slot, optionally before a target date"""
        available_slots = [s for s in slots if s.available]

        if not available_slots:
            return None

        if target_date:
            available_slots = [s for s in available_slots if s.date <= target_date]

        if not available_slots:
            return None

        return min(available_slots, key=lambda x: x.date)

class SlotNotifier:
    """Handle notifications when slots become available"""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def notify_slot_available(self, slots: List[VisaSlot]):
        """Send notifications when slots become available"""
        message = self._format_slot_message(slots)

        # Send Telegram notification
        if self.config.telegram_bot_token and self.config.telegram_chat_id:
            await self._send_telegram_message(message)

        # Log the notification
        self.logger.info(f"🔔 Notification sent: {message}")

    def _format_slot_message(self, slots: List[VisaSlot]) -> str:
        """Format slot information for notifications"""
        if not slots:
            return "No slots available"

        message = f"🎯 VISA SLOTS AVAILABLE! ({len(slots)} found)\n\n"

        for i, slot in enumerate(slots[:5], 1):  # Show first 5 slots
            message += f"{i}. {slot.date.strftime('%B %d, %Y')} - {slot.consulate}\n"

        if len(slots) > 5:
            message += f"\n... and {len(slots) - 5} more slots!"

        message += "\n⚡ Book now using the automation system!"
        return message

    async def _send_telegram_message(self, message: str):
        """Send message via Telegram bot"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"

                payload = {
                    'chat_id': self.config.telegram_chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }

                response = await client.post(url, json=payload, timeout=10.0)

                if response.status_code == 200:
                    self.logger.info("📱 Telegram notification sent successfully")
                else:
                    self.logger.error(f"❌ Telegram notification failed: {response.status_code}")

        except Exception as e:
            self.logger.error(f"❌ Telegram notification error: {e}")
