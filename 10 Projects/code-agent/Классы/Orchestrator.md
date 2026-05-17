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

Получает пользовательскую задачу, передаёт её planner'у, направляет подзадачи worker'у, отслеживает результаты и управляет циклом перепланирования.
Orchestrator — единственная точка, которая знает весь процесс целиком.

## Важные решения
- Orchestrator хранит состояние текущего процесса
- Orchestrator ограничивает число итераций
- Orchestrator предотвращает бесконечную рекурсию
- Orchestrator записывает ключевые события в ConversationStore
- Orchestrator собирает финальный ответ пользователю

## Основная ответственность
- запуск сценария выполнения задачи
- вызов `PlannerAgent.plan()`
- вызов `WorkerAgent.solve_subtask()` по каждому шагу плана
- обработка `needs_replan` — возврат в planner с feedback
- защита от бесконечного цикла через лимит итераций
- запись событий в ConversationStore
- возврат `OrchestratorResult`

## Ожидаемые методы
- `run(task, context) -> OrchestratorResult`
- `dispatch(plan, context) -> OrchestratorResult`

## Контракты
Входные данные для `run()`:
- `task: UserTask`
- `context: dict` — conversation_id, project_id, retrieval-контекст

Выход `OrchestratorResult`:
- `success: bool`
- `final_answer: str`
- `steps_completed: int`
- `replans: int`
- `messages_used: int`
- `artifacts: list[dict]`

## Жизненный цикл задачи

```text
run(task)
  │
  ├── planner.plan(task) -> PlanResult
  │      │
  │      └── если done=True → вернуть финальный ответ напрямую
  │
  ├── для каждого шага плана:
  │      worker.solve_subtask(step)
  │          │
  │          ├── status: done → следующий шаг
  │          ├── status: failed → зафиксировать ошибку, продолжить или завершить
  │          └── status: needs_replan:
  │                  replans += 1
  │                  если replans >= MAX_REPLANS → завершить с ошибкой
  │                  planner.replan(step, feedback) -> новый PlanResult
  │                  продолжить с новым планом
  │
  └── вернуть OrchestratorResult
```

## Лимиты
- `MAX_REPLANS` — максимальное число перепланировок за одну задачу (рекомендуется: 3)
- `MAX_STEPS` — максимальное число шагов в плане (рекомендуется: 10)
- `MAX_ITERATIONS` — общий лимит итераций planner+worker (рекомендуется: 20)

## События для ConversationStore
Orchestrator должен записывать:
- `user_task` — исходная задача пользователя
- `plan_created` — план создан planner'ом
- `step_done` — шаг завершён worker'ом
- `step_failed` — шаг провалился
- `replan_triggered` — запущено перепланирование
- `final_answer` — финальный ответ пользователю

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
  AND project = [[code-agent]]
  AND contains(file.outlinks, this.file.link)
  AND !contains(file.path, "90 Templates")
  AND !contains(file.path, "40 Archives")
SORT deadline ASC
```

## Черновые заметки