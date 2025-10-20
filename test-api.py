import requests
import time
import json
from datetime import datetime

class TwitchChatBot:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.last_message = None
        
    def get_app_access_token(self):
        """Get app access token using client credentials"""
        url = "https://id.twitch.tv/oauth2/token"
        
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            print("✅ Successfully obtained access token")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting access token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return False
    
    def get_channel_info(self, username):
        """Get channel ID from username"""
        headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.access_token}'
        }
        
        url = f"https://api.twitch.tv/helix/users?login={username}"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data['data']:
                channel_id = data['data'][0]['id']
                print(f"✅ Found channel ID: {channel_id} for {username}")
                return channel_id
            else:
                print(f"❌ Channel {username} not found")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting channel info: {e}")
            return None
    
    def get_chat_messages(self, channel_id, limit=10):
        """Get recent chat messages"""
        headers = {
            'Client-ID': self.client_id,
            'Authorization': f'Bearer {self.access_token}'
        }
        
        url = f"https://api.twitch.tv/helix/chat/messages?broadcaster_id={channel_id}"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data', [])
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting chat messages: {e}")
            return []
    
    def monitor_chat(self, channel_username):
        """Monitor chat and save last message every 30 seconds"""
        print(f"🚀 Starting chat monitor for: {channel_username}")
        
        # Get access token
        if not self.get_app_access_token():
            return
        
        # Get channel ID
        channel_id = self.get_channel_info(channel_username)
        if not channel_id:
            return
        
        print("📝 Monitoring chat... (Ctrl+C to stop)")
        
        try:
            while True:
                messages = self.get_chat_messages(channel_id)
                
                if messages:
                    latest_message = messages[0]  # Most recent message
                    
                    self.last_message = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'username': latest_message.get('commenter', {}).get('display_name', 'Unknown'),
                        'message': latest_message.get('message', {}).get('body', '')
                    }
                    
                    # Save to file
                    self.save_message()
                    print(f"💾 Saved: {self.last_message['username']}: {self.last_message['message']}")
                else:
                    print("⏳ No new messages")
                
                # Wait 30 seconds
                print("⏰ Waiting 30 seconds...")
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
    
    def save_message(self):
        """Save message to file"""
        if self.last_message:
            filename = "twitch_chat.txt"
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(f"{self.last_message['timestamp']} - {self.last_message['username']}: {self.last_message['message']}\n")

def load_credentials():
    """Load credentials from credentials.json file"""
    try:
        with open('credentials.json', 'r') as f:
            credentials = json.load(f)
            return (
                credentials['client_id'],
                credentials['client_secret'],
                credentials['channel_username']
            )
    except FileNotFoundError:
        print("❌ credentials.json file not found")
        return None
    except json.JSONDecodeError:
        print("❌ Error reading credentials.json file")
        return None
    except KeyError as e:
        print(f"❌ Missing required field in credentials.json: {e}")
        return None

# Replace the hardcoded credentials with the loading function
if __name__ == "__main__":
    credentials = load_credentials()
    if credentials:
        CLIENT_ID, CLIENT_SECRET, CHANNEL_USERNAME = credentials
        bot = TwitchChatBot(CLIENT_ID, CLIENT_SECRET)
        bot.monitor_chat(CHANNEL_USERNAME)
    else:
        print("Failed to load credentials. Please check your credentials.json file.")