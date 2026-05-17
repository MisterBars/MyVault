---
type: reference
tags:
  - hardware
  - pc
  - infrastructure
  - ai
updated: 2026-05-17
---

# Характеристики ПК

## Назначение

Основной рабочий ПК для:
- локальных LLM через Ollama
- Python-разработки
- AI-агентов
- Docker / WSL2 / Git / Obsidian
- работы с базами данных и автоматизацией

## Основная конфигурация

| Компонент | Значение |
|---|---|
| CPU | AMD Ryzen 7 7700 |
| GPU | NVIDIA RTX 5060 16 GB VRAM *(нужно уточнить: возможно RTX 5060 Ti 16 GB)* |
| RAM | 64 GB DDR5 |
| Частота RAM | 6400 MT/s |
| Тайминги RAM | 30-40-40 |
| Материнская плата | ASRock B650 Steel Legend WiFi |
| ОС | Windows 11 |
| Linux-среда | WSL2 |

## Мониторы

| Роль | Модель | Характеристики |
|---|---|---|
| Основной | MSI MAG 275QF | 27", 2K, IPS |
| Второй | Xiaomi G27Qi / G27i | 27", Full HD, IPS |

## Накопители

| Тип | Примечание |
|---|---|
| NVMe SSD #1 | ADATA LEGEND 860, 1 TB |
| NVMe SSD #2 | ARDOR GAMING Ally AL1288, 1 TB |

## Корпус и питание

| Компонент | Значение |
|---|---|
| Корпус | Montech King 95 Pro |
| Блок питания | 850W |

## Локальные AI-модели

Модели Ollama, используемые на этом ПК:

- `qwen2.5-coder:7b`
- `qwen2.5-coder:14b`
- `qwen3-coder:30b`
- `deepseek-coder-v2:16b`
- `gpt-oss:20b`
- `my-gpu-coder:latest`
- `sleechengn/nomic-embed-text:latest`
- `nomic-embed-text-v2-moe:latest`

## Для каких задач используется

- локальный Code Agent на Python
- эксперименты с Ollama и локальными кодовыми LLM
- RAG / embeddings
- Docker-контейнеры
- PostgreSQL и автоматизация
- Obsidian Vault + GitHub

## Примечания

- RAM разогнана с 6000 до 6400 MT/s.
- Конфигурация подходит для локальной разработки AI-агентов и запуска кодовых моделей.
- Уточнить точную модель видеокарты: `RTX 5060` или `RTX 5060 Ti`.