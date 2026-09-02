# Рекламный ролик «AI-наставник 360»

45–60 с, 30 fps, русский, субтитры. Автор проекта: Степанов Д.А.

## Сборка

Из корня репозитория:

```bash
.venv/Scripts/python promo-video/src/build.py
```

Только 16:9:

```bash
.venv/Scripts/python promo-video/src/build.py --aspect 16x9
```

Только 9:16:

```bash
.venv/Scripts/python promo-video/src/build.py --aspect 9x16
```

Результаты: `promo-video/output/ai-nastavnik-360-16x9.mp4` и `promo-video/output/ai-nastavnik-360-9x16.mp4`.  
Субтитры: `promo-video/subtitles/subtitles-ru.srt`.

Нужны пакеты в `.venv`: `pillow`, `numpy`, `imageio-ffmpeg`, `edge-tts`.

## Содержание

Не использует `.env`, токены и реальные персональные данные. На экране только вымышленные демо-имена.
