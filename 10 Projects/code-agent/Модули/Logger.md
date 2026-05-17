---
type: module
status: active
done_date:
project: "[[code-agent]]"
skill: python
tags:
  - module
  - skill/python
reward_xp: 30
---

# Модуль Logger

## Назначение
Единое логирование для всего проекта.
Пишет в консоль и в файл `agent.log` с временными метками.
Все классы используют только `Logger.log()` — не `print()`.

## Важные решения
- Простой модуль без классов — функции уровня модуля достаточно.
- Уровни: `info`, `warn`, `error` — минимальный набор для агента.
- Файл лога перезаписывается при каждом запуске (`mode='w'`), чтобы не копился мусор.


## Задачи по модулю

```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task"
  AND project = this.project
  AND contains(file.outlinks, this.file.link)
SORT deadline ASC
```

## Взаимосвязи (исходящие вызовы)

```dataviewjs
const TYPES = ['module', 'class'];
const current = dv.current();
const currentProject = current.project;
if (!currentProject) {
  dv.paragraph('У текущего модуля не заполнено поле project — нечего сканировать.');
  return;
}
const allPages = dv.pages()
  .where(p => TYPES.includes(p.type))
  .where(p => p.project && dv.func.contains(p.project, currentProject))
  .array();

async function getPyBlocks(path) {
  const text = await dv.io.load(path);
  if (!text) return [];
  const blocks = [];
  const re = /```python([\s\S]*?)```/g;
  let m;
  while ((m = re.exec(text)) !== null) blocks.push(m[1]);
  return blocks;
}

const reDef = /^\s*(?:async\s+)?def\s+(\w+)/m;
const reDefG = /^\s*(?:async\s+)?def\s+(\w+)/gm;

const procIndex = {};
for (const page of allPages) {
  const blocks = await getPyBlocks(page.file.path);
  for (const block of blocks) {
    let m;
    while ((m = reDefG.exec(block)) !== null) {
      const name = m[1];
      if (!procIndex[name]) procIndex[name] = [];
      procIndex[name].push({ modulePath: page.file.path, moduleLink: page.file.link });
    }
  }
}

const currentBlocks = await getPyBlocks(current.file.path);
const reCall = /\b(\w+)\s*\(/g;
const callMap = new Map();

for (const block of currentBlocks) {
  const lines = block.split('\n');
  let currentFunc = null;
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('#')) continue;
    const defMatch = /^\s*(?:async\s+)?def\s+(\w+)/.exec(line);
    if (defMatch) { currentFunc = defMatch[1]; continue; }
    if (!currentFunc) continue;
    let m;
    while ((m = reCall.exec(line)) !== null) {
      const calledName = m[1];
      const targets = procIndex[calledName];
      if (!targets) continue;
      for (const t of targets) {
        if (t.modulePath === current.file.path) continue;
        const key = `${currentFunc}||${t.modulePath}`;
        if (!callMap.has(key)) callMap.set(key, { fromFunc: currentFunc, toModuleLink: t.moduleLink, calledNames: new Set() });
        callMap.get(key).calledNames.add(calledName);
      }
    }
  }
}

const rows = [];
for (const entry of callMap.values()) {
  rows.push([entry.fromFunc, entry.toModuleLink, Array.from(entry.calledNames).sort().join(', ')]);
}
if (rows.length === 0) {
  dv.paragraph('Исходящих вызовов других модулей/классов в рамках этого проекта не найдено.');
} else {
  dv.table(['Функция', 'Куда (модуль)', 'Что вызывает'], rows);
}
```

## Функции и методы

```dataviewjs
const page = dv.current();
const text = await dv.io.load(page.file.path);
const blocks = [];
const re = /```python([\s\S]*?)```/g;
let m;
while ((m = re.exec(text)) !== null) blocks.push(m[1]);

const reDef = /^\s*(?:(async)\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([\w\[\], |None]+))?/;
const reTag = /^\s*#\s*@(\w+):\s*(.+)$/;

const rows = [];
for (const block of blocks) {
  const lines = block.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const dm = reDef.exec(lines[i]);
    if (!dm) continue;
    const isAsync = dm[1] ? 'async ' : '';
    const name = dm[2];
    const params = dm[3] ? dm[3].trim() : '';
    const returnType = dm[4] ? dm[4].trim() : '';
    const tags = { desc: '', role: '', todo: '' };
    let k = i + 1;
    while (k < lines.length) {
      const cur = lines[k].trim();
      if (cur === '') { k++; continue; }
      const tm = reTag.exec(lines[k]);
      if (!tm) break;
      const tn = tm[1].toLowerCase();
      if (Object.prototype.hasOwnProperty.call(tags, tn)) tags[tn] = tm[2].trim();
      k++;
    }
    rows.push([isAsync + name, params, returnType, tags.desc, tags.role, tags.todo]);
  }
}
if (rows.length === 0) {
  dv.paragraph('Функции и методы в коде не найдены.');
} else {
  dv.table(['Имя', 'Параметры', 'Возврат', 'Описание', 'Роль', 'TODO'], rows);
}
```

## Код

```python
import sys
from datetime import datetime
from pathlib import Path

# @desc: Настройки логгера
# @role: Config
# @todo: Вынести LOG_FILE в конфиг проекта

LOG_FILE = Path("agent.log")
_log_handle = None

def _get_handle():
    # @desc: Возвращает открытый файловый дескриптор для лога (ленивая инициализация)
    # @role: Internal
    # @todo: Добавить ротацию файла при превышении 1 МБ
    global _log_handle
    if _log_handle is None:
        _log_handle = open(LOG_FILE, "w", encoding="utf-8")
    return _log_handle

def _write(level: str, message: str):
    # @desc: Форматирует строку лога и пишет в консоль и файл
    # @role: Internal
    # @todo: Добавить цвета в консоль через colorama
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [{level.upper():5s}] {message}"
    print(line, file=sys.stdout if level != "error" else sys.stderr)
    try:
        _get_handle().write(line + "\n")
        _get_handle().flush()
    except Exception:
        pass

def info(message: str):
    # @desc: Логирует информационное сообщение
    # @role: Logging
    # @todo: -
    _write("info", message)

def warn(message: str):
    # @desc: Логирует предупреждение
    # @role: Logging
    # @todo: -
    _write("warn", message)

def error(message: str):
    # @desc: Логирует ошибку
    # @role: Logging
    # @todo: -
    _write("error", message)

def separator(label: str = ""):
    # @desc: Пишет разделитель в лог для визуального разделения попыток
    # @role: Logging
    # @todo: -
    line = f"{'─' * 20} {label} {'─' * 20}" if label else "─" * 50
    _write("info", line)

def close():
    # @desc: Закрывает файловый дескриптор лога
    # @role: Lifecycle
    # @todo: Вызывать в finally основного скрипта
    global _log_handle
    if _log_handle:
        _log_handle.close()
        _log_handle = None

# ─── Тест-запуск ───
if __name__ == "__main__":
    info("Логгер запущен")
    warn("Это предупреждение")
    error("Это ошибка")
    separator("Попытка 1")
    close()
    print("Лог записан в:", LOG_FILE)
```

## Черновые заметки
