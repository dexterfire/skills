# 🌐 Universal VK Wall Poster Skill

> **Универсальный, кроссплатформенный навык и CLI-инструмент для публикации новостей, дайджестов и медиа-постов в любые сообщества и на стены ВКонтакте из любой ОС (Windows, Linux, macOS), любого браузера (Chrome, Yandex, Vivaldi, Firefox, Safari, Edge) и любого AI-агента.**

---

## 📌 Оглавление
1. [Преимущества и возможности](#-преимущества-и-возможности)
2. [Быстрый старт (CLI)](#-быстрый-старт-cli)
3. [Установка в любые CLI-агенты](#-установка-в-любые-cli-агенты)
4. [Использование в Python коде](#-использование-в-python-коде)
5. [Полный справочник аргументов CLI](#-полный-справочник-аргументов-cli)

---

## 🚀 Преимущества и возможности

- 🌍 **Любая ОС**: Нативная работа на Windows, Linux и macOS.
- 🎯 **Любой целевой паблик**: Понимает короткие имена (`glfire_streamer`), числовые ID (`137821447`), полные ссылки (`https://vk.ru/glfire_streamer`) или личные страницы.
- 🌐 **Любой браузер / сессия**: Авто-определение Chrome, Yandex Browser, Vivaldi, Firefox, Safari, Edge, Brave, Opera с работой через CDP порт (`9223`).
- 🔑 **Два режима авторизации**:
  1. *Браузерная сессия (CDP)* — запросы через `fetch` в контексте VK, обход ошибки `error 5:1130 (IP mismatch)`.
  2. *Прямой токен API* (`--token`, `VK_COMMUNITY_TOKEN`) — для серверов.
- 📸 **Медиа-поддержка**: Загрузка до 10 изображений в одном посте (`--photo pic1.jpg pic2.png`).
- ⏰ **Умное расписание**: Указание точного unix timestamp (`--publish-date`) или удобных относительных интервалов (`--delay 1h`, `--delay 30m`, `--delay 24h`).
- 🔄 **Auto-Recovery**: Автоматическое обновление протухшего токена браузера без ручного вмешательства.

---

## ⚡ Быстрый старт (CLI)

```bash
# 1. Установка зависимостей
pip install websocket-client requests pillow

# 2. Проверить доступность группы и права администратора
python scripts/vk_wall_poster.py --check --target glfire_streamer

# 3. Опубликовать новость
python scripts/vk_wall_poster.py --target glfire_streamer --text "🎮 Важная новость в паблике!"

# 4. Опубликовать с картинкой и отложенным таймером на 1 час
python scripts/vk_wall_poster.py --target glfire_streamer --file news.txt --photo cover.jpg --delay 1h
```

---

## 🤖 Установка в любые CLI-агенты

### 1. Hermes Agent
```powershell
Expand-Archive -Path "vk-wall-poster-universal.zip" -DestinationPath "$env:LOCALAPPDATA\hermes\skills\vk-wall-poster-universal" -Force
```

### 2. Claude Code
```bash
mkdir -p .claude/skills
unzip -o vk-wall-poster-universal.zip -d .claude/skills/
```

### 3. OpenCode / Antigravity
```powershell
Copy-Item -Path ".\vk-wall-poster-universal" -Destination "$env:USERPROFILE\.gemini\antigravity\skills\vk-wall-poster-universal" -Recurse -Force
```

---

## ⚙️ Справка по аргументам CLI

```text
usage: vk_wall_poster.py [-h] [--check] [--setup] [--target TARGET]
                         [--text TEXT] [--file FILE] [--photo PHOTO [PHOTO ...]]
                         [--publish-date PUBLISH_DATE] [--delay DELAY]
                         [--as-user] [--token TOKEN] [--port PORT]
                         [--user-data-dir USER_DATA_DIR]
                         [--browser-path BROWSER_PATH]
```
