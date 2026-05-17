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

## Основная ответственность
- анализ исходной задачи
- построение плана
- разбиение на подзадачи
- приоритизация
- перепланирование

## Ожидаемые методы
- `plan(task, context) -> PlanResult`
- `replan(subtask, feedback, context) -> PlanResult`

## Зависимости
- [[10 Projects/code-agent/Модули/OllamaClient|OllamaClient]]
- [[10 Projects/code-agent/Модули/RAGService|RAGService]]
- [[10 Projects/code-agent/Классы/Orchestrator|Orchestrator]]

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