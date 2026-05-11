import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import json
import os
import re
import threading
import time
from datetime import datetime
import pyttsx3
import queue
import requests
import tempfile
import pygame
import uuid
import subprocess
import tkinter.font as tkfont
import sys
import ctypes
import urllib.request
import shutil
import webbrowser

myappid = 'poechattool'

class PoEChatTool:
    def __init__(self):
        self.version = "1.0.4"
        if getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(sys.executable)
            appdata_dir = os.getenv('APPDATA')
            if appdata_dir:
                config_dir = os.path.join(appdata_dir, "PoEChatTool")
                os.makedirs(config_dir, exist_ok=True)
                self.config_file = os.path.join(config_dir, "poe_chat_config.json")
            else:
                self.config_file = os.path.join(script_dir, "poe_chat_config.json")
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_file = os.path.join(script_dir, "poe_chat_config.json")
        
        self.config = self.load_config()
        self.tts_engine = None
        self.main_window = None
        self.chat_text = None
        self.settings_window = None
        self.ng_words_window = None
        self.last_file_positions = {}
        self.tts_queue = queue.Queue()
        self.tts_thread = None
        self.font_size = self.config.get('font_size', 10)
        self.font_family = self.config.get('font_family', 'Consolas')
        self.message_ids = {}
        self.message_entry_tags = {}
        self.displayed_entries = []
        self.scrollable_canvases = []
        self.missing_log_files = set()
        self.max_log_messages = self.config.get('max_log_messages', 100)
        self.theme_mode = self.config.get('theme_mode', 'dark')
        self.theme_palettes = {
            'dark': {
                'window': '#111827',
                'surface': '#182033',
                'surface_alt': '#222c42',
                'menu_bg': '#0b1020',
                'menu_hover': '#182033',
                'menu_border': '#263247',
                'border': '#334155',
                'text': '#e5e7eb',
                'muted': '#94a3b8',
                'accent': '#60a5fa',
                'chat_bg': '#0b1020',
                'chat_text': '#e5e7eb',
                'chat_border': '#263247',
                'selection': '#334155',
                'tree_selection': '#334155',
                'translation': '#38bdf8',
                'translation_result': '#34d399',
                'update': '#facc15'
            },
            'light': {
                'window': '#f5f7fb',
                'surface': '#ffffff',
                'surface_alt': '#eef2f7',
                'menu_bg': '#ffffff',
                'menu_hover': '#eef2f7',
                'menu_border': '#d9e2ec',
                'border': '#d9e2ec',
                'text': '#1f2937',
                'muted': '#64748b',
                'accent': '#2563eb',
                'chat_bg': '#ffffff',
                'chat_text': '#111827',
                'chat_border': '#d9e2ec',
                'selection': '#dbeafe',
                'tree_selection': '#dbeafe',
                'translation': '#0284c7',
                'translation_result': '#047857',
                'update': '#b45309'
            }
        }
        if self.theme_mode not in self.theme_palettes:
            self.theme_mode = 'dark'
        self.palette = self.theme_palettes[self.theme_mode]
        
        self.monitoring_enabled = self.config.get('monitoring_enabled', True)
        self.monitoring_threads = {}
        self.stop_monitoring = threading.Event()
        
        self.check_for_updates_on_startup = self.config.get('check_for_updates', True)
        
        self.translation_service = self.config.get('translation_service', 'google')
        self.target_language = self.config.get('target_language', 'en')
        self.source_language = self.config.get('source_language', 'auto')
        self.deepl_api_key = self.config.get('deepl_api_key', '')
        self.google_cloud_api_key = self.config.get('google_cloud_api_key', '')
        
        self.default_chat_colors = {
            'グローバル': '#FF0000',
            'パーティー': '#0080FF',
            'トレード': '#FFA500',
            'ウィスパー': '#800080',
            'ギルド': '#808080',
            'その他': '#FFFFFF'
        }
        self.chat_colors = self.config.get('chat_colors', self.default_chat_colors.copy())
        
        self.voicevox_process = None
        
        self.voicevox_speakers = {
            'ずんだもん': {'ノーマル': 3, 'あまあま': 1, 'ツンツン': 7, 'セクシー': 5, 'ささヤキ': 22, 'ヒソヒソ': 38, 'ヘロヘロ': 75, 'なみだめ': 76},
            '四国めたん': {'ノーマル': 2, 'あまあま': 0, 'ツンツン': 6, 'セクシー': 4, 'ささヤキ': 36, 'ヒソヒソ': 37},
            '春日部つむぎ': {'ノーマル': 8},
            '中国うさぎ': {'ノーマル': 61, 'おどろき': 62, 'こわがり': 63, 'へろへろ': 64},
            '雨晴はう': {'ノーマル': 10},
            '冥鳴ひまり': {'ノーマル': 14},
            '東北ずん子': {'ノーマル': 107},
            '東北きりたん': {'ノーマル': 108},
            '東北イタコ': {'ノーマル': 109},
            '栄田まめん': {'ノーマル': 67},
            '波音リツ': {'ノーマル': 9, 'クイーン': 65},
            '玄野武宏': {'ノーマル': 11, '喜び': 39, 'ツンギレ': 40, '悲しみ': 41},
            '白上虎太郎': {'ふつう': 12, 'わーい': 32, 'びくびく': 33, 'おこ': 34, 'びえーん': 35},
            '青山龍星': {'ノーマル': 13, '熱血': 81, '不機嫌': 82, '喜び': 83, 'しっとり': 84, 'かなしみ': 85, 'ささヤキ': 86},
            '九州そら': {'ノーマル': 16, 'あまあま': 15, 'ツンツン': 18, 'セクシー': 17, 'ささヤキ': 19},
            'もち子さん': {'ノーマル': 20, 'セクシー♡あん子': 66, '泣き': 77, '怒り': 78, '喜び': 79, 'のんびり': 80},
            '剣崎雌雄': {'ノーマル': 21},
            'WhiteCUL': {'ノーマル': 23, 'たのしい': 24, 'かなしい': 25, 'びえーん': 26},
            '後鬼': {'人間ver.': 27, 'ぬいぐるみver.': 28, '人間（怒り）ver.': 87, '鬼ver.': 88},
            'No.7': {'ノーマル': 29, 'アナウンス': 30, '読み聞かせ': 31},
            'ちび式じい': {'ノーマル': 42},
            '櫻歌ミコ': {'ノーマル': 43, '第二形態': 44, 'ロリ': 45},
            '小夜/SAYO': {'ノーマル': 46},
            'ナースロボ＿タイプＴ': {'ノーマル': 47, '楽々': 48, '恐怖': 49, '内緒話': 50},
            '†聖騎士 紅桜†': {'ノーマル': 51},
            '雀松朱司': {'ノーマル': 52},
            '麒ヶ島宗麟': {'ノーマル': 53},
            '春歌ナナ': {'ノーマル': 54},
            '猫使アル': {'ノーマル': 55, 'おちつき': 56, 'うきうき': 57, 'つよつよ': 110, 'へろへろ': 111},
            '猫使ビィ': {'ノーマル': 58, 'おちつき': 59, '人見知り': 60, 'つよつよ': 112},
            'あいえるたん': {'ノーマル': 68},
            '満別花丸': {'ノーマル': 69, '元気': 70, 'ささヤキ': 71, 'ぶりっ子': 72, 'ボーイ': 73},
            '琴詠ニア': {'ノーマル': 74},
            'Voidoll': {'ノーマル': 89},
            'ずぼん子': {'ノーマル': 90, '低血圧': 91, '覚醒': 92, '実況風': 93},
            '中部つるぎ': {'ノーマル': 94, '怒り': 95, 'ヒソヒソ': 96, 'おどおど': 97, '絶望と敗北': 98},
            '離縁': {'ノーマル': 99, 'シリアス': 101},
            '黒沢冴白': {'ノーマル': 100},
            'ユーレイちゃん': {'ノーマル': 102, '甘々': 103, '哀しみ': 104, 'ささヤキ': 105, 'ツクモちゃん': 106}
        }
        
        self.init_tts()
        self.init_pygame()
        self.create_main_window()
        self.start_tts_thread()
        
        if os.name == 'nt':
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except AttributeError:
                pass
        
        if self.config.get('auto_start_voicevox', False) and self.config.get('voicevox_path', ''):
            self.start_voicevox_if_needed()
    
    def load_config(self):
        default_config = {
            'log_file_path': '',
            'log_file_path2': '',
            'enable_tts': True,
            'auto_scroll': True,
            'tts_engine': 'pyttsx3',
            'voicevox_url': 'http://127.0.0.1:50021',
            'voicevox_character': 'ずんだもん',
            'voicevox_style': 'ノーマル',
            'tts_mode': 'queue',
            'tts_rate': 175,
            'tts_volume': 0.5,
            'voicevox_speed_scale': 1.25,
            'voicevox_volume_scale': 1.005,
            'font_size': 12,
            'font_family': 'Meiryo UI',
            'theme_mode': 'dark',
            'max_log_messages': 100,
            'chat_filter': {
                'グローバル': True,
                'パーティー': True,
                'トレード': True,
                'ウィスパー': True,
                'ギルド': True
            },
            'chat_tts_filter': {
                'グローバル': True,
                'パーティー': True,
                'トレード': True,
                'ウィスパー': True,
                'ギルド': True
            },
            'chat_colors': {
                'グローバル': '#FF0000',
                'パーティー': '#0080FF',
                'トレード': '#FFA500',
                'ウィスパー': '#800080',
                'ギルド': '#808080',
                'その他': '#FFFFFF'
            },
            'window_settings': {
                'width': 800,
                'height': 600,
                'x': 100,
                'y': 100
            },
            'settings_window_settings': {
                'width': 600,
                'height': 800,
                'x': 200,
                'y': 200
            },
            'ng_window_settings': {
                'width': 600,
                'height': 500,
                'x': 300,
                'y': 300
            },
            'show_timestamp': True,
            'show_chat_type': True,
            'translation_service': 'google',
            'target_language': 'ja',
            'source_language': 'auto',
            'deepl_api_key': '',
            'google_cloud_api_key': '',
            'show_translation_buttons': True,
            'auto_start_voicevox': True,
            'voicevox_path': '',
            'enable_Webhook': False,
            'Webhook_webhook_url': '',
            'Webhook_message_format': '[{type}] {username}: {message}',
            'monitoring_enabled': True,
            'check_for_updates': True,
            'ng_words': [{'word': 'Ŵ', 'display': True, 'tts': True}, {'word': 'Ƈ', 'display': True, 'tts': True}],
            'ng_word_display_filter': True,
            'ng_word_tts_filter': True,
            'spam_space_threshold': 7,
            'spam_space_filter': False
        }

        def normalize_config(config):
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            if not isinstance(config.get('chat_colors'), dict):
                config['chat_colors'] = default_config['chat_colors'].copy()
            if not isinstance(config.get('chat_filter'), dict):
                config['chat_filter'] = default_config['chat_filter'].copy()
            if not isinstance(config.get('chat_tts_filter'), dict):
                config['chat_tts_filter'] = default_config['chat_tts_filter'].copy()
            for chat_type in default_config['chat_colors']:
                if chat_type not in config['chat_colors']:
                    config['chat_colors'][chat_type] = default_config['chat_colors'][chat_type]
                if chat_type in default_config['chat_filter'] and chat_type not in config['chat_filter']:
                    config['chat_filter'][chat_type] = default_config['chat_filter'][chat_type]
                if chat_type in default_config['chat_tts_filter'] and chat_type not in config['chat_tts_filter']:
                    config['chat_tts_filter'][chat_type] = default_config['chat_tts_filter'][chat_type]
            if not isinstance(config.get('ng_words'), list):
                config['ng_words'] = default_config['ng_words']
            try:
                config['max_log_messages'] = max(1, int(config.get('max_log_messages', 100)))
            except (TypeError, ValueError):
                config['max_log_messages'] = default_config['max_log_messages']
            return config

        def backup_broken_config():
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"{self.config_file}.broken_{timestamp}.bak"
                shutil.copy2(self.config_file, backup_path)
            except Exception:
                pass
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    config = normalize_config(config)
                    with open(self.config_file, 'w', encoding='utf-8') as out_f:
                        json.dump(config, out_f, ensure_ascii=False, indent=2)
                    return config
            except Exception as e:
                backup_broken_config()
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        return default_config
    
    def save_config(self):
        self.config['auto_scroll'] = self.auto_scroll_var.get()
        self.config['enable_tts'] = self.tts_enabled_var.get()
        self.config['monitoring_enabled'] = self.monitoring_enabled
        self.config['theme_mode'] = self.theme_mode
        self.config['max_log_messages'] = self.max_log_messages
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("保存エラー", f"設定の保存に失敗しました:\n{e}")
    
    def init_pygame(self):
        try:
            pygame.mixer.init()
        except Exception as e:
            messagebox.showerror("初期化エラー", f"pygameの初期化に失敗しました:\n{e}")
    
    def init_tts(self):
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', self.config['tts_rate'])
            self.tts_engine.setProperty('volume', self.config['tts_volume'])
        except Exception as e:
            messagebox.showerror("TTSエラー", "TTSの初期化に失敗しました。TTS機能は無効になります。")
            self.config['enable_tts'] = False
    
    def configure_app_style(self):
        palette = self.palette
        self.main_window.configure(bg=palette['window'])

        style = ttk.Style(self.main_window)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        base_font = ('Meiryo UI', 9)
        style.configure('.', font=base_font, background=palette['window'], foreground=palette['text'])
        style.configure('TFrame', background=palette['window'])
        style.configure('Surface.TFrame', background=palette['surface'])
        style.configure('TLabel', background=palette['window'], foreground=palette['text'])

        style.configure('TButton', padding=(12, 6), relief='flat', borderwidth=1,
                        background=palette['surface'], foreground=palette['text'])
        style.map('TButton',
                  background=[('active', palette['surface_alt']), ('pressed', palette['border'])],
                  foreground=[('disabled', palette['muted'])])

        style.configure('TCheckbutton', background=palette['window'], foreground=palette['text'], padding=(2, 4))
        style.map('TCheckbutton', background=[('active', palette['window'])])
        style.configure('TRadiobutton', background=palette['window'], foreground=palette['text'], padding=(2, 4))
        style.map('TRadiobutton', background=[('active', palette['window'])])

        style.configure('TEntry', fieldbackground=palette['surface'], foreground=palette['text'],
                        bordercolor=palette['border'], lightcolor=palette['border'],
                        darkcolor=palette['border'], padding=(8, 5))
        style.configure('TCombobox', fieldbackground=palette['surface'], foreground=palette['text'],
                        bordercolor=palette['border'], arrowcolor=palette['muted'], padding=(8, 5))
        style.map('TCombobox', fieldbackground=[('readonly', palette['surface'])])

        style.configure('TNotebook', background=palette['window'], borderwidth=0)
        style.configure('TNotebook.Tab', background=palette['surface_alt'], foreground=palette['muted'],
                        padding=(14, 8), borderwidth=0)
        style.map('TNotebook.Tab',
                  background=[('selected', palette['surface']), ('active', palette['surface_alt'])],
                  foreground=[('selected', palette['text']), ('active', palette['text'])])

        style.configure('TLabelframe', background=palette['window'], bordercolor=palette['border'],
                        relief='solid', padding=(12, 10))
        style.configure('TLabelframe.Label', background=palette['window'], foreground=palette['muted'])

        style.configure('Treeview', background=palette['surface'], fieldbackground=palette['surface'],
                        foreground=palette['text'], bordercolor=palette['border'], rowheight=28)
        style.configure('Treeview.Heading', background=palette['surface_alt'], foreground=palette['muted'],
                        relief='flat', padding=(8, 6))
        style.map('Treeview', background=[('selected', palette['tree_selection'])], foreground=[('selected', palette['text'])])

        style.configure('Vertical.TScrollbar', background=palette['surface_alt'], troughcolor=palette['window'],
                        bordercolor=palette['window'], arrowcolor=palette['muted'],
                        lightcolor=palette['surface_alt'], darkcolor=palette['surface_alt'],
                        gripcount=0, relief='flat', borderwidth=0)
        style.map('Vertical.TScrollbar',
                  background=[('active', palette['border']), ('pressed', palette['border'])],
                  arrowcolor=[('active', palette['text']), ('pressed', palette['text'])])

    def configure_menu_style(self, menu):
        palette = self.palette
        try:
            menu.configure(
                bg=palette['menu_bg'],
                fg=palette['text'],
                activebackground=palette['menu_hover'],
                activeforeground=palette['text'],
                selectcolor=palette['accent'],
                relief='flat',
                bd=0
            )
        except tk.TclError:
            pass

    def configure_custom_menu_bar_style(self):
        if not getattr(self, 'menu_bar', None):
            return

        palette = self.palette
        self.menu_bar.configure(
            bg=palette['menu_bg'],
            highlightbackground=palette['menu_border'],
            highlightcolor=palette['menu_border']
        )

        for child in self.menu_bar.winfo_children():
            try:
                child.configure(
                    bg=palette['menu_bg'],
                    fg=palette['text'],
                    activebackground=palette['menu_hover'],
                    activeforeground=palette['text'],
                    relief=tk.FLAT,
                    bd=0,
                    padx=10,
                    pady=6,
                    cursor="hand2"
                )
            except tk.TclError:
                pass

    def show_custom_menu(self, button, menu):
        try:
            menu.tk_popup(button.winfo_rootx(), button.winfo_rooty() + button.winfo_height())
        finally:
            try:
                menu.grab_release()
            except tk.TclError:
                pass

    def create_menu_button(self, parent, text, menu=None, command=None):
        options = {
            'text': text,
            'bg': self.palette['menu_bg'],
            'fg': self.palette['text'],
            'activebackground': self.palette['menu_hover'],
            'activeforeground': self.palette['text'],
            'relief': tk.FLAT,
            'bd': 0,
            'padx': 10,
            'pady': 6,
            'cursor': "hand2",
            'font': ('Meiryo UI', 9)
        }

        if menu is not None:
            button = tk.Button(
                parent,
                command=lambda b=None: self.show_custom_menu(button, menu),
                **options
            )
        else:
            button = tk.Button(parent, command=command, **options)

        button.pack(side=tk.LEFT)
        return button

    def configure_title_bar_style(self, window):
        if os.name != 'nt' or not window:
            return

        try:
            window.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()
            value = ctypes.c_int(1 if self.theme_mode == 'dark' else 0)
            for attribute in (20, 19):
                result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    ctypes.c_void_p(hwnd),
                    ctypes.c_int(attribute),
                    ctypes.byref(value),
                    ctypes.sizeof(value)
                )
                if result == 0:
                    break
        except Exception:
            pass

    def schedule_title_bar_style(self, window):
        self.configure_title_bar_style(window)
        try:
            window.after(50, lambda: self.configure_title_bar_style(window))
            window.after(250, lambda: self.configure_title_bar_style(window))
        except tk.TclError:
            pass

    def create_scrollable_tab(self, notebook, title):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=title)

        canvas = tk.Canvas(
            tab,
            bg=self.palette['window'],
            highlightthickness=0,
            bd=0
        )
        scrollbar = ttk.Scrollbar(
            tab,
            orient=tk.VERTICAL,
            command=canvas.yview,
            style='Vertical.TScrollbar'
        )
        content = ttk.Frame(canvas)
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")

        def update_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def fit_content_width(event):
            canvas.itemconfigure(content_window, width=event.width)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        content.bind("<Configure>", update_scrollregion)
        canvas.bind("<Configure>", fit_content_width)
        canvas.bind("<Enter>", lambda event: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda event: canvas.unbind_all("<MouseWheel>"))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollable_canvases.append(canvas)
        return content

    def configure_chat_text_style(self):
        if not self.chat_text:
            return

        palette = self.palette
        self.chat_text.configure(
            bg=palette['chat_bg'],
            fg=palette['chat_text'],
            insertbackground=palette['chat_text'],
            selectbackground=palette['selection'],
            selectforeground=palette['chat_text'],
            highlightbackground=palette['chat_border'],
            highlightcolor=palette['accent']
        )
        self.chat_text.tag_config('message', foreground=palette['chat_text'])
        self.chat_text.tag_config('translation_button', foreground=palette['translation'], underline=True)
        self.chat_text.tag_config('translation_result', foreground=palette['translation_result'])
        self.chat_text.tag_config('update_url', foreground=palette['update'], underline=True)
        self.update_chat_colors()

    def get_readable_chat_color(self, color):
        if self.theme_mode == 'light' and color.lower() in ('#ffffff', 'white'):
            return self.palette['chat_text']
        return color

    def apply_theme(self, mode=None, save=True):
        if mode:
            self.theme_mode = mode
        if self.theme_mode not in self.theme_palettes:
            self.theme_mode = 'dark'

        self.palette = self.theme_palettes[self.theme_mode]
        if hasattr(self, 'theme_var'):
            self.theme_var.set(self.theme_mode)

        if self.main_window:
            self.configure_app_style()
            self.schedule_title_bar_style(self.main_window)
            self.configure_custom_menu_bar_style()
        self.configure_chat_text_style()

        for canvas in list(self.scrollable_canvases):
            try:
                if canvas.winfo_exists():
                    canvas.configure(bg=self.palette['window'])
            except tk.TclError:
                self.scrollable_canvases.remove(canvas)

        for window in (self.settings_window, self.ng_words_window):
            try:
                if window and window.winfo_exists():
                    window.configure(bg=self.palette['window'])
                    self.schedule_title_bar_style(window)
            except tk.TclError:
                pass

        for menu_name in ('file_menu', 'theme_menu', 'translation_menu', 'help_menu', 'context_menu', 'ng_tree_context_menu', 'settings_ng_tree_context_menu'):
            menu = getattr(self, menu_name, None)
            if menu:
                self.configure_menu_style(menu)

        if save:
            self.save_config()

    def create_main_window(self):
        self.main_window = tk.Tk()
        self.configure_app_style()
        self.main_window.title(f"ぽえちゃっと v{self.version}")
        self.schedule_title_bar_style(self.main_window)
        
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
            else:
                icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
            self.main_window.iconbitmap(icon_path)
        except Exception as e:
            pass
        
        self.auto_scroll_var = tk.BooleanVar(value=self.config.get('auto_scroll', True))
        self.tts_enabled_var = tk.BooleanVar(value=self.config.get('enable_tts', True))
        self.theme_var = tk.StringVar(value=self.theme_mode)
        
        w_settings = self.config['window_settings']
        self.main_window.geometry(f"{w_settings['width']}x{w_settings['height']}+{w_settings['x']}+{w_settings['y']}")
        self.main_window.protocol("WM_DELETE_WINDOW", self.close_main_window)
        
        menubar = tk.Frame(
            self.main_window,
            bg=self.palette['menu_bg'],
            bd=0,
            highlightthickness=1,
            highlightbackground=self.palette['menu_border']
        )
        menubar.pack(fill="x")
        self.menu_bar = menubar
        
        file_menu = tk.Menu(menubar, tearoff=0)
        self.configure_menu_style(file_menu)
        file_menu.add_command(label="設定", command=self.open_settings)
        file_menu.add_command(label="チャットクリア", command=self.clear_chat)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.close_main_window)
        self.file_menu = file_menu
        self.create_menu_button(menubar, "ファイル", menu=file_menu)

        theme_menu = tk.Menu(menubar, tearoff=0)
        self.configure_menu_style(theme_menu)
        theme_menu.add_radiobutton(
            label="ダークモード",
            variable=self.theme_var,
            value="dark",
            command=lambda: self.apply_theme("dark")
        )
        theme_menu.add_radiobutton(
            label="ライトモード",
            variable=self.theme_var,
            value="light",
            command=lambda: self.apply_theme("light")
        )
        self.theme_menu = theme_menu
        self.create_menu_button(menubar, "表示", menu=theme_menu)
        
        self.source_lang_var = tk.StringVar(value=self.source_language)
        self.languages = [
            ('自動検出', 'auto'), ('英語', 'en'), ('日本語', 'ja'),
            ('韓国語', 'ko'), ('中国語', 'zh'), ('スペイン語', 'es'),
            ('フランス語', 'fr'), ('ドイツ語', 'de'), ('ロシア語', 'ru')
        ]
        self.translation_menu = tk.Menu(menubar, tearoff=0)
        self.configure_menu_style(self.translation_menu)
        self.create_menu_button(menubar, "翻訳", menu=self.translation_menu)
        
        for name, code in self.languages:
            self.translation_menu.add_radiobutton(
                label=name,
                variable=self.source_lang_var,
                value=code,
                command=lambda c=code: self.set_source_language(c)
            )
        
        self.monitoring_button = self.create_menu_button(menubar, "監視 [ON]", command=self.toggle_monitoring)
        
        self.tts_button = self.create_menu_button(menubar, "読み上げ [ON]", command=self.toggle_tts)
        
        self.scroll_button = self.create_menu_button(menubar, "スクロール [ON]", command=self.toggle_auto_scroll)
        
        self.create_menu_button(menubar, "NG設定", command=self.open_ng_words_settings)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        self.configure_menu_style(help_menu)
        help_menu.add_command(label="アップデートを確認", command=lambda: self.check_for_updates(silent=False))
        help_menu.add_command(label="バージョン情報", command=self.show_version_info)
        self.help_menu = help_menu
        self.create_menu_button(menubar, "ヘルプ", menu=help_menu)
        
        self.menubar = menubar
        self.configure_custom_menu_bar_style()
        self.update_menu_labels()
        
        self.status_var = tk.StringVar(value="監視: 実行中" if self.monitoring_enabled else "監視: 停止中")
        
        chat_frame = ttk.Frame(self.main_window)
        chat_frame.pack(fill="both", expand=True, padx=12, pady=12)
        
        self.chat_text = tk.Text(
            chat_frame, 
            bg=self.palette['chat_bg'], 
            fg=self.palette['chat_text'], 
            insertbackground=self.palette['chat_text'],
            selectbackground=self.palette['selection'],
            selectforeground=self.palette['chat_text'],
            font=(self.font_family, self.font_size),
            wrap=tk.WORD,
            relief=tk.FLAT,
            bd=0,
            padx=14,
            pady=12,
            spacing1=2,
            spacing3=4,
            highlightthickness=1,
            highlightbackground=self.palette['chat_border'],
            highlightcolor=self.palette['accent']
        )
        scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_text.yview, style='Vertical.TScrollbar')
        scrollbar.pack(side="right", fill="y")
        self.chat_text.config(yscrollcommand=scrollbar.set)
        self.chat_text.pack(side="left", fill="both", expand=True)
        
        self.context_menu = tk.Menu(self.chat_text, tearoff=0)
        self.configure_menu_style(self.context_menu)
        self.context_menu.add_command(label="NGワードに追加", command=self.add_selected_to_ng_words)
        self.chat_text.bind("<Button-3>", self.show_context_menu)
        
        self.update_chat_colors()
        
        self.configure_chat_text_style()
        
        self.chat_text.tag_bind('update_url', '<Button-1>', self.open_update_url)
        self.chat_text.tag_bind('update_url', '<Enter>', lambda e: self.chat_text.config(cursor="hand2"))
        self.chat_text.tag_bind('update_url', '<Leave>', lambda e: self.chat_text.config(cursor=""))
            
        if self.monitoring_enabled:
            self.start_monitoring()
    
    def show_context_menu(self, event):
        try:
            if self.chat_text.tag_ranges(tk.SEL):
                self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            pass
    
    def add_selected_to_ng_words(self):
        try:
            selected_text = self.chat_text.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
            if selected_text and not any(ng['word'] == selected_text for ng in self.config['ng_words']):
                self.config['ng_words'].append({'word': selected_text, 'display': True, 'tts': True})
                self.save_config()
                self.display_system_message(f"NGワードに追加しました: {selected_text}")
                if self.ng_words_window and self.ng_words_window.winfo_exists():
                    self.refresh_ng_words_list()
        except Exception as e:
            pass
    
    def open_ng_words_settings(self):
        if self.ng_words_window and self.ng_words_window.winfo_exists():
            self.ng_words_window.lift()
            return
        self.create_ng_words_window()
    
    
    def create_ng_words_window(self):
        self.ng_words_window = tk.Toplevel(self.main_window)
        self.ng_words_window.withdraw()
        self.ng_words_window.configure(bg=self.palette['window'])
        self.ng_words_window.title("NGワード設定")
        self.schedule_title_bar_style(self.ng_words_window)
        
        ng_settings = self.config.get('ng_window_settings', {'width': 600, 'height': 500, 'x': 300, 'y': 300})
        self.ng_words_window.geometry(f"{ng_settings['width']}x{ng_settings['height']}+{ng_settings['x']}+{ng_settings['y']}")
        
        self.ng_words_window.transient(self.main_window)
        self.ng_words_window.grab_set()
        self.ng_words_window.protocol("WM_DELETE_WINDOW", self.close_ng_words_window)
        
        main_frame = ttk.Frame(self.ng_words_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="NGワードリスト（一致するメッセージはフィルターされます）").pack(anchor=tk.W)
        
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        self.ng_word_display_var = tk.BooleanVar(value=self.config.get('ng_word_display_filter', False))
        ttk.Checkbutton(filter_frame, text="NGワード表示フィルター", variable=self.ng_word_display_var,
                       command=self.toggle_ng_word_display_filter).pack(side=tk.LEFT, padx=5)
        
        self.ng_word_tts_var = tk.BooleanVar(value=self.config.get('ng_word_tts_filter', False))
        ttk.Checkbutton(filter_frame, text="NGワード読み上げフィルター", variable=self.ng_word_tts_var,
                       command=self.toggle_ng_word_tts_filter).pack(side=tk.LEFT, padx=5)
        
        spam_frame = ttk.Frame(main_frame)
        spam_frame.pack(fill=tk.X, pady=5)
        
        self.spam_space_var = tk.BooleanVar(value=self.config.get('spam_space_filter', False))
        ttk.Checkbutton(spam_frame, text="スペーススパムフィルター", variable=self.spam_space_var,
                       command=self.toggle_spam_space_filter).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(spam_frame, text="閾値:").pack(side=tk.LEFT, padx=5)
        self.spam_space_threshold_var = tk.IntVar(value=self.config.get('spam_space_threshold', 10))
        threshold_spin = ttk.Spinbox(spam_frame, from_=5, to=50, width=5, textvariable=self.spam_space_threshold_var,
                                    command=self.update_spam_space_threshold)
        threshold_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(main_frame, text="※ON=フィルターをON(表示しない)　OFF=フィルターをOFF(表示する)").pack(anchor=tk.W, pady=5)
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ('word', 'display', 'tts')
        self.ng_words_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        self.ng_words_tree.heading('word', text='NGワード')
        self.ng_words_tree.heading('display', text='表示')
        self.ng_words_tree.heading('tts', text='読み上げ')
        
        self.ng_words_tree.column('word', width=300)
        self.ng_words_tree.column('display', width=80, anchor='center')
        self.ng_words_tree.column('tts', width=80, anchor='center')
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ng_words_tree.yview, style='Vertical.TScrollbar')
        self.ng_words_tree.configure(yscrollcommand=scrollbar.set)
        
        self.ng_words_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.ng_tree_context_menu = tk.Menu(self.ng_words_tree, tearoff=0)
        self.configure_menu_style(self.ng_tree_context_menu)
        self.ng_tree_context_menu.add_command(label="削除", command=self.remove_ng_word_from_tree)
        self.ng_words_tree.bind("<Button-3>", self.show_ng_tree_context_menu)
        
        self.refresh_ng_words_list()
        
        self.ng_words_tree.bind('<ButtonRelease-1>', self.on_ng_word_click)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        add_frame = ttk.Frame(button_frame)
        add_frame.pack(fill=tk.X, pady=5)
        
        self.new_ng_word_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.new_ng_word_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(add_frame, text="追加", command=self.add_ng_word).pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="選択項目を削除", command=self.remove_ng_word).pack(pady=5)
        
        ttk.Button(main_frame, text="閉じる", command=self.close_ng_words_window).pack(pady=5)
        self.schedule_title_bar_style(self.ng_words_window)
        self.ng_words_window.deiconify()
        self.ng_words_window.lift()
        self.ng_words_window.focus_force()
    
    def show_ng_tree_context_menu(self, event):
        item = self.ng_words_tree.identify_row(event.y)
        if item:
            self.ng_words_tree.selection_set(item)
            self.ng_tree_context_menu.post(event.x_root, event.y_root)
    
    def remove_ng_word_from_tree(self):
        self.remove_ng_word()
    
    def refresh_ng_words_list(self):
        for item in self.ng_words_tree.get_children():
            self.ng_words_tree.delete(item)
        
        for ng_word in self.config['ng_words']:
            self.ng_words_tree.insert('', 'end', values=(
                ng_word['word'], 
                'ON' if ng_word['display'] else 'OFF', 
                'ON' if ng_word['tts'] else 'OFF'
            ))
    
    def add_ng_word(self):
        new_word = self.new_ng_word_var.get().strip()
        if new_word and not any(ng['word'] == new_word for ng in self.config['ng_words']):
            self.config['ng_words'].append({'word': new_word, 'display': True, 'tts': True})
            self.ng_words_tree.insert('', 'end', values=(new_word, 'ON', 'ON'))
            self.new_ng_word_var.set("")
            self.save_config()
            self.display_system_message(f"NGワードを追加しました: {new_word}")
    
    def close_ng_words_window(self):
        if self.ng_words_window:
            geometry = self.ng_words_window.geometry()
            match = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', geometry)
            if match:
                w, h, x, y = map(int, match.groups())
                self.config['ng_window_settings'] = {'width': w, 'height': h, 'x': x, 'y': y}
                self.save_config()
            
            self.ng_words_window.destroy()
            self.ng_words_window = None
    
    def on_ng_word_click(self, event):
        item = self.ng_words_tree.selection()
        if item:
            column = self.ng_words_tree.identify_column(event.x)
            if column == '#2':
                self.toggle_ng_word_display(item[0])
            elif column == '#3':
                self.toggle_ng_word_tts(item[0])
    
    def toggle_ng_word_display(self, item_id):
        item = self.ng_words_tree.item(item_id)
        values = item['values']
        word = values[0]
        
        for ng_word in self.config['ng_words']:
            if ng_word['word'] == word:
                ng_word['display'] = not ng_word['display']
                self.ng_words_tree.set(item_id, 'display', 'ON' if ng_word['display'] else 'OFF')
                self.save_config()
                break
    
    def toggle_ng_word_tts(self, item_id):
        item = self.ng_words_tree.item(item_id)
        values = item['values']
        word = values[0]
        
        for ng_word in self.config['ng_words']:
            if ng_word['word'] == word:
                ng_word['tts'] = not ng_word['tts']
                self.ng_words_tree.set(item_id, 'tts', 'ON' if ng_word['tts'] else 'OFF')
                self.save_config()
                break
    
    def toggle_ng_word_display_filter(self):
        self.config['ng_word_display_filter'] = self.ng_word_display_var.get()
        self.save_config()
        self.display_system_message(f"NGワード表示フィルター: {'ON' if self.config['ng_word_display_filter'] else 'OFF'}")
    
    def toggle_ng_word_tts_filter(self):
        self.config['ng_word_tts_filter'] = self.ng_word_tts_var.get()
        self.save_config()
        self.display_system_message(f"NGワード読み上げフィルター: {'ON' if self.config['ng_word_tts_filter'] else 'OFF'}")
    
    def toggle_spam_space_filter(self):
        self.config['spam_space_filter'] = self.spam_space_var.get()
        self.save_config()
        self.display_system_message(f"スペーススパムフィルター: {'ON' if self.config['spam_space_filter'] else 'OFF'}")
    
    def update_spam_space_threshold(self):
        self.config['spam_space_threshold'] = self.spam_space_threshold_var.get()
        self.save_config()
    
    def remove_ng_word(self):
        selection = self.ng_words_tree.selection()
        if selection:
            item = self.ng_words_tree.item(selection[0])
            word = item['values'][0]
            self.ng_words_tree.delete(selection[0])
            self.config['ng_words'] = [ng for ng in self.config['ng_words'] if ng['word'] != word]
            self.save_config()
            self.display_system_message(f"NGワードを削除しました: {word}")
    
    def is_ng_word(self, message, filter_type):
        if not self.config.get(f'ng_word_{filter_type}_filter', False):
            return False
            
        for ng_word in self.config['ng_words']:
            if ng_word[filter_type] and ng_word['word'].lower() in message.lower():
                return True
        return False
    
    def is_spam_space(self, message):
        if not self.config.get('spam_space_filter', False):
            return False
            
        threshold = self.config.get('spam_space_threshold', 10)
        space_count = message.count(' ')
        return space_count >= threshold
    
    def open_update_url(self, event=None):
        try:
            webbrowser.open("https://github.com/ochi3/PoEChatTool/releases")
        except Exception as e:
            pass
    
    def toggle_monitoring(self):
        self.monitoring_enabled = not self.monitoring_enabled
        
        if self.monitoring_enabled:
            self.start_monitoring()
            self.status_var.set("監視: 実行中")
            self.display_system_message("監視を開始しました")
        else:
            self.stop_monitoring.set()
            for thread in self.monitoring_threads.values():
                if thread and thread.is_alive():
                    thread.join(timeout=1.0)
            self.monitoring_threads.clear()
            self.status_var.set("監視: 停止中")
            self.display_system_message("監視を停止しました")
        
        self.update_menu_labels()
        self.save_config()
    
    def start_monitoring(self):
        if not self.monitoring_enabled:
            return
        
        self.stop_monitoring.set()
        for thread in self.monitoring_threads.values():
            if thread and thread.is_alive():
                thread.join(timeout=1.0)
        self.monitoring_threads.clear()
        self.stop_monitoring.clear()
        
        log_files = [
            ('log_file_path', 'PoE1'),
            ('log_file_path2', 'PoE2')
        ]
        
        for log_file_key, log_file_name in log_files:
            log_path = self.config.get(log_file_key, '')
            if log_path and os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        f.seek(0, 2)
                        self.last_file_positions[log_file_key] = f.tell()
                    
                    thread = threading.Thread(
                        target=self.monitor_log_file, 
                        args=(log_file_key, log_file_name),
                        daemon=True
                    )
                    self.monitoring_threads[log_file_key] = thread
                    thread.start()
                except Exception as e:
                    self.display_system_message(f"{log_file_name} 監視開始エラー: {e}")
    
    def monitor_log_file(self, log_file_key, log_file_name):
        log_path = self.config.get(log_file_key, '')
        if not log_path:
            return
        
        while not self.stop_monitoring.is_set():
            try:
                if not os.path.exists(log_path):
                    if log_file_key not in self.missing_log_files:
                        self.missing_log_files.add(log_file_key)
                        self.display_system_message(f"{log_file_name} のログファイルが見つかりません。再作成を待っています。")
                    time.sleep(1.0)
                    continue

                if log_file_key in self.missing_log_files:
                    self.missing_log_files.remove(log_file_key)
                    self.last_file_positions[log_file_key] = 0
                    self.display_system_message(f"{log_file_name} のログファイルを再検出しました。先頭から読み込みます。")

                current_size = os.path.getsize(log_path)
                last_position = self.last_file_positions.get(log_file_key, 0)
                if last_position > current_size:
                    last_position = 0
                    self.last_file_positions[log_file_key] = 0
                    self.display_system_message(f"{log_file_name} のログファイルが更新されたため、読み取り位置をリセットしました。")

                with open(log_path, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    self.last_file_positions[log_file_key] = f.tell()
                    
                    for line in new_lines:
                        line = line.strip()
                        if line:
                            self.process_log_line(line, log_file_name)
            except Exception as e:
                pass
            time.sleep(0.5)
    
    def process_log_line(self, line, source_name):
        chat_info = self.parse_chat_line(line)
        if chat_info:
            chat_info['source'] = source_name
            
            if self.is_ng_word(chat_info['message'], 'display'):
                return
                
            if self.is_spam_space(chat_info['message']):
                return
                
            chat_type = chat_info['type']
            if self.config['chat_filter'].get(chat_type, True):
                self.display_chat_message(chat_info)
                if self.tts_enabled_var.get() and self.config['chat_tts_filter'].get(chat_type, True):
                    if not self.is_ng_word(chat_info['message'], 'tts'):
                        self.speak_message(chat_info['message'])
                if self.config.get('enable_Webhook', False) and self.config.get('Webhook_webhook_url', ''):
                    self.send_to_Webhook(chat_info)
    
    def update_chat_colors(self):
        for chat_type, color in self.chat_colors.items():
            self.chat_text.tag_config(chat_type, foreground=self.get_readable_chat_color(color))
    
    def update_menu_labels(self):
        if self.menubar:
            try:
                monitoring_status = "ON" if self.monitoring_enabled else "OFF"
                self.monitoring_button.configure(text=f"監視 [{monitoring_status}]")
                
                tts_status = "ON" if self.tts_enabled_var.get() else "OFF"
                self.tts_button.configure(text=f"読み上げ [{tts_status}]")
                
                scroll_status = "ON" if self.auto_scroll_var.get() else "OFF"
                self.scroll_button.configure(text=f"スクロール [{scroll_status}]")
            except Exception as e:
                pass

    def set_source_language(self, code):
        self.source_language = code
        self.config['source_language'] = code
        self.save_config()
        self.display_system_message(f"ソース言語を {code} に設定しました")
    
    def toggle_tts(self):
        self.tts_enabled_var.set(not self.tts_enabled_var.get())
        self.update_menu_labels()
        self.save_config()
    
    def toggle_auto_scroll(self):
        self.auto_scroll_var.set(not self.auto_scroll_var.get())
        self.update_menu_labels()
        self.save_config()
    
    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        self.create_settings_window()
    
    def create_settings_window(self):
        self.settings_window = tk.Toplevel(self.main_window)
        self.settings_window.withdraw()
        self.settings_window.configure(bg=self.palette['window'])
        self.settings_window.title("設定")
        self.schedule_title_bar_style(self.settings_window)
        
        sw_settings = self.config.get('settings_window_settings', {'width': 600, 'height': 800, 'x': 200, 'y': 200})
        self.settings_window.geometry(f"{sw_settings['width']}x{sw_settings['height']}+{sw_settings['x']}+{sw_settings['y']}")
        
        self.settings_window.transient(self.main_window)
        self.settings_window.grab_set()
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings_window)
        self.settings_window.grid_rowconfigure(0, weight=1)
        self.settings_window.grid_rowconfigure(1, weight=0)
        self.settings_window.grid_columnconfigure(0, weight=1)
        
        notebook = ttk.Notebook(self.settings_window)
        notebook.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        
        general_tab = self.create_scrollable_tab(notebook, "一般")
        
        log_frame = ttk.LabelFrame(general_tab, text="ログファイル設定")
        log_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(log_frame, text="PoE1 ログファイル:").pack(anchor="w")
        self.log_path_var = tk.StringVar(value=self.config['log_file_path'])
        path_frame = ttk.Frame(log_frame)
        path_frame.pack(fill="x", pady=2)
        ttk.Entry(path_frame, textvariable=self.log_path_var, width=60).pack(side="left", fill="x", expand=True)
        ttk.Button(path_frame, text="参照", command=lambda: self.browse_log_file(self.log_path_var)).pack(side="right", padx=(5, 0))
        
        ttk.Label(log_frame, text="PoE2 ログファイル:").pack(anchor="w", pady=(5, 0))
        self.log_path2_var = tk.StringVar(value=self.config.get('log_file_path2', ''))
        path_frame2 = ttk.Frame(log_frame)
        path_frame2.pack(fill="x", pady=2)
        ttk.Entry(path_frame2, textvariable=self.log_path2_var, width=60).pack(side="left", fill="x", expand=True)
        ttk.Button(path_frame2, text="参照", command=lambda: self.browse_log_file(self.log_path2_var)).pack(side="right", padx=(5, 0))
        
        font_frame = ttk.LabelFrame(general_tab, text="表示設定")
        font_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(font_frame, text="フォントサイズ:").pack(anchor="w")
        self.font_size_var = tk.StringVar(value=str(self.config['font_size']))
        font_size_entry = ttk.Entry(font_frame, textvariable=self.font_size_var, width=10)
        font_size_entry.pack(anchor="w")

        ttk.Label(font_frame, text="表示ログ上限:").pack(anchor="w", pady=(5, 0))
        self.max_log_messages_var = tk.StringVar(value=str(self.config.get('max_log_messages', 100)))
        max_log_messages_entry = ttk.Entry(font_frame, textvariable=self.max_log_messages_var, width=10)
        max_log_messages_entry.pack(anchor="w")
        
        ttk.Label(font_frame, text="フォントファミリー:").pack(anchor="w", pady=(5, 0))
        self.font_family_var = tk.StringVar(value=self.config.get('font_family', 'Consolas'))
        
        try:
            self.font_families = sorted(tkfont.families())
        except Exception:
            self.font_families = ['Consolas', 'Arial', 'Courier New', 'Times New Roman']
        
        search_frame = ttk.Frame(font_frame)
        search_frame.pack(fill="x", pady=(5, 0))
        self.font_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.font_search_var)
        search_entry.pack(fill="x")
        search_entry.bind("<KeyRelease>", self.update_font_combobox)
        
        self.font_combo = ttk.Combobox(
            font_frame, 
            textvariable=self.font_family_var,
            values=self.font_families,
            state="readonly",
            width=30
        )
        self.font_combo.pack(anchor="w")
        
        self.show_timestamp_var = tk.BooleanVar(value=self.config.get('show_timestamp', True))
        ttk.Checkbutton(font_frame, text="タイムスタンプを表示", variable=self.show_timestamp_var).pack(anchor="w", pady=(5, 0))
        
        self.show_chat_type_var = tk.BooleanVar(value=self.config.get('show_chat_type', True))
        ttk.Checkbutton(font_frame, text="チャットタイプを表示", variable=self.show_chat_type_var).pack(anchor="w")
        
        update_frame = ttk.LabelFrame(general_tab, text="アップデート設定")
        update_frame.pack(fill="x", padx=10, pady=5)
        
        self.check_updates_var = tk.BooleanVar(value=self.config.get('check_for_updates', True))
        ttk.Checkbutton(update_frame, text="起動時にアップデートを確認", variable=self.check_updates_var).pack(anchor="w")
        
        chat_frame = ttk.LabelFrame(general_tab, text="チャット設定")
        chat_frame.pack(fill="x", padx=10, pady=5)
        
        header_frame = ttk.Frame(chat_frame)
        header_frame.pack(fill="x")
        ttk.Label(header_frame, text="タイプ", width=14).pack(side="left", padx=5)
        ttk.Label(header_frame, text="表示", width=4).pack(side="left", padx=5)
        ttk.Label(header_frame, text="読み", width=8).pack(side="left", padx=5)
        ttk.Label(header_frame, text="色", width=20).pack(side="left", padx=5)
        ttk.Label(header_frame, text="デフォルトに戻す", width=15).pack(side="left", padx=5)
        
        self.chat_filter_vars = {}
        self.chat_tts_filter_vars = {}
        self.chat_color_vars = {}
        self.chat_color_labels = {}
        
        chat_types = ['グローバル', 'パーティー', 'トレード', 'ウィスパー', 'ギルド']
        
        for chat_type in chat_types:
            row_frame = ttk.Frame(chat_frame)
            row_frame.pack(fill="x", pady=2)
            
            ttk.Label(row_frame, text=chat_type, width=15).pack(side="left", padx=5)
            
            filter_var = tk.BooleanVar(value=self.config['chat_filter'].get(chat_type, True))
            self.chat_filter_vars[chat_type] = filter_var
            ttk.Checkbutton(row_frame, variable=filter_var).pack(side="left", padx=5)
            
            tts_var = tk.BooleanVar(value=self.config['chat_tts_filter'].get(chat_type, True))
            self.chat_tts_filter_vars[chat_type] = tts_var
            ttk.Checkbutton(row_frame, variable=tts_var).pack(side="left", padx=5)
            
            color = self.config['chat_colors'].get(chat_type, self.default_chat_colors[chat_type])
            color_var = tk.StringVar(value=color)
            self.chat_color_vars[chat_type] = color_var
            
            color_button = ttk.Button(row_frame, text="選択", command=lambda ct=chat_type: self.choose_color(ct))
            color_button.pack(side="left", padx=5)
            
            color_label = ttk.Label(row_frame, text=color, background=color, width=10)
            color_label.pack(side="left", padx=5)
            self.chat_color_labels[chat_type] = color_label
            
            def update_color_label(*args, ct=chat_type):
                color = self.chat_color_vars[ct].get()
                self.chat_color_labels[ct].config(text=color, background=color)
            
            color_var.trace("w", update_color_label)
            
            reset_button = ttk.Button(row_frame, text="リセット", command=lambda ct=chat_type: self.reset_color(ct))
            reset_button.pack(side="left", padx=5)
        
        ng_tab = self.create_scrollable_tab(notebook, "NG設定")
        
        ng_filter_frame = ttk.LabelFrame(ng_tab, text="NGワードフィルター設定")
        ng_filter_frame.pack(fill="x", padx=10, pady=5)
        
        self.ng_word_display_filter_var = tk.BooleanVar(value=self.config.get('ng_word_display_filter', False))
        ttk.Checkbutton(ng_filter_frame, text="NGワード表示フィルターを有効化", 
                       variable=self.ng_word_display_filter_var).pack(anchor="w")
        
        self.ng_word_tts_filter_var = tk.BooleanVar(value=self.config.get('ng_word_tts_filter', False))
        ttk.Checkbutton(ng_filter_frame, text="NGワード読み上げフィルターを有効化", 
                       variable=self.ng_word_tts_filter_var).pack(anchor="w")
        
        spam_filter_frame = ttk.LabelFrame(ng_tab, text="スペーススパムフィルター設定")
        spam_filter_frame.pack(fill="x", padx=10, pady=5)
        
        self.spam_space_filter_var = tk.BooleanVar(value=self.config.get('spam_space_filter', False))
        ttk.Checkbutton(spam_filter_frame, text="スペーススパムフィルターを有効化", 
                       variable=self.spam_space_filter_var).pack(anchor="w")
        
        ttk.Label(spam_filter_frame, text="スペース数の閾値:").pack(anchor="w", pady=(5, 0))
        self.spam_space_threshold_var = tk.IntVar(value=self.config.get('spam_space_threshold', 10))
        threshold_frame = ttk.Frame(spam_filter_frame)
        threshold_frame.pack(fill="x")
        ttk.Spinbox(threshold_frame, from_=5, to=50, textvariable=self.spam_space_threshold_var, width=10).pack(side="left")
        ttk.Label(threshold_frame, text="文字以上のスペースを含むメッセージをフィルター").pack(side="left", padx=(5, 0))
        
        ttk.Label(ng_tab, text="　※ON=フィルターをON(表示しない)　OFF=フィルターをOFF(表示する)").pack(anchor=tk.W, pady=5)
        
        ng_list_frame = ttk.LabelFrame(ng_tab, text="NGワードリスト")
        ng_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ('word', 'display', 'tts')
        self.settings_ng_words_tree = ttk.Treeview(ng_list_frame, columns=columns, show='headings', height=10)
        
        self.settings_ng_words_tree.heading('word', text='NGワード')
        self.settings_ng_words_tree.heading('display', text='表示')
        self.settings_ng_words_tree.heading('tts', text='読み上げ')
        
        self.settings_ng_words_tree.column('word', width=300)
        self.settings_ng_words_tree.column('display', width=80, anchor='center')
        self.settings_ng_words_tree.column('tts', width=80, anchor='center')
        
        scrollbar = ttk.Scrollbar(ng_list_frame, orient=tk.VERTICAL, command=self.settings_ng_words_tree.yview, style='Vertical.TScrollbar')
        self.settings_ng_words_tree.configure(yscrollcommand=scrollbar.set)
        
        self.settings_ng_words_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.settings_ng_tree_context_menu = tk.Menu(self.settings_ng_words_tree, tearoff=0)
        self.configure_menu_style(self.settings_ng_tree_context_menu)
        self.settings_ng_tree_context_menu.add_command(label="削除", command=self.remove_ng_word_from_settings_tree)
        self.settings_ng_words_tree.bind("<Button-3>", self.show_settings_ng_tree_context_menu)
        
        self.refresh_settings_ng_words_list()
        
        self.settings_ng_words_tree.bind('<ButtonRelease-1>', self.on_settings_ng_word_click)
        
        button_frame = ttk.Frame(ng_tab)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        add_frame = ttk.Frame(button_frame)
        add_frame.pack(fill="x", pady=5)
        
        self.settings_new_ng_word_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.settings_new_ng_word_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(add_frame, text="追加", command=self.add_ng_word_from_settings).pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="選択項目を削除", command=self.remove_ng_word_from_settings).pack(pady=5)
        
        tts_tab = self.create_scrollable_tab(notebook, "読み上げ")
        
        tts_frame = ttk.LabelFrame(tts_tab, text="読み上げ設定")
        tts_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(tts_frame, text="読み上げエンジン:").pack(anchor="w")
        self.tts_engine_var = tk.StringVar(value=self.config['tts_engine'])
        engine_frame = ttk.Frame(tts_frame)
        engine_frame.pack(fill="x")
        ttk.Radiobutton(engine_frame, text="pyttsx3（システム標準）", variable=self.tts_engine_var, value="pyttsx3").pack(side="left")
        ttk.Radiobutton(engine_frame, text="VOICEVOX", variable=self.tts_engine_var, value="voicevox").pack(side="left", padx=(10, 0))
        
        voicevox_frame = ttk.LabelFrame(tts_frame, text="VOICEVOX設定")
        voicevox_frame.pack(fill="x", pady=(10, 0))
        
        self.auto_start_voicevox_var = tk.BooleanVar(value=self.config.get('auto_start_voicevox', False))
        ttk.Checkbutton(voicevox_frame, text="起動時にVOICEVOXを自動起動", variable=self.auto_start_voicevox_var).pack(anchor="w")
        
        ttk.Label(voicevox_frame, text="VOICEVOX実行ファイルパス:").pack(anchor="w", pady=(5, 0))
        self.voicevox_path_var = tk.StringVar(value=self.config.get('voicevox_path', ''))
        path_frame = ttk.Frame(voicevox_frame)
        path_frame.pack(fill="x")
        ttk.Entry(path_frame, textvariable=self.voicevox_path_var, width=50).pack(side="left", fill="x", expand=True)
        ttk.Button(path_frame, text="参照", command=self.browse_voicevox_path).pack(side="right", padx=(5, 0))
        
        ttk.Label(voicevox_frame, text="サーバーURL:").pack(anchor="w")
        self.voicevox_url_var = tk.StringVar(value=self.config['voicevox_url'])
        ttk.Entry(voicevox_frame, textvariable=self.voicevox_url_var, width=40).pack(anchor="w")
        
        current_character = self.config.get('voicevox_character', 'ずんだもん')
        current_style = self.config.get('voicevox_style', 'ノーマル')

        ttk.Label(voicevox_frame, text="キャラクター:").pack(anchor="w", pady=(5, 0))
        self.voicevox_character_var = tk.StringVar(value=current_character)
        character_combo = ttk.Combobox(voicevox_frame, textvariable=self.voicevox_character_var, values=list(self.voicevox_speakers.keys()), state="readonly")
        character_combo.pack(anchor="w")

        ttk.Label(voicevox_frame, text="スタイル:").pack(anchor="w", pady=(5, 0))
        self.voicevox_style_var = tk.StringVar(value=current_style)
        style_combo = ttk.Combobox(voicevox_frame, textvariable=self.voicevox_style_var, state="readonly")
        style_combo.pack(anchor="w")

        def update_style_combo(*args):
            selected_char = self.voicevox_character_var.get()
            styles = list(self.voicevox_speakers.get(selected_char, {}).keys())
            style_combo['values'] = styles
            if styles:
                self.voicevox_style_var.set(styles[0])

        self.voicevox_character_var.trace("w", update_style_combo)
        update_style_combo()
        if current_style in self.voicevox_speakers.get(current_character, {}):
            self.voicevox_style_var.set(current_style)

        ttk.Button(voicevox_frame, text="接続テスト", command=self.test_voicevox).pack(anchor="w", pady=(5, 0))
        ttk.Button(voicevox_frame, text="テスト音声再生", command=self.test_voicevox_speech).pack(anchor="w", pady=(5, 0))
        
        ttk.Label(voicevox_frame, text="VOICEVOX 読み上げ速度 (0.5-2.0):").pack(anchor="w", pady=(10, 0))
        self.voicevox_speed_scale_var = tk.DoubleVar(value=self.config['voicevox_speed_scale'])
        speed_frame = ttk.Frame(voicevox_frame)
        speed_frame.pack(fill="x")
        speed_label = ttk.Label(speed_frame, text=f"{self.voicevox_speed_scale_var.get():.2f}")
        speed_label.pack(side="left", padx=(10, 0))
        def update_speed_label(*args):
            speed_label.config(text=f"{self.voicevox_speed_scale_var.get():.2f}")
            self.settings_window.update()
        ttk.Scale(speed_frame, from_=0.5, to=2.0, orient="horizontal", variable=self.voicevox_speed_scale_var, 
                  length=250, command=lambda x: update_speed_label()).pack(side="left")
        self.voicevox_speed_scale_var.trace("w", update_speed_label)
        
        ttk.Label(voicevox_frame, text="VOICEVOX 音量 (0.01-2.0):").pack(anchor="w", pady=(10, 0))
        self.voicevox_volume_scale_var = tk.DoubleVar(value=max(0.01, self.config['voicevox_volume_scale']))
        volume_frame = ttk.Frame(voicevox_frame)
        volume_frame.pack(fill="x")
        voicevox_volume_label = ttk.Label(volume_frame, text=f"{self.voicevox_volume_scale_var.get():.2f}")
        voicevox_volume_label.pack(side="left", padx=(10, 0))
        def update_voicevox_volume_label(*args):
            voicevox_volume_label.config(text=f"{self.voicevox_volume_scale_var.get():.2f}")
            self.settings_window.update()
        ttk.Scale(volume_frame, from_=0.01, to=2.0, orient="horizontal", variable=self.voicevox_volume_scale_var, 
                  length=250, command=lambda x: update_voicevox_volume_label()).pack(side="left")
        self.voicevox_volume_scale_var.trace("w", update_voicevox_volume_label)
        
        ttk.Label(tts_frame, text="読み上げモード:").pack(anchor="w", pady=(10, 0))
        self.tts_mode_var = tk.StringVar(value=self.config['tts_mode'])
        mode_frame = ttk.Frame(tts_frame)
        mode_frame.pack(fill="x")
        ttk.Radiobutton(mode_frame, text="そのまま読み上げる", variable=self.tts_mode_var, value="queue").pack(side="left")
        ttk.Radiobutton(mode_frame, text="スキップする", variable=self.tts_mode_var, value="skip").pack(side="left", padx=(10, 0))
        
        ttk.Label(tts_frame, text="pyttsx3 読み上げ速度 (50-300):").pack(anchor="w", pady=(10, 0))
        self.tts_rate_var = tk.IntVar(value=self.config['tts_rate'])
        rate_frame = ttk.Frame(tts_frame)
        rate_frame.pack(fill="x")
        rate_label = ttk.Label(rate_frame, text=f"{self.tts_rate_var.get()}")
        rate_label.pack(side="left", padx=(10, 0))
        def update_rate_label(*args):
            rate_label.config(text=f"{self.tts_rate_var.get()}")
            self.settings_window.update()
        ttk.Scale(rate_frame, from_=50, to=300, orient="horizontal", variable=self.tts_rate_var, 
                  length=250, command=lambda x: update_rate_label()).pack(side="left")
        self.tts_rate_var.trace("w", update_rate_label)
        
        ttk.Label(tts_frame, text="pyttsx3 音量 (0.0-1.0):").pack(anchor="w", pady=(10, 0))
        self.tts_volume_var = tk.DoubleVar(value=self.config['tts_volume'])
        volume_frame = ttk.Frame(tts_frame)
        volume_frame.pack(fill="x")
        pyttsx_volume_label = ttk.Label(volume_frame, text=f"{self.tts_volume_var.get():.1f}")
        pyttsx_volume_label.pack(side="left", padx=(10, 0))
        def update_pyttsx_volume_label(*args):
            pyttsx_volume_label.config(text=f"{self.tts_volume_var.get():.1f}")
            self.settings_window.update()
        ttk.Scale(volume_frame, from_=0.0, to=1.0, orient="horizontal", variable=self.tts_volume_var, 
                  length=250, command=lambda x: update_pyttsx_volume_label()).pack(side="left")
        self.tts_volume_var.trace("w", update_pyttsx_volume_label)
        
        translation_tab = self.create_scrollable_tab(notebook, "翻訳")
        
        translation_frame = ttk.LabelFrame(translation_tab, text="翻訳設定")
        translation_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(translation_frame, text="翻訳サービス:").pack(anchor="w")
        self.translation_service_var = tk.StringVar(value=self.config.get('translation_service', 'google'))
        service_frame = ttk.Frame(translation_frame)
        service_frame.pack(fill="x")
        ttk.Radiobutton(service_frame, text="Google翻訳", variable=self.translation_service_var, value="google").pack(side="left")
        ttk.Radiobutton(service_frame, text="Google Cloud Translation", variable=self.translation_service_var, value="google_cloud").pack(side="left", padx=(10, 0))
        ttk.Radiobutton(service_frame, text="DeepL翻訳", variable=self.translation_service_var, value="deepl").pack(side="left", padx=(10, 0))
        
        ttk.Label(translation_frame, text="ソース言語:").pack(anchor="w", pady=(5, 0))
        self.source_language_var = tk.StringVar(value=self.config.get('source_language', 'auto'))
        lang_combo = ttk.Combobox(
            translation_frame, 
            textvariable=self.source_language_var, 
            values=['auto', 'en', 'ja', 'ko', 'zh', 'es', 'fr', 'de', 'ru'],
            state="readonly",
            width=10
        )
        lang_combo.pack(anchor="w")
        
        ttk.Label(translation_frame, text="翻訳先言語:").pack(anchor="w", pady=(5, 0))
        self.target_language_var = tk.StringVar(value=self.config.get('target_language', 'en'))
        lang_frame = ttk.Frame(translation_frame)
        lang_frame.pack(fill="x")
        ttk.Combobox(lang_frame, textvariable=self.target_language_var, values=[
            'en', 'ja', 'ko', 'zh', 'es', 'fr', 'de', 'ru', 'pt'
        ], width=10).pack(side="left")
        ttk.Label(lang_frame, text="(例: en=英語, ja=日本語, ko=韓国語)").pack(side="left", padx=(5, 0))
        
        ttk.Label(translation_frame, text="DeepL APIキー:").pack(anchor="w", pady=(5, 0))
        self.deepl_api_key_var = tk.StringVar(value=self.config.get('deepl_api_key', ''))
        ttk.Entry(translation_frame, textvariable=self.deepl_api_key_var, show="*", width=50).pack(anchor="w")
        
        ttk.Label(translation_frame, text="Google Cloud APIキー:").pack(anchor="w", pady=(5, 0))
        self.google_cloud_api_key_var = tk.StringVar(value=self.config.get('google_cloud_api_key', ''))
        ttk.Entry(translation_frame, textvariable=self.google_cloud_api_key_var, show="*", width=50).pack(anchor="w")
        
        self.show_translation_buttons_var = tk.BooleanVar(value=self.config.get('show_translation_buttons', True))
        ttk.Checkbutton(
            translation_frame, 
            text="メッセージ横に翻訳ボタンを表示",
            variable=self.show_translation_buttons_var
        ).pack(anchor="w", pady=(5, 0))
        
        Webhook_tab = self.create_scrollable_tab(notebook, "Webhook")
        
        Webhook_frame = ttk.LabelFrame(Webhook_tab, text="Webhook設定")
        Webhook_frame.pack(fill="x", padx=10, pady=5)
        
        self.enable_Webhook_var = tk.BooleanVar(value=self.config.get('enable_Webhook', False))
        ttk.Checkbutton(Webhook_frame, text="Webhookを有効化", variable=self.enable_Webhook_var).pack(anchor="w")
        
        ttk.Label(Webhook_frame, text="Webhook URL:").pack(anchor="w", pady=(5, 0))
        self.Webhook_webhook_url_var = tk.StringVar(value=self.config.get('Webhook_webhook_url', ''))
        ttk.Entry(Webhook_frame, textvariable=self.Webhook_webhook_url_var, width=50).pack(anchor="w")
        
        ttk.Label(Webhook_frame, text="メッセージフォーマット:").pack(anchor="w", pady=(5, 0))
        self.Webhook_message_format_var = tk.StringVar(
            value=self.config.get('Webhook_message_format', '[{timestamp}] [{type}] {username}: {message}'))
        format_entry = ttk.Entry(Webhook_frame, textvariable=self.Webhook_message_format_var, width=50)
        format_entry.pack(anchor="w")
        ttk.Label(Webhook_frame, text="使用可能な変数: {timestamp}, {type}, {username}, {message}").pack(anchor="w")
        
        button_frame = ttk.Frame(self.settings_window, style='Surface.TFrame', padding=(12, 10))
        button_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        ttk.Button(button_frame, text="キャンセル", command=self.settings_window.destroy).pack(side="right")
        ttk.Button(button_frame, text="保存", command=self.save_settings).pack(side="right", padx=(0, 10))
        self.settings_window.bind("<Control-s>", lambda event: self.save_settings())
        self.schedule_title_bar_style(self.settings_window)
        self.settings_window.deiconify()
        self.settings_window.lift()
        self.settings_window.focus_force()
    
    def show_settings_ng_tree_context_menu(self, event):
        item = self.settings_ng_words_tree.identify_row(event.y)
        if item:
            self.settings_ng_words_tree.selection_set(item)
            self.settings_ng_tree_context_menu.post(event.x_root, event.y_root)
    
    def remove_ng_word_from_settings_tree(self):
        self.remove_ng_word_from_settings()
    
    def refresh_settings_ng_words_list(self):
        for item in self.settings_ng_words_tree.get_children():
            self.settings_ng_words_tree.delete(item)
        
        for ng_word in self.config['ng_words']:
            self.settings_ng_words_tree.insert('', 'end', values=(
                ng_word['word'], 
                'ON' if ng_word['display'] else 'OFF', 
                'ON' if ng_word['tts'] else 'OFF'
            ))
    
    def on_settings_ng_word_click(self, event):
        item = self.settings_ng_words_tree.selection()
        if item:
            column = self.settings_ng_words_tree.identify_column(event.x)
            if column == '#2':
                self.toggle_settings_ng_word_display(item[0])
            elif column == '#3':
                self.toggle_settings_ng_word_tts(item[0])
    
    def toggle_settings_ng_word_display(self, item_id):
        item = self.settings_ng_words_tree.item(item_id)
        values = item['values']
        word = values[0]
        
        for ng_word in self.config['ng_words']:
            if ng_word['word'] == word:
                ng_word['display'] = not ng_word['display']
                self.settings_ng_words_tree.set(item_id, 'display', 'ON' if ng_word['display'] else 'OFF')
                self.save_config()
                break
    
    def toggle_settings_ng_word_tts(self, item_id):
        item = self.settings_ng_words_tree.item(item_id)
        values = item['values']
        word = values[0]
        
        for ng_word in self.config['ng_words']:
            if ng_word['word'] == word:
                ng_word['tts'] = not ng_word['tts']
                self.settings_ng_words_tree.set(item_id, 'tts', 'ON' if ng_word['tts'] else 'OFF')
                self.save_config()
                break
    
    def add_ng_word_from_settings(self):
        new_word = self.settings_new_ng_word_var.get().strip()
        if new_word and not any(ng['word'] == new_word for ng in self.config['ng_words']):
            self.config['ng_words'].append({'word': new_word, 'display': True, 'tts': True})
            self.settings_ng_words_tree.insert('', 'end', values=(new_word, 'ON', 'ON'))
            self.settings_new_ng_word_var.set("")
            self.save_config()
            
            if self.ng_words_window and self.ng_words_window.winfo_exists():
                self.refresh_ng_words_list()
    
    def remove_ng_word_from_settings(self):
        selection = self.settings_ng_words_tree.selection()
        if selection:
            item = self.settings_ng_words_tree.item(selection[0])
            word = item['values'][0]
            self.settings_ng_words_tree.delete(selection[0])
            self.config['ng_words'] = [ng for ng in self.config['ng_words'] if ng['word'] != word]
            self.save_config()
            
            if self.ng_words_window and self.ng_words_window.winfo_exists():
                self.refresh_ng_words_list()

    def update_font_combobox(self, event=None):
        search_term = self.font_search_var.get().lower()
        filtered_fonts = [font for font in self.font_families if search_term in font.lower()]
        self.font_combo['values'] = filtered_fonts
        if filtered_fonts:
            self.font_combo.current(0)
    
    def choose_color(self, chat_type):
        color = colorchooser.askcolor(title="色を選択", initialcolor=self.chat_color_vars[chat_type].get())
        if color[1]:
            self.chat_color_vars[chat_type].set(color[1])
    
    def reset_color(self, chat_type):
        default_color = self.default_chat_colors.get(chat_type, '#FFFFFF')
        self.chat_color_vars[chat_type].set(default_color)
    
    def browse_voicevox_path(self):
        file_path = filedialog.askopenfilename(title="VOICEVOX実行ファイルを選択", filetypes=[("実行ファイル", "*.exe"), ("すべてのファイル", "*.*")])
        if file_path:
            self.voicevox_path_var.set(file_path)
    
    def close_settings_window(self):
        if self.settings_window:
            geometry = self.settings_window.geometry()
            match = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', geometry)
            if match:
                w, h, x, y = map(int, match.groups())
                self.config['settings_window_settings'] = {'width': w, 'height': h, 'x': x, 'y': y}
                self.save_config()
            self.settings_window.destroy()
            self.settings_window = None
    
    def test_voicevox(self):
        try:
            url = self.voicevox_url_var.get()
            response = requests.get(f"{url}/speakers", timeout=3)
            if response.status_code == 200:
                messagebox.showinfo("接続テスト", "VOICEVOXサーバーに接続できました！")
            else:
                messagebox.showerror("接続テスト", f"サーバーエラー: {response.status_code}")
        except Exception as e:
            messagebox.showerror("接続テスト", f"VOICEVOXサーバーに接続できません。\nサーバーが起動しているか確認してください。\nエラー: {e}")
    
    def test_voicevox_speech(self):
        test_text = "これはテスト音声です。"
        
        original_config = {
            'voicevox_character': self.config['voicevox_character'],
            'voicevox_style': self.config['voicevox_style'],
            'voicevox_speed_scale': self.config['voicevox_speed_scale'],
            'voicevox_volume_scale': self.config['voicevox_volume_scale'],
            'voicevox_url': self.config['voicevox_url']
        }
        
        self.config['voicevox_character'] = self.voicevox_character_var.get()
        self.config['voicevox_style'] = self.voicevox_style_var.get()
        self.config['voicevox_speed_scale'] = self.voicevox_speed_scale_var.get()
        self.config['voicevox_volume_scale'] = self.voicevox_volume_scale_var.get()
        self.config['voicevox_url'] = self.voicevox_url_var.get()
        
        try:
            audio_data = self.synthesize_voicevox(test_text)
            if audio_data:
                self.play_voicevox_audio(audio_data)
            else:
                messagebox.showerror("テスト音声", "テスト音声の合成に失敗しました。")
        finally:
            self.config.update(original_config)

    
    def browse_log_file(self, path_var):
        file_path = filedialog.askopenfilename(title="PoEクライアントログファイルを選択", filetypes=[("ログファイル", '*.txt'), ("すべてのファイル", "*.*")])
        if file_path:
            path_var.set(file_path)
    
    def save_settings(self):
        self.config['log_file_path'] = self.log_path_var.get()
        self.config['log_file_path2'] = self.log_path2_var.get()
        self.config['tts_engine'] = self.tts_engine_var.get()
        self.config['voicevox_url'] = self.voicevox_url_var.get()
        self.config['voicevox_character'] = self.voicevox_character_var.get()
        self.config['voicevox_style'] = self.voicevox_style_var.get()
        self.config['tts_mode'] = self.tts_mode_var.get()
        self.config['tts_rate'] = self.tts_rate_var.get()
        self.config['tts_volume'] = self.tts_volume_var.get()
        self.config['voicevox_speed_scale'] = self.voicevox_speed_scale_var.get()
        self.config['voicevox_volume_scale'] = max(0.01, self.voicevox_volume_scale_var.get())
        self.config['translation_service'] = self.translation_service_var.get()
        self.config['target_language'] = self.target_language_var.get()
        self.config['source_language'] = self.source_language_var.get()
        self.config['deepl_api_key'] = self.deepl_api_key_var.get()
        self.config['google_cloud_api_key'] = self.google_cloud_api_key_var.get()
        self.config['show_translation_buttons'] = self.show_translation_buttons_var.get()
        self.config['auto_start_voicevox'] = self.auto_start_voicevox_var.get()
        self.config['voicevox_path'] = self.voicevox_path_var.get()
        self.config['enable_Webhook'] = self.enable_Webhook_var.get()
        self.config['Webhook_webhook_url'] = self.Webhook_webhook_url_var.get()
        self.config['Webhook_message_format'] = self.Webhook_message_format_var.get()
        self.config['font_family'] = self.font_family_var.get()
        self.config['check_for_updates'] = self.check_updates_var.get()
        self.config['ng_word_display_filter'] = self.ng_word_display_filter_var.get()
        self.config['ng_word_tts_filter'] = self.ng_word_tts_filter_var.get()
        self.config['spam_space_filter'] = self.spam_space_filter_var.get()
        self.config['spam_space_threshold'] = self.spam_space_threshold_var.get()
        
        for chat_type in self.chat_filter_vars:
            self.config['chat_filter'][chat_type] = self.chat_filter_vars[chat_type].get()
            self.config['chat_tts_filter'][chat_type] = self.chat_tts_filter_vars[chat_type].get()
            self.config['chat_colors'][chat_type] = self.chat_color_vars[chat_type].get()
        
        self.config['show_timestamp'] = self.show_timestamp_var.get()
        self.config['show_chat_type'] = self.show_chat_type_var.get()
        
        self.save_config()
        
        if self.tts_engine:
            self.tts_engine.setProperty('rate', self.config['tts_rate'])
            self.tts_engine.setProperty('volume', self.config['tts_volume'])
        
        try:
            self.config['font_size'] = int(self.font_size_var.get())
        except ValueError:
            messagebox.showerror("エラー", "フォントサイズは数値を入力してください")
            return

        try:
            self.config['max_log_messages'] = max(1, int(self.max_log_messages_var.get()))
        except ValueError:
            messagebox.showerror("エラー", "表示ログ上限は数値を入力してください")
            return

        self.font_size = self.config['font_size']
        self.font_family = self.config['font_family']
        self.max_log_messages = self.config['max_log_messages']
        self.chat_colors = self.config['chat_colors']
        self.chat_text.config(font=(self.font_family, self.font_size))
        
        self.source_language = self.config['source_language']
        self.update_menu_labels()
        
        self.update_chat_colors()
        self.trim_chat_entries()
        self.save_config()
        
        self.check_for_updates_on_startup = self.config['check_for_updates']
        
        messagebox.showinfo("保存完了", f"設定を保存しました。\nTTSエンジン: {self.config['tts_engine']}")
        self.settings_window.destroy()
        
        if self.config['log_file_path'] and os.path.exists(self.config['log_file_path']):
            if self.monitoring_enabled:
                self.start_monitoring()
    
    def is_voicevox_running(self):
        try:
            url = self.config['voicevox_url']
            response = requests.get(f"{url}/speakers", timeout=1)
            return response.status_code == 200
        except Exception:
            return False 
    
    def start_voicevox_if_needed(self):
        if not self.is_voicevox_running():
            voicevox_path = self.config['voicevox_path']
            if os.path.exists(voicevox_path):
                try:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                    
                    self.voicevox_process = subprocess.Popen(
                        [voicevox_path], 
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    for _ in range(30):
                        time.sleep(1)
                        if self.is_voicevox_running():
                            self.display_system_message("VOICEVOXを自動起動しました")
                            return
                except Exception as e:
                    pass
            else:
                pass
        else:
            self.voicevox_process = None
    
    def clear_chat(self):
        self.chat_text.delete(1.0, tk.END)
        self.message_ids.clear()
        self.message_entry_tags.clear()
        self.displayed_entries.clear()

    def register_chat_entry(self, start_index, end_index, message_id=None):
        entry_tag = f"entry_{uuid.uuid4().hex}"
        self.chat_text.tag_add(entry_tag, start_index, end_index)
        self.displayed_entries.append({'tag': entry_tag, 'message_id': message_id})
        if message_id:
            self.message_entry_tags[message_id] = entry_tag
        self.trim_chat_entries()
        return entry_tag

    def trim_chat_entries(self):
        limit = max(1, int(self.max_log_messages))
        while len(self.displayed_entries) > limit:
            entry = self.displayed_entries.pop(0)
            tag = entry['tag']
            message_id = entry.get('message_id')
            ranges = self.chat_text.tag_ranges(tag)
            if ranges:
                self.chat_text.delete(ranges[0], ranges[-1])
            self.chat_text.tag_delete(tag)
            if message_id:
                self.message_ids.pop(message_id, None)
                self.message_entry_tags.pop(message_id, None)
    
    def send_to_Webhook(self, chat_info):
        def send_thread():
            try:
                webhook_url = self.config['Webhook_webhook_url']
                format_str = self.config.get('Webhook_message_format', '[{timestamp}] [{type}] {username}: {message}')
                
                dt = datetime.strptime(chat_info['timestamp'], '%Y/%m/%d %H:%M:%S')
                timestamp_short = dt.strftime('%H:%M')
                
                message = format_str.format(
                    timestamp=timestamp_short,
                    type=chat_info['type'],
                    username=chat_info['username'],
                    message=chat_info['message']
                )
                
                data = {"content": message}
                response = requests.post(webhook_url, json=data)
                if response.status_code != 204:
                    pass
            except Exception as e:
                pass
        
        threading.Thread(target=send_thread, daemon=True).start()
    
    def speak_message(self, message):
        if self.config['tts_mode'] == 'skip':
            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                except queue.Empty:
                    pass
            self.tts_queue.put(message)
        else:
            self.tts_queue.put(message)
    
    def parse_chat_line(self, line):
        patterns = [
            r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \d+ \w+ $ INFO Client \d+ $ ([#%$@&])([^:]+): (.+)',
            r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}).*?$ INFO Client \d+ $ ([#%$@&])([^:]+): (.+)',
            r'.*?(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}).*?([#%$@&])([^:]+): (.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match and len(match.groups()) == 4:
                timestamp, prefix, username, message = match.groups()
                chat_type_map = {'#': 'グローバル', '%': 'パーティー', '$': 'トレード', '@': 'ウィスパー', '&': 'ギルド'}
                chat_type = chat_type_map.get(prefix, 'その他')
                return {'timestamp': timestamp, 'type': chat_type, 'username': username.strip(), 'message': message.strip()}
        return None
    
    def display_chat_message(self, chat_info):
        if not self.main_window:
            return
        self.main_window.after(0, self._display_message_thread_safe, chat_info)
    
    def display_system_message(self, message):
        if not self.main_window:
            return
        self.main_window.after(0, self._display_system_message_thread_safe, message)
    
    def _display_system_message_thread_safe(self, message):
        try:
            time_str = f"[{datetime.now().strftime('%H:%M')}] " if self.config.get('show_timestamp', True) else ""
            system_str = f"[システム] {message}\n"
            start_index = self.chat_text.index(tk.END)
            self.chat_text.insert(tk.END, time_str, 'その他')
            self.chat_text.insert(tk.END, system_str, 'その他')
            end_index = self.chat_text.index(tk.END)
            self.register_chat_entry(start_index, end_index)
            
            if self.auto_scroll_var.get() and self.chat_text.yview()[1] >= 0.9:
                self.chat_text.see(tk.END)
        except Exception as e:
            pass
    
    def _display_message_thread_safe(self, chat_info):
        try:
            current_font = (self.font_family, self.font_size)
            dt = datetime.strptime(chat_info['timestamp'], '%Y/%m/%d %H:%M:%S')
            time_str = f"[{dt.strftime('%H:%M')}] " if self.config.get('show_timestamp', True) else ""
            type_str = f"[{chat_info['type']}] " if self.config.get('show_chat_type', True) else ""
            user_str = f"{chat_info['username']}: "
            message_str = f"{chat_info['message']}"
            
            message_id = str(uuid.uuid4())
            self.message_ids[message_id] = chat_info['message']

            start_index = self.chat_text.index(tk.END)

            if self.config.get('show_translation_buttons', True):
                self.chat_text.insert(tk.END, "🔍 ", ('translation_button', message_id))

            self.chat_text.insert(tk.END, time_str, ('その他', current_font))
            self.chat_text.insert(tk.END, type_str, (chat_info['type'], current_font))
            self.chat_text.insert(tk.END, user_str, (chat_info['type'], current_font))
            self.chat_text.insert(tk.END, message_str, ('message', current_font))

            self.chat_text.insert(tk.END, "\n")

            end_index = self.chat_text.index(tk.END)

            self.chat_text.tag_add(message_id, start_index, end_index)
            self.register_chat_entry(start_index, end_index, message_id)

            self.chat_text.tag_bind(
                message_id, 
                '<Button-1>', 
                lambda e, mid=message_id: self.translate_message(mid)
            )
            self.chat_text.tag_configure('translation_button', foreground=self.palette['translation'], underline=True)
            self.chat_text.tag_bind(
                'translation_button', 
                '<Enter>', 
                lambda e: self.chat_text.config(cursor="hand2")
            )
            self.chat_text.tag_bind(
                'translation_button', 
                '<Leave>', 
                lambda e: self.chat_text.config(cursor="")
            )

            if self.auto_scroll_var.get() and self.chat_text.yview()[1] >= 0.9:
                self.chat_text.see(tk.END)
        except Exception as e:
            pass

    def translate_message(self, message_id):
        if message_id in self.message_ids:
            message = self.message_ids[message_id]
            self._display_translation(message_id, "翻訳中...")
            threading.Thread(target=self._translate_message_thread, args=(message, message_id), daemon=True).start()
        else:
            pass

    def _translate_message_thread(self, message, message_id):
        try:
            service = self.config.get('translation_service', 'google')
            source_lang = self.config.get('source_language', 'auto')
            target_lang = self.config.get('target_language', 'en')
            
            translated = ""
            
            if service == 'google':
                try:
                    from deep_translator import GoogleTranslator
                    translated = GoogleTranslator(source=source_lang, target=target_lang).translate(message)
                except ImportError:
                    translated = "翻訳エラー: Google翻訳に必要な deep-translator が未インストールです。pip install -r requirements.txt を実行してください。"
                except Exception as e:
                    translated = f"翻訳エラー: {str(e)}"
            
            elif service == 'google_cloud':
                api_key = self.config.get('google_cloud_api_key', '')
                if not api_key:
                    translated = "Google Cloud APIキーが設定されていません"
                else:
                    try:
                        url = f"https://translation.googleapis.com/language/translate/v2?key={api_key}"
                        headers = {"Content-Type": "application/json"}
                        data = {
                            "q": message,
                            "target": target_lang
                        }
                        if source_lang != 'auto':
                            data["source"] = source_lang
                        response = requests.post(url, headers=headers, json=data, timeout=10)
                        if response.status_code == 200:
                            result = response.json()
                            translated = result['data']['translations'][0]['translatedText']
                        else:
                            translated = f"Google Cloudエラー: {response.status_code} - {response.text}"
                    except Exception as e:
                        translated = f"Google Cloud接続エラー: {str(e)}"
            
            elif service == 'deepl':
                api_key = self.config.get('deepl_api_key', '')
                if not api_key:
                    translated = "DeepL APIキーが設定されていません"
                else:
                    try:
                        url = 'https://api-free.deepl.com/v2/translate'
                        params = {
                            'auth_key': api_key,
                            'text': message,
                            'target_lang': target_lang.upper()
                        }
                        if source_lang != 'auto':
                            params['source_lang'] = source_lang.upper()
                        response = requests.post(url, data=params, timeout=10)
                        if response.status_code == 200:
                            result = response.json()
                            translated = result['translations'][0]['text']
                        else:
                            translated = f"DeepLエラー: {response.status_code} - {response.text}"
                    except Exception as e:
                        translated = f"DeepL接続エラー: {str(e)}"
            
            self.main_window.after(0, self._display_translation, message_id, translated)
            
        except Exception as e:
            error_msg = f"翻訳処理エラー: {str(e)}"
            self.main_window.after(0, self._display_translation, message_id, error_msg)

    def _display_translation(self, message_id, translation):
        try:
            if self.chat_text.tag_ranges(message_id):
                result_tag = f"translation_{message_id}"
                ranges = self.chat_text.tag_ranges(result_tag)
                for start, end in zip(ranges[0::2], ranges[1::2]):
                    self.chat_text.delete(start, end)

                entry_tag = self.message_entry_tags.get(message_id)
                tag_end = self.chat_text.tag_ranges(message_id)[1]
                end_index = self.chat_text.index(f"{tag_end} lineend +1c")
                tags = ('translation_result', result_tag, entry_tag) if entry_tag else ('translation_result', result_tag)
                self.chat_text.insert(end_index, f"[翻訳] {translation}\n", tags)
                
                if self.auto_scroll_var.get() and self.chat_text.yview()[1] >= 0.9:
                    self.chat_text.see(tk.END)
        except Exception as e:
            pass

    def synthesize_voicevox(self, text):
        try:
            speed_scale = float(self.config['voicevox_speed_scale'])
            volume_scale = float(max(0.01, self.config['voicevox_volume_scale']))
            
            speaker_id = self.voicevox_speakers.get(self.config['voicevox_character'], {}).get(self.config['voicevox_style'], 3)
            
            query_params = {
                "text": text,
                "speaker": speaker_id,
                "speedScale": speed_scale,
                "volumeScale": volume_scale
            }
            
            query_response = requests.post(
                f"{self.config['voicevox_url']}/audio_query",
                params=query_params,
                timeout=10
            )
            if query_response.status_code != 200:
                return None
            
            query_data = query_response.json()
            query_data['speedScale'] = speed_scale
            query_data['volumeScale'] = volume_scale
            
            synthesis_response = requests.post(
                f"{self.config['voicevox_url']}/synthesis",
                headers={"Content-Type": "application/json"},
                params={"speaker": speaker_id},
                json=query_data,
                timeout=30
            )
            if synthesis_response.status_code == 200:
                audio_data = synthesis_response.content
                pygame.mixer.music.set_volume(min(volume_scale / 2.0, 1.0))
                return audio_data
            else:
                return None
        except Exception as e:
            return None
    
    def play_voicevox_audio(self, audio_data):
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        
        except Exception as e:
            pass
        
        finally:
            if temp_path:
                for attempt in range(5):
                    try:
                        pygame.mixer.music.unload()
                        os.unlink(temp_path)
                        break
                    except PermissionError:
                        time.sleep(0.2)
                    except Exception as e:
                        break
    
    def start_tts_thread(self):
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
    
    def _tts_worker(self):
        while True:
            try:
                message = self.tts_queue.get()
                if message is None:
                    break
                
                if self.config['tts_engine'] == 'voicevox':
                    audio_data = self.synthesize_voicevox(message)
                    if audio_data:
                        self.play_voicevox_audio(audio_data)
                    else:
                        if self.tts_engine:
                            self.tts_engine.say(message)
                            self.tts_engine.runAndWait()
                else:
                    if self.tts_engine:
                        self.tts_engine.say(message)
                        self.tts_engine.runAndWait()
            except Exception as e:
                pass
    
    def close_main_window(self):
        geometry = self.main_window.geometry()
        match = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', geometry)
        if match:
            w, h, x, y = map(int, match.groups())
            self.config['window_settings'] = {'width': w, 'height': h, 'x': x, 'y': y}
            self.save_config()
        
        self.stop_monitoring.set()
        for thread in self.monitoring_threads.values():
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
        
        if self.tts_queue:
            self.tts_queue.put(None)
        
        if self.voicevox_process:
            try:
                self.voicevox_process.terminate()
                self.voicevox_process.wait(timeout=5)
            except Exception as e:
                pass
        
        temp_dir = tempfile.gettempdir()
        for file in os.listdir(temp_dir):
            if file.endswith('.wav'):
                try:
                    os.unlink(os.path.join(temp_dir, file))
                except Exception:
                    pass
        
        self.main_window.quit()
        self.main_window.destroy()
    
    def check_for_updates(self, silent=False):
        try:
            update_url = "https://raw.githubusercontent.com/ochi3/PoEChatTool/main/update.json"
            
            with urllib.request.urlopen(update_url, timeout=5) as response:
                update_info = json.loads(response.read().decode())
                
                if update_info['version'] > self.version:
                    update_message = f"新しいバージョン {update_info['version']} が利用可能です。"
                    
                    if silent:
                        self.display_system_message_with_url(update_message, "https://github.com/ochi3/PoEChatTool/releases")
                    else:
                        result = messagebox.askyesnocancel(
                            "アップデートの確認",
                            f"{update_message}\n\nリリースページを開きますか？\n「はい」でページを開く、「いいえ」で閉じる"
                        )
                        if result:
                            webbrowser.open("https://github.com/ochi3/PoEChatTool/releases")
                elif not silent:
                    messagebox.showinfo("アップデート", "お使いのバージョンは最新です")
        except Exception as e:
            if not silent:
                messagebox.showerror("アップデートエラー", f"アップデートの確認に失敗しました:\n{str(e)}")
    
    def display_system_message_with_url(self, message, url):
        if not self.main_window:
            return
        self.main_window.after(0, self._display_system_message_with_url_thread_safe, message, url)
    
    def _display_system_message_with_url_thread_safe(self, message, url):
        try:
            time_str = f"[{datetime.now().strftime('%H:%M')}] " if self.config.get('show_timestamp', True) else ""
            system_str = f"[システム] {message} "
            url_str = "ダウンロードページを開く\n"
            
            start_index = self.chat_text.index(tk.END)
            self.chat_text.insert(tk.END, time_str, 'その他')
            self.chat_text.insert(tk.END, system_str, 'その他')
            
            url_start = self.chat_text.index(tk.END)
            self.chat_text.insert(tk.END, url_str, 'update_url')
            end_index = self.chat_text.index(tk.END)
            self.register_chat_entry(start_index, end_index)
            
            if self.auto_scroll_var.get() and self.chat_text.yview()[1] >= 0.9:
                self.chat_text.see(tk.END)
        except Exception as e:
            pass
    
    def show_version_info(self):
        messagebox.showinfo(
            "バージョン情報",
            f"PoE Chat Tool\nバージョン: {self.version}\n\n"
            "© 2025 ochi3"
        )
    
    def run(self):
        if self.check_for_updates_on_startup:
            threading.Thread(target=self.check_for_updates, args=(True,), daemon=True).start()
        
        self.main_window.mainloop()

if __name__ == "__main__":
    try:
        import pyttsx3
        import requests
        import pygame
        import deep_translator
    except ImportError as e:
        print(f"必要なライブラリがインストールされていません: {e}")
        print("以下のコマンドでインストールしてください:")
        print("pip install -r requirements.txt")
        exit(1)
    app = PoEChatTool()
    app.run()
