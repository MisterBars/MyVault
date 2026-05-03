---
type: module
status: done
done_date: 2026-05-03
project: "[[Учёт ВВТ]]"
skill: vba
tags:
  - module
  - skill/vba
reward_xp: 50
---
# Модуль

## Назначение
- Кратко, за что отвечает модуль, какие задачи решает.

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

// будем искать вызовы более аккуратно:
// 1) Call Name ...
// 2) Name(...)
// 3) Name <что-то>, но не Name =, не Dim Name, не Set Name =
const reCallPattern = /\b(?:Call\s+)?([A-Za-z_][A-Za-z0-9_]*)\b/g;

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

    // Не считать строки, где имя функции слева от "=":
    //   FuncName = ...
    //   Set obj = ...
    //   Dim FuncName As ...
    // Обработаем это внутри цикла по совпадениям.

    let m;
    while ((m = reCallPattern.exec(line)) !== null) {
      const calledName = m[1];

      // Позиция найденного имени в строке
      const idx = m.index;

      // Левая часть строки до имени
      const before = line.slice(0, idx);
      const after = line.slice(idx + calledName.length);

      const beforeTrim = before.trim();
      const afterTrim = after.trimStart();

      // 1) Если это присваивание результата функции: "FuncName = ..."
      //    — имя стоит в начале строки / после пробелов, а сразу после него "="
      const isAssignmentResult =
        beforeTrim === "" && afterTrim.startsWith("=");

      if (isAssignmentResult) {
        // Это возврат из функции, НЕ вызов
        continue;
      }

      // 2) Если это объявление переменной: "Dim FuncName As ..."
      if (/^\s*Dim\s+$/i.test(before) || /^\s*Dim\s+/i.test(beforeTrim)) {
        continue;
      }

      // 3) Если это левая часть Set: "Set obj = ..."
      //    — нас интересуют вызовы, а не имя слева от Set/=
      if (/^\s*Set\s+$/i.test(before) || /^\s*Set\s+/i.test(beforeTrim)) {
        continue;
      }

      // 4) Если после имени нет "(", нет пробела + аргументов, и нет "Call",
      //    можно попасть в кучу ложных срабатываний. Но:
      //    - уже отсекли очевидные присваивания и Dim/Set.
      //    - оставим это как потенциальный вызов (вызов без скобок: Name arg1, arg2).
      //    При желании можно ещё проверить, что после имени не конец строки и не оператор.

      const targets = procIndex[calledName];
      if (!targets) continue;

      for (const t of targets) {
        // не считаем самовызов внутри того же модуля той же процедуры
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
' @role: **какое место она занимает в системе**
' @todo: **заметка по процедуре/функции**


Option Explicit

Public Type NomenclatureInfo
    nomenclatureID As Long
    nomenclatureTypeID As Long
    NomenclatureTypeName As String
    nomenclatureCode As String
    nomenclatureName As String
    description As String
End Type

Private Const TBL_NOMS As String = "Nomenclatures"
Private Const TBL_NOM_TYPES As String = "NomenclatureTypes"
Private Const TBL_PRODUCTS As String = "Products"

Private Const FLD_ID As String = "NomenclatureID"
Private Const FLD_TYPE_ID As String = "NomenclatureTypeID"
Private Const FLD_CODE As String = "NomenclatureCode"
Private Const FLD_NAME As String = "NomenclatureName"
Private Const FLD_DESC As String = "Description"

Private Sub ValidateNomenclatureInput(ByVal nomenclatureTypeID As Long, ByVal nomenclatureCode As String, ByVal nomenclatureName As String)
' @desc: Проверяет правильность ввода номенклатуры
' @role: Validation
' @todo: --
    nomenclatureCode = Trim$(nomenclatureCode)
    nomenclatureName = Trim$(nomenclatureName)
    Dim message As String
    message = Empty
    If nomenclatureTypeID <= 0 Then
        message = message + "Не выбран тип номенклатуры." + vbCrLf
    End If

    If LenB(nomenclatureCode) = 0 Then
        message = message + "Не заполнен код номенклатуры." + vbCrLf
    End If

    If Len(nomenclatureCode) > 50 Then
        message = message + "Код номенклатуры не должен быть длиннее 50 символов." + vbCrLf
    End If

    If Len(nomenclatureName) > 255 Then
        message = message + "Наименование номенклатуры не должно быть длиннее 255 символов." + vbCrLf
    End If
    If message <> Empty Then ShowWarning message
End Sub

Public Function GetNomenclatureById(ByVal nomenclatureID As Long) As NomenclatureInfo
' @desc: Получает номенклатуру по её ID
' @role: Query.Read
' @todo: --
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim info As NomenclatureInfo

    If nomenclatureID <= 0 Then Exit Function

    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset( _
        "SELECT N.NomenclatureID, N.NomenclatureTypeID, T.TypeName, N.NomenclatureCode, N.NomenclatureName, N.Description " & _
        "FROM Nomenclatures AS N " & _
        "INNER JOIN NomenclatureTypes AS T ON N.NomenclatureTypeID = T.NomenclatureTypeID " & _
        "WHERE N.NomenclatureID = " & nomenclatureID, _
        dbOpenSnapshot)

    If Not rs.EOF Then
        info.nomenclatureID = NzLng(rs.Fields("NomenclatureID").Value)
        info.nomenclatureTypeID = NzLng(rs.Fields("NomenclatureTypeID").Value)
        info.NomenclatureTypeName = NzStr(rs.Fields("TypeName").Value)
        info.nomenclatureCode = NzStr(rs.Fields("NomenclatureCode").Value)
        info.nomenclatureName = NzStr(rs.Fields("NomenclatureName").Value)
        info.description = NzStr(rs.Fields("Description").Value)
    End If

    rs.Close
    Set rs = Nothing
    Set db = Nothing

    GetNomenclatureById = info
End Function

Public Function GetNomenclatureIdByCode(ByVal nomenclatureCode As String) As Long
' @desc: Получает ID номенклатуры по её коду
' @role: Query.Read
' @todo: --
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    
    On Error GoTo EH
    
    If nomenclatureCode <= 0 Then Exit Function

    Set db = OpenCurrentDb()
    Set rs = db.OpenRecordset( _
        "SELECT NomenclatureID " & _
        "FROM Nomenclatures " & _
        "WHERE NomenclatureCode = " & Q(nomenclatureCode), _
        dbOpenSnapshot)

    If Not rs.EOF Then
        GetNomenclatureIdByCode = NzLng(rs.Fields(0).Value)
    End If

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Exit Function
EH:
    On Error Resume Next
    ShowError "GetNomenclatureIdByCode", Err.Number, Err.description
    Resume CleanExit
End Function

Public Function NomenclatureExists( _
    ByVal nomenclatureTypeID As Long, _
    ByVal nomenclatureCode As String, _
    Optional ByVal excludeID As Long = 0, _
    Optional ByVal db As DAO.Database = Nothing) As Boolean
' @desc: Проверяет существание номенклатуры по её ID и коду
' @role: Query.Read
' @todo: --

    Dim ownDb As Boolean
    Dim rs As DAO.Recordset
    Dim sql As String

    nomenclatureCode = Trim$(nomenclatureCode)
    If nomenclatureTypeID <= 0 Or LenB(nomenclatureCode) = 0 Then Exit Function

    If db Is Nothing Then
        Set db = OpenCurrentDb()
        ownDb = True
    End If

    sql = "SELECT NomenclatureID " & _
          "FROM Nomenclatures " & _
          "WHERE NomenclatureTypeID = " & nomenclatureTypeID & _
          " AND NomenclatureCode = " & Q(nomenclatureCode)

    If excludeID > 0 Then
        sql = sql & " AND NomenclatureID <> " & excludeID
    End If

    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)
    NomenclatureExists = Not rs.EOF

    rs.Close
    Set rs = Nothing
    If ownDb Then Set db = Nothing
End Function

Public Function CreateNomenclature( _
    ByVal nomenclatureTypeID As Long, _
    ByVal nomenclatureCode As String, _
    ByVal nomenclatureName As String, _
    ByVal description As String, _
    ByVal changedByUserId As Long) As Long
' @desc: Безопасное создание номенклатуры
' @role: Query.Write
' @todo: --

    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim newID As Long

    nomenclatureCode = Trim$(nomenclatureCode)
    nomenclatureName = Trim$(nomenclatureName)
    description = Trim$(description)

    ValidateNomenclatureInput nomenclatureTypeID, nomenclatureCode, nomenclatureName

    If GetNomenclatureTypeById(nomenclatureTypeID).nomenclatureTypeID = 0 Then
        ShowWarning "Указанный тип номенклатуры не найден."
        GoTo CleanExit
    End If

    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb()

    On Error GoTo EH
    ws.BeginTrans

    If NomenclatureExists(nomenclatureTypeID, nomenclatureCode, 0, db) Then
        ShowWarning "Номенклатура с таким кодом уже существует для выбранного типа."
        GoTo CleanExit
    End If

    Set rs = db.OpenRecordset(TBL_NOMS, dbOpenDynaset, dbAppendOnly)

    rs.AddNew
    rs.Fields(FLD_TYPE_ID).Value = nomenclatureTypeID
    rs.Fields(FLD_CODE).Value = nomenclatureCode

    If LenB(nomenclatureName) > 0 Then
        rs.Fields(FLD_NAME).Value = Left$(nomenclatureName, 255)
    Else
        rs.Fields(FLD_NAME).Value = Null
    End If

    If LenB(description) > 0 Then
        rs.Fields(FLD_DESC).Value = description
    Else
        rs.Fields(FLD_DESC).Value = Null
    End If

    rs.Update
    rs.Bookmark = rs.LastModified
    newID = NzLng(rs.Fields(FLD_ID).Value)

    rs.Close
    Set rs = Nothing

    WriteAuditEvent db, TBL_NOMS, newID, FLD_TYPE_ID, vbNullString, CStr(nomenclatureTypeID), "INSERT", "NomenclatureCreate", changedByUserId, Null
    WriteAuditEvent db, TBL_NOMS, newID, FLD_CODE, vbNullString, nomenclatureCode, "INSERT", "NomenclatureCreate", changedByUserId, Null
    WriteAuditEvent db, TBL_NOMS, newID, FLD_NAME, vbNullString, nomenclatureName, "INSERT", "NomenclatureCreate", changedByUserId, Null
    WriteAuditEvent db, TBL_NOMS, newID, FLD_DESC, vbNullString, description, "INSERT", "NomenclatureCreate", changedByUserId, Null

    ws.CommitTrans
    CreateNomenclature = newID

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Function

EH:
    On Error Resume Next
    ws.Rollback
    ShowError "CreateNomenclature", Err.Number, , Err.description
    Resume CleanExit
End Function

Public Sub UpdateNomenclature( _
    ByVal nomenclatureID As Long, _
    ByVal newNomenclatureTypeID As Long, _
    ByVal newNomenclatureCode As String, _
    ByVal newNomenclatureName As String, _
    ByVal newDescription As String, _
    ByVal changedByUserId As Long)
' @desc: Безопасное обновление номенклатуры
' @role: Query.Update
' @todo: --
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim oldInfo As NomenclatureInfo

    If nomenclatureID <= 0 Then
        ShowWarning "Некорректный NomenclatureID."
        GoTo CleanExit
    End If

    newNomenclatureCode = Trim$(newNomenclatureCode)
    newNomenclatureName = Trim$(newNomenclatureName)
    newDescription = Trim$(newDescription)

    ValidateNomenclatureInput newNomenclatureTypeID, newNomenclatureCode, newNomenclatureName

    oldInfo = GetNomenclatureById(nomenclatureID)
    If oldInfo.nomenclatureID = 0 Then
        ShowWarning "Номенклатура не найдена."
        GoTo CleanExit
    End If

    If GetNomenclatureTypeById(newNomenclatureTypeID).nomenclatureTypeID = 0 Then
        ShowWarning "Указанный тип номенклатуры не найден."
        GoTo CleanExit
    End If

    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb()

    On Error GoTo EH
    ws.BeginTrans

    If oldInfo.nomenclatureTypeID <> newNomenclatureTypeID _
       Or StrComp(oldInfo.nomenclatureCode, newNomenclatureCode, vbTextCompare) <> 0 Then
        If NomenclatureExists(newNomenclatureTypeID, newNomenclatureCode, nomenclatureID, db) Then
            ShowWarning "Номенклатура с таким кодом уже существует для выбранного типа."
            GoTo CleanExit
        End If
    End If

    Set rs = db.OpenRecordset( _
        "SELECT * FROM Nomenclatures WHERE NomenclatureID = " & nomenclatureID, _
        dbOpenDynaset)

    If rs.EOF Then
        ShowWarning "Номенклатура не найдена."
        GoTo CleanExit
    End If

    rs.Edit
    rs.Fields(FLD_TYPE_ID).Value = newNomenclatureTypeID
    rs.Fields(FLD_CODE).Value = newNomenclatureCode

    If LenB(newNomenclatureName) > 0 Then
        rs.Fields(FLD_NAME).Value = Left$(newNomenclatureName, 255)
    Else
        rs.Fields(FLD_NAME).Value = Null
    End If

    If LenB(newDescription) > 0 Then
        rs.Fields(FLD_DESC).Value = newDescription
    Else
        rs.Fields(FLD_DESC).Value = Null
    End If

    rs.Update
    rs.Close
    Set rs = Nothing

    If oldInfo.nomenclatureTypeID <> newNomenclatureTypeID Then
        WriteAuditEvent db, TBL_NOMS, nomenclatureID, FLD_TYPE_ID, CStr(oldInfo.nomenclatureTypeID), CStr(newNomenclatureTypeID), "UPDATE", "NomenclatureUpdate", changedByUserId, Null
    End If

    If StrComp(oldInfo.nomenclatureCode, newNomenclatureCode, vbBinaryCompare) <> 0 Then
        WriteAuditEvent db, TBL_NOMS, nomenclatureID, FLD_CODE, oldInfo.nomenclatureCode, newNomenclatureCode, "UPDATE", "NomenclatureUpdate", changedByUserId, Null
    End If

    If NzStr(oldInfo.nomenclatureName) <> NzStr(newNomenclatureName) Then
        WriteAuditEvent db, TBL_NOMS, nomenclatureID, FLD_NAME, oldInfo.nomenclatureName, newNomenclatureName, "UPDATE", "NomenclatureUpdate", changedByUserId, Null
    End If

    If NzStr(oldInfo.description) <> NzStr(newDescription) Then
        WriteAuditEvent db, TBL_NOMS, nomenclatureID, FLD_DESC, oldInfo.description, newDescription, "UPDATE", "NomenclatureUpdate", changedByUserId, Null
    End If

    ws.CommitTrans

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Sub

EH:
    On Error Resume Next
    ws.Rollback
    ShowError "UpdateNomenclature", Err.Number, , Err.description
    Resume CleanExit
End Sub

Public Sub DeleteNomenclatureSafe(ByVal nomenclatureID As Long, ByVal changedByUserId As Long)
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim info As NomenclatureInfo
    Dim cnt As Long

    If nomenclatureID <= 0 Then
        ShowWarning "Некорректный NomenclatureID."
        GoTo CleanExit
    End If

    info = GetNomenclatureById(nomenclatureID)
    If info.nomenclatureID = 0 Then
        ShowWarning "Номенклатура не найдена."
        GoTo CleanExit
    End If

    Set ws = DBEngine.Workspaces(0)
    Set db = OpenCurrentDb()

    Set rs = db.OpenRecordset( _
        "SELECT COUNT(*) AS Cnt FROM Products WHERE NomenclatureID = " & nomenclatureID & " AND IsDeleted = False", _
        dbOpenSnapshot)

    If Not rs.EOF Then cnt = NzLng(rs.Fields(0).Value)
    rs.Close
    Set rs = Nothing

    If cnt > 0 Then
        ShowWarning "Номенклатуру нельзя удалить, так как она используется в изделиях. Количество связанных записей: " & cnt & "."
        GoTo CleanExit
    End If

    On Error GoTo EH
    ws.BeginTrans

    db.Execute "DELETE FROM Nomenclatures WHERE NomenclatureID = " & nomenclatureID, dbFailOnError

    WriteAuditEvent db, TBL_NOMS, nomenclatureID, FLD_CODE, info.nomenclatureCode, "DELETED", "DELETE", "NomenclatureDelete", changedByUserId, Null

    ws.CommitTrans

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Sub

EH:
    On Error Resume Next
    ws.Rollback
    ShowError "DeleteNomenclatureSafe", Err.Number, , Err.description
    Resume CleanExit
End Sub

Public Function GetAllNomenclatures(Optional ByVal nomenclatureTypeID As Long = 0) As DAO.Recordset
    Dim db As DAO.Database
    Dim sql As String

    Set db = OpenCurrentDb()

    sql = "SELECT N.NomenclatureID, N.NomenclatureTypeID, T.TypeName, N.NomenclatureCode, N.NomenclatureName, N.Description " & _
          "FROM Nomenclatures AS N " & _
          "INNER JOIN NomenclatureTypes AS T ON N.NomenclatureTypeID = T.NomenclatureTypeID"

    If nomenclatureTypeID > 0 Then
        sql = sql & " WHERE N.NomenclatureTypeID = " & nomenclatureTypeID
    End If

    sql = sql & " ORDER BY T.TypeName, N.NomenclatureCode, N.NomenclatureName"

    Set GetAllNomenclatures = db.OpenRecordset(sql, dbOpenSnapshot)
End Function
```

## Черновые заметки

