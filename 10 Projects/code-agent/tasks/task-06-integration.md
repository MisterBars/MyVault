---
type: task
task_type: dev
status: backlog
project: "[[code-agent]]"
deadline: 2026-06-15
reward_xp: 100
tags:
  - task
  - skill/python
  - skill/ai
---

# Задача: Orchestrator + PlannerAgent + WorkerAgent

## Что нужно сделать
- [ ] Создать карточку [[10 Projects/code-agent/Классы/PlannerAgent]]
- [ ] Создать карточку [[10 Projects/code-agent/Классы/WorkerAgent]]
- [ ] Создать карточку [[10 Projects/code-agent/Классы/Orchestrator]]
- [ ] Описать контракт между planner и worker
- [ ] Описать правило возврата сложной подзадачи на перепланирование
- [ ] Зафиксировать ограничение глубины перепланирования
- [ ] Зафиксировать минимальный сценарий Phase 1: только текстовые ответы, без тяжёлых tools

## Критерий выполнения
В заметках проекта описан минимальный рабочий контур:
User → Orchestrator → PlannerAgent → WorkerAgent → ответ.

Если подзадача слишком сложная:
WorkerAgent → PlannerAgent → новая декомпозиция.

## Заметки
Это новая интеграционная задача v2.
Старая интеграция вокруг одного CodeAgent больше не является целевой архитектурой.