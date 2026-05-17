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
- Worker должен уметь явно сигнализировать: `done / failed / needs_replan`

## Основная ответственность
- выполнение подзадач
- работа с tools
- использование retrieval
- возврат результата
- возврат сложной задачи на перепланирование

## Ожидаемые методы
- `solve_subtask(subtask, context) -> WorkerResult`
- `request_replan(subtask, reason, context) -> WorkerResult`

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
  AND project = this.project
  AND contains(file.outlinks, this.file.link)
SORT deadline ASC
```

## Черновые заметки