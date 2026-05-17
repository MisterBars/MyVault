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
reward_xp: 70
---

# Класс PlannerAgent

## Назначение класса
Агент-планировщик.

Получает исходную задачу пользователя, анализирует её и разбивает на подзадачи.
Если worker возвращает задачу как слишком сложную или плохо определённую, planner выполняет перепланирование.

## Важные решения
- Planner не выполняет tools напрямую
- Planner отвечает за структуру решения, а не за действия
- Planner может работать итеративно, шаг за шагом
- Перепланирование должно быть ограничено по глубине
- Если задача простая и не требует worker — planner может ответить сам

## Основная ответственность
- анализ исходной задачи
- построение плана из подзадач
- приоритизация шагов
- перепланирование при возврате сложной подзадачи
- определение момента завершения

## Ожидаемые методы
- `plan(task, context) -> PlanResult`
- `replan(subtask, feedback, context) -> PlanResult`

## Контракты
Входные данные для `plan()`:
- `task: UserTask`
- `context: dict` — история беседы, retrieval-контекст, метаданные проекта

Выход `PlanResult`:
- `plan_id: str`
- `goal: str`
- `steps: list[PlanStep]`
- `reasoning_summary: str`
- `done: bool` — True если задача не требует worker
- `needs_worker: bool`

## Поведение при перепланировании
Worker сигнализирует `needs_replan` с причиной.
Planner получает `subtask` и `feedback`, обновляет план.
Глубина перепланирования ограничена — максимум задаётся в конфиге Orchestrator.
Если лимит превышен — Orchestrator завершает цикл с ошибкой.

## Промпт-стратегия
Planner использует системный промпт с инструкцией:
- разобрать задачу
- выделить конкретные подзадачи
- присвоить каждой приоритет и зависимости
- вернуть ответ строго в формате JSON

В промпт передаётся:
- текст задачи
- краткая история беседы
- retrieval-контекст (если есть)
- hint о доступных tools (в Phase 1 — только text-response)

## Зависимости
- [[10 Projects/code-agent/Модули/OllamaClient|OllamaClient]]
- [[10 Projects/code-agent/Модули/RAGService|RAGService]]
- [[10 Projects/code-agent/Классы/Orchestrator|Orchestrator]]

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