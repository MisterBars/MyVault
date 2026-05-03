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
Public mIsDirty As Boolean

Private Sub Btn_Add_Click()
    On Error GoTo EH
    Select Case ID_table_change
        Case 0:
            SaveRoles Me
        Case 1:
            SaveUsers Me
        Case 2:
            SaveNomTypes Me
        Case 3:
            SaveNoms Me
        Case 4:
            SaveServiceAndUsers Me
        Case Else:
            Me.Hide
    End Select
    Exit Sub
EH:
    ShowError "F_Change.Btn_Add_Click", Err.Number, Err.description
End Sub

Private Sub Btn_AddUS_Click()
    On Error GoTo EH
    Dim userID As Long
    Dim login As String
    Dim fullName As String

    If Me.LB_UserWOService.ListIndex < 1 Then Exit Sub

    userID = NzLng(Me.LB_UserWOService.List(Me.LB_UserWOService.ListIndex, 0))
    login = NzStr(Me.LB_UserWOService.List(Me.LB_UserWOService.ListIndex, 1))
    fullName = NzStr(Me.LB_UserWOService.List(Me.LB_UserWOService.ListIndex, 2))

    If SvcBuf_AddLink(userID, login, fullName) Then
        Call MarkDirty
        RefreshAllServiceLists Me.LB_UserWService, Me.LB_UserWOService
    End If
    Exit Sub
EH:
    ShowError "F_Change.Btn_AddUS_Click", Err.Number, Err.description
End Sub

Private Sub Btn_Cansel_Click()
    If Not ConfirmDiscardChanges() Then Exit Sub
    Me.Hide
End Sub

Private Sub Btn_DelUS_Click()
On Error GoTo EH
    Dim userID As Long
    Dim rightsByRole As Boolean

    If Me.LB_UserWService.ListIndex < 1 Then Exit Sub

    userID = NzLng(Me.LB_UserWService.List(Me.LB_UserWService.ListIndex, 0))
    rightsByRole = (NzLng(Me.LB_UserWService.List(Me.LB_UserWService.ListIndex, 6)) = 1)

    If rightsByRole Then
        ShowWarning "Эта строка задана правами роли и не может быть удалена.", vbInformation
        Exit Sub
    End If

    If SvcBuf_RemoveLink(userID) Then
        Call MarkDirty
        RefreshAllServiceLists Me.LB_UserWService, Me.LB_UserWOService
    End If
    Exit Sub
EH:
    ShowError "F_Change.Btn_DelUS_Click", Err.Number, Err.description
End Sub

Private Sub Btn_NewPwdGen_Click()
    Me.TB_UserPwd.Text = Application.Run("'" & ADDIN_PATH & "Encrypt_VVT.xlam'!ModCrypt.GenerateSimplePassword")
End Sub

Private Sub Btn_USCanApprove_Click()
    On Error GoTo EH
    Dim userID As Long
    Dim rightsByRole As Boolean

    If Me.LB_UserWService.ListIndex < 1 Then Exit Sub

    userID = NzLng(Me.LB_UserWService.List(Me.LB_UserWService.ListIndex, 0))
    rightsByRole = (NzLng(Me.LB_UserWService.List(Me.LB_UserWService.ListIndex, 6)) = 1)

    If rightsByRole Then
        ShowWarning "Для этой строки право задается ролью пользователя."
        Exit Sub
    End If

    If SvcBuf_ToggleApprove(userID) Then
        Call MarkDirty
        RefreshAllServiceLists Me.LB_UserWService, Me.LB_UserWOService
    End If
    Exit Sub
EH:
    ShowError "F_Change.Btn_USCanApprove_Click", Err.Number, Err.description
End Sub

Private Sub Btn_USCanEdit_Click()
    On Error GoTo EH
    Dim userID As Long
    Dim rightsByRole As Boolean

    If Me.LB_UserWService.ListIndex < 1 Then Exit Sub

    userID = NzLng(Me.LB_UserWService.List(Me.LB_UserWService.ListIndex, 0))
    rightsByRole = (NzLng(Me.LB_UserWService.List(Me.LB_UserWService.ListIndex, 6)) = 1)

    If rightsByRole Then
        ShowWarning "Для этой строки право задается ролью пользователя.", vbInformation
        Exit Sub
    End If

    If SvcBuf_ToggleEdit(userID) Then
        Call MarkDirty
        RefreshAllServiceLists Me.LB_UserWService, Me.LB_UserWOService
    End If
    Exit Sub
EH:
    ShowError "F_Change.Btn_USCanEdit_Click", Err.Number, Err.description
End Sub

Private Sub CB_UserChangePwd_Change()
    TB_UserPwd.Enabled = CB_UserChangePwd.Value
    Lbl_UserPwd.Enabled = CB_UserChangePwd.Value
End Sub

Private Sub TB_UserPwd_Enter()
    Me.TB_UserPwd.PasswordChar = vbNullChar
End Sub

Private Sub TB_UserPwd_Exit(ByVal Cancel As MSForms.ReturnBoolean)
    Me.TB_UserPwd.PasswordChar = "*"
End Sub

Private Sub UserForm_Initialize()
    Me.MP_Change.Style = fmTabStyleNone
End Sub

