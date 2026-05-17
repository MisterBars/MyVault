---
type: class
status: planned
done_date:
project: "[[code-agent]]"
skill: python
tags:
  - class
  - skill/python
  - skill/ai
reward_xp: 80
---

# Класс WorkerAgent

## Назначение класса
Агент-исполнитель.

Получает конкретную подзадачу от planner и пытается её выполнить.
Если подзадача слишком сложная, неоднозначная или требует дополнительной декомпозиции, worker возвращает её planner'у.

## Важные решения
- Worker не отвечает за глобальное планирование
- Worker может использовать tools
- Worker может использовать retrieval-контекст
- Worker явно сигнализирует результат: `done / failed / needs_replan`
- В Phase 1 worker отвечает текстом без тяжёлых tool-вызовов

## Основная ответственность
- выполнение конкретной подзадачи
- использование доступных tools
- запрос retrieval-контекста при необходимости
- возврат результата в структуре `WorkerResult`
- возврат задачи на перепланирование с явной причиной

## Ожидаемые методы
- `solve_subtask(subtask, context) -> WorkerResult`
- `request_replan(subtask, reason, context) -> WorkerResult`

## Контракты
Входные данные для `solve_subtask()`:
- `subtask: PlanStep`
- `context: dict` — retrieval, история, tool context

Выход `WorkerResult`:
- `step_id: str`
- `status: str` — `done / failed / needs_replan`
- `output: str`
- `artifacts: list[dict]`
- `error: str | None`
- `reason: str | None` — обязателен при `needs_replan`

## Правила возврата задачи
Worker должен вернуть `needs_replan` если:
- подзадача требует знаний, которых нет в контексте
- подзадача содержит несколько независимых частей
- подзадача слишком абстрактна для конкретного действия

Worker не должен молча провалить задачу — всегда явный статус.

## Tools в Phase 1
В первой фазе worker работает только через text-response.
Следующие tools будут добавляться поэтапно:
- `CodeRunner` — запуск Python-кода
- `FileReader` — чтение файлов
- `GitReader` — анализ репозитория
- `WebFetcher` — чтение веб-страниц

## Промпт-стратегия
Worker использует системный промпт с инструкцией:
- получить конкретную подзадачу
- выполнить её максимально точно
- если задача выполнена — вернуть JSON с `status: done`
- если задача слишком сложная — вернуть JSON с `status: needs_replan` и причиной

## Зависимости
- [[10 Projects/code-agent/Модули/OllamaClient|OllamaClient]]
- [[10 Projects/code-agent/Классы/CodeRunner|CodeRunner]]
- [[10 Projects/code-agent/Классы/FixLoop|FixLoop]]
- [[10 Projects/code-agent/Модули/RAGService|RAGService]]

## Задачи по модулю

```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task"
  AND project = [[code-agent]]
  AND contains(file.outlinks, this.file.link)
  AND !contains(file.path, "90 Templates")
  AND !contains(file.path, "40 Archives")
SORT deadline ASC
```

## Черновые заметки