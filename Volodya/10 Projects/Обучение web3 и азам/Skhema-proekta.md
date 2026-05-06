---
type: learning-schema
status: in-progress
project: "[[web3]]"
schema_version: v1
source_of_truth: "[[Промт к ИИ]]"
tags:
  - schema
  - learning
  - web3
---

# Схема проекта web3

## Назначение
Этот документ описывает структуру учебного проекта `web3`: какие сущности используются в vault, как связаны фазы, модули, задачи, артефакты, сессии и XP, и по каким правилам считается прогресс.

## Источник актуальности
- Основной контекст проекта: [[Промт к ИИ]]
- Главная карточка проекта: [[web3]]
- Операционный прогресс: [[Прогресс обучения]]
- При расхождении между отдельными заметками, приоритет у текущего актуального плана обучения и карточек модулей.

## Принципы проектирования
- Обучение строится не от теории к теории, а от цели к практическому результату.
- Каждый модуль должен иметь статус, reward_xp, фазу и связь с проектом.
- Каждая задача должна быть проверяемой и иметь Definition of Done.
- Каждый крупный навык должен быть подтверждён артефактом.
- Каждая учебная сессия фиксирует, что было сделано, что понято, что осталось неясным.
- XP начисляется не за “чтение в вакууме”, а за завершённые сущности.

## Типы сущностей

| Тип                 | Назначение                   | Пример                    |
| ------------------- | ---------------------------- | ------------------------- |
| `project`           | Верхний уровень направления  | `[[web3]]                 |
| `learning-schema`   | Документ структуры и правил  | `[[Схема проекта web3]]`  |
| `learning-progress` | Текущий прогресс и состояние | `[[Прогресс обучения]]`   |
| `module`            | Учебный модуль               | `[[Solidity basics]]`     |
| `skill`             | Навык верхнего уровня        | `[[Solidity]]`            |
| `task`              | Конкретная задача            | `[[Написать ERC-20]]`     |
| `artifact`          | Результат практики           | `[[Mini ERC-20 repo]]`    |
| `study-session`     | Отдельная учебная сессия     | `[[Session 2026-05-06]]`  |
| `checkpoint`        | Контрольная точка            | `[[Фаза 3 checkpoint 1]]` |
| `resource`          | Полезный источник            | `[[Solidity docs]]`       |

## Фазы проекта

| Фаза | Название | Назначение | Статус |
|---|---|---|---|
| 0 | Git & GitHub | База для учебной дисциплины и портфолио | planned |
| 1 | Python / SQL / Backend base | Основа для инженерного мышления и data/backend части | planned |
| 2 | MLOps / infra background | Усиление инфраструктурной базы | planned |
| 3 | Web3 core | Основной целевой контур web3 | active |

## Домены внутри web3

### Blockchain Fundamentals
- EVM
- Accounts
- Transactions
- Gas
- Storage
- ABI

### Smart Contracts
- Solidity
- ERC-20
- ERC-721
- Security
- Testing
- Deployment

### Tooling
- Hardhat
- Foundry
- ethers.js
- web3.py

### Frontend / Integration
- React
- Wagmi
- WalletConnect
- MetaMask
- Event reading

### Data / Infra
- The Graph
- On-chain analytics
- PostgreSQL
- Indexing
- ETL

### Decentralized Storage
- IPFS
- Arweave
- Ceramic
- OrbitDB

## Правила прохождения модуля
- `planned` — модуль запланирован, но не начат.
- `active` — модуль в работе.
- `review` — теорию прошёл, нужна практика/закрепление.
- `done` — модуль закрыт теорией + практикой + заметкой/артефактом.
- `blocked` — есть внешний блокер.

## Правила начисления XP
- Простой модуль: 25–50 XP.
- Практическая задача: 20–80 XP.
- Mini-project / artifact: 100–250 XP.
- Контрольная точка по фазе: 150–300 XP.
- Учебная сессия сама по себе может давать 5–15 XP, если хочешь геймификацию.

## Основные связи
- `project -> module`
- `project -> task`
- `project -> artifact`
- `module -> task`
- `module -> artifact`
- `skill -> module`
- `study-session -> module/task`
- `checkpoint -> modules/artifacts`

## Минимальная структура папок
```text
web3/
  web3.md
  Skhema-proekta-web3.md
  Progress-obucheniia.md

  Modules/
  Skills/
  Tasks/
  Artifacts/
  Sessions/
  Checkpoints/
  Resources/
```

## Замечания
- Главная сущность в учебном проекте — модуль, а не файл с теорией.
- Если заметка не помогает принять решение “что делать дальше”, она должна быть либо упрощена, либо связана с задачей.
- Если модуль закрыт без практики, это не `done`, а максимум `review`.