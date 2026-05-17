---
type: module
status: planned
done_date:
project: "[[code-agent]]"
skill: python
tags:
  - module
  - skill/python
  - skill/ai
reward_xp: 60
---

# Модуль ConversationStore

## Назначение
Слой хранения бесед и сессий.

Нужен для web UI и project-oriented общения:
- история сообщений
- связь сообщений с проектом
- отдельные сессии
- метаданные беседы

## Важные решения
- conversation history не равна RAG
- одна беседа привязана к проекту или общему пространству
- сообщения planner/worker должны храниться отдельно по ролям
- storage должен быть простым на старте

## Основная ответственность
- создать беседу
- сохранить сообщение
- получить историю беседы
- отфильтровать беседы по проекту

## Ожидаемые функции
- `create_conversation(project_id=None) -> str`
- `append_message(conversation_id, role, content, meta=None) -> None`
- `get_messages(conversation_id) -> list[dict]`
- `list_conversations(project_id=None) -> list[dict]`

## Черновые заметки