#!/usr/bin/env python3
"""
J.A.R.V.I.S. - Just A Rather Very Intelligent System
A Voice-Activated AI Assistant
Features: Voice Recognition, Text-to-Speech, Smart Commands, Learning System
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import datetime
import webbrowser
import os
import json
import random
import subprocess
import sys

# Try to import voice libraries, provide fallback if not available
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_ENABLED = True
except ImportError:
    VOICE_ENABLED = False
    print("Voice libraries not installed. Running in text-only mode.")
    print("Install with: pip install speechrecognition pyttsx3 pyaudio")

class JarvisAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("J.A.R.V.I.S. - AI Assistant")
        self.root.geometry("1000x700")
        self.root.configure(bg='#0a0a0a')
        
        # Initialize voice engine
        self.voice_engine = None
        self.recognizer = None
        self.microphone = None
        self.is_listening = False
        
        if VOICE_ENABLED:
            try:
                self.voice_engine = pyttsx3.init()
                self.voice_engine.setProperty('rate', 150)
                self.voice_engine.setProperty('volume', 0.9)
                # Try to set a male voice like JARVIS
                voices = self.voice_engine.getProperty('voices')
                for voice in voices:
                    if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                        self.voice_engine.setProperty('voice', voice.id)
                        break
                
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                
                # Calibrate for ambient noise
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    
            except Exception as e:
                print(f"Voice initialization error: {e}")
                VOICE_ENABLED = False
        
        # Memory/Knowledge base
        self.memory_file = "jarvis_memory.json"
        self.memory = self.load_memory()
        
        # Conversation history
        self.conversation = []
        
        # Command handlers
        self.commands = {
            'time': self.tell_time,
            'date': self.tell_date,
            'day': self.tell_day,
            'search': self.web_search,
            'open': self.open_application,
            'weather': self.tell_weather,
            'joke': self.tell_joke,
            'remember': self.remember_this,
            'what do you know': self.recall_memory,
            'who are you': self.introduce_self,
            'help': self.show_help,
            'exit': self.shutdown,
            'quit': self.shutdown,
            'goodbye': self.shutdown,
            'calculate': self.calculate,
            'news': self.open_news,
            'youtube': self.open_youtube,
            'google': self.open_google,
            'music': self.play_music,
            'system': self.system_info,
        }
        
        self.setup_ui()
        self.speak("JARVIS online. Systems operational. Awaiting your command, sir.")
        
    def load_memory(self):
        """Load learned information from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {
            'facts': {},
            'preferences': {},
            'conversations': []
        }
    
    def save_memory(self):
        """Save learned information to file"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def setup_ui(self):
        """Setup the futuristic JARVIS interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header with JARVIS logo
        header = tk.Frame(main_frame, bg='#0a0a0a')
        header.pack(fill='x', pady=(0, 20))
        
        self.status_label = tk.Label(header, text="● ONLINE", font=('Consolas', 12), 
                                    bg='#0a0a0a', fg='#00ff00')
        self.status_label.pack(side='left')
        
        title = tk.Label(header, text="J.A.R.V.I.S.", font=('Orbitron', 32, 'bold'), 
                        bg='#0a0a0a', fg='#00d4ff')
        title.pack(side='right')
        
        subtitle = tk.Label(header, text="Just A Rather Very Intelligent System", 
                           font=('Consolas', 10), bg='#0a0a0a', fg='#666666')
        subtitle.pack(side='right', padx=20)
        
        # Main content area
        content = tk.Frame(main_frame, bg='#0a0a0a')
        content.pack(fill='both', expand=True)
        
        # Left panel - Visualizer/Status
        left_panel = tk.Frame(content, bg='#111111', width=300)
        left_panel.pack(side='left', fill='y', padx=(0, 20))
        left_panel.pack_propagate(False)
        
        # Voice visualizer (animated circles)
        self.visualizer_canvas = tk.Canvas(left_panel, bg='#111111', highlightthickness=0, height=200)
        self.visualizer_canvas.pack(fill='x', pady=20)
        
        self.voice_bars = []
        for i in range(7):
            x = 50 + i * 35
            bar = self.visualizer_canvas.create_rectangle(x, 100, x+20, 100, fill='#00d4ff', outline='')
            self.voice_bars.append(bar)
        
        # Status indicators
        status_frame = tk.Frame(left_panel, bg='#111111')
        status_frame.pack(fill='x', padx=20, pady=20)
        
        indicators = [
            ("Voice Recognition", VOICE_ENABLED),
            ("Memory System", True),
            ("Learning Mode", True),
            ("Internet", self.check_internet())
        ]
        
        for name, status in indicators:
            frame = tk.Frame(status_frame, bg='#111111')
            frame.pack(fill='x', pady=5)
            
            dot = "●" if status else "○"
            color = '#00ff00' if status else '#ff0000'
            
            tk.Label(frame, text=dot, font=('Consolas', 14), bg='#111111', fg=color).pack(side='left')
            tk.Label(frame, text=name, font=('Consolas', 11), bg='#111111', fg='#ffffff').pack(side='left', padx=10)
        
        # Voice control button
        self.voice_btn = tk.Button(left_panel, text="🎤 HOLD TO SPEAK", font=('Consolas', 12, 'bold'),
                                  bg='#00d4ff', fg='#000000', activebackground='#0099cc',
                                  bd=0, padx=20, pady=15, cursor='hand2',
                                  command=self.toggle_voice_listen)
        self.voice_btn.pack(fill='x', padx=20, pady=20)
        
        # Quick commands
        quick_frame = tk.LabelFrame(left_panel, text="QUICK COMMANDS", font=('Consolas', 10),
                                   bg='#111111', fg='#00d4ff', bd=2)
        quick_frame.pack(fill='x', padx=20, pady=10)
        
        quick_commands = ['Time', 'Weather', 'Search', 'Joke', 'System']
        for cmd in quick_commands:
            btn = tk.Button(quick_frame, text=cmd, font=('Consolas', 10),
                          bg='#222222', fg='#00d4ff', bd=0, padx=10, pady=5,
                          command=lambda c=cmd: self.process_command(c.lower()))
            btn.pack(fill='x', pady=2)
        
        # Right panel - Conversation
        right_panel = tk.Frame(content, bg='#0a0a0a')
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Conversation display
        convo_frame = tk.LabelFrame(right_panel, text="CONVERSATION LOG", font=('Consolas', 12),
                                   bg='#0a0a0a', fg='#00d4ff', bd=2)
        convo_frame.pack(fill='both', expand=True)
        
        self.conversation_text = scrolledtext.ScrolledText(convo_frame, font=('Consolas', 11),
                                                          bg='#0a0a0a', fg='#00ff00',
                                                          insertbackground='#00ff00',
                                                          wrap=tk.WORD, state='disabled')
        self.conversation_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Input area
        input_frame = tk.Frame(right_panel, bg='#0a0a0a')
        input_frame.pack(fill='x', pady=(20, 0))
        
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(input_frame, font=('Consolas', 12),
                                   bg='#111111', fg='#ffffff',
                                   insertbackground='#00d4ff',
                                   textvariable=self.input_var)
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.input_entry.bind('<Return>', lambda e: self.send_text_command())
        
        send_btn = tk.Button(input_frame, text="SEND", font=('Consolas', 12, 'bold'),
                            bg='#00d4ff', fg='#000000', bd=0, padx=20, pady=10,
                            command=self.send_text_command)
        send_btn.pack(side='right')
        
        # Footer
        footer = tk.Frame(main_frame, bg='#0a0a0a')
        footer.pack(fill='x', pady=(20, 0))
        
        self.typing_label = tk.Label(footer, text="", font=('Consolas', 10),
                                    bg='#0a0a0a', fg='#00d4ff')
        self.typing_label.pack(side='left')
        
        version_label = tk.Label(footer, text="v2.0 | Stark Industries", 
                                font=('Consolas', 9),
                                bg='#0a0a0a', fg='#444444')
        version_label.pack(side='right')
        
        # Start visualizer animation
        self.animate_visualizer()
    
    def check_internet(self):
        """Check if internet connection is available"""
        try:
            import urllib.request
            urllib.request.urlopen('http://www.google.com', timeout=1)
            return True
        except:
            return False
    
    def animate_visualizer(self):
        """Animate the voice visualizer bars"""
        if self.is_listening:
            # Active listening animation
            for i, bar in enumerate(self.voice_bars):
                height = random.randint(20, 150)
                self.visualizer_canvas.coords(bar, 50 + i * 35, 150 - height, 70 + i * 35, 150)
        else:
            # Idle animation
            for i, bar in enumerate(self.voice_bars):
                self.visualizer_canvas.coords(bar, 50 + i * 35, 145, 70 + i * 35, 150)
        
        self.root.after(100, self.animate_visualizer)
    
    def speak(self, text):
        """Speak text using TTS and add to conversation"""
        self.add_to_conversation(f"JARVIS: {text}", '#00d4ff')
        
        if VOICE_ENABLED and self.voice_engine:
            try:
                self.voice_engine.say(text)
                self.voice_engine.runAndWait()
            except Exception as e:
                print(f"Speech error: {e}")
    
    def add_to_conversation(self, text, color='#00ff00'):
        """Add text to conversation log"""
        self.conversation_text.config(state='normal')
        self.conversation_text.insert('end', text + '\n\n', color)
        self.conversation_text.tag_config(color, foreground=color)
        self.conversation_text.see('end')
        self.conversation_text.config(state='disabled')
        
        # Save to memory
        self.memory['conversations'].append({
            'timestamp': datetime.datetime.now().isoformat(),
            'text': text
        })
        self.save_memory()
    
    def listen_for_command(self):
        """Listen for voice command in background thread"""
        if not VOICE_ENABLED or not self.recognizer:
            self.speak("Voice recognition is not available. Please type your command.")
            return
        
        self.is_listening = True
        self.status_label.config(text="● LISTENING", fg='#ffff00')
        self.typing_label.config(text="Listening...")
        
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            self.status_label.config(text="● PROCESSING", fg='#ff9900')
            self.typing_label.config(text="Processing speech...")
            
            command = self.recognizer.recognize_google(audio).lower()
            
            self.add_to_conversation(f"YOU: {command}", '#ffffff')
            self.process_command(command)
            
        except sr.WaitTimeoutError:
            self.speak("I didn't hear anything. Please try again.")
        except sr.UnknownValueError:
            self.speak("I didn't understand that. Could you repeat, please?")
        except sr.RequestError:
            self.speak("Speech service is unavailable. Please type your command.")
        except Exception as e:
            self.speak(f"An error occurred: {str(e)}")
        
        finally:
            self.is_listening = False
            self.status_label.config(text="● ONLINE", fg='#00ff00')
            self.typing_label.config(text="")
    
    def toggle_voice_listen(self):
        """Toggle voice listening on/off"""
        if self.is_listening:
            self.is_listening = False
            self.status_label.config(text="● ONLINE", fg='#00ff00')
        else:
            thread = threading.Thread(target=self.listen_for_command)
            thread.daemon = True
            thread.start()
    
    def send_text_command(self):
        """Process text command from input field"""
        command = self.input_var.get().strip()
        if command:
            self.add_to_conversation(f"YOU: {command}", '#ffffff')
            self.input_var.set("")
            self.process_command(command.lower())
    
    def process_command(self, command):
        """Process and execute command"""
        self.typing_label.config(text="JARVIS is thinking...")
        
        # Check for exact command matches
        for key, handler in self.commands.items():
            if key in command:
                handler(command)
                self.typing_label.config(text="")
                return
        
        # Check memory for learned facts
        for fact_key, fact_value in self.memory['facts'].items():
            if fact_key in command:
                self.speak(f"I recall that {fact_key} is {fact_value}")
                self.typing_label.config(text="")
                return
        
        # Default response
        responses = [
            "I'm not sure I understand. Could you rephrase that?",
            "That command is not in my database. Try 'help' for available commands.",
            "I'm still learning. Could you teach me what that means?",
            "Interesting. Tell me more, or ask for help to see what I can do."
        ]
        self.speak(random.choice(responses))
        self.typing_label.config(text="")
    
    # ==================== COMMAND HANDLERS ====================
    
    def tell_time(self, command=None):
        """Tell current time"""
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        self.speak(f"The current time is {time_str}")
    
    def tell_date(self, command=None):
        """Tell current date"""
        now = datetime.datetime.now()
        date_str = now.strftime("%B %d, %Y")
        self.speak(f"Today is {date_str}")
    
    def tell_day(self, command=None):
        """Tell current day"""
        now = datetime.datetime.now()
        day_str = now.strftime("%A")
        self.speak(f"Today is {day_str}")
    
    def web_search(self, command):
        """Search the web"""
        query = command.replace('search', '').replace('for', '').strip()
        if query:
            self.speak(f"Searching for {query}")
            webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        else:
            self.speak("What would you like me to search for?")
    
    def open_application(self, command):
        """Open applications"""
        app = command.replace('open', '').strip()
        
        apps = {
            'chrome': 'chrome',
            'firefox': 'firefox',
            'notepad': 'notepad',
            'calculator': 'calc',
            'explorer': 'explorer',
            'cmd': 'cmd',
            'terminal': 'terminal'
        }
        
        for key, value in apps.items():
            if key in app:
                try:
                    self.speak(f"Opening {key}")
                    subprocess.Popen(value)
                    return
                except:
                    self.speak(f"Unable to open {key}")
                    return
        
        self.speak("I don't know that application. Try: chrome, notepad, calculator, or explorer")
    
    def tell_weather(self, command=None):
        """Tell weather (mock - requires API for real data)"""
        self.speak("I don't have weather API access yet. You can add an OpenWeatherMap API key to enable this feature.")
    
    def tell_joke(self, command=None):
        """Tell a joke"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look sad? Because it had too many problems."
        ]
        self.speak(random.choice(jokes))
    
    def remember_this(self, command):
        """Remember a fact"""
        # Parse "remember that [key] is [value]"
        text = command.replace('remember', '').replace('that', '').strip()
        if ' is ' in text:
            parts = text.split(' is ', 1)
            key = parts[0].strip()
            value = parts[1].strip()
            
            self.memory['facts'][key] = value
            self.save_memory()
            self.speak(f"I'll remember that {key} is {value}")
        else:
            self.speak("Please tell me what to remember in the format: 'remember that [something] is [value]'")
    
    def recall_memory(self, command=None):
        """Recall what JARVIS knows"""
        facts = self.memory['facts']
        if facts:
            self.speak(f"I know {len(facts)} things. Here's what I remember:")
            for key, value in list(facts.items())[:5]:  # Show first 5
                self.add_to_conversation(f"  • {key} = {value}", '#888888')
        else:
            self.speak("My memory is empty. Teach me something by saying 'remember that [something] is [value]'")
    
    def introduce_self(self, command=None):
        """Introduce JARVIS"""
        intro = """I am JARVIS, Just A Rather Very Intelligent System. 
        I was designed to assist you with various tasks including voice commands, 
        web searches, system operations, and learning from our conversations. 
        I can remember information you teach me, and I'm constantly improving. 
        How may I assist you today, sir?"""
        self.speak(intro)
    
    def show_help(self, command=None):
        """Show available commands"""
        help_text = """Available commands:
        
        TIME - Current time
        DATE - Current date
        DAY - Current day
        SEARCH [query] - Search Google
        OPEN [app] - Open applications
        YOUTUBE - Open YouTube
        GOOGLE - Open Google
        JOKE - Tell a joke
        REMEMBER THAT [X] IS [Y] - Store information
        WHAT DO YOU KNOW - Recall stored information
        CALCULATE [math] - Do calculations
        SYSTEM - System information
        HELP - Show this help
        EXIT/QUIT - Shutdown JARVIS"""
        
        self.speak("Here are the commands I understand:")
        self.add_to_conversation(help_text, '#888888')
    
    def calculate(self, command):
        """Perform calculations"""
        expression = command.replace('calculate', '').strip()
        try:
            # Safe evaluation
            allowed = set('0123456789+-*/.() ')
            if all(c in allowed for c in expression):
                result = eval(expression)
                self.speak(f"The answer is {result}")
            else:
                self.speak("I can only calculate basic math operations")
        except:
            self.speak("I couldn't calculate that. Please use simple numbers and operators")
    
    def open_news(self, command=None):
        """Open news website"""
        self.speak("Opening news")
        webbrowser.open("https://news.google.com")
    
    def open_youtube(self, command=None):
        """Open YouTube"""
        self.speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")
    
    def open_google(self, command=None):
        """Open Google"""
        self.speak("Opening Google")
        webbrowser.open("https://www.google.com")
    
    def play_music(self, command=None):
        """Open music"""
        self.speak("Opening Spotify")
        webbrowser.open("https://open.spotify.com")
    
    def system_info(self, command=None):
        """Show system information"""
        import platform
        info = f"""System Information:
        Operating System: {platform.system()} {platform.release()}
        Processor: {platform.processor()}
        Python Version: {platform.python_version()}
        JARVIS Version: 2.0
        Memory Entries: {len(self.memory['facts'])}"""
        
        self.speak("Here's your system information:")
        self.add_to_conversation(info, '#888888')
    
    def shutdown(self, command=None):
        """Shutdown JARVIS"""
        self.speak("Shutting down systems. Goodbye, sir.")
        self.root.after(2000, self.root.quit)

# ==================== MAIN ENTRY ====================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════╗
    ║     J.A.R.V.I.S. INITIALIZING...         ║
    ║     Just A Rather Very Intelligent System ║
    ╚══════════════════════════════════════════╝
    """)
    
    if not VOICE_ENABLED:
        print("\n[!] Voice features disabled. Install required libraries:")
        print("    pip install speechrecognition pyttsx3 pyaudio")
        print("\n[!] JARVIS will work in text-only mode.\n")
    
    root = tk.Tk()
    app = JarvisAssistant(root)
    root.mainloop()
