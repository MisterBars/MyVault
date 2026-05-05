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

| Форма | Тип элемента | Имя элемента | Caption / Text |
| --- | --- | --- | --- |
| F_ChangeDB | CommandButton | Btn_Cansel | Отмена |
| F_ChangeDB | CommandButton | Btn_Save | Сохранить |
| F_ChangeDB | CommandButton | Btn_SelLoc | Выбрать |
| F_ChangeDB | CommandButton | Btn_SelLocDoc | Выбрать |
| F_ChangeDB | CommandButton | Btn_SelServ | Выбрать |
| F_ChangeDB | CommandButton | Btn_SelServDoc | Выбрать |
| F_ChangeDB | Label | Label1 | База даных |
| F_ChangeDB | Label | Label2 | База даных |
| F_ChangeDB | Label | Label3 | Архив документов |
| F_ChangeDB | Label | Label4 | Архив документов |
| F_ChangeDB | Label | Lbl_zglv | Выбор базы данных |
| F_ChangeDB | OptionButton | OB_Local | Локальная |
| F_ChangeDB | OptionButton | OB_Server | Серверная |
| F_ChangeDB | TextBox | TB_Local |  |
| F_ChangeDB | TextBox | TB_LocDoc |  |
| F_ChangeDB | TextBox | TB_ServDoc |  |
| F_ChangeDB | TextBox | TB_Server |  |

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

Private Const msoFileDialogFilePicker As Long = 3

Private Sub Btn_Cansel_Click()
' @desc: Закрывает форму изменения путей к базе и документам без сохранения изменений.
' @role: UI
' @todo: Привести имя кнопки/процедуры к Btn_Cancel_Click для единообразия.
    Unload Me
End Sub

Private Sub Btn_Save_Click()
' @desc: Сохраняет выбранные пути и режим Local/Server в ModSettings через ChangeConstantInModSettings и сохраняет книгу.
' @role: Config
' @todo: Добавить валидацию путей перед сохранением и сообщение об успешном завершении через ShowInfo.
    If OB_Local.Value = True Then
        Call ChangeConstantInModSettings("SRV_LOC", "False")
    Else
        Call ChangeConstantInModSettings("SRV_LOC", "True")
    End If
    Call ChangeConstantInModSettings("LOCAL_BASE", TB_Local.Text)
    Call ChangeConstantInModSettings("LOCAL_DOC", TB_LocDoc.Text)
    Call ChangeConstantInModSettings("SERVER_BASE", TB_Server.Text)
    Call ChangeConstantInModSettings("SERVER_DOC", TB_ServDoc.Text)
    ThisWorkbook.Save
End Sub

Private Sub Btn_SelLoc_Click()
' @desc: Открывает выбор файла локальной базы и подставляет путь в поле TB_Local.
' @role: UI
' @todo: Добавить проверку, что пользователь действительно выбрал .accdb.
    TB_Local.Text = SelectBase()
End Sub

Private Sub Btn_SelLocDoc_Click()
' @desc: Открывает выбор папки локальных документов и подставляет её путь в TB_LocDoc.
' @role: UI
' @todo: Нормализовать добавление "\" в конце пути через отдельный helper.
    Dim DocPath As String
    
    DocPath = SelectFolderPath(Replace(LOCAL_BASE, "vvt_db.accdb", ""))
    
    If DocPath <> "" Then
        TB_LocDoc.Text = DocPath & "\"
    End If
End Sub

Private Sub Btn_SelServ_Click()
' @desc: Открывает выбор файла серверной базы и подставляет путь в поле TB_Server.
' @role: UI
' @todo: Добавить проверку доступности сетевого пути до сохранения.
    TB_Server.Text = SelectBase()
End Sub

Private Sub Btn_SelServDoc_Click()
' @desc: Открывает выбор папки серверных документов и подставляет её путь в TB_ServDoc.
' @role: UI
' @todo: Аналогично локальному пути, лучше вынести добавление "\" в отдельную функцию.
    Dim DocPath As String
    
    DocPath = SelectFolderPath(Replace(SERVER_BASE, "vvt_db.accdb", ""))
    
    If DocPath <> "" Then
        TB_ServDoc.Text = DocPath & "\"
    End If
End Sub

Private Sub UserForm_Initialize()
' @desc: Инициализирует форму настройки путей, подставляет текущие значения ModSettings и отмечает активный режим Local/Server.
' @role: UI
' @todo: После инициализации можно отключать неактуальные поля в зависимости от выбранного режима.
    On Error GoTo EH

    If CBool(SRV_LOC) Then
        OB_Server.Value = True
    Else
        OB_Local.Value = True
    End If

    TB_Local.Text = CStr(LOCAL_BASE)
    TB_LocDoc.Text = CStr(LOCAL_DOC)
    TB_Server.Text = CStr(SERVER_BASE)
    TB_ServDoc.Text = CStr(SERVER_DOC)
    Exit Sub

EH:
    ShowError "F_ChangeDB.UserForm_Initialize", Err.Number, Err.description
End Sub

Private Function SelectBase() As String
' @desc: Показывает диалог выбора файла Access и возвращает путь к выбранной базе данных.
' @role: UI
' @todo: Добавить On Error GoTo EH и ShowError на случай проблем с FileDialog.
    Dim fd As Object
    Dim res As Long

    Set fd = Application.FileDialog(msoFileDialogFilePicker)

    With fd
        .Title = "Выберите файл"
        .AllowMultiSelect = False
        .Filters.Clear
        .Filters.Add "База Access", "*.accdb"
        .Filters.Add "Все файлы", "*.*"

        res = .Show
        If res <> 0 Then
            SelectBase = .SelectedItems(1)
        Else
            SelectBase = vbNullString
        End If
    End With

    Set fd = Nothing
End Function

Function SelectFolderPath(Optional ByVal InitialPath As String = "") As String
' @desc: Показывает диалог выбора папки и возвращает путь к каталогу документов.
' @role: UI
' @todo: Добавить обработчик ошибок и Set fd = Nothing в конце процедуры.
    Dim fd As FileDialog
    Dim res As Long

    Set fd = Application.FileDialog(msoFileDialogFolderPicker)

    With fd
        .Title = "Выберите папку с документами"
        .AllowMultiSelect = False
        
        If Len(InitialPath) > 0 Then
            .InitialFileName = InitialPath
        End If
        
        res = .Show
        
        If res <> 0 Then
            SelectFolderPath = .SelectedItems(1)
        Else
            SelectFolderPath = vbNullString
        End If
    End With
End Function
```

## Черновые заметки