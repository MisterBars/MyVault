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
reward_xp: 90
---

# Класс Orchestrator

## Назначение класса
Главный координатор multi-agent архитектуры.

Оркестратор получает пользовательскую задачу, передаёт её planner'у, направляет подзадачи worker'у, отслеживает результаты и контролирует цикл перепланирования.

## Важные решения
- Orchestrator хранит состояние процесса
- Orchestrator ограничивает количество итераций
- Orchestrator предотвращает бесконечную рекурсию planner/worker
- Orchestrator собирает итоговый ответ

## Основная ответственность
- запуск сценария решения задачи
- передача задачи planner'у
- передача подзадач worker'у
- обработка `needs_replan`
- сбор финального результата

## Ожидаемые методы
- `run(task, context) -> OrchestratorResult`
- `dispatch(plan, context) -> OrchestratorResult`

## Зависимости
- [[10 Projects/code-agent/Классы/PlannerAgent|PlannerAgent]]
- [[10 Projects/code-agent/Классы/WorkerAgent|WorkerAgent]]
- [[10 Projects/code-agent/Модули/ConversationStore|ConversationStore]]
- [[10 Projects/code-agent/Модули/Logger|Logger]]

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