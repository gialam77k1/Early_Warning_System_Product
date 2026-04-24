# Changelog — EWS Platform

## [2026-04-23] Major Admin Dashboard Fixes & Features

### ✅ Fixed: Add Class Button Not Working
**File:** `frontend/admin.html`
- Added form submit event listener to `classForm`
- Now creates classes properly when "Save Class" is clicked
- Form resets after successful submission

### ✅ Fixed: Can't Add Students
**Files:** `frontend/admin.html`, Backend: `POST /api/students/`
- Added "Add Student" modal with dropdown to select user
- Added class assignment during student creation
- Auto-generates student ID if not provided
- Date of birth and gender fields added
- New modal ID: `studentModal` with full form

### ✅ Fixed: Edit Class - Add Teachers After Creation
**File:** `frontend/admin.html`
- Added "Edit Class" modal with ability to assign/change teacher
- Edit button added to each class row
- Loads available teachers from `GET /api/admin/teachers/`
- Saves changes via `PUT /api/classes/<id>/`
- New modal ID: `editClassModal`

### ✅ Fixed: Teachers Section Empty
**File:** `frontend/admin.html`
- Added `loadTeachers()` function that calls `GET /api/admin/teachers/`
- Added `filterTeachers()` for searching by name
- Displays teacher name, email, phone number
- Search functionality with real-time filtering
- Added "Teachers" to sectionConfig

### ✅ Fixed: Search Functionality Not Working
**File:** `frontend/admin.html`
- **Students:** Added search by name + filter by class
- **Teachers:** Search by name or username with live filtering
- **Users:** Search by name, username, or email with `searchUsers()` function
- All filters now update dynamically on input

### ✅ Fixed: Gradebook Pending Approvals
**File:** `frontend/admin.html`
- Separated "Pending Grade Approvals" and "Approved Scores" tables
- Shows pending count in orange badge
- Teachers submit grades → Admin approves/rejects
- Approve button: Sets `is_approved=True` via `PUT /api/admin/scores/<id>/approve/`
- Reject button: Deletes score with `action='reject'`
- Only approved scores appear in final gradebook

### 🎓 Changed: Student Management
**File:** `frontend/admin.html`
- Students no longer auto-created on user registration
- Admin must explicitly add users as students via "Add Student" modal
- Students must be assigned to a class
- Student profile includes: ID, name, email, class, gender

### 💡 Clarified: Role Management
- **Admin:** System administrator with full access
- **Teacher:** Can manage classes and enter grades (pending admin approval)
- **Student:** Learner in classes; default role for public registration
- Admin can upgrade/downgrade roles dynamically in User Management

### 🗑️ Removed: Settings Section
- Settings menu item removed (no functionality)
- Simplified admin navigation

---

## [2026-04-23] UI Fixes

### 🐛 Bug Fix: Login Form — Nút "Sign In" bị lệch chữ sang trái

**File:** `frontend/css/style.css`

**Vấn đề:**  
Nút "Sign In" trên trang login (`index.html`) hiển thị chữ bị lệch sang bên trái thay vì nằm chính giữa nút.

**Nguyên nhân:**  
Class `.btn` sử dụng `display: inline-flex` nhưng thiếu `justify-content: center`. Khi nút được set `width: 100%` (qua inline style trên trang login), nội dung text bị đẩy sang trái theo mặc định của flexbox (`flex-start`).

**Cách fix:**  
Thêm `justify-content: center` vào class `.btn` trong `style.css`.

```diff
 .btn {
-  display: inline-flex; align-items: center; gap: 8px;
+  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
   padding: 10px 20px;
   ...
 }
```

---

### 🗑️ Removed: Icon chuông thông báo (Notification Bell)

**Files:** `frontend/admin.html`, `frontend/teacher.html`, `frontend/student.html`

**Vấn đề:**  
Icon chuông 🔔 trên topbar chỉ là UI trang trí — không có chức năng thực tế. Badge số (3, 5, 2) là hardcoded, ấn vào không có phản hồi. Gây hiểu nhầm cho người dùng.

**Cách fix:**  
Xóa bỏ hoàn toàn `div.notif-btn` khỏi cả 3 trang (admin, teacher, student).

```diff
 <div class="topbar-actions">
-  <div class="notif-btn">
-    🔔 <span class="notif-badge">3</span>
-  </div>
   <div class="top-user">
```
## [2026-04-23] Admin Dashboard Overhaul + Registration

### 🆕 Feature: Public Registration Page
- **File:** `frontend/register.html` (NEW), `frontend/index.html`
- Tạo trang đăng ký công khai cho student
- Đăng ký tự động tạo tài khoản với role `student`
- Login page giờ có link "Register"
- **Backend:** `POST /api/auth/public-register/` (AllowAny, luôn tạo student)

### 🆕 Feature: User Management (Admin)
- **Files:** `frontend/admin.html`, `core/views.py`, `core/urls.py`
- Admin có thể xem danh sách tất cả users
- Admin có thể **thay đổi vai trò** (Admin/Teacher/Student) bằng dropdown
- Admin có thể **xóa tài khoản** (trừ chính mình)
- **Backend APIs:**
  - `GET /api/admin/users/` — danh sách users
  - `PUT /api/admin/users/<id>/role/` — đổi vai trò
  - `DELETE /api/admin/users/<id>/` — xóa user

### ✅ Fix: Add Class form không hoạt động
- **File:** `frontend/admin.html`
- Thêm `submit` event listener cho `classForm` → gọi `api.post('/classes/')`
- Giờ ấn "Save Class" sẽ thực sự tạo lớp mới

### ✅ Fix: Teachers section trống
- **File:** `frontend/admin.html`
- Thay thế Teachers section bằng **Users Management** — quản lý toàn bộ tài khoản, bao gồm cả teachers

### ✅ Fix: Warnings section không load data
- **File:** `frontend/admin.html`
- `loadWarnings()` trước đó gây infinite loop (`showSection('warnings')`)
- Đổi thành `loadWarningsData()` — gọi API `/predictions/warnings/`

### 🗑️ Removed: AI Analytics trong admin
- Không cần thiết, đã có ML predict trong Teacher dashboard
- Xóa nav item + section + sectionConfig entry

### 🗑️ Removed: Settings trong admin
- Không có chức năng, gây confuse
- Xóa nav item

### 🗑️ Removed: Search bar (tất cả pages)
- Search bar trên topbar chỉ là UI, không có logic
- Thay bằng label text đơn giản

### 💡 Clarification: Gradebook
- **Gradebook = Sổ điểm**: hiển thị điểm tất cả students + AI risk prediction
- Description đã được cập nhật rõ ràng hơn

---

## [2026-04-23] UI Fixes (Earlier)

### 🐛 Fix: Login Form — Nút "Sign In" bị lệch chữ sang trái
- **File:** `frontend/css/style.css`
- Thêm `justify-content: center` vào class `.btn`

### 🗑️ Removed: Notification Bell (tất cả pages)
- Xóa `div.notif-btn` khỏi admin.html, teacher.html, student.html

---

## [2026-04-24] Functional Fix Pass: Admin, Teacher, Student, MLOps

### ✅ Fixed: Admin add class / edit class now works end-to-end
- **Files:** `frontend/admin.html`, `early_waring_backend/core/views.py`
- Form tạo lớp giờ nạp danh sách giáo viên thật và gửi dữ liệu đầy đủ.
- Modal sửa lớp giờ đọc đúng `giao_vien` từ API, có thể gán/đổi giáo viên sau khi lớp đã tạo.
- Sau khi tạo/sửa/xóa lớp, danh sách lớp và filter học viên được refresh lại.

### ✅ Fixed: Student management trong admin
- **Files:** `frontend/admin.html`, `early_waring_backend/core/views.py`, `early_waring_backend/core/serializers.py`
- Sửa filter học viên theo lớp bằng field `lop_id` thật từ serializer nên không còn tình trạng chọn lớp mà không ra ai.
- Thêm modal sửa học viên để đổi mã học viên, lớp, ngày sinh, giới tính.
- Thêm xóa hồ sơ học viên từ admin.
- Modal add student chỉ hiện các user role `student` chưa có hồ sơ học viên để tránh add trùng.

### ✅ Fixed: User/Teacher search và role management
- **Files:** `frontend/admin.html`, `early_waring_backend/core/views.py`
- Search ở Users / Students / Teachers đều lọc theo dữ liệu thật thay vì UI placeholder.
- Admin đổi role không còn xóa hồ sơ học viên một cách ngoài ý muốn khi upgrade/downgrade account.
- Admin vẫn có thể xóa tài khoản và không được tự xóa chính mình.

### ✅ Fixed: Teachers section trong admin
- **Files:** `frontend/admin.html`, `early_waring_backend/core/views.py`
- Mục Teachers giờ load danh sách giáo viên thật từ `GET /api/admin/teachers/`.
- Có tìm kiếm theo tên/username và hiển thị email, số điện thoại, trạng thái.

### ✅ Fixed: Grade approval workflow
- **Files:** `frontend/admin.html`, `frontend/teacher.html`, `early_waring_backend/core/views.py`, `early_waring_backend/core/serializers.py`
- Giáo viên nhập hoặc sửa điểm ở giao diện teacher, bản ghi sẽ quay về trạng thái `pending admin approval`.
- Admin duyệt hoặc từ chối các bản ghi pending ở Gradebook.
- Gradebook admin hiển thị rõ pending/approved và thông tin người duyệt.
- Dữ liệu dashboard/warnings giờ ưu tiên dữ liệu đã được duyệt chính thức.

### ✅ Fixed: Teacher dashboard / enter grade / edit grade
- **File:** `frontend/teacher.html`
- Bổ sung nút `Enter Grade`, select học viên thật trong lớp đang chọn.
- Có thể tạo mới điểm hoặc sửa điểm hiện có ngay trong teacher dashboard.
- Thêm mục `Students` và `Analytics` hoạt động thật thay vì bấm vào không hiện gì.
- Analytics hiển thị điểm chờ duyệt và cảnh báo của lớp hiện tại.

### ✅ Fixed: Student dashboard navigation
- **File:** `frontend/student.html`
- Bổ sung section `My Scores` và `My Class` để các menu không còn rỗng.
- Hiển thị lịch sử điểm đã duyệt, thông tin lớp hiện tại, trạng thái cảnh báo.
- Chuẩn hóa hiển thị điểm theo dạng `/10` để tránh nhầm với `%`.

### ✅ Fixed: MLOps status page
- **Files:** `frontend/admin.html`, `early_waring_backend/core/views.py`, `early_waring_backend/core/urls.py`
- Thêm API `GET /api/admin/mlops/status/` để đọc model hiện tại và kết quả retrain gần nhất từ `ml/saved_models`.
- Admin MLOps page giờ không còn chỉ là placeholder; có hiện tên model, F1 gần nhất, thời gian chạy gần nhất và quyết định accept/reject.

### ✅ Fixed: Public registration + student default role flow remains supported
- **Files:** `frontend/register.html`, `early_waring_backend/core/views.py`
- Luồng đăng ký public vẫn giữ role mặc định là `student`.
- Admin có thể nâng role lên `teacher` hoặc hạ về `student` sau đó.

### 🔎 Verification
- `python -m compileall core` chạy thành công sau khi sửa backend.
- Đã kiểm tra syntax script trong `frontend/admin.html`, `frontend/teacher.html`, `frontend/student.html` bằng `node --check`.
- `python manage.py check` chưa chạy được trong môi trường hiện tại vì Python đang thiếu Django package.

### ✅ Fixed: `register.html` 404 when opening public registration page
- **File:** `early_waring_backend/early_waring_backend/urls.py`
- Bổ sung route Django cho `register.html` để link từ trang login hoạt động đúng.
- Trang đăng ký public giờ được serve giống `index.html`, `admin.html`, `teacher.html`, `student.html`.

### ✅ Improved: Teacher `My Students` now supports class + risk filtering
- **File:** `frontend/teacher.html`
- Thêm lọc theo lớp ngay trong màn `My Students`.
- Thêm lọc theo `risk_level` gồm `High / Medium / Low / No Risk / Chưa có dự đoán`.
- Bộ lọc lớp được đồng bộ với class selector phía trên để giáo viên chuyển lớp và quản lý nhanh hơn.

### ✅ Updated: Website logo + tab icon now use `frontend/img/logo.png`
- **Files:** `frontend/index.html`, `frontend/register.html`, `frontend/admin.html`, `frontend/teacher.html`, `frontend/student.html`, `frontend/css/style.css`, `early_waring_backend/early_waring_backend/urls.py`
- Thay favicon mặc định trên tab bằng logo mới trong `frontend/img/logo.png`.
- Thêm serve route cho thư mục `img` để Django trả ảnh logo trực tiếp.
- Login/Register page và các sidebar dashboard giờ dùng logo ảnh mới thay cho hiển thị mặc định cũ.

### ✅ Added: All roles can edit their own profile
- **Files:** `frontend/admin.html`, `frontend/teacher.html`, `frontend/student.html`
- Admin, Teacher, Student giờ đều có modal `My Profile` khi bấm vào khu vực user ở topbar.
- Có thể tự cập nhật `họ tên`, `email`, `số điện thoại` thông qua `PUT /api/auth/me/`.
- Sau khi lưu, tên/avatar trên giao diện được refresh ngay mà không cần đăng nhập lại.
