---
type: reference
tags:
  - hardware
  - infrastructure
updated: 2026-05-17
---

# Характеристики ПК

## Общее
| Параметр | Значение |
|---|---|
| ОС | Windows (+ WSL2) |
| Python | 3.11+ |
| Пакетный менеджер | pip / venv |

## GPU — Локальные LLM

Модели Ollama, доступные на GPU:

| Модель | Размер | Назначение |
|---|---|---|
| `qwen2.5-coder:7b` | ~4.7 GB VRAM | Code Agent (default, быстрый) |
| `qwen2.5-coder:14b` | ~9 GB VRAM | Code Agent (точный) |
| `deepseek-coder-v2:16b` | ~10 GB VRAM | Сложный код |
| `gpt-oss:20b` | ~13 GB VRAM | Общее назначение |
| `qwen3-coder:30b` | ~20 GB VRAM | Самая сильная для кода |
| `my-gpu-coder:latest` | — | Персональная fine-tuned модель |

**Embed-модели (RAG):**
- `nomic-embed-text-v2-moe:latest`
- `sleechengn/nomic-embed-text:latest`

## Среда разработки

| Инструмент | Роль |
|---|---|
| Docker Desktop | Контейнеризация |
| WSL2 (Ubuntu) | Linux-среда на Windows |
| Git / GitHub | Версионирование |
| Obsidian | Заметки / вики |
| PostgreSQL | Базы данных |
| Ollama | Локальные LLM |

## Проекты на этом ПК

- [[code-agent]] — локальный AI Code Agent
- Аниме-бот (Python + PostgreSQL + Playwright + Docker)
- VBA/Access автоматизация

## Заметки

> Дополнить: конкретные характеристики CPU/RAM/GPU после уточнения.
