# Jarvis Voice

**Офлайн-диктовка для Claude Code и любого текстового поля.** Скажи «Джарвис», продиктуй мысль голосом, скажи «конец» — текст появится в активном окне. Без облачного распознавания, API-ключей и подписок.

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platforms](https://img.shields.io/badge/macOS%20%C2%B7%20Windows%20%C2%B7%20Linux-supported-success)
![Vosk](https://img.shields.io/badge/Vosk-offline-orange)
![License](https://img.shields.io/badge/license-MIT-green)

## Зачем

Проект помогает диктовать промты и обычный текст, не переключаясь между мыслью и клавиатурой. Jarvis работает в фоне: после вставки он не завершается, а снова ждёт wake word.

## Возможности

- **Офлайн-распознавание русской речи** через [Vosk](https://github.com/alphacep/vosk-api).
- **Непрерывная работа:** один запуск — сколько угодно команд и вставок.
- **Голосовое приветствие** на macOS, Windows и Linux.
- **Вставка в активное окно** через `Cmd+V` или `Ctrl+V`.
- **Паузы без таймаута:** запись заканчивается только командой «конец».
- **Приватность:** после установки аудио и текст не покидают компьютер.
- **Тесты без микрофона:** состояние команд, вставка и приветствие проверяются отдельно.

## Голосовые команды

| Команда | Действие |
| --- | --- |
| **«Джарвис»** | Озвучить приветствие и начать запись |
| **«конец»** | Вставить распознанный текст и снова ждать «Джарвис» |
| **«пока Джарвис»** | Полностью остановить приложение |
| **Ctrl+C** | Остановить приложение из терминала |

По умолчанию приветствие: **«Здравствуйте, Сын Пелея»**.

## Требования

- Python 3.10+; рекомендуется Python 3.12.
- Микрофон.
- Интернет во время установки для зависимостей и русской модели.
- Разрешение на микрофон и эмуляцию вставки в активное окно.

## Быстрый старт

### macOS

```sh
git clone https://github.com/memph11s/jarvis-voice.git jarvis-voice
cd jarvis-voice
./setup.sh
./run.sh
```

Если `python3` ссылается на старую версию:

```sh
PYTHON=/opt/homebrew/opt/python@3.12/bin/python3 ./setup.sh
```

В `System Settings → Privacy & Security` выдай терминалу или VS Code:

- **Microphone** — для записи речи;
- **Accessibility** — для эмуляции `Cmd+V`.

Если Jarvis запущен из Terminal или iTerm, Accessibility нужен **именно Terminal/iTerm**, а не только VS Code. После изменения разрешений перезапусти терминал и Jarvis.

### Windows

В PowerShell:

```powershell
git clone https://github.com/memph11s/jarvis-voice.git jarvis-voice
cd jarvis-voice
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
.\run.ps1
```

Если Python запускается через Python Launcher:

```powershell
.\setup.ps1 -Python "py"
```

Включи доступ к микрофону для классических приложений в `Settings → Privacy & security → Microphone`. Вставка использует `System.Windows.Forms.SendKeys`.

### Linux

Debian/Ubuntu с X11:

```sh
sudo apt install python3 python3-venv libportaudio2 xclip xdotool pulseaudio-utils speech-dispatcher espeak
git clone https://github.com/memph11s/jarvis-voice.git jarvis-voice
cd jarvis-voice
./setup.sh
./run.sh
```

Для Wayland замени `xclip` и `xdotool` на `wl-clipboard` и `ydotool`:

```sh
sudo apt install python3 python3-venv libportaudio2 wl-clipboard ydotool pulseaudio-utils speech-dispatcher espeak
```

`ydotoold` должен быть запущен и доступен пользователю. При установленном `WAYLAND_DISPLAY` приложение использует `ydotool`, иначе — `xdotool`.

## Использование

1. Поставь курсор в поле ввода Claude Code или другого приложения.
2. Скажи **«Джарвис»** и дождись приветствия.
3. Диктуй текст сколько нужно; паузы запись не завершают.
4. Скажи **«конец»** — текст будет вставлен в активное окно.
5. Для следующей фразы повтори команды без перезапуска.

Jarvis не открывает и не переключает приложения. Перед командой «конец» нужное окно должно быть активным. Для вставки используется системный буфер обмена, поэтому его предыдущее содержимое заменяется.

## Приветствие и голос

- **macOS:** `say`, по умолчанию голос `Lesya`.
- **Windows:** `System.Speech`.
- **Linux:** `spd-say` или `espeak`; без синтезатора воспроизводится обычный сигнал.

Изменить текст:

```sh
JARVIS_GREETING="Здравствуйте, я слушаю" ./run.sh
```

Выбрать другую установленную голосовую на macOS:

```sh
JARVIS_VOICE="Milena" ./run.sh
```

Аудио, записанное во время приветствия, отбрасывается, чтобы собственный голос Jarvis не попадал в распознанный текст.

## Как устроен проект

```text
jarvis_voice/
  app.py          # микрофон, Vosk и жизненный цикл приложения
  session.py      # команды и состояние записи
  platform_io.py  # приветствие, буфер обмена и вставка
run.py            # точка входа
setup.sh          # установка macOS/Linux
setup.ps1         # установка Windows
tests/            # тесты без микрофона
```

Русская модель `vosk-model-small-ru-0.22` скачивается установочными скриптами с [зеркала Hugging Face](https://huggingface.co/Derur/vosk-models/tree/main/stt/ru/vosk-model-small-ru-0.22) и не включается в репозиторий. Для более точного распознавания можно установить большую модель Vosk и изменить `MODEL_PATH` в `jarvis_voice/app.py`.

## Разработка и тесты

macOS/Linux:

```sh
.venv/bin/python -m unittest discover -s tests -t . -v
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Тесты используют поддельные распознаватели и не требуют модель, микрофон или системные разрешения. На текущей машине проверены загрузка модели и тесты под macOS; живой запуск Windows и Linux требует проверки в соответствующем окружении.

## Дальнейшие планы

- Улучшение точности распознавания и пунктуации.
- Настраиваемые голосовые команды.
- Интеграция с отдельным assistant-проектом.

## Лицензия

Код проекта распространяется под [MIT License](LICENSE). Vosk, голосовая модель и системные голоса имеют собственные лицензии.