Public Sub PrepareFormForAdd()
    On Error GoTo EH
    Me.MP_Change.Value = ID_table_change
    Select Case ID_table_change
        Case 0:
            Btn_Add.Caption = "Добавить"
            Me.Caption = "Добавить роль"
            TB_RoleName.Value = Empty
            TB_RoleDescription.Value = Empty
            CB_CanManageUsers.Value = False
            CB_CanManageAdmin.Value = False
            CB_CanEditAny.Value = False
            CB_CanApproveAny.Value = False
            CB_CanChangeOwnPWD.Value = False
        Case 1:
            Btn_Add.Caption = "Добавить"
            Me.Caption = "Добавить пользователя"
            TB_UserLogin.Value = Empty
            TB_UserFullName.Value = Empty
            ComB_UserRole.Value = Empty
            CB_UserIsActive.Value = True
            CB_UserChangePwd.Value = True
            CB_UserChangePwd.Enabled = False
            TB_UserPwd.Value = Empty
            Lbl_UserPwd.Enabled = True
        Case 2:
            Btn_Add.Caption = "Добавить"
            Me.Caption = "Добавить тип номенклатуры"
            TB_NomTypesName.Value = Empty
            TB_NomTypesKod.Value = Empty
            TB_NomTypesDescription.Value = Empty
            CB_NomTypesIsActive.Value = True
        Case 3:
            Btn_Add.Caption = "Добавить"
            Me.Caption = "Добавить номенклатуру"
            ComB_NomType.Value = Empty
            ComB_NomType.ListRows = 20
            TB_NomKod.Value = Empty
            TB_NomName.Value = Empty
            TB_NomTypesDescription.Value = Empty
        Case 4:
            Btn_Add.Caption = "Добавить"
            Me.Caption = "Добавить службу"
            TB_ServicesName.Value = Empty
            TB_ServicesCode.Value = Empty
            TB_ServicesDescription.Value = Empty
            CB_ServicesIsActive.Value = True
            InitServiceFormState Me.LB_UserWService, Me.LB_UserWOService, CLng(Me.TB_ServicesName.Tag)
        Case Else:
            Exit Sub
    End Select
    Me.MP_Change.Height = Me.Controls("Frame" & ID_table_change).Height
    Me.MP_Change.Width = Me.Controls("Frame" & ID_table_change).Width
    Me.Btn_Add.Top = Me.MP_Change.Height + 6
    Me.Btn_Cansel.Top = Me.MP_Change.Height + 6
    Me.Height = Me.Btn_Add.Top + (Me.Btn_Add.Height * 2) + 12
    Me.Width = Me.MP_Change.Width + 12
    Me.Btn_Add.Left = Me.Width / 2 + 18
    Me.Btn_Cansel.Left = Me.Width / 2 - Me.Btn_Cansel.Width - 18
    Lbl_podskazka.Top = Me.Height + 50
    Exit Sub
EH:
    ShowError "F_Change.PrepareFormForAdd", Err.Number, Err.description
End Sub

Public Sub PrepareFormForChange()
    On Error GoTo EH
    Me.MP_Change.Value = ID_table_change
    Select Case ID_table_change
        Case 0:
            Btn_Add.Caption = "Изменить"
            Me.Caption = "Изменить роль"
        Case 1:
            Btn_Add.Caption = "Изменить"
            Me.Caption = "Изменить пользователя"
            CB_UserChangePwd.Value = False
            TB_UserPwd.Enabled = False
            TB_UserPwd.Value = Empty
            Lbl_UserPwd.Enabled = False
        Case 2:
            Btn_Add.Caption = "Изменить"
            Me.Caption = "Изменить тип"
        Case 3:
            Btn_Add.Caption = "Изменить"
            Me.Caption = "Изменить номенклатуру"
        Case 4:
            Btn_Add.Caption = "Изменить"
            Me.Caption = "Изменить службу"
            InitServiceFormState Me.LB_UserWService, Me.LB_UserWOService, CLng(Me.TB_ServicesName.Tag)
        Case Else:
            Exit Sub
    End Select
    Me.MP_Change.Height = Me.Controls("Frame" & ID_table_change).Height
    Me.MP_Change.Width = Me.Controls("Frame" & ID_table_change).Width
    Me.Btn_Add.Top = Me.MP_Change.Height + 6
    Me.Btn_Cansel.Top = Me.MP_Change.Height + 6
    Me.Height = Me.Btn_Add.Top + (Me.Btn_Add.Height * 2) + 12
    Me.Width = Me.MP_Change.Width + 12
    Me.Btn_Add.Left = Me.Width / 2 + 18
    Me.Btn_Cansel.Left = Me.Width / 2 - Me.Btn_Cansel.Width - 18
    Lbl_podskazka.Top = Me.Height + 50
    Exit Sub
EH:
    ShowError "F_Change.PrepareFormForChange", Err.Number, Err.description
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    If CloseMode = vbFormControlMenu Then
        If Not ConfirmDiscardChanges() Then
            Cancel = True
            Me.Hide
        End If
    End If
End Sub

Private Function IsMissingOrNull(ByVal v As Variant) As Boolean
    If IsObject(v) Then
        IsMissingOrNull = (v Is Nothing)
    ElseIf IsNull(v) Then
        IsMissingOrNull = True
    ElseIf VarType(v) = vbString Then
        IsMissingOrNull = (Trim$(CStr(v)) = "")
    Else
        IsMissingOrNull = False
    End If
End Function

Public Sub MarkDirty()
    mIsDirty = True
End Sub

Public Sub ResetDirty()
    mIsDirty = False
End Sub

Private Function ConfirmDiscardChanges() As Boolean
    If Not mIsDirty Then
        ConfirmDiscardChanges = True
        Exit Function
    End If

    ConfirmDiscardChanges = (MsgBox( _
        "Есть несохраненные изменения. Отменить их?", _
        vbQuestion + vbYesNo + vbDefaultButton2, _
        "Подтверждение") = vbYes)
End Function

```

## Черновые заметки