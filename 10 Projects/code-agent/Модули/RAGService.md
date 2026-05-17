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
reward_xp: 80
---

# Модуль RAGService

## Назначение
Слой retrieval и памяти знаний.

Используется для:
- общей базы знаний
- проектной базы знаний
- загрузки файлов
- retrieval-контекста для planner и worker

## Важные решения
- общая и проектная базы знаний должны быть разделены
- retrieval не равен conversation history
- retrieval-контекст должен быть ограниченным и контролируемым
- в первой версии достаточно простого ingest + search

## Основная ответственность
- индексировать документы
- искать релевантные фрагменты
- разделять global/project knowledge
- отдавать контекст агентам

## Ожидаемые функции
- `ingest_file(path, project_id=None) -> IngestResult`
- `search(query, project_id=None, k=5) -> list[Chunk]`
- `delete_source(source_id) -> None`

## Черновые заметки