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
            'checkvisaslots': 'https://app.checkvisaslots.com',
            'api_endpoint': 'https://app.checkvisaslots.com/slots/v3',
            'indian_portal': 'https://www.usvisascheduling.com'
        }
        self.api_key = 'HZK5KL'  # API key for checkvisaslots.com

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
        Check slots using checkvisaslots.com API v3 for Indian visa appointments
        """
        slots = []
        try:
            async with httpx.AsyncClient() as client:
                # Construct API request for Indian visa slots using the actual API
                params = {
                    'country': 'india',
                    'consulate': self.config.consular_id,
                    'visa_type': 'us_visa',  # US visa appointments in India
                }

                if target_date:
                    params['date_from'] = target_date.strftime('%Y-%m-%d')

                # Use the exact headers from the working curl command
                headers = {
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

                # Use the actual API endpoint
                endpoint = self.base_urls['api_endpoint']
                
                try:
                    response = await client.get(
                        endpoint,
                        params=params,
                        headers=headers,
                        timeout=30.0
                    )

                    if response.status_code == 200:
                        data = response.json()
                        slots = self._parse_api_response(data)
                        self.logger.info(f"📊 Found {len(slots)} slots via checkvisaslots.com API v3")
                    else:
                        self.logger.warning(f"API request failed with status {response.status_code}")
                        self.logger.debug(f"Response: {response.text}")

                except Exception as e:
                    self.logger.error(f"API endpoint {endpoint} failed: {e}")

        except Exception as e:
            self.logger.error(f"❌ API slot check failed: {e}")

        return slots

    def _parse_api_response(self, data: Dict) -> List[VisaSlot]:
        """Parse checkvisaslots.com API v3 response into VisaSlot objects"""
        slots = []

        try:
            # Parse checkvisaslots.com API v3 response format
            if isinstance(data, dict) and 'slotDetails' in data:
                # This is the actual API v3 response format
                slot_details = data['slotDetails']
                
                for slot_info in slot_details:
                    slot = self._parse_slot_details(slot_info)
                    if slot:
                        slots.append(slot)
                        
            elif isinstance(data, list):
                # Direct list of slots
                for slot_info in data:
                    slot = self._parse_slot_info(slot_info)
                    if slot:
                        slots.append(slot)
                        
            elif isinstance(data, dict):
                # Check for different response structures
                if 'slots' in data:
                    # Nested slots array
                    for slot_info in data['slots']:
                        slot = self._parse_slot_info(slot_info)
                        if slot:
                            slots.append(slot)
                            
                elif 'data' in data:
                    # Data wrapper
                    for slot_info in data['data']:
                        slot = self._parse_slot_info(slot_info)
                        if slot:
                            slots.append(slot)
                            
                elif 'available_dates' in data:
                    # Available dates format
                    for date_info in data['available_dates']:
                        slot = self._parse_date_info(date_info)
                        if slot:
                            slots.append(slot)
                            
                elif 'appointments' in data:
                    # Appointments format
                    for appt_info in data['appointments']:
                        slot = self._parse_appointment_info(appt_info)
                        if slot:
                            slots.append(slot)

        except Exception as e:
            self.logger.error(f"Error parsing API response: {e}")
            self.logger.debug(f"Raw response data: {data}")

        return slots

    def _parse_slot_details(self, slot_info: Dict) -> Optional[VisaSlot]:
        """Parse slotDetails from checkvisaslots.com API v3"""
        try:
            # Extract location info
            location = slot_info.get('visa_location', 'Unknown')
            slots_count = slot_info.get('slots', 0)
            
            # Map location names to consulate IDs
            location_mapping = {
                'CHENNAI': '122',
                'CHENNAI VAC': '122',
                'HYDERABAD': '123', 
                'HYDERABAD VAC': '123',
                'KOLKATA': '124',
                'KOLKATA VAC': '124',
                'MUMBAI': '125',
                'MUMBAI VAC': '125',
                'NEW DELHI': '126',
                'NEW DELHI VAC': '126',
                'DELHI': '126',
                'DELHI VAC': '126'
            }
            
            consulate_id = location_mapping.get(location.upper(), self.config.consular_id)
            
            # Clean up location name
            consulate_name = location.replace(' VAC', '').title()
            
            # Create a slot for today (since API doesn't provide specific dates)
            # In a real implementation, you might want to check multiple days
            from datetime import datetime, timedelta
            today = datetime.now().date()
            
            # Create slots for the next 30 days if available
            available_slots = []
            for i in range(30):
                slot_date = today + timedelta(days=i)
                
                slot = VisaSlot(
                    date=datetime.combine(slot_date, datetime.min.time()),
                    consulate=consulate_name,
                    consulate_id=consulate_id,
                    available=slots_count > 0,
                    slot_type='regular'
                )
                available_slots.append(slot)
                
                # Only create one slot per location if slots are available
                if slots_count > 0:
                    break
            
            # Return the first available slot or the first slot if none available
            return available_slots[0] if available_slots else None
            
        except Exception as e:
            self.logger.warning(f"Error parsing slot details: {e}")
            return None

    def _parse_slot_info(self, slot_info: Dict) -> Optional[VisaSlot]:
        """Parse individual slot information"""
        try:
            # Extract date
            date_str = slot_info.get('date') or slot_info.get('appointment_date') or slot_info.get('available_date')
            if not date_str:
                return None
                
            slot_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Extract consulate info
            consulate_name = slot_info.get('consulate', slot_info.get('location', slot_info.get('facility', 'Unknown')))
            consulate_id = slot_info.get('consulate_id', slot_info.get('facility_id', self.config.consular_id))
            
            # Check availability
            available = slot_info.get('available', slot_info.get('is_available', True))
            
            return VisaSlot(
                date=slot_date,
                consulate=consulate_name,
                consulate_id=str(consulate_id),
                available=available,
                slot_type=slot_info.get('type', 'regular')
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing slot info: {e}")
            return None

    def _parse_date_info(self, date_info: Dict) -> Optional[VisaSlot]:
        """Parse date-based slot information"""
        try:
            date_str = date_info.get('date')
            if not date_str:
                return None
                
            slot_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            return VisaSlot(
                date=slot_date,
                consulate=date_info.get('consulate', 'Unknown'),
                consulate_id=str(date_info.get('consulate_id', self.config.consular_id)),
                available=True,
                slot_type='regular'
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing date info: {e}")
            return None

    def _parse_appointment_info(self, appt_info: Dict) -> Optional[VisaSlot]:
        """Parse appointment-based slot information"""
        try:
            date_str = appt_info.get('date') or appt_info.get('appointment_date')
            if not date_str:
                return None
                
            slot_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            return VisaSlot(
                date=slot_date,
                consulate=appt_info.get('consulate', 'Unknown'),
                consulate_id=str(appt_info.get('consulate_id', self.config.consular_id)),
                available=appt_info.get('available', True),
                slot_type=appt_info.get('appointment_type', 'regular')
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing appointment info: {e}")
            return None

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
