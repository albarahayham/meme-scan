# 🚀 دليل رفع المشروع إلى GitHub

## 📋 المتطلبات

- حساب GitHub (إن لم يكن لديك، أنشئ واحداً على [github.com](https://github.com))
- Git مثبت على جهازك

---

## 🔧 الخطوة 1: إنشاء مستودع جديد على GitHub

### 1.1 الدخول إلى GitHub

1. افتح المتصفح واذهب إلى: **https://github.com**
2. سجل دخولك بحسابك

### 1.2 إنشاء مستودع جديد

1. اضغط على زر **+** في أعلى اليمين
2. اختر **New repository**

### 1.3 إعداد المستودع

```
Repository name: meme-scan
Description: 🔍 Meme Token Security Scanner - Analyze and detect risks in new tokens
Visibility: ✅ Public (أو Private إذا تريد)
```

**⚠️ مهم:** 
- ❌ **لا** تضع علامة على "Add a README file"
- ❌ **لا** تضع علامة على "Add .gitignore"
- ❌ **لا** تختار License (لأننا لديها بالفعل)

4. اضغط **Create repository**

---

## 💻 الخطوة 2: إعداد Git على جهازك

### 2.1 تثبيت Git (إذا لم يكن مثبتاً)

**على Linux/Termux:**
```bash
pkg install git -y   # على Termux
# أو
sudo apt install git -y   # على Ubuntu/Debian
```

**على Windows:**
- حمل من: https://git-scm.com/download/win

### 2.2 إعداد Git (أول مرة فقط)

```bash
# تعيين اسم المستخدم
git config --global user.name "اسمك"

# تعيين البريد الإلكتروني (نفس بريد GitHub)
git config --global user.email "your-email@example.com"

# التحقق
git config --global --list
```

---

## 🔐 الخطوة 3: إعداد التوثيق مع GitHub

### الطريقة A: باستخدام Personal Access Token (الأسهل)

#### 3.1 إنشاء Token

1. اذهب إلى GitHub → **Settings**
2. من القائمة الجانبية: **Developer settings**
3. اضغط **Personal access tokens** → **Tokens (classic)**
4. اضغط **Generate new token (classic)**
5. املأ:
   - Note: `meme-scan-upload`
   - Expiration: `No expiration` أو حسب رغبتك
   - Select scopes: فعّل **repo** (جميع خيارات repo)
6. اضغط **Generate token**
7. **⚠️ انسخ الـ Token فوراً** (لن تتمكن من رؤيته مرة أخرى!)

#### 3.2 حفظ Token للاستخدام

```bash
# على Linux/Termux
echo "export GH_TOKEN='your_token_here'" >> ~/.bashrc
source ~/.bashrc
```

### الطريقة B: باستخدام SSH Keys

```bash
# إنشاء مفتاح SSH
ssh-keygen -t ed25519 -C "your-email@example.com"
# اضغط Enter لجميع الأسئلة

# عرض المفتاح العام
cat ~/.ssh/id_ed25519.pub

# انسخ المفتاح وأضفه في GitHub → Settings → SSH Keys
```

---

## 📤 الخطوة 4: رفع المشروع

### 4.1 الدخول إلى مجلد المشروع

```bash
cd /home/z/my-project/meme-scan
```

### 4.2 تهيئة Git

```bash
# تهيئة مستودع Git جديد
git init

# إضافة جميع الملفات
git add .

# أو إضافة ملفات محددة
git add src/ tests/ requirements.txt README.md LICENSE config.example.yaml .gitignore

# التحقق من الملفات المضافة
git status
```

### 4.3 إنشاء أول commit

```bash
git commit -m "🎉 Initial commit: Meme Token Scanner

Features:
- Multi-chain support (ETH, BSC, Polygon, Base, etc.)
- Security detectors (Honeypot, Mint, Tax, LP Lock, etc.)
- GoPlus, DEXScreener, GeckoTerminal APIs
- Rich CLI with colored output
- Termux notifications support
- Async processing with rate limiting"
```

### 4.4 ربط المستودع المحلي بـ GitHub

```bash
# استبدل YOUR_USERNAME باسم مستخدم GitHub الخاص بك
git remote add origin https://github.com/YOUR_USERNAME/meme-scan.git

# أو باستخدام SSH:
git remote add origin git@github.com:YOUR_USERNAME/meme-scan.git
```

### 4.5 رفع الكود

```bash
# تغيير الفرع إلى main
git branch -M main

# رفع الملفات
git push -u origin main
```

**إذا طلب كلمة مرور:**
- Username: اسم مستخدم GitHub
- Password: استخدم الـ **Personal Access Token** (وليس كلمة مرور GitHub)

---

## ✅ الخطوة 5: التحقق من الرفع

1. افتح المتصفح واذهب إلى:
   ```
   https://github.com/YOUR_USERNAME/meme-scan
   ```

2. يجب أن ترى جميع الملفات!

---

## 🔄 أوامر Git المفيدة

### رفع تحديثات جديدة

```bash
# التحقق من التغييرات
git status

# إضافة الملفات المتغيرة
git add .

# إنشاء commit
git commit -m "وصف التغيير"

# رفع التحديثات
git push
```

### عرض السجل

```bash
# عرض تاريخ الـ commits
git log --oneline

# عرض تفاصيل commit معين
git show <commit-hash>
```

### التراجع عن تغييرات

```bash
# التراجع عن تغييرات في ملف (قبل add)
git checkout -- filename.py

# التراجع عن آخر commit (قبل push)
git reset --soft HEAD~1
```

---

## 🌟 تحسين المستودع (اختياري)

### إضافة مواضيع (Topics)

1. اذهب للمستودع على GitHub
2. اضغط على **⚙️ Settings**
3. أضف Topics:
   ```
   python, crypto, memecoin, security-scanner, 
   ethereum, bsc, blockchain, termux, 
   honeypot-detector, dexscreener
   ```

### إضافة About

1. اضغط **⚙️** بجانب "About"
2. أضف وصف:
   ```
   🔍 Comprehensive meme token security scanner with 
   honeypot detection, multi-chain support, and Termux integration
   ```
3. أضف رابط Demo أو Website إن وجد

### إضافة Social Preview

1. اذهب إلى Settings → General
2. ارفع صورة للمستودع (1200x630 px)

---

## 📋 ملخص سريع

```bash
# 1. إنشاء مستودع على GitHub
# 2. تهيئة Git
git init
git add .
git commit -m "Initial commit"

# 3. ربط ورفع
git remote add origin https://github.com/YOUR_USERNAME/meme-scan.git
git branch -M main
git push -u origin main
```

---

## ⚠️ أخطاء شائحة وحلولها

### خطأ: "remote origin already exists"

```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/meme-scan.git
```

### خطأ: "Authentication failed"

```bash
# استخدم Token بدلاً من كلمة المرور
git remote set-url origin https://TOKEN@github.com/YOUR_USERNAME/meme-scan.git
```

### خطأ: "Push rejected"

```bash
# اجلب التغييرات أولاً
git pull origin main --rebase
git push -u origin main
```

---

## 🎉 تهانينا!

مشروعك الآن على GitHub:
**https://github.com/YOUR_USERNAME/meme-scan**

يمكن لأي شخص تحميله:
```bash
git clone https://github.com/YOUR_USERNAME/meme-scan.git
```
