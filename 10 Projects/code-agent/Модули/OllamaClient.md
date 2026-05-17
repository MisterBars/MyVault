---
type: module
status: active
done_date:
project: "[[code-agent]]"
skill: python
tags:
  - module
  - skill/python
  - skill/ai
reward_xp: 50
---

# Модуль OllamaClient

## Назначение
HTTP-клиент к локальному Ollama API (`http://localhost:11434`).
Отвечает за отправку промптов и получение ответов от LLM.
Остальные классы не знают про HTTP — только вызывают `ask()`.

## Важные решения
- Использует `requests` вместо `httpx` — меньше зависимостей, синхронный код проще для отладки.
- `stream=False` — ждём полный ответ, чтобы не усложнять парсинг в агенте.
- Таймаут `timeout=120` — большие модели могут отвечать долго при первом запуске.


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
import requests
import json

# @desc: Клиент для работы с Ollama REST API
# @role: LLM / Infrastructure
# @todo: Добавить поддержку streaming для отображения прогресса

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5-coder:7b"

def ask(prompt: str, model: str = DEFAULT_MODEL, system: str = "") -> str:
    # @desc: Отправляет промпт в Ollama и возвращает текстовый ответ
    # @role: LLM
    # @todo: Добавить retry при ConnectionError (Ollama может быть не запущен)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Ollama не запущен. Запусти: ollama serve")
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama не ответил за 120 секунд — попробуй модель поменьше")
    except Exception as e:
        raise RuntimeError(f"Ошибка Ollama API: {e}")

def extract_python_code(text: str) -> str:
    # @desc: Извлекает Python-код из блока ```python ... ``` в ответе LLM
    # @role: Parser
    # @todo: Обработать случай когда LLM вернул несколько блоков кода
    import re
    match = re.search(r"```python\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    # Если блока нет — возвращаем весь текст как есть
    return text.strip()

def list_models() -> list[str]:
    # @desc: Возвращает список доступных моделей Ollama
    # @role: Utility
    # @todo: Использовать при инициализации агента для проверки наличия нужной модели
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=10)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return [m["name"] for m in models]
    except Exception:
        return []

# ─── Тест-запуск (не рабочий, только для проверки импорта) ───
if __name__ == "__main__":
    models = list_models()
    print("Доступные модели:", models if models else "Ollama не запущен")
    # answer = ask("напиши hello world на python")
    # code = extract_python_code(answer)
    # print("Код от LLM:", code)
```

## Черновые заметки
