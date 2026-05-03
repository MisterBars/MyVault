---
type: form
status: in-progress
done_date:
project: "[[Учёт ВВТ]]"
skill: vba
tags:
  - form
  - skill/vba
reward_xp: 50
---

# Форма
## Назначение формы
- Кратко: для чего форма нужна, кто её пользователь (роль).
## Элементы интерфейса
- Поля ввода (textbox, combobox, checkbox) и их смысл.
- Кнопки и действия.
- Таблицы/списки и что они показывают.
## Поведение

- Что происходит при открытии формы.
- Что происходит при нажатии основных кнопок.
- Валидация данных, сообщения об ошибках.
## Состояния и сценарии
- Состояние “новая запись”.
- Состояние “редактирование”.
- Состояние “просмотр”.
## Связанные задачи
```dataview
TABLE status as "Статус", task_type as "Тип", deadline as "Срок"
FROM ""
WHERE type = "task" AND project = this.project AND contains(file.outlinks, this.file.link)
SORT deadline ASC
```

## Взаимосвязи (исходящие вызовы)
```dataviewjs
const TYPES = ['module', 'form', 'class'];

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

// Диагностика — сохраняем, но не показываем
const debugModulesCount = allPages.length;

async function getVbaBlocks(path) {
  const text = await dv.io.load(path);
  if (!text) return [];

  const blocks = [];
  let inBlock = false;
  let currentBlock = [];

  for (const line of text.split('\n')) {
    const trimmed = line.trim();

    if (!inBlock && trimmed.toLowerCase().startsWith('```vba')) {
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

const reProcDecl = /^\s*(?:(Public|Private)\s+)?(?:Static\s+)?(Sub|Function)\s+([A-Za-z0-9_]+)/i;

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

// Диагностика — сохраняем, но не показываем
const debugProcNames = Object.keys(procIndex);
const debugProcCount = debugProcNames.length;

const currentBlocks = await getVbaBlocks(current.file.path);

// Вызовы: Foo(...), Call Bar(...)
const reCall = /\b(?:Call\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?=\()/g;

const callMap = new Map();

for (const block of currentBlocks) {
  const lines = block.split('\n');
  let currentProc = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed.startsWith("'")) continue;

    const declMatch = line.match(reProcDecl);
    if (declMatch) {
      currentProc = declMatch[3];
      continue;
    }

    if (!currentProc) continue;

    let m;
    while ((m = reCall.exec(line)) !== null) {
      const calledName = m[1];
      const targets = procIndex[calledName];
      if (!targets) continue;

      for (const t of targets) {
        if (t.modulePath === current.file.path && calledName === currentProc) continue;

        const key = `${currentProc}||${t.modulePath}`;
        if (!callMap.has(key)) {
          callMap.set(key, {
            fromProc: currentProc,
            toModuleLink: t.moduleLink,
            calledNames: new Set()
          });
        }

        callMap.get(key).calledNames.add(calledName);
      }
    }
  }
}

const rows = [];

for (const entry of callMap.values()) {
  const calledList = Array.from(entry.calledNames).sort().join(", ");
  rows.push([
    entry.fromProc,
    entry.toModuleLink,
    calledList
  ]);
}

if (rows.length === 0) {
  dv.paragraph('Исходящих вызовов других модулей/форм/классов в рамках этого проекта не найдено.');
} else {
  dv.table(
    ['Процедура', 'Куда (модуль)', 'Что вызывает'],
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
' @role: **какое место она занимает в системе(Audit/UI/Navigation и т.д.)**
' @todo: **заметка по процедуре/функции**

Option Explicit

Private m_ButtonHandlers As Collection
Private m_DynamicControlNames As Collection

Private Sub ClearDynamicMenu()
    Dim i As Long
    Dim ctrlName As String
    
    On Error Resume Next
    
    If Not m_DynamicControlNames Is Nothing Then
        For i = m_DynamicControlNames.Count To 1 Step -1
            ctrlName = CStr(m_DynamicControlNames(i))
            Me.Controls.Remove ctrlName
        Next i
    End If
    
    Set m_DynamicControlNames = New Collection
    Set m_ButtonHandlers = New Collection
End Sub

Private Sub AddMenuButton(ByVal captionText As String, _
                          ByVal actionKey As String, _
                          ByVal leftPos As Single, _
                          ByVal topPos As Single, _
                          ByVal btnWidth As Single, _
                          ByVal btnHeight As Single, _
                          ByVal btnColor As Long)
                          
    Dim Btn As MSForms.CommandButton
    Dim h As CMenuButtonHandler
    Dim ctrlName As String
    
    ctrlName = "dyBtn_" & Replace(actionKey, " ", "_") & "_" & CStr(Me.Controls.Count + 1)
    
    Set Btn = Me.Controls.Add("Forms.CommandButton.1", ctrlName, True)
    
    With Btn
        .Caption = captionText
        .Left = leftPos
        .Top = topPos
        .Width = btnWidth
        .Height = btnHeight
        .BackColor = btnColor
        .ForeColor = vbWhite
        .TakeFocusOnClick = False
        .Font.Size = 12
        .Font.name = "Calibri"
        .Font.Bold = True
    End With
    
    Set h = New CMenuButtonHandler
    Set h.Btn = Btn
    h.actionKey = actionKey
    
    m_DynamicControlNames.Add ctrlName
    m_ButtonHandlers.Add h
End Sub

Private Sub BuildRoleMenu()
    Const MARGIN_LEFT As Single = 12
    Const MARGIN_TOP As Single = 12
    Const BTN_WIDTH As Single = 180
    Const BTN_HEIGHT As Single = 24
    Const BTN_GAP As Single = 6
    Const FORM_EXTRA_H As Single = 36
    Const FORM_EXTRA_W As Single = 26
    
    Dim rInfo As RoleInfo
    Dim items As Variant
    Dim i As Long
    Dim topPos As Single
    Dim visibleCount As Long
    
    On Error GoTo EH
    
    ClearDynamicMenu
    
    rInfo = GetCurrentRoleInfo
    items = GetMenuItems
    
    Me.Caption = GetMenuCaptionByRole(rInfo)
    topPos = MARGIN_TOP
    
    For i = LBound(items) To UBound(items)
        If HasMenuPermission(rInfo, CStr(items(i)(2))) Then
            AddMenuButton CStr(items(i)(0)), CStr(items(i)(1)), MARGIN_LEFT, topPos, BTN_WIDTH, BTN_HEIGHT, IIf(CStr(items(i)(1)) = "logout", &H8080FF, &H8000000D)
            topPos = topPos + BTN_HEIGHT + BTN_GAP
            visibleCount = visibleCount + 1
        End If
    Next i
    
    If visibleCount = 0 Then
        AddMenuButton "Выход из аккаунта", "logout", MARGIN_LEFT, topPos, BTN_WIDTH, BTN_HEIGHT, "&H008080FF&"
        topPos = topPos + BTN_HEIGHT + BTN_GAP
    End If
    
    Me.Width = BTN_WIDTH + MARGIN_LEFT + FORM_EXTRA_W
    Me.Height = topPos + FORM_EXTRA_H
    
    Exit Sub
EH:
    ShowError "F_Menu.BuildRoleMenu", Err.Number, Err.description
End Sub

Private Function ControlExists(ByVal ctrlName As String) As Boolean
    Dim ctrl As Object
    On Error Resume Next
    Set ctrl = Me.Controls(ctrlName)
    ControlExists = Not ctrl Is Nothing
    Set ctrl = Nothing
    On Error GoTo 0
End Function

Private Sub UserForm_Initialize()
    On Error GoTo ErrRS
    Set m_DynamicControlNames = New Collection
    Set m_ButtonHandlers = New Collection
    
    BuildRoleMenu
    Exit Sub
ErrRS:
    ShowError "F_Menu.UserForm_Initialize", Err.Number, Err.description
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    CloseChildForms Me
End Sub

Private Sub CloseChildForms(ByVal mainFrm As F_Menu)
    Dim i As Long
    
    For i = VBA.UserForms.Count - 1 To 0 Step -1
        If Not VBA.UserForms(i) Is mainFrm Then Unload VBA.UserForms(i)
    Next i
End Sub

```

## Черновые заметки