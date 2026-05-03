---
type: module
status: in-progress
done_date:
project: "[[Учёт ВВТ]]"
skill: vba
tags:
  - module
  - skill/vba
reward_xp: 50
---
# Модуль

## Назначение

Кратко, за что отвечает модуль, какие задачи решает.

## Важные решения

- Почему выбрана такая архитектура.
- Комментарии по производительности/ограничениям.

## Задачи по модулю

```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task" AND project = this.project AND contains(file.outlinks, this.file.link)
SORT deadline ASC
```

## Взаимосвязи (исходящие вызовы)

```dataviewjs
// Какие типы считаем VBA-кодом
const TYPES = ['module', 'form', 'class'];

// Проект текущего модуля (ссылка)
const current = dv.current();
const currentProject = current.project;

if (!currentProject) {
  dv.paragraph('У текущего модуля не заполнено поле project — нечего сканировать.');
  return;
}

// Фильтруем только те страницы, у которых такой же project
// p.project может быть ссылкой или массивом ссылок, поэтому используем dv.func.contains
const allPages = dv.pages()
  .where(p => TYPES.includes(p.type))
  .where(p => p.project && dv.func.contains(p.project, currentProject));

// === Функция: вытащить все VBA-блоки ```vba из файла ===
async function getVbaBlocks(path) {
  const text = await dv.io.load(path);
  if (!text) return [];

  const blocks = [];
  let inBlock = false;
  let currentBlock = [];

  for (const line of text.split('\n')) {
    const trimmed = line.trim();
    if (!inBlock && trimmed.startsWith('```vba')) {
      inBlock = true;
      currentBlock = [];
      continue;
    }
    if (inBlock && trimmed.startsWith('```')) {
      inBlock = false;
      blocks.push(currentBlock.join('\n'));
      currentBlock = [];
      continue;
    }
    if (inBlock) currentBlock.push(line);
  }
  return blocks;
}

// Регэксп объявления процедур / функций (как в твоём шаблоне)
const reProcDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;

// Индекс: имя процедуры → список мест, где она объявлена
const procIndex = {};

for (const page of allPages) {
  const vbaBlocks = await getVbaBlocks(page.file.path);

  for (const block of vbaBlocks) {
    const lines = block.split('\n');
    for (const line of lines) {
      const m = line.match(reProcDecl);
      if (!m) continue;

      const name = m[3];

      if (!procIndex[name]) procIndex[name] = [];
      procIndex[name].push({
        modulePath: page.file.path,
        moduleLink: page.file.link,
        moduleType: page.type
      });
    }
  }
}

// === Анализируем текущий модуль: кто кого вызывает ===

const currentBlocks = await getVbaBlocks(current.file.path);

// Вызовы: Foo(...), Call Bar(...)
const reCall = /\b(?:Call\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()/g;

const rows = [];

for (const block of currentBlocks) {
  const lines = block.split('\n');
  let currentProc = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // пропускаем комментарии
    if (trimmed.startsWith("'")) continue;

    // новая процедура / функция
    const declMatch = line.match(reProcDecl);
    if (declMatch) {
      currentProc = declMatch[3];
      continue;
    }

    if (!currentProc) continue;

    // ищем вызовы
    let m;
    while ((m = reCall.exec(line)) !== null) {
      const calledName = m[1];
      const targets = procIndex[calledName];
      if (!targets) continue;

      for (const t of targets) {
        // если не хочешь самовызовы — можно фильтрануть
        if (t.modulePath === current.file.path && calledName === currentProc) continue;

        rows.push([
          current.file.link,   // Откуда (модуль)
          currentProc,         // Какая процедура
          t.moduleLink,        // Куда (модуль)
          calledName           // Что вызывает
        ]);
      }
    }
  }
}

if (rows.length === 0) {
  dv.paragraph('Исходящих вызовов других модулей/форм/классов в рамках этого проекта не найдено.');
} else {
  dv.table(
    ['Откуда (модуль)', 'Процедура', 'Куда (модуль)', 'Что вызывает'],
    rows
  );
}
```
# Функции и процедуры
```dataviewjs
const page = dv.current();
const text = await dv.io.load(page.file.path);

const vbaBlocks = [];
let inBlock = false;
let current = [];

for (const line of text.split("\n")) {
  if (line.trim().startsWith("```vba")) {
    inBlock = true;
    current = [];
    continue;
  }

  if (inBlock && line.trim().startsWith("```")) {
    inBlock = false;
    vbaBlocks.push(current.join("\n"));
    current = [];
    continue;
  }

  if (inBlock) current.push(line);
}

const reDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;
const reReturnType = /\)\s*As\s+([A-Za-z0-9_\.]+)/i;
const reTag = /^'\s*@([a-zA-Z0-9_]+):\s*(.+)$/i;

const rows = [];

for (const block of vbaBlocks) {
  const lines = block.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(reDecl);
    if (!m) continue;

    const scopeRaw = m[1];
    const kindRaw = m[2];
    const name = m[3];

    const kindLower = String(kindRaw ?? "").toLowerCase();
    const kind = kindLower === "sub" ? "Процедура" : "Функция";
    const scope = scopeRaw ? String(scopeRaw) : "По умолчанию (Public)";

    let j = i;
    while (j < lines.length - 1 && lines[j].trim().endsWith("_")) {
      j++;
    }

    const signatureLines = lines.slice(i, j + 1);
    const signatureText = signatureLines.join(" ");
    const mReturn = signatureText.match(reReturnType);
    const returnType = kind === "Функция" && mReturn ? String(mReturn[1]) : "";

    const tags = {
      desc: "",
      role: "",
      todo: ""
    };

    let k = j + 1;

    while (k < lines.length) {
      const cur = lines[k].trim();

      if (cur === "") {
        k++;
        continue;
      }

      const tagMatch = cur.match(reTag);
      if (!tagMatch) break;

      const tagName = String(tagMatch[1] ?? "").toLowerCase();
      const tagValue = String(tagMatch[2] ?? "").trim();

      if (Object.prototype.hasOwnProperty.call(tags, tagName)) {
        tags[tagName] = tagValue;
      }

      k++;
    }

    rows.push([
      name,
      kind,
      scope,
      returnType,
      tags.desc,
      tags.role,
      tags.todo
    ]);
  }
}

if (rows.length === 0) {
  dv.paragraph("Процедуры и функции в коде не найдены.");
} else {
  dv.table(
    ["Имя", "Тип", "Область", "Возврат", "Описание", "Роль", "TODO"],
    rows
  );
}
```
# Код
```vba
' @desc: **что делает конкретно эта процедура**
' @role: **какое место она занимает в системе**
' @todo: **заметка по процедуре/функции**


Option Explicit

Private Const VVT_BAR_NAME As String = "VVTMenu"

Public Sub CreateVVTMenu()
    On Error Resume Next
    
    Dim cmdBarVVT As CommandBar
    Dim btnDB, btnPathDB, btnAuth As CommandBarButton
'    Dim btnDB As CommandBarControl
    
    
    Application.CommandBars(VVT_BAR_NAME).Delete
    On Error GoTo 0
    
    Set cmdBarVVT = Application.CommandBars.Add( _
        name:=VVT_BAR_NAME, _
        Temporary:=True)
    
    cmdBarVVT.Visible = True
    
    If Dir(ThisWorkbook.Path & "\vvt_db.accdb") = "" Then
        Set btnDB = cmdBarVVT.Controls.Add(Type:=msoControlButton, Temporary:=True)
        With btnDB
            .Caption = "Ñîçäàòü ÁÄ"
            .Style = msoButtonCaption
            .BeginGroup = True
            .OnAction = "'" & ThisWorkbook.name & "'!CreateVVTDatabase"
        End With
    Else
        Set btnPathDB = cmdBarVVT.Controls.Add(Type:=msoControlButton, Temporary:=True)
        With btnPathDB
            .Caption = "Âûáðàòü ÁÄ"
            .Style = msoButtonCaption
            .BeginGroup = True
            .OnAction = "'" & ThisWorkbook.name & "'!ChangeDB"
        End With
        Set btnAuth = cmdBarVVT.Controls.Add(Type:=msoControlButton, Temporary:=True)
        With btnAuth
            .Caption = "Ìåíþ"
            .Style = msoButtonCaption
            .BeginGroup = True
            .OnAction = "'" & ThisWorkbook.name & "'!Auth"
        End With
    End If
End Sub

' Ñîçäàåòñÿ ïàíåëü ñî âñåìè èêîíêàìè, ïîòîì ìîæíî óäàëèòü
Sub ShowAllIcons()
    Dim i As Long
    Dim topPosition As Long
    Dim cmdBar As CommandBar
    Dim ctrl As CommandBarButton
    
    ' Óäàëÿåì ñòàðóþ ïàíåëü åñëè åñòü
    On Error Resume Next
    Application.CommandBars("IconViewer").Delete
    On Error GoTo 0
    
    ' Ñîçäàåì âðåìåííóþ ïàíåëü èíñòðóìåíòîâ
    Set cmdBar = Application.CommandBars.Add(name:="IconViewer", Temporary:=True)
    cmdBar.Visible = True
    cmdBar.Position = msoBarFloating
    
    ' Äîáàâëÿåì êíîïêè ñ èêîíêàìè
    For i = 1 To 2000 ' Ìîæíî óâåëè÷èòü äèàïàçîí
        On Error Resume Next
        Set ctrl = cmdBar.Controls.Add(Type:=msoControlButton)
        ctrl.FaceId = i
        ctrl.TooltipText = "ID: " & i
        If Err.Number <> 0 Then
            ' Ïðîïóñêàåì íåñóùåñòâóþùèå ID
            Err.Clear
            ctrl.Delete
        End If
        On Error GoTo 0
    Next i
End Sub
```

## Черновые заметки

