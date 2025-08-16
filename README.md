# ぽえちゃっと (PoEChatTool)

**ぽえちゃっと** は、Path of Exile 1 (PoE1) のクライアントログを監視して、  
リアルタイムで **チャットの表示・音声読み上げ・翻訳** を行うツールです。

---

## 主な機能
- **音声読み上げ**
  - VOICEVOX：「ずんだもん」「四国めたん」などのキャラクター音声
  - pyttsx3：Windows標準の音声エンジン

- **翻訳機能**
  - Google翻訳（無料・API不要）
  - DeepL（APIキー必須・高精度・月50万文字無料）
  - Google Cloud Translation（APIキー必須・多言語対応）
  - 🔍 ワンクリック翻訳対応

- **外部連携**
  - WebhookでDiscordにチャットを転送可能
  - PoBなどURLを簡単コピー

⚠️ **ローカルチャットは読み込み対象外です**

---

## インストール方法

### 必要環境
- Windows 10 / 11

### ダウンロード & 実行
1. [GitHub Releases](https://github.com/ochi3/PoEChatTool/releases) から最新版をダウンロード
2. `ぽえちゃっと.exe` を実行  
   ※ ウイルス警告が出る場合は許可してください  
   ※ 起動できない場合は、`ぽえちゃっと.exe` を右クリック → プロパティ → 「許可する」を押してください

- 自動アップデート機能はありますが基本はReleasesから再ダウンロード推奨  
- 設定ファイルは `C:\Users\ユーザー名\AppData\Roaming\PoEChatTool` に保存されるため、再インストールしても設定は維持されます

---

## 使い方

### 初期設定
#### 1. ログファイルの設定
- メニューバー → 「ファイル」→「設定」
- 「ログファイル」→「参照」ボタンから以下を指定  

スタンドアロン版: `C:/Program Files (x86)/Grinding Gear Games/Path of Exile/logs/Client.txt`  
Steam版 : `C:/Program Files (x86)/Steam/steamapps/common/Path of Exile/logs/Client.txt`

#### 2. 音声設定（VOICEVOX利用）
1. [VOICEVOX公式サイト](https://voicevox.hiroshiba.jp/) からZIPをダウンロード  
2. ツールの設定で「読み上げエンジン」を「VOICEVOX」に変更  
3. キャラクター・スタイルを選択  
4. `VOICEVOX/vv-engine/run.exe` を起動  
   - ぽえちゃっとと同時に起動したい場合はファイルパスを設定してください  

---

### 基本操作（メニューバー）
- **監視 [ON/OFF]**：ログ監視の開始/停止  
- **読み上げ [ON/OFF]**：音声読み上げの有効/無効  
- **スクロール [ON/OFF]**：自動スクロールの有効/無効  
- **翻訳元選択**：翻訳元言語を指定（日本語混在時の検出失敗対策）  
- **🔍 ボタン**：ワンクリック翻訳  

---

### 翻訳サービスの使い分け
- **Google翻訳**：無料 / API不要 /使えなくなる可能性あり  
- **DeepL**：精度高い / APIキー必須 / 月50万文字無料  
- **Google Cloud Translation**：APIキー必須 / 多言語対応  

---

### フィルタリング機能
チャットタイプごとに以下を設定可能：
- 表示するかどうか  
- 読み上げするかどうか  
- 表示色の変更  

---

### Webhook（Discord連携）
1. Discordサーバー → チャンネル設定 → **連携** → **Webhookを作成**  
2. Webhook URLをコピー  
3. ツールの「設定」→「Webhook」タブでURLを設定  
4. メッセージフォーマットをカスタマイズ可能  
