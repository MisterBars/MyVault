---
type: task
task_type: architecture
status: active
project: "[[code-agent]]"
deadline: 2026-06-15
reward_xp: 100
phase: architecture
tags:
  - task
  - skill/python
  - skill/ai
  - architecture
---

# Задача: Зафиксировать контур planner / worker / orchestrator

## Что нужно сделать
- [ ] Создать и заполнить [[10 Projects/code-agent/Контракты и типы данных]]
- [ ] Зафиксировать `PlanResult`
- [ ] Зафиксировать `WorkerResult`
- [ ] Зафиксировать `OrchestratorResult`
- [ ] Описать правило `needs_replan`
- [ ] Описать ограничение по глубине перепланирования
- [ ] Описать минимальный сценарий Phase 1 без тяжёлых tools

## Критерий выполнения
Есть отдельный документ с контрактами и типами данных.
Роли planner, worker и orchestrator связаны единым протоколом.
Понятно, какие данные передаются между сущностями и что считается успешным завершением шага.

## Заметки
Это уже не задача на создание карточек.
Карточки ролей созданы, теперь нужно согласовать их между собой.