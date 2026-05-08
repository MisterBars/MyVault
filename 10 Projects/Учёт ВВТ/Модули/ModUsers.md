---
type: module
status: done
done_date: 2026-05-02
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

Public Type UserInfo
    userID As Long
    login As String
    fullName As String
    roleID As Long
    PasswordHash As String
    Salt As String
    isActive As Boolean
    LastLogin As Variant
    CreatedAt As Variant
    createdByUserID As Long
End Type

' =========================
' Публичные API
' =========================

Public Function CreateUser( _
    ByVal userLogin As String, _
    ByVal userFullName As String, _
    ByVal roleID As Long, _
    ByVal plainPassword As String, _
    ByVal changedByUserId As Long, _
    Optional ByVal isActive As Boolean = True, _
    Optional ByVal createdByUserID As Variant) As Long
' @desc: Создаёт пользователя с логином, ФИО, ролью и паролем в транзакции и пишет аудит.
' @role: Users
' @todo: Добавить проверку результата ValidateUserInput и выйти при ошибках валидации.
    
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sSalt As String
    Dim sCipher As String
    Dim newId As Long

    ValidateUserInput userLogin, userFullName, roleID, plainPassword

    Set ws = OpenWorkspace
    Set db = OpenCurrentDb

    On Error GoTo EH
    ws.BeginTrans

    If UserExists(userLogin, db) Then
        ShowWarning "Пользователь с логином '" & userLogin & "' уже существует."
        GoTo CleanExit
    End If

    sSalt = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.GenerateSalt")
    Dim encoded As String
    encoded = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.EncodeForData", plainPassword)
    sCipher = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.EncryptString", encoded, sSalt)

    Set rs = db.OpenRecordset("Users", dbOpenDynaset, dbAppendOnly)
    rs.AddNew
    rs.Fields("Login").Value = Trim$(userLogin)
    rs.Fields("FullName").Value = Trim$(userFullName)
    rs.Fields("RoleID").Value = roleID
    rs.Fields("PasswordHash").Value = sCipher
    rs.Fields("Salt").Value = sSalt
    rs.Fields("IsActive").Value = isActive
    rs.Fields("CreatedAt").Value = Now
    If Not IsMissingOrNull(createdByUserID) Then
        rs.Fields("CreatedByUserID").Value = CLng(createdByUserID)
    ElseIf changedByUserId > 0 Then
        rs.Fields("CreatedByUserID").Value = changedByUserId
    End If
    rs.Update
    rs.Bookmark = rs.LastModified
    newId = NzLng(rs.Fields("UserID").Value)
    rs.Close
    Set rs = Nothing

    WriteAuditEvent db, "Users", newId, "Login", vbNullString, Trim$(userLogin), "INSERT", "UserCreate", changedByUserId, Null
    WriteAuditEvent db, "Users", newId, "RoleID", vbNullString, CStr(roleID), "INSERT", "UserCreate", changedByUserId, Null
    WriteAuditEvent db, "Users", newId, "IsActive", vbNullString, BoolToText(isActive), "INSERT", "UserCreate", changedByUserId, Null
    WriteAuditEvent db, "Users", newId, "PasswordHash", vbNullString, "[CHANGED]", "INSERT", "UserCreate", changedByUserId, Null
    WriteAuditEvent db, "Users", newId, "Salt", vbNullString, "[CHANGED]", "INSERT", "UserCreate", changedByUserId, Null

    ws.CommitTrans
    CreateUser = newId

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Function
EH:
    On Error Resume Next
    ws.RollBack
    ShowError "CreateUser", Err.Number, Err.description
    Resume CleanExit
End Function

Public Function CreateUserWithRoleCheck( _
    ByVal currentUserId As Long, _
    ByVal userLogin As String, _
    ByVal userFullName As String, _
    ByVal roleID As Long, _
    ByVal plainPassword As String, _
    Optional ByVal isActive As Boolean = True) As Long
' @desc: Создаёт пользователя только если текущий пользователь имеет право управлять целевой ролью.
' @role: Users
' @todo: Проверить, что CreateUser корректно обрабатывает ошибки валидации и возврат 0.

    If Not CanManageRole(currentUserId, roleID) Then
        ShowWarning "Недостаточно прав для создания пользователя с этой ролью."
        Exit Function
    End If

    CreateUserWithRoleCheck = CreateUser( _
        userLogin:=userLogin, _
        userFullName:=userFullName, _
        roleID:=roleID, _
        plainPassword:=plainPassword, _
        changedByUserId:=currentUserId, _
        isActive:=isActive, _
        createdByUserID:=currentUserId)
End Function

Public Function EnsureDefaultAdmin(Optional ByVal changedByUserId As Long = 0) As Long
' @desc: Гарантирует наличие дефолтного администратора, создаёт его из настроек если не найден.
' @role: Users
' @todo: Проверить корректность получения adminRoleId (сейчас параметр для GetRoleIdByName выглядит сомнительно).
    Dim adminRoleId As Long
    Dim existingUserId As Long

    adminRoleId = GetRoleIdByName(Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModSettings.GetConstant", "DEFAULT_ADMIN_LOGIN"))

    existingUserId = GetUserIdByLogin(Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModSettings.GetConstant", "DEFAULT_ADMIN_LOGIN"))
    If existingUserId > 0 Then
        EnsureDefaultAdmin = existingUserId
        Exit Function
    End If
    Dim login, Name, psw  As String
    login = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModSettings.GetConstant", "DEFAULT_ADMIN_LOGIN")
    Name = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModSettings.GetConstant", "DEFAULT_ADMIN_FULLNAME")
    psw = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModSettings.GetConstant", "DEFAULT_ADMIN_PASSWORD")
    EnsureDefaultAdmin = CreateUser( _
        userLogin:=login, _
        userFullName:=Name, _
        roleID:=adminRoleId, _
        plainPassword:=psw, _
        changedByUserId:=changedByUserId, _
        isActive:=True, _
        createdByUserID:=Null)
End Function

Public Sub UpdateUser( _
    ByVal userID As Long, _
    ByVal newLogin As String, _
    ByVal newFullName As String, _
    ByVal newRoleID As Long, _
    ByVal changedByUserId As Long, _
    Optional ByVal newIsActive As Boolean = True)
' @desc: Обновляет логин, ФИО, роль и активность пользователя с валидацией и аудитом.
' @role: Users
' @todo: Вынести повторяющиеся проверки длины в отдельную функцию валидации.

    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim oldLogin As String
    Dim oldFullName As String
    Dim oldRoleID As Long
    Dim oldIsActive As Boolean
    Dim sql As String

    If userID <= 0 Then
        ShowWarning "Некорректный UserID."
         GoTo CleanExit
    End If
    If LenB(Trim$(newLogin)) = 0 Then
        ShowWarning "Пустой логин."
         GoTo CleanExit
    End If
    If Len(Trim$(newLogin)) > 50 Then
        ShowWarning "Логин длиннее 50 символов."
         GoTo CleanExit
    End If
    If LenB(Trim$(newFullName)) = 0 Then
        ShowWarning "Пустое ФИО."
         GoTo CleanExit
    End If
    If Len(Trim$(newFullName)) > 200 Then
        ShowWarning "ФИО длиннее 200 символов."
         GoTo CleanExit
    End If
    If newRoleID <= 0 Then
        ShowWarning "Некорректный RoleID."
         GoTo CleanExit
    End If

    If Not CanManageRole(changedByUserId, newRoleID) Then
        ShowWarning "Недостаточно прав для назначения данной роли."
        GoTo CleanExit
    End If

    Set ws = OpenWorkspace
    Set db = OpenCurrentDb

    On Error GoTo EH
    ws.BeginTrans

    Set rs = db.OpenRecordset( _
        "SELECT UserID, Login, FullName, RoleID, IsActive FROM Users WHERE UserID=" & userID, _
        dbOpenDynaset)

    If rs.EOF Then
        ShowWarning "Пользователь не найден."
        GoTo CleanExit
    End If
    
    oldLogin = NzStr(rs.Fields("Login").Value)
    oldFullName = NzStr(rs.Fields("FullName").Value)
    oldRoleID = NzLng(rs.Fields("RoleID").Value)
    oldIsActive = NzBool(rs.Fields("IsActive").Value, False)

    If StrComp(oldLogin, Trim$(newLogin), vbTextCompare) <> 0 Then
        sql = "SELECT UserID FROM Users WHERE Login=" & Q(Trim$(newLogin)) & " AND UserID<>" & userID
        Dim rsDup As DAO.Recordset
        Set rsDup = db.OpenRecordset(sql, dbOpenSnapshot)
        If Not rsDup.EOF Then
            rsDup.Close
            Set rsDup = Nothing
            ShowWarning "Пользователь с логином '" & Trim$(newLogin) & "' уже существует."
            GoTo CleanExit
        End If
        rsDup.Close
        Set rsDup = Nothing
    End If

    rs.Edit
    rs.Fields("Login").Value = Trim$(newLogin)
    rs.Fields("FullName").Value = Trim$(newFullName)
    rs.Fields("RoleID").Value = newRoleID
    rs.Fields("IsActive").Value = newIsActive
    rs.Update
    rs.Close
    Set rs = Nothing

    If StrComp(oldLogin, Trim$(newLogin), vbBinaryCompare) <> 0 Then
        WriteAuditEvent db, "Users", userID, "Login", oldLogin, Trim$(newLogin), "UPDATE", "UpdateUser", changedByUserId, Null
    End If

    If StrComp(oldFullName, Trim$(newFullName), vbBinaryCompare) <> 0 Then
        WriteAuditEvent db, "Users", userID, "FullName", oldFullName, Trim$(newFullName), "UPDATE", "UpdateUser", changedByUserId, Null
    End If

    If oldRoleID <> newRoleID Then
        WriteAuditEvent db, "Users", userID, "RoleID", CStr(oldRoleID), CStr(newRoleID), "UPDATE", "UpdateUser", changedByUserId, Null
    End If

    If oldIsActive <> newIsActive Then
        WriteAuditEvent db, "Users", userID, "IsActive", BoolToText(oldIsActive), BoolToText(newIsActive), "UPDATE", "UpdateUser", changedByUserId, Null
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
    ws.RollBack
    ShowError "UpdateUser", Err.Number, Err.description
    Resume CleanExit
End Sub

' =========================
' Удаление / мягкое удаление пользователей
' =========================

Private Function BuildDeletedLogin(ByVal oldLogin As String, ByVal userID As Long) As String
' @desc: Формирует уникальный логин для soft-delete в формате old_login_deleted_ID, обрезая до 50 символов.
' @role: Users
' @todo: Убедиться, что длина итоговой строки всегда укладывается в ограничение поля Login.
    BuildDeletedLogin = Left$(Trim$(oldLogin), 50 - Len("_deleted_") - Len(CStr(userID))) & "_deleted_" & CStr(userID)
End Function

Public Function HasRows(ByVal db As DAO.Database, ByVal sql As String) As Boolean
' @desc: Выполняет запрос и проверяет, вернул ли он хотя бы одну строку.
' @role: Helper
' @todo: Используется как универсальная проверка зависимостей, критично не забывать закрывать rs.
    Dim rs As DAO.Recordset

    On Error GoTo EH
    Set rs = db.OpenRecordset(sql, dbOpenSnapshot)

    HasRows = Not (rs.BOF And rs.EOF)

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Exit Function

EH:
    ShowError "HasRows", Err.Number, Err.description, sql
    Resume CleanExit
End Function

Private Function UserHasProtectedHistory(ByVal userID As Long, Optional ByVal db As DAO.Database = Nothing) As Boolean
' @desc: Проверяет, есть ли у пользователя связанные данные, запрещающие полное удаление (оставляем только soft-delete).
' @role: Users
' @todo: При добавлении новых сущностей с CreatedBy/UpdatedBy не забывать расширять этот список.
    Dim ownDb As Boolean

    If userID <= 0 Then Exit Function

    If db Is Nothing Then
        Set db = OpenCurrentDb
        ownDb = True
    End If

    If HasRows(db, "SELECT TOP 1 UserID FROM Users WHERE CreatedByUserID=" & userID) Then GoTo Found
    If HasRows(db, "SELECT TOP 1 CaseID FROM ArchiveCases WHERE CreatedByUserID=" & userID) Then GoTo Found
    If HasRows(db, "SELECT TOP 1 ProductID FROM Products WHERE CreatedByUserID=" & userID & " OR UpdatedByUserID=" & userID) Then GoTo Found
    If HasRows(db, "SELECT TOP 1 ProductServiceID FROM ProductServices WHERE AssignedByUserID=" & userID) Then GoTo Found
    If HasRows(db, "SELECT TOP 1 ChangeRequestID FROM ChangeRequests WHERE LockedByUserID=" & userID & " AND Status IN ('Approved','Applied')") Then GoTo Found
    If HasRows(db, "SELECT TOP 1 AuditLogID FROM AuditLog WHERE ChangedByUserID=" & userID & " AND ChangeRequestID IS NULL") Then GoTo Found
    If HasRows(db, "SELECT TOP 1 A.AuditLogID " & _
                      "FROM AuditLog AS A INNER JOIN ChangeRequests AS C ON A.ChangeRequestID = C.ChangeRequestID " & _
                      "WHERE A.ChangedByUserID=" & userID & " AND C.Status IN ('Approved','Applied')") Then GoTo Found

    UserHasProtectedHistory = False
    GoTo CleanExit

Found:
    UserHasProtectedHistory = True

CleanExit:
    If ownDb Then Set db = Nothing
End Function

Private Sub PurgeUserGarbage(ByVal userID As Long, ByVal db As DAO.Database)
' @desc: Удаляет все временные/черновые следы пользователя перед полным удалением (аудит, черновые заявоки, сессии, связи).
' @role: Users
' @todo: Следить, чтобы сюда попадали все новые черновые сущности, связанные с пользователем.
    db.Execute "DELETE FROM AuditLog " & _
               "WHERE ChangedByUserID=" & userID & _
               " AND BusinessEventType='UserCreate'", dbFailOnError

    db.Execute "DELETE FROM AuditLog " & _
               "WHERE ChangedByUserID=" & userID & _
               " AND ChangeRequestID IN (" & _
               "SELECT ChangeRequestID FROM ChangeRequests " & _
               "WHERE Status IN ('Draft','Pending','Rejected') AND LockedByUserID=" & userID & _
               ")", dbFailOnError

    db.Execute "DELETE FROM ChangeRequestItems " & _
               "WHERE ChangeRequestID IN (" & _
               "SELECT ChangeRequestID FROM ChangeRequests " & _
               "WHERE Status IN ('Draft','Pending','Rejected') AND LockedByUserID=" & userID & _
               ")", dbFailOnError

    db.Execute "DELETE FROM ChangeRequests " & _
               "WHERE Status IN ('Draft','Pending','Rejected') AND LockedByUserID=" & userID, dbFailOnError

    db.Execute "DELETE FROM UserSessions WHERE UserID=" & userID, dbFailOnError
    db.Execute "DELETE FROM UserServices WHERE UserID=" & userID, dbFailOnError
End Sub

Public Sub DeleteUserSmart(ByVal userID As Long, ByVal changedByUserId As Long)
' @desc: Выполняет умное удаление пользователя: либо soft-delete с переименованием логина, либо полное удаление без истории.
' @role: Users
' @todo: Возможно, стоит возвращать Boolean с результатом операции, а не только сообщения.
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim oldLogin As String
    Dim oldFullName As String
    Dim oldRoleID As Long
    Dim newDeletedLogin As String

    If userID <= 0 Then
        ShowWarning "Некорректный UserID."
        GoTo CleanExit
    End If
    If changedByUserId <= 0 Then
        ShowWarning "Некорректный changedByUserId."
        GoTo CleanExit
    End If
    If userID = changedByUserId Then
        ShowWarning "Нельзя удалить самого себя."
        GoTo CleanExit
    End If

    Set ws = OpenWorkspace
    Set db = OpenCurrentDb

    On Error GoTo EH

    Set rs = db.OpenRecordset( _
        "SELECT UserID, Login, FullName, RoleID, IsActive FROM Users WHERE UserID=" & userID, _
        dbOpenSnapshot)

    If rs.EOF Then
        ShowWarning "Пользователь не найден."
        GoTo CleanExit
    End If

    oldLogin = NzStr(rs.Fields("Login").Value)
    oldFullName = NzStr(rs.Fields("FullName").Value)
    oldRoleID = NzLng(rs.Fields("RoleID").Value)

    rs.Close
    Set rs = Nothing

    If Not CanManageRole(changedByUserId, oldRoleID) Then
        ShowWarning "Недостаточно прав для удаления пользователя с данной ролью."
        GoTo CleanExit
    End If

    ws.BeginTrans

    If UserHasProtectedHistory(userID, db) Then
        newDeletedLogin = BuildDeletedLogin(oldLogin, userID)

        db.Execute _
            "UPDATE Users SET " & _
            "IsActive=False, " & _
            "Login=" & Q(newDeletedLogin) & " " & _
            "WHERE UserID=" & userID, dbFailOnError

        db.Execute _
            "UPDATE UserSessions SET SessionStatus='Closed', LogoutTime=Now() " & _
            "WHERE UserID=" & userID & " AND SessionStatus='Active'", dbFailOnError

        WriteAuditEvent db, "Users", userID, "IsActive", "True", "False", "UPDATE", "UserSoftDelete", changedByUserId, Null
        WriteAuditEvent db, "Users", userID, "Login", oldLogin, newDeletedLogin, "UPDATE", "UserSoftDelete", changedByUserId, Null
    Else
        Call PurgeUserGarbage(userID, db)

        db.Execute "DELETE FROM AuditLog WHERE TableName='Users' AND RecordID=" & userID, dbFailOnError
        db.Execute "DELETE FROM Users WHERE UserID=" & userID, dbFailOnError
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
    ws.RollBack
    ShowError "DeleteUserSmart", Err.Number, Err.description
    Resume CleanExit
End Sub

Public Sub ChangeUserPassword(ByVal userID As Long, ByVal newPlainPassword As String, ByVal changedByUserId As Long)
' @desc: Меняет пароль пользователя, пересчитывая хэш и соль, и пишет аудит изменения.
' @role: Security
' @todo: Добавить политику сложности пароля и ограничение по длине.
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim sSalt As String
    Dim sCipher As String

    If userID <= 0 Then
        ShowWarning "Некорректный UserID."
        GoTo CleanExit
    End If
    If LenB(Trim$(newPlainPassword)) = 0 Then
        ShowWarning "Новый пароль не задан."
        GoTo CleanExit
    End If

    Set ws = OpenWorkspace
    Set db = OpenCurrentDb

    On Error GoTo EH
    ws.BeginTrans

    Set rs = db.OpenRecordset("SELECT UserID, Salt, PasswordHash FROM Users WHERE UserID=" & userID, dbOpenDynaset)
    If rs.EOF Then
        ShowWarning "Пользователь не найден."
        GoTo CleanExit
    End If

    sSalt = NzStr(rs.Fields("Salt").Value)
    If LenB(sSalt) = 0 Then sSalt = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.GenerateSalt")
    Dim encoded As String
    encoded = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.EncodeForData", newPlainPassword)
    sCipher = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.EncryptString", encoded, sSalt)

    rs.Edit
    rs.Fields("PasswordHash").Value = sCipher
    rs.Fields("Salt").Value = sSalt
    rs.Update
    rs.Close
    Set rs = Nothing

    WriteAuditEvent db, "Users", userID, "PasswordHash", "[HIDDEN]", "[CHANGED]", "UPDATE", "PasswordChange", changedByUserId, Null
    WriteAuditEvent db, "Users", userID, "Salt", "[HIDDEN]", "[UNCHANGED_OR_REUSED]", "UPDATE", "PasswordChange", changedByUserId, Null

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
    ws.RollBack
    ShowError "ChangeUserPassword", Err.Number, Err.description
    Resume CleanExit
End Sub

Public Sub RotateUserSalt(ByVal userID As Long, ByVal changedByUserId As Long)
' @desc: Переинициализирует соль и хэш пароля одного пользователя без изменения самого пароля.
' @role: Security
' @todo: Подумать о логике повторного вызова при частичных ошибках шифрования.
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim oldSalt As String, oldCipher As String
    Dim plainPassword As String
    Dim newSalt As String, newCipher As String

    If userID <= 0 Then
        ShowWarning "Некорректный UserID."
        GoTo CleanExit
    End If

    Set ws = OpenWorkspace
    Set db = OpenCurrentDb

    On Error GoTo EH
    ws.BeginTrans

    Set rs = db.OpenRecordset("SELECT UserID, PasswordHash, Salt FROM Users WHERE UserID=" & userID, dbOpenDynaset)
    If rs.EOF Then
        ShowWarning "Пользователь не найден."
        GoTo CleanExit
    End If

    oldCipher = NzStr(rs.Fields("PasswordHash").Value)
    oldSalt = NzStr(rs.Fields("Salt").Value)
    If LenB(oldCipher) = 0 Then
        ShowWarning "Пустой PasswordHash."
        GoTo CleanExit
    End If
    If LenB(oldSalt) = 0 Then
        ShowWarning "Пустая Salt."
        GoTo CleanExit
    End If
    Dim decrypted As String
    decrypted = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.DecryptString", oldCipher, oldSalt)
    plainPassword = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.DecodeFromData", decrypted)
    newSalt = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.GenerateSalt")
    Dim encoded As String
    encoded = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.EncodeForData", plainPassword)
    newCipher = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.EncryptString", encoded, newSalt)

    rs.Edit
    rs.Fields("Salt").Value = newSalt
    rs.Fields("PasswordHash").Value = newCipher
    rs.Update
    rs.Close
    Set rs = Nothing

    WriteAuditEvent db, "Users", userID, "Salt", "[HIDDEN]", "[CHANGED]", "UPDATE", "SaltRotate", changedByUserId, Null
    WriteAuditEvent db, "Users", userID, "PasswordHash", "[HIDDEN]", "[CHANGED]", "UPDATE", "SaltRotate", changedByUserId, Null

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
    ws.RollBack
    ShowError "RotateUserSalt", Err.Number, Err.description
    Resume CleanExit
End Sub

Public Function RotateAllUsersSalt(ByVal changedByUserId As Long, Optional ByVal onlyActive As Boolean = True) As Long
' @desc: Массово пересчитывает соль и хэш пароля для всех (или только активных) пользователей и пишет аудит.
' @role: Security
' @todo: Сейчас при первой проблеме с конкретным пользователем делается GoTo CleanExit — стоит либо пропускать проблемных, либо логировать.
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim SqlText As String
    Dim oldSalt As String, oldCipher As String
    Dim plainPassword As String
    Dim newSalt As String, newCipher As String
    Dim cnt As Long
    Dim curUserId As Long

    Set ws = OpenWorkspace
    Set db = OpenCurrentDb

    SqlText = "SELECT UserID, Login, PasswordHash, Salt, IsActive FROM Users"
    If onlyActive Then SqlText = SqlText & " WHERE IsActive=True"
    SqlText = SqlText & " ORDER BY UserID"

    On Error GoTo EH
    ws.BeginTrans

    Set rs = db.OpenRecordset(SqlText, dbOpenDynaset)
    Do While Not rs.EOF
        curUserId = NzLng(rs.Fields("UserID").Value)
        oldCipher = NzStr(rs.Fields("PasswordHash").Value)
        oldSalt = NzStr(rs.Fields("Salt").Value)

        If LenB(oldCipher) = 0 Then
            ShowWarning "Пустой PasswordHash у UserID=" & curUserId
            GoTo CleanExit
        End If
        If LenB(oldSalt) = 0 Then
            ShowWarning "Пустая Salt у UserID=" & curUserId
            GoTo CleanExit
        End If
        Dim decrypted As String
        decrypted = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.DecryptString", oldCipher, oldSalt)
        plainPassword = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.DecodeFromData", decrypted)
        newSalt = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.GenerateSalt")
        Dim encoded As String
        encoded = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.EncodeForData", plainPassword)
        newCipher = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.EncryptString", encoded, newSalt)

        rs.Edit
        rs.Fields("Salt").Value = newSalt
        rs.Fields("PasswordHash").Value = newCipher
        rs.Update

        WriteAuditEvent db, "Users", curUserId, "Salt", "[HIDDEN]", "[CHANGED]", "UPDATE", "SaltRotateAll", changedByUserId, Null
        WriteAuditEvent db, "Users", curUserId, "PasswordHash", "[HIDDEN]", "[CHANGED]", "UPDATE", "SaltRotateAll", changedByUserId, Null

        cnt = cnt + 1
        rs.MoveNext
    Loop
    rs.Close
    Set rs = Nothing

    ws.CommitTrans
    RotateAllUsersSalt = cnt

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    Exit Function
EH:
    On Error Resume Next
    ws.RollBack
    ShowError "RotateAllUsersSalt", Err.Number, Err.description
    Resume CleanExit
End Function

Public Sub SetUserActive(ByVal userID As Long, ByVal newIsActive As Boolean, ByVal changedByUserId As Long)
' @desc: Включает или отключает пользователя (IsActive) с записью события в аудит.
' @role: Users
' @todo: Возможен запрет отключения собственных прав; сейчас это не проверяется.
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim oldValue As Boolean

    If userID <= 0 Then
        ShowWarning "Некорректный UserID."
        GoTo CleanExit
    End If

    Set ws = OpenWorkspace
    Set db = OpenCurrentDb

    On Error GoTo EH
    ws.BeginTrans

    Set rs = db.OpenRecordset("SELECT UserID, IsActive FROM Users WHERE UserID=" & userID, dbOpenDynaset)
    If rs.EOF Then
        ShowWarning "Пользователь не найден."
        GoTo CleanExit
    End If

    oldValue = NzBool(rs.Fields("IsActive").Value, False)
    If oldValue <> newIsActive Then
        rs.Edit
        rs.Fields("IsActive").Value = newIsActive
        rs.Update
        WriteAuditEvent db, "Users", userID, "IsActive", BoolToText(oldValue), BoolToText(newIsActive), "UPDATE", "SetUserActive", changedByUserId, Null
    End If

    rs.Close
    Set rs = Nothing
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
    ws.RollBack
    ShowError "SetUserActive", Err.Number, Err.description
    Resume CleanExit
End Sub

Public Sub RenameUserLogin(ByVal userID As Long, ByVal newLogin As String, ByVal changedByUserId As Long)
' @desc: Переименовывает логин пользователя с проверкой уникальности и записью в аудит.
' @role: Users
' @todo: Локализовать текст предупреждений и унифицировать формат сообщений о занятости логина.
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim oldLogin As String

    If userID <= 0 Then
        ShowWarning "Некорректный UserID."
        GoTo CleanExit
    End If
    If LenB(Trim$(newLogin)) = 0 Then
        ShowWarning "Новый логин пустой."
        GoTo CleanExit
    End If

    Set ws = OpenWorkspace
    Set db = OpenCurrentDb

    On Error GoTo EH
    ws.BeginTrans

    If UserExists(newLogin, db) Then
        ShowWarning "Логин уже занят: " & newLogin
        GoTo CleanExit
    End If

    Set rs = db.OpenRecordset("SELECT UserID, Login FROM Users WHERE UserID=" & userID, dbOpenDynaset)
    If rs.EOF Then
        ShowWarning "Пользователь не найден."
        GoTo CleanExit
    End If

    oldLogin = NzStr(rs.Fields("Login").Value)
    If StrComp(oldLogin, Trim$(newLogin), vbTextCompare) <> 0 Then
        rs.Edit
        rs.Fields("Login").Value = Trim$(newLogin)
        rs.Update
        WriteAuditEvent db, "Users", userID, "Login", oldLogin, Trim$(newLogin), "UPDATE", "RenameUserLogin", changedByUserId, Null
    End If

    rs.Close
    Set rs = Nothing
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
    ws.RollBack
    ShowError "RenameUserLogin", Err.Number, Err.description
    Resume CleanExit
End Sub

Public Function ValidateUserPassword(ByVal userLogin As String, ByVal plainPassword As String) As Boolean
' @desc: Проверяет, соответствует ли введённый пароль хранимому хэшу и соли для активного пользователя.
' @role: Auth
' @todo: Добавить обработку ошибок шифрования и логирование неудачных попыток входа.
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim storedCipher As String, storedSalt As String
    Dim decodedPassword As String

    Set db = OpenCurrentDb
    Set rs = db.OpenRecordset( _
        "SELECT PasswordHash, Salt, IsActive FROM Users WHERE Login=" & Q(userLogin), _
        dbOpenSnapshot)

    If rs.EOF Then
        ValidateUserPassword = False
    ElseIf NzBool(rs.Fields("IsActive").Value, False) = False Then
        ValidateUserPassword = False
    Else
        storedCipher = NzStr(rs.Fields("PasswordHash").Value)
        storedSalt = NzStr(rs.Fields("Salt").Value)
        Dim decrypted As String
        decrypted = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.DecryptString", storedCipher, storedSalt)
        decodedPassword = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.DecodeFromData", decrypted)
        ValidateUserPassword = (StrComp(decodedPassword, plainPassword, vbBinaryCompare) = 0)
    End If

    rs.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Function GetUserIdByLogin(ByVal userLogin As String) As Long
' @desc: Возвращает ID пользователя по логину или 0, если пользователь не найден.
' @role: Users
' @todo: При необходимости добавить фильтр по IsActive, если где-то важно игнорировать отключённых.
    Dim db As DAO.Database
    Dim rs As DAO.Recordset

    Set db = OpenCurrentDb
    Set rs = db.OpenRecordset("SELECT UserID FROM Users WHERE Login=" & Q(userLogin), dbOpenSnapshot)

    If Not rs.EOF Then GetUserIdByLogin = NzLng(rs.Fields("UserID").Value)

    rs.Close
    Set rs = Nothing
    Set db = Nothing
End Function

Public Function UserExists(ByVal userLogin As String, Optional ByVal db As DAO.Database = Nothing) As Boolean
' @desc: Проверяет факт существования пользователя с заданным логином.
' @role: Users
' @todo: В будущем можно разделить варианты проверки “любой” и “только активный” пользователь.
    Dim ownDb As Boolean
    Dim rs As DAO.Recordset

    If db Is Nothing Then
        Set db = OpenCurrentDb
        ownDb = True
    End If

    Set rs = db.OpenRecordset("SELECT UserID FROM Users WHERE Login=" & Q(userLogin), dbOpenSnapshot)
    UserExists = Not rs.EOF
    rs.Close
    Set rs = Nothing

    If ownDb Then Set db = Nothing
End Function

Public Function GetUserRoleId(ByVal userID As Long) As Long
' @desc: Возвращает ID роли пользователя по его UserID.
' @role: Users
' @todo: При ошибке лучше возвращать 0 и логировать, сейчас просто Exit Function.
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim result As Long
    
    If userID <= 0 Then Exit Function
        
    Set ws = OpenWorkspace
    Set db = OpenCurrentDb
    Set rs = db.OpenRecordset("SELECT RoleID FROM Users WHERE UserID=" & userID, dbOpenSnapshot)
    If Not rs.EOF Then
        result = NzLng(rs.Fields(0).Value)
    End If
    
    rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing
    
    GetUserRoleId = result
End Function

' =========================
' Проверки прав
' =========================

Public Function CanManageRole(ByVal currentUserId As Long, ByVal targetRoleID As Long) As Boolean
' @desc: Проверяет, может ли пользователь менять/назначать указанную роль с учётом флагов CanManageUsers/CanManageAdmin.
' @role: Security
' @todo: Добавить обработку случая, когда роль не найдена, и явное логирование отказов.
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim curRoleId As Long
    Dim CanManageUsers As Boolean
    Dim CanManageAdmin As Boolean
    Dim targetRoleName As String

    If currentUserId <= 0 Then Exit Function

    Set db = OpenCurrentDb

    Set rs = db.OpenRecordset( _
        "SELECT U.RoleID, R.CanManageUsers, R.CanManageAdmin " & _
        "FROM Users AS U INNER JOIN Roles AS R ON U.RoleID = R.RoleID " & _
        "WHERE U.UserID=" & currentUserId, dbOpenSnapshot)

    If rs.EOF Then GoTo CleanExit

    curRoleId = NzLng(rs.Fields("RoleID").Value)
    CanManageUsers = NzBool(rs.Fields("CanManageUsers").Value, False)
    CanManageAdmin = NzBool(rs.Fields("CanManageAdmin").Value, False)
    rs.Close
    Set rs = Nothing

    If Not CanManageUsers Then GoTo CleanExit

    Set rs = db.OpenRecordset("SELECT RoleName FROM Roles WHERE RoleID=" & targetRoleID, dbOpenSnapshot)
    If rs.EOF Then GoTo CleanExit
    targetRoleName = NzStr(rs.Fields("RoleName").Value)

    If StrComp(targetRoleName, Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModSettings.GetConstant", "ROLE_ADMIN_NAME"), vbTextCompare) = 0 Then
        CanManageRole = CanManageAdmin
    Else
        CanManageRole = True
    End If

CleanExit:
    On Error Resume Next
    If Not rs Is Nothing Then rs.Close
    Set rs = Nothing
    Set db = Nothing
End Function

' =========================
' Вспомогательные проверки
' =========================

Private Sub ValidateUserInput(ByVal userLogin As String, ByVal userFullName As String, ByVal roleID As Long, ByVal plainPassword As String)
' @desc: Валидирует логин, ФИО, роль и пароль и показывает предупреждения при нарушении правил.
' @role: Validation
' @todo: Возвращать Boolean-результат вместо набора ShowWarning, чтобы вызывать CreateUser только при успехе.
    If LenB(Trim$(userLogin)) = 0 Then ShowWarning "Логин не может быть пустым."
    If Len(Trim$(userLogin)) > 50 Then ShowWarning "Логин должен быть короче 50 символов."
    If LenB(Trim$(userFullName)) = 0 Then ShowWarning "ФИО не может быть пустым."
    If Len(Trim$(userFullName)) > 200 Then ShowWarning "ФИО должно быть короче 200 символов."
    If roleID <= 0 Then ShowWarning "Некорректный ID роли."
    If LenB(plainPassword) = 0 Then ShowWarning "Пароль не должен быть пустым."
End Sub


' =========================
' Служебные примеры вызова
' =========================

Public Sub CreateDefaultAdmin()
' @desc: Создаёт администратора по умолчанию и показывает пользователю его стандартный пароль.
' @role: Test
' @todo: --
    Dim newId As Long
    newId = EnsureDefaultAdmin(0)
    ShowInfo "Базовый пользователь Admin создан с паролем " & Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModSettings.GetConstant", "DEFAULT_ADMIN_PASSWORD"), vbInformation
End Sub

' ================================================================
' Получение данных о всех пользователях
' ================================================================

Public Function GetAllUsers() As DAO.Recordset
' @desc: Возвращает snapshot со всеми пользователями и их ролями, кроме логинов вида *_deleted_*.
' @role: Users
' @todo: Вызывать только там, где корректно закрывается возвращённый Recordset.
    Dim db As DAO.Database
    Dim sql As String

    Set db = OpenCurrentDb

    sql = "SELECT U.UserID, U.Login, U.FullName, U.RoleID, R.RoleName, U.IsActive " & _
          "FROM Users AS U INNER JOIN Roles AS R ON U.RoleID = R.RoleID " & _
          "WHERE U.Login Not Like '*_deleted_*' " & _
          "ORDER BY U.Login"

    Set GetAllUsers = db.OpenRecordset(sql, dbOpenSnapshot)
End Function

Public Function GetUserById(ByVal userID As Long) As UserInfo
' @desc: Загружает полную информацию о пользователе в структуру UserInfo по его ID.
' @role: Users
' @todo: При необходимости добавить флаг для включения/исключения чувствительных полей (PasswordHash/Salt).
    Dim ws As DAO.Workspace
    Dim db As DAO.Database
    Dim rs As DAO.Recordset
    Dim u As UserInfo

    If userID <= 0 Then Exit Function
    
    Set ws = OpenWorkspace
    Set db = OpenCurrentDb

    Set rs = db.OpenRecordset( _
        "SELECT UserID, Login, FullName, RoleID, PasswordHash, Salt, IsActive, LastLogin, CreatedAt, CreatedByUserID " & _
        "FROM Users WHERE UserID = " & userID, _
        dbOpenSnapshot)

    If Not rs.EOF Then
        u.userID = NzLng(rs.Fields("UserID").Value)
        u.login = NzStr(rs.Fields("Login").Value)
        u.fullName = NzStr(rs.Fields("FullName").Value)
        u.roleID = NzLng(rs.Fields("RoleID").Value)
        u.PasswordHash = NzStr(rs.Fields("PasswordHash").Value)
        u.Salt = NzStr(rs.Fields("Salt").Value)
        u.isActive = NzBool(rs.Fields("IsActive").Value, False)

        If IsNull(rs.Fields("LastLogin").Value) Then
            u.LastLogin = Null
        Else
            u.LastLogin = rs.Fields("LastLogin").Value
        End If

        If IsNull(rs.Fields("CreatedAt").Value) Then
            u.CreatedAt = Null
        Else
            u.CreatedAt = rs.Fields("CreatedAt").Value
        End If

        u.createdByUserID = NzLng(rs.Fields("CreatedByUserID").Value)
    End If

    rs.Close
    Set rs = Nothing
    Set db = Nothing
    Set ws = Nothing

    GetUserById = u
End Function

Public Function UserExistsById(ByVal userID As Long, Optional ByVal db As DAO.Database = Nothing) As Boolean
' @desc: Проверяет, существует ли пользователь с указанным ID.
' @role: Users
' @todo: Аналогично UserExists, можно добавить вариант проверки только активных.
    Dim ownDb As Boolean
    Dim rs As DAO.Recordset

    If userID <= 0 Then Exit Function

    If db Is Nothing Then
        Set db = OpenCurrentDb
        ownDb = True
    End If

    Set rs = db.OpenRecordset("SELECT UserID FROM Users WHERE UserID = " & userID, dbOpenSnapshot)
    UserExistsById = Not rs.EOF

    rs.Close
    Set rs = Nothing
    If ownDb Then Set db = Nothing
End Function

Public Function GetUsersByService(ByVal serviceID As Long) As DAO.Recordset
' @desc: Возвращает подробный список пользователей и их прав для конкретной службы (ServiceID).
' @role: Users
' @todo: Сейчас при serviceID=0 только предупреждение; можно сразу выходить из функции.
    Dim db As DAO.Database
    Dim sqlA As String
    Dim sqlB As String
    Dim sqlC As String
    Dim sqlD As String
    Dim sqlE As String
    Dim sqlF As String
    Dim sql As String

    If serviceID <= 0 Then
        ShowWarning "ServiceID = 0."
    End If

    Set db = OpenCurrentDb

    sqlA = "SELECT " & _
           "IIf(IsNull(US.UserServiceID),0,US.UserServiceID) AS UserServiceID, " & _
           "U.UserID, U.Login, U.FullName, U.IsActive, R.RoleName, " & _
           "R.CanEditAny AS RoleCanEditAny, R.CanApproveAny AS RoleCanApproveAny, "

    sqlB = "IIf(IsNull(US.CanEdit),False,US.CanEdit) AS LinkCanEdit, " & _
           "IIf(IsNull(US.CanApprove),False,US.CanApprove) AS LinkCanApprove, " & _
           "IIf(R.CanEditAny=True Or R.CanApproveAny=True,True,False) AS RightsByRole, " & _
           "IIf(IsNull(US.UserServiceID),False,True) AS HasUserServiceLink, "

    sqlC = "IIf(R.CanEditAny=True Or R.CanApproveAny=True,False, " & _
           "IIf(IsNull(US.UserServiceID),False,True)) AS CanRemoveLink, " & _
           "IIf(U.Login Like 'deleted*',True,False) AS IsDeletedLogin "

    sqlD = "FROM (Users AS U " & _
           "INNER JOIN Roles AS R ON U.RoleID = R.RoleID) " & _
           "LEFT JOIN UserServices AS US ON U.UserID = US.UserID "

    sqlE = "WHERE (US.ServiceID = " & serviceID & _
           " OR R.CanEditAny=True " & _
           " OR R.CanApproveAny=True) "

    sqlF = "ORDER BY " & _
           "IIf(R.CanEditAny=True Or R.CanApproveAny=True,0,1), " & _
           "U.Login;"

    sql = sqlA & sqlB & sqlC & sqlD & sqlE & sqlF

    Set GetUsersByService = db.OpenRecordset(sql, dbOpenSnapshot)
End Function

Public Function GetUsersForNewService() As DAO.Recordset
' @desc: Возвращает список активных пользователей и их ролей для назначения на новую службу.
' @role: Users
' @todo: Проверить, нужно ли фильтровать логины с *_deleted_* по тому же правилу, что и в GetAllUsers.
    Dim db As DAO.Database
    Dim sqlA As String
    Dim sqlB As String
    Dim sql As String

    Set db = OpenCurrentDb

    sqlA = "SELECT U.UserID, U.Login, U.FullName, U.IsActive, " & _
           "R.RoleName, R.CanEditAny AS RoleCanEditAny, R.CanApproveAny AS RoleCanApproveAny "

    sqlB = "FROM Users AS U INNER JOIN Roles AS R ON U.RoleID = R.RoleID " & _
           "WHERE U.IsActive=True AND U.Login Not Like 'deleted*' " & _
           "ORDER BY U.Login;"

    sql = sqlA & sqlB
    Set GetUsersForNewService = db.OpenRecordset(sql, dbOpenSnapshot)
End Function
```

## Черновые заметки

