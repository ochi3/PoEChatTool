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

# アイコン設定用のWindows API
myappid = 'poechattool'

class PoEChatTool:
    def __init__(self):
        # バージョン情報
        self.version = "1.0.1"
        # 設定ファイルのパスを設定
        if getattr(sys, 'frozen', False):
            # EXEが実行されている場合
            script_dir = os.path.dirname(sys.executable)
            # AppData/Roamingディレクトリを使用
            appdata_dir = os.getenv('APPDATA')
            if appdata_dir:
                config_dir = os.path.join(appdata_dir, "PoEChatTool")
                os.makedirs(config_dir, exist_ok=True)
                self.config_file = os.path.join(config_dir, "poe_chat_config.json")
            else:
                self.config_file = os.path.join(script_dir, "poe_chat_config.json")
        else:
            # スクリプトが実行されている場合
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_file = os.path.join(script_dir, "poe_chat_config.json")
        
        print(f"設定ファイルパス: {self.config_file}")  # デバッグ用
        self.config = self.load_config()
        self.tts_engine = None
        self.main_window = None
        self.settings_window = None
        self.last_file_position = 0
        self.tts_queue = queue.Queue()
        self.tts_thread = None
        self.font_size = self.config.get('font_size', 10)
        self.font_family = self.config.get('font_family', 'Consolas')
        self.message_ids = {}
        
        # 監視状態管理
        self.monitoring_enabled = self.config.get('monitoring_enabled', True)
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        
        # アップデート設定
        self.check_for_updates_on_startup = self.config.get('check_for_updates', True)
        
        # 翻訳設定
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
        
        self.init_tts()
        self.init_pygame()
        self.create_main_window()
        self.start_tts_thread()
        
        # Windowsのタスクバーアイコン設定
        if os.name == 'nt':
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except AttributeError:
                pass  # 古いWindowsバージョンではスキップ
    
        # VOICEVOX自動起動
        if self.config.get('auto_start_voicevox', False) and self.config.get('voicevox_path', ''):
            self.start_voicevox_if_needed()
    
    def load_config(self):
        default_config = {
            'log_file_path': '',
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
            'check_for_updates': True
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    for chat_type in default_config['chat_colors']:
                        if chat_type not in config['chat_colors']:
                            config['chat_colors'][chat_type] = default_config['chat_colors'][chat_type]
                    return config
            except Exception as e:
                print(f"設定ファイル読み込みエラー: {e}")
                messagebox.showerror("設定エラー", f"設定ファイルの読み込みに失敗しました:\n{e}")
        
        # 設定ファイルがない場合はデフォルト設定を保存
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        return default_config
    
    def save_config(self):
        self.config['auto_scroll'] = self.auto_scroll_var.get()
        self.config['enable_tts'] = self.tts_enabled_var.get()
        self.config['monitoring_enabled'] = self.monitoring_enabled
        self.config['check_for_updates'] = self.check_for_updates_on_startup
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
            messagebox.showerror("保存エラー", f"設定の保存に失敗しました:\n{e}")
    
    def init_pygame(self):
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"pygame初期化エラー: {e}")
            messagebox.showerror("初期化エラー", f"pygameの初期化に失敗しました:\n{e}")
    
    def init_tts(self):
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', self.config['tts_rate'])
            self.tts_engine.setProperty('volume', self.config['tts_volume'])
        except Exception as e:
            print(f"TTS初期化エラー: {e}")
            messagebox.showerror("TTSエラー", "TTSの初期化に失敗しました。TTS機能は無効になります。")
            self.config['enable_tts'] = False
    
    def create_main_window(self):
        self.main_window = tk.Tk()
        self.main_window.title(f"ぽえちゃっと v{self.version}")
        
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
            else:
                icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
            self.main_window.iconbitmap(icon_path)
        except Exception as e:
            print(f"アイコン読み込みエラー: {e}")
        
        self.auto_scroll_var = tk.BooleanVar(value=self.config.get('auto_scroll', True))
        self.tts_enabled_var = tk.BooleanVar(value=self.config.get('enable_tts', True))
        
        w_settings = self.config['window_settings']
        self.main_window.geometry(f"{w_settings['width']}x{w_settings['height']}+{w_settings['x']}+{w_settings['y']}")
        self.main_window.protocol("WM_DELETE_WINDOW", self.close_main_window)
        
        menubar = tk.Menu(self.main_window)
        self.main_window.config(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="設定", command=self.open_settings)
        file_menu.add_command(label="チャットクリア", command=self.clear_chat)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.close_main_window)
                
        # 監視メニュー
        self.monitoring_menu_index = menubar.index("end") + 1
        menubar.add_command(label="監視 [ON]", command=self.toggle_monitoring)
        
        # 翻訳メニュー
        self.languages = [
            ('自動検出', 'auto'), ('英語', 'en'), ('日本語', 'ja'),
            ('韓国語', 'ko'), ('中国語', 'zh'), ('スペイン語', 'es'),
            ('フランス語', 'fr'), ('ドイツ語', 'de'), ('ロシア語', 'ru')
        ]
        self.translation_menu_index = None

        menubar.add_command(label="翻訳元 ▼", command=self.show_translation_popup)
        self.translation_menu_index = menubar.index('end')

        # TTSメニュー
        self.tts_menu_index = menubar.index('end') + 1
        menubar.add_command(label="読み上げ [ON]", command=self.toggle_tts)
        
        # スクロールメニュー
        self.scroll_menu_index = menubar.index('end') + 1
        menubar.add_command(label="スクロール [ON]", command=self.toggle_auto_scroll)
        
        # ヘルプメニュー (追加)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="アップデートを確認", command=lambda: self.check_for_updates(silent=False))
        help_menu.add_command(label="バージョン情報", command=self.show_version_info)
        
        self.menubar = menubar
        self.update_menu_labels()
        
        status_frame = ttk.Frame(self.main_window)
        status_frame.pack(fill="x", padx=5, pady=2)
        
        # ステータスバー
        self.status_var = tk.StringVar(value="監視: 実行中" if self.monitoring_enabled else "監視: 停止中")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side="left", padx=5)
        
        # バージョン表示 (追加)
        version_label = ttk.Label(status_frame, text=f"バージョン: {self.version}")
        version_label.pack(side="right", padx=5)
        
        chat_frame = ttk.Frame(self.main_window)
        chat_frame.pack(fill="both", expand=True, padx=5, pady=2)
        
        self.chat_text = tk.Text(
            chat_frame, 
            bg='black', 
            fg='white', 
            font=(self.font_family, self.font_size),
            wrap=tk.WORD
        )
        scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.chat_text.config(yscrollcommand=scrollbar.set)
        self.chat_text.pack(side="left", fill="both", expand=True)
        
        self.update_chat_colors()
        
        self.chat_text.tag_config('translation_button', foreground='#00BFFF', underline=True)
        self.chat_text.tag_config('translation_result', foreground='#00FF00')
            
        # ログファイルがある場合、監視を開始
        if self.config['log_file_path'] and os.path.exists(self.config['log_file_path']) and self.monitoring_enabled:
            self.start_monitoring()
    
    def toggle_monitoring(self):
        self.monitoring_enabled = not self.monitoring_enabled
        
        if self.monitoring_enabled:
            self.start_monitoring()
            self.status_var.set("監視: 実行中")
            self.display_system_message("監視を開始しました")
        else:
            self.stop_monitoring.set()
            self.status_var.set("監視: 停止中")
            self.display_system_message("監視を停止しました")
        
        self.update_menu_labels()
        self.save_config()
    
    def start_monitoring(self):
        """監視を開始する"""
        if not self.monitoring_enabled:
            return
            
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
            
        try:
            with open(self.config['log_file_path'], 'r', encoding='utf-8') as f:
                f.seek(0, 2)
                self.last_file_position = f.tell()
            
            self.stop_monitoring.clear()
            self.monitoring_thread = threading.Thread(target=self.monitor_log_file, daemon=True)
            self.monitoring_thread.start()
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
            self.display_system_message(f"監視開始エラー: {e}")
    
    def update_chat_colors(self):
        for chat_type, color in self.chat_colors.items():
            self.chat_text.tag_config(chat_type, foreground=color)
    
    def update_menu_labels(self):
        if self.menubar:
            try:
                # 監視状態更新
                monitoring_status = "ON" if self.monitoring_enabled else "OFF"
                self.menubar.entryconfig(self.monitoring_menu_index, label=f"監視 [{monitoring_status}]")
                
                # TTS状態更新
                tts_status = "ON" if self.tts_enabled_var.get() else "OFF"
                self.menubar.entryconfig(self.tts_menu_index, label=f"読み上げ [{tts_status}]")
                
                # スクロール状態更新
                scroll_status = "ON" if self.auto_scroll_var.get() else "OFF"
                self.menubar.entryconfig(self.scroll_menu_index, label=f"スクロール [{scroll_status}]")
                
                # ソース言語表示更新
                if self.menubar and self.translation_menu_index is not None:
                    lang_name = next((name for name, code in self.languages if code == self.source_language), self.source_language)
                    self.menubar.entryconfig(self.translation_menu_index, label=f"翻訳: {lang_name} ▼")
            except Exception as e:
                print(f"メニュー更新エラー: {e}")

    def cycle_source_language(self):
        """ソース言語を順番に切り替える"""
        codes = [code for _, code in self.languages]
        try:
            idx = codes.index(self.source_language)
            next_idx = (idx + 1) % len(codes)
        except ValueError:
            next_idx = 0
        self.source_language = codes[next_idx]
        self.config['source_language'] = self.source_language
        self.save_config()
        self.update_menu_labels()
        self.display_system_message(f"ソース言語を {self.source_language} に設定しました")
    
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
        self.settings_window.title("設定")
        
        sw_settings = self.config.get('settings_window_settings', {'width': 600, 'height': 800, 'x': 200, 'y': 200})
        self.settings_window.geometry(f"{sw_settings['width']}x{sw_settings['height']}+{sw_settings['x']}+{sw_settings['y']}")
        
        self.settings_window.transient(self.main_window)
        self.settings_window.grab_set()
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings_window)
        
        notebook = ttk.Notebook(self.settings_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 一般タブ
        general_tab = ttk.Frame(notebook)
        notebook.add(general_tab, text="一般")
        
        log_frame = ttk.LabelFrame(general_tab, text="ログファイル設定")
        log_frame.pack(fill="x", padx=10, pady=5)
        self.log_path_var = tk.StringVar(value=self.config['log_file_path'])
        ttk.Label(log_frame, text="ログファイル:").pack(anchor="w")
        path_frame = ttk.Frame(log_frame)
        path_frame.pack(fill="x", pady=2)
        ttk.Entry(path_frame, textvariable=self.log_path_var, width=60).pack(side="left", fill="x", expand=True)
        ttk.Button(path_frame, text="参照", command=self.browse_log_file).pack(side="right", padx=(5, 0))
        
        font_frame = ttk.LabelFrame(general_tab, text="表示設定")
        font_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(font_frame, text="フォントサイズ:").pack(anchor="w")
        self.font_size_var = tk.StringVar(value=str(self.config['font_size']))
        font_size_entry = ttk.Entry(font_frame, textvariable=self.font_size_var, width=10)
        font_size_entry.pack(anchor="w")
        
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
        
        # アップデート設定を追加
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
        
        # 読み上げタブ
        tts_tab = ttk.Frame(notebook)
        notebook.add(tts_tab, text="読み上げ")
        
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
        
        # キャラクターとスタイルの選択
        self.voicevox_speakers = {
            'ずんだもん': {'ノーマル': 3, 'あまあま': 1, 'ツンツン': 7, 'セクシー': 5, 'ささやき': 22, 'ヒソヒソ': 38, 'ヘロヘロ': 75, 'なみだめ': 76},
            '四国めたん': {'ノーマル': 2, 'あまあま': 0, 'ツンツン': 6, 'セクシー': 4, 'ささやき': 36, 'ヒソヒソ': 37},
            '春日部つむぎ': {'ノーマル': 8},
            '中国うさぎ': {'ノーマル': 61, 'おどろき': 62, 'こわがり': 63, 'へろへろ': 64},
            '雨晴はう': {'ノーマル': 10},
            '冥鳴ひまり': {'ノーマル': 14},
            '東北ずん子': {'ノーマル': 107},
            '東北きりたん': {'ノーマル': 108},
            '東北イタコ': {'ノーマル': 109},
            '栗田まろん': {'ノーマル': 67},
            '波音リツ': {'ノーマル': 9, 'クイーン': 65},
            '玄野武宏': {'ノーマル': 11, '喜び': 39, 'ツンギレ': 40, '悲しみ': 41},
            '白上虎太郎': {'ふつう': 12, 'わーい': 32, 'びくびく': 33, 'おこ': 34, 'びえーん': 35},
            '青山龍星': {'ノーマル': 13, '熱血': 81, '不機嫌': 82, '喜び': 83, 'しっとり': 84, 'かなしみ': 85, '囁き': 86},
            '九州そら': {'ノーマル': 16, 'あまあま': 15, 'ツンツン': 18, 'セクシー': 17, 'ささやき': 19},
            'もち子さん': {'ノーマル': 20, 'セクシー／あん子': 66, '泣き': 77, '怒り': 78, '喜び': 79, 'のんびり': 80},
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
            '満別花丸': {'ノーマル': 69, '元気': 70, 'ささやき': 71, 'ぶりっ子': 72, 'ボーイ': 73},
            '琴詠ニア': {'ノーマル': 74},
            'Voidoll': {'ノーマル': 89},
            'ぞん子': {'ノーマル': 90, '低血圧': 91, '覚醒': 92, '実況風': 93},
            '中部つるぎ': {'ノーマル': 94, '怒り': 95, 'ヒソヒソ': 96, 'おどおど': 97, '絶望と敗北': 98},
            '離途': {'ノーマル': 99, 'シリアス': 101},
            '黒沢冴白': {'ノーマル': 100},
            'ユーレイちゃん': {'ノーマル': 102, '甘々': 103, '哀しみ': 104, 'ささやき': 105, 'ツクモちゃん': 106}
        }
        
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
        update_style_combo()  # 初期更新
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
        
        # 翻訳タブ
        translation_tab = ttk.Frame(notebook)
        notebook.add(translation_tab, text="翻訳")
        
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
        
        # Webhook タブ
        Webhook_tab = ttk.Frame(notebook)
        notebook.add(Webhook_tab, text="Webhook")
        
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
        
        # 保存とキャンセルボタン
        button_frame = ttk.Frame(self.settings_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(button_frame, text="保存", command=self.save_settings).pack(side="left")
        ttk.Button(button_frame, text="キャンセル", command=self.settings_window.destroy).pack(side="left", padx=(10, 0))
    
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
        
        # 現在の設定で直接合成
        character = self.voicevox_character_var.get()
        style = self.voicevox_style_var.get()
        speed = self.voicevox_speed_scale_var.get()
        volume = self.voicevox_volume_scale_var.get()
        url = self.voicevox_url_var.get()
        
        # 一時的に設定を保存
        original_config = {
            'voicevox_character': self.config['voicevox_character'],
            'voicevox_style': self.config['voicevox_style'],
            'voicevox_speed_scale': self.config['voicevox_speed_scale'],
            'voicevox_volume_scale': self.config['voicevox_volume_scale'],
            'voicevox_url': self.config['voicevox_url']
        }
        
        # 現在の設定で上書き
        self.config['voicevox_character'] = character
        self.config['voicevox_style'] = style
        self.config['voicevox_speed_scale'] = speed
        self.config['voicevox_volume_scale'] = volume
        self.config['voicevox_url'] = url
        
        try:
            audio_data = self.synthesize_voicevox(test_text)
            if audio_data:
                self.play_voicevox_audio(audio_data)
            else:
                messagebox.showerror("テスト音声", "テスト音声の合成に失敗しました。")
        finally:
            # 元の設定に戻す
            self.config.update(original_config)

    
    def browse_log_file(self):
        file_path = filedialog.askopenfilename(title="PoEクライアントログファイルを選択", filetypes=[("ログファイル", "*.txt"), ("すべてのファイル", "*.*")])
        if file_path:
            self.log_path_var.set(file_path)
    
    def save_settings(self):
        self.config['log_file_path'] = self.log_path_var.get()
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

        self.font_size = self.config['font_size']
        self.font_family = self.config['font_family']
        self.chat_text.config(font=(self.font_family, self.font_size))
        
        self.source_language = self.config['source_language']
        self.update_menu_labels()
        
        self.update_chat_colors()
        
        self.check_for_updates_on_startup = self.config['check_for_updates']
        
        messagebox.showinfo("保存完了", f"設定を保存しました。\nTTSエンジン: {self.config['tts_engine']}")
        self.settings_window.destroy()
        
        # 監視設定が変更された場合の処理
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
                    self.voicevox_process = subprocess.Popen([voicevox_path])
                    for _ in range(30):
                        time.sleep(1)
                        if self.is_voicevox_running():
                            print("VOICEVOXを自動起動しました")
                            self.display_system_message("VOICEVOXを自動起動しました")
                            return
                    print("VOICEVOXの起動に失敗しました（タイムアウト）")
                except Exception as e:
                    print(f"VOICEVOX起動エラー: {e}")
            else:
                print("VOICEVOXパスが無効です")
        else:
            print("VOICEVOXは既に起動しています")
            self.voicevox_process = None
    
    def clear_chat(self):
        self.chat_text.delete(1.0, tk.END)
        self.message_ids.clear()
    
    def monitor_log_file(self):
        while not self.stop_monitoring.is_set():
            try:
                with open(self.config['log_file_path'], 'r', encoding='utf-8') as f:
                    f.seek(self.last_file_position)
                    new_lines = f.readlines()
                    self.last_file_position = f.tell()
                    for line in new_lines:
                        line = line.strip()
                        if line:
                            self.process_log_line(line)
            except Exception as e:
                print(f"ログ監視エラー: {e}")
            time.sleep(0.5)
    
    def process_log_line(self, line):
        chat_info = self.parse_chat_line(line)
        if chat_info:
            chat_type = chat_info['type']
            if self.config['chat_filter'].get(chat_type, True):
                self.display_chat_message(chat_info)
                if self.tts_enabled_var.get() and self.config['chat_tts_filter'].get(chat_type, True):
                    self.speak_message(chat_info['message'])
                if self.config.get('enable_Webhook', False) and self.config.get('Webhook_webhook_url', ''):
                    self.send_to_Webhook(chat_info)
    
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
                    print(f"Webhook送信エラー: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Webhook送信エラー: {e}")
        
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
            r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \d+ \w+ $$ INFO Client \d+ $$ ([#%$@&])([^:]+): (.+)',
            r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}).*?$$ INFO Client \d+ $$ ([#%$@&])([^:]+): (.+)',
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
            self.chat_text.insert(tk.END, time_str, 'その他')
            self.chat_text.insert(tk.END, system_str, 'その他')
            
            if self.auto_scroll_var.get() and self.chat_text.yview()[1] >= 0.9:
                self.chat_text.see(tk.END)
        except Exception as e:
            print(f"システムメッセージ表示エラー: {e}")
    
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

            self.chat_text.tag_add(message_id, start_index, f"{end_index}-1c")

            self.chat_text.tag_bind(
                message_id, 
                '<Button-1>', 
                lambda e, mid=message_id: self.translate_message(mid)
            )
            self.chat_text.tag_configure('translation_button', foreground='#00BFFF', underline=True)
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
            print(f"メッセージ表示エラー: {e}")

    def translate_message(self, message_id):
        if message_id in self.message_ids:
            message = self.message_ids[message_id]
            threading.Thread(target=self._translate_message_thread, args=(message, message_id), daemon=True).start()
        else:
            print(f"メッセージIDが見つかりません: {message_id}")

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
                tag_end = self.chat_text.tag_ranges(message_id)[1]
                end_index = self.chat_text.index(f"{tag_end} lineend +1c")
                
                self.chat_text.insert(end_index, f"[翻訳] {translation}\n", 'translation_result')
                
                if self.auto_scroll_var.get() and self.chat_text.yview()[1] >= 0.9:
                    self.chat_text.see(tk.END)
        except Exception as e:
            print(f"翻訳結果表示エラー: {e}")

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
                print(f"VOICEVOX audio_queryエラー: ステータスコード {query_response.status_code}")
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
                print(f"VOICEVOX synthesisエラー: ステータスコード {synthesis_response.status_code}")
                return None
        except Exception as e:
            print(f"VOICEVOX合成エラー: {e}")
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
            print(f"VOICEVOX再生エラー: {e}")
        
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
                        print(f"一時ファイル削除エラー: {e}")
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
                print(f"TTSエラー: {e}")
    
    def close_main_window(self):
        geometry = self.main_window.geometry()
        match = re.match(r'(\d+)x(\d+)\+(\d+)\+(\d+)', geometry)
        if match:
            w, h, x, y = map(int, match.groups())
            self.config['window_settings'] = {'width': w, 'height': h, 'x': x, 'y': y}
            self.save_config()
        
        # 監視を停止
        self.stop_monitoring.set()
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)
        
        # TTSを停止
        if self.tts_queue:
            self.tts_queue.put(None)
        
        # VOICEVOXを停止
        if self.voicevox_process:
            try:
                self.voicevox_process.terminate()
                self.voicevox_process.wait(timeout=5)
            except Exception as e:
                print(f"VOICEVOX終了エラー: {e}")
        
        # 一時ファイルクリーンアップ
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
        """アップデートを確認する"""
        try:
            # アップデート情報を取得するURL
            update_url = "https://raw.githubusercontent.com/ochi3/PoEChatTool/main/update.json"
            
            with urllib.request.urlopen(update_url, timeout=5) as response:
                update_info = json.loads(response.read().decode())
                
                if update_info['version'] > self.version:
                    if silent:
                        # サイレントモードでは通知のみ
                        self.display_system_message(f"新しいバージョン {update_info['version']} が利用可能です")
                    else:
                        # アップデート確認ダイアログ
                        if messagebox.askyesno(
                            "アップデートの確認",
                            f"新しいバージョン {update_info['version']} が利用可能です。\n今すぐアップデートしますか？"
                        ):
                            self.download_and_install_update(update_info)
                elif not silent:
                    messagebox.showinfo("アップデート", "お使いのバージョンは最新です")
        except Exception as e:
            if not silent:
                messagebox.showerror("アップデートエラー", f"アップデートの確認に失敗しました:\n{str(e)}")
    
    def download_and_install_update(self, update_info):
        """アップデートをダウンロードしてインストールする"""
        try:
            # ダウンロードURL
            download_url = update_info['download_url']
            
            # 一時ファイルパス
            temp_dir = tempfile.gettempdir()
            temp_exe = os.path.join(temp_dir, "PoEChatTool_Update.exe")
            
            # ファイルをダウンロード
            with urllib.request.urlopen(download_url) as response, open(temp_exe, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
            # アップデートスクリプトを作成
            current_exe = sys.argv[0]
            batch_script = f"""
            @echo off
            TIMEOUT /T 3 /NOBREAK
            TASKKILL /F /IM "{os.path.basename(current_exe)}"
            MOVE /Y "{temp_exe}" "{current_exe}"
            START "" "{current_exe}"
            DEL "%~f0"
            """
            
            batch_path = os.path.join(temp_dir, "update_script.bat")
            with open(batch_path, 'w') as f:
                f.write(batch_script)
            
            # アップデートスクリプトを実行
            subprocess.Popen([batch_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.close_main_window()
            
        except Exception as e:
            messagebox.showerror("アップデートエラー", f"アップデートのダウンロードに失敗しました:\n{str(e)}")
    
    def show_version_info(self):
        """バージョン情報を表示"""
        messagebox.showinfo(
            "バージョン情報",
            f"PoE Chat Tool\nバージョン: {self.version}\n\n"
            "© 2025 ochi3"
        )
    
    def run(self):
        # 起動時にアップデートを確認
        if self.check_for_updates_on_startup:
            threading.Thread(target=self.check_for_updates, args=(True,), daemon=True).start()
        
        self.main_window.mainloop()

    def show_translation_popup(self):
        """翻訳メニューをポップアップ表示し、言語選択できるようにする"""
        popup = tk.Menu(self.main_window, tearoff=0)
        for name, code in self.languages:
            popup.add_radiobutton(
                label=name,
                value=code,
                variable=tk.StringVar(value=self.source_language),
                command=lambda c=code: self.set_source_language(c)
            )
        # マウスカーソルの位置に表示
        x = self.main_window.winfo_pointerx()
        y = self.main_window.winfo_rooty() + 30
        popup.tk_popup(x, y)

    def set_source_language(self, code):
        self.source_language = code
        self.config['source_language'] = code
        self.save_config()
        self.update_menu_labels()
        self.display_system_message(f"ソース言語を {code} に設定しました")

if __name__ == "__main__":
    try:
        import pyttsx3
        import requests
        import pygame
    except ImportError as e:
        print(f"必要なライブラリがインストールされていません: {e}")
        print("以下のコマンドでインストールしてください:")
        print("pip install pyttsx3 requests pygame")
        exit(1)
    app = PoEChatTool()
    app.run()