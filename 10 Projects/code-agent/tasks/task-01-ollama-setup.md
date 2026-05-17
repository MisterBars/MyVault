---
type: task
task_type: setup
status: active
project: "[[code-agent]]"
deadline: 2026-05-25
reward_xp: 50
tags:
  - task
  - skill/ai
---

# Задача: Настроить Ollama + выбрать модель

## Что нужно сделать
- [ ] Установить Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
- [ ] Скачать модель: `ollama pull qwen2.5-coder:7b`
- [ ] Проверить CLI: `ollama run qwen2.5-coder:7b "напиши hello world на python"`
- [ ] Проверить HTTP API: `curl http://localhost:11434/api/generate -d '{"model":"qwen2.5-coder:7b","prompt":"hi","stream":false}'`
- [ ] Зафиксировать endpoint в [[10 Projects/code-agent/Модули/OllamaClient]]

## Критерий выполнения
Модель запущена, отвечает через HTTP API, задержка первого токена < 5 сек на второй запрос.

## Заметки
