import socket
import threading
import time
import json
from datetime import datetime

class TwitchChatReader:
    def __init__(self, channel, nickname, token):
        self.channel = channel.lower()
        self.nickname = nickname.lower()
        self.token = token
        self.socket = None
        self.last_message = None
        self.running = False
        self.last_save_time = time.time()
        
    def connect(self):
        """Connect to Twitch IRC server"""
        try:
            self.socket = socket.socket()
            self.socket.settimeout(10.0)
            self.socket.connect(('irc.chat.twitch.tv', 6667))
            
            # Authenticate
            self.socket.send(f"PASS {self.token}\r\n".encode('utf-8'))
            self.socket.send(f"NICK {self.nickname}\r\n".encode('utf-8'))
            self.socket.send(f"JOIN #{self.channel}\r\n".encode('utf-8'))
            
            print(f"✅ Connected to #{self.channel}'s chat")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
        
    def listen(self):
        """Listen for messages"""
        buffer = ""
        
        while self.running:
            try:
                data = self.socket.recv(1024).decode('utf-8', errors='ignore')
                if not data:
                    print("⚠️  Connection lost, reconnecting...")
                    self.reconnect()
                    continue
                    
                buffer += data
                lines = buffer.split("\r\n")
                buffer = lines.pop()
                
                for line in lines:
                    if line:
                        self.handle_line(line)
                        
            except socket.timeout:
                continue
            except Exception as e:
                print(f"❌ Listen error: {e}")
                if self.running:
                    self.reconnect()
                
    def handle_line(self, line):
        """Handle incoming IRC messages"""
        # Respond to PING
        if line.startswith('PING'):
            self.socket.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
            return
            
        # Handle PRIVMSG (chat messages)
        if 'PRIVMSG' in line:
            try:
                # Parse the message
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    username = parts[1].split('!')[0]
                    message = parts[2].strip()
                    
                    self.last_message = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'username': username,
                        'message': message
                    }
                    
                    print(f"💬 [{self.last_message['timestamp']}] {username}: {message}")
                    
            except Exception as e:
                print(f"Error parsing message: {e}")
                
    def reconnect(self):
        """Reconnect to Twitch IRC"""
        time.sleep(5)
        try:
            if self.socket:
                self.socket.close()
            self.connect()
        except Exception as e:
            print(f"Reconnection failed: {e}")
            
    def save_last_message(self):
        """Save the last message every 30 seconds"""
        while self.running:
            current_time = time.time()
            if current_time - self.last_save_time >= 30 and self.last_message:
                filename = f"twitch_chat_{datetime.now().strftime('%Y%m%d')}.txt"
                
                try:
                    with open(filename, 'a', encoding='utf-8') as f:
                        f.write(f"{self.last_message['timestamp']} - {self.last_message['username']}: {self.last_message['message']}\n")
                    
                    print(f"💾 Saved message to {filename}")
                    self.last_save_time = current_time
                    self.last_message = None  # Reset for next interval
                    
                except Exception as e:
                    print(f"Error saving message: {e}")
                    
            time.sleep(1)
            
    def start(self):
        """Start the chat reader"""
        if not self.connect():
            return
            
        self.running = True
        
        # Start listening thread
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.daemon = True
        listen_thread.start()
        
        # Start saving thread
        save_thread = threading.Thread(target=self.save_last_message)
        save_thread.daemon = True
        save_thread.start()
        
        print("🚀 Chat reader started! Press Ctrl+C to stop.")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
            self.running = False
            if self.socket:
                self.socket.close()

def load_credentials():
    """Load Twitch credentials from credentials.json file"""
    try:
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
            return creds['channel'], creds['nickname'], creds['token']
    except FileNotFoundError:
        print("❌ credentials.json file not found")
        return None, None, None
    except json.JSONDecodeError:
        print("❌ Error parsing credentials.json file")
        return None, None, None
    except KeyError as e:
        print(f"❌ Missing required field in credentials.json: {e}")
        return None, None, None

# Update the main section
if __name__ == "__main__":
    CHANNEL, NICKNAME, TOKEN = load_credentials()
    
    if not all([CHANNEL, NICKNAME, TOKEN]):
        print("❌ Failed to load credentials. Please check your credentials.json file.")
        exit(1)
        
    reader = TwitchChatReader(CHANNEL, NICKNAME, TOKEN)
    reader.start()