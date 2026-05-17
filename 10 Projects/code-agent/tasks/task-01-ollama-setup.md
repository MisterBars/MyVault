---
type: task
task_type: setup
status: done
project: "[[code-agent]]"
deadline: 2026-05-25
reward_xp: 50
tags:
  - task
  - skill/ai
---

# Задача: Настроить Ollama + выбрать модель

## Что нужно сделать
- [x] Установить Ollama: `curl -fsSL https://ollama.com/install.sh | sh` ✅ 2026-05-17
- [x] Скачать модель: `ollama pull qwen2.5-coder:7b` ✅ 2026-05-17
- [x] Проверить CLI: `ollama run qwen2.5-coder:7b "напиши hello world на python"` ✅ 2026-05-17
- [x] Проверить HTTP API: `curl http://localhost:11434/api/generate -d '{"model":"qwen2.5-coder:7b","prompt":"hi","stream":false}'` ✅ 2026-05-17
- [x] Зафиксировать endpoint в [[10 Projects/code-agent/Модули/OllamaClient]] ✅ 2026-05-17

## Критерий выполнения
Модель запущена, отвечает через HTTP API, задержка первого токена < 5 сек на второй запрос.

## Заметки
