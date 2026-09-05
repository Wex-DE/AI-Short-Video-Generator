# WexAuto - AI Short Video Generator 🎬⚡

**WexAuto** is an automated AI-powered video creation studio. Simply provide a **topic** or **script**, and WexAuto will automatically generate scripts, match stock footage or AI clips, synthesize voiceovers (TTS), generate animated subtitles, add background music, and render high-definition videos ready for YouTube Shorts, TikTok, and Instagram Reels.

---

## ✨ Features

- 🤖 **AI Script & Keyword Generation**: Integrated with OpenAI, Anthropic Claude, Google Gemini, DeepSeek, Kimi, and custom LLM providers.
- 🎥 **Smart Material Matching**: Automatically searches and downloads high-quality footage from Pexels, Pixabay, Coverr, or AI Video Generators.
- 🎙️ **Natural AI Voiceover (TTS)**: Microsoft Azure Edge TTS (Free, 100+ languages and natural voices), ElevenLabs, SiliconFlow, and more.
- 💬 **Dynamic Animated Subtitles**: Word-by-word animated subtitles with spring pop-up effects and customizable fonts, colors, and positioning.
- 🎵 **Background Music Integration**: Built-in royalty-free presets or custom uploaded background music.
- 🔒 **Device-Locked License (DRM) System**: Manage client access via a remote `userverify.txt` database on GitHub.

---

## 🚀 Quick Start (Portable)

### Windows
1. Clone or download the repository.
2. Double-click **`WexAuto_Run.bat`** or run:
   ```bash
   .\webui.bat
   ```
3. Open your browser at **`http://127.0.0.1:8501`**.

---

## 🛡️ Device Authentication Setup (`userverify.txt`)

To authorize users or your own devices, add the client's **Device Code** to `userverify.txt` in your repository:

```text
# WexAuto User Verification Database
# Format: <Device_Code>, <Duration_Or_Expiry>, <Status>

# Example:
0xA3558CAEB1, 365d, verified
0x1234567890, 30d, verified
0x3216478900, 60d, ban
```

- **`verified`**: Activates the license for the specified duration (e.g. `30d`, `365d`, `lifetime`, or `YYYY-MM-DD`).
- **`ban`**: Immediately revokes access for the device.

---

## 📄 License
Released under the MIT License.
