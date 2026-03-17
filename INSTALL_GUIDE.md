# 📱 دليل التثبيت الكامل على Termux

## دليل تفصيلي خطوة بخطوة لتشغيل Meme Token Scanner على Android

---

## 📋 المتطلبات المسبقة

### 1. تحميل التطبيقات المطلوبة

قم بتحميل التطبيقات التالية من F-Droid (مهم: لا تحمل من Google Play):

| التطبيق | المصدر | الملاحظة |
|---------|--------|----------|
| **Termux** | F-Droid | تطبيق الطرفية |
| **Termux:API** | F-Droid | للإشعارات والوظائف الإضافية |
| **Termux:Styling** | F-Droid | (اختياري) لتخصيص المظهر |

> ⚠️ **تحذير مهم**: قم بتحميل Termux من **F-Droid فقط** وليس من Google Play، لأن نسخة Google Play قديمة ولا تعمل بشكل صحيح.

### روابط التحميل:
```
https://f-droid.org/packages/com.termux/
https://f-droid.org/packages/com.termux.api/
https://f-droid.org/packages/com.termux.styling/
```

---

## 🔧 الخطوة 1: تحديث Termux

افتح تطبيق Termux وانتظر حتى يكتمل التحميل، ثم نفذ:

```bash
# تحديث قائمة الحزم
pkg update

# تحديث الحزم المثبتة
pkg upgrade -y

# إذا طلب تأكيد، اضغط y ثم Enter
```

**⏱️ الوقت المتوقع:** 2-5 دقائق حسب سرعة الإنترنت

---

## 📦 الخطوة 2: تثبيت الحزم الأساسية

```bash
# تثبيت Python و Git والأدوات الأساسية
pkg install python python-pip git wget curl -y

# تثبيت أدوات الصوت (للإشعارات الصوتية)
pkg install ffmpeg pulseaudio -y

# تثبيت Termux API (مهم للإشعارات)
pkg install termux-api -y
```

**⏱️ الوقت المتوقع:** 3-5 دقائق

---

## 🔑 الخطوة 3: منح صلاحيات التطبيق

### 3.1 منح صلاحية التخزين

```bash
# طلب صلاحية التخزين
termux-setup-storage

# سيظهر مربع حوار - اضغط "سماح" أو "Allow"
```

### 3.2 منح صلاحية الإشعارات

1. اخرج من Termux (اضغط Home)
2. اذهب إلى: **الإعدادات** → **التطبيقات** → **Termux**
3. اضغط على **الأذونات** أو **Permissions**
4. فعّل: **الإشعارات** و **الاهتزاز**

### 3.3 اختبار صلاحيات الإشعارات

```bash
# اختبار الإشعارات
termux-notification --title "اختبار" --content "الإشعارات تعمل!"

# اختبار الاهتزاز
termux-vibrate -d 500
```

---

## 📁 الخطوة 4: تحميل المشروع

### الطريقة A: من GitHub (إذا كان المشروع مرفوعاً)

```bash
# الانتقال إلى مجلد التخزين المشترك
cd ~/storage/downloads

# تحميل المشروع
git clone https://github.com/your-username/meme-scan.git

# الدخول إلى مجلد المشروع
cd meme-scan
```

### الطريقة B: نقل الملفات يدوياً (إذا كانت الملفات على جهازك)

1. انسخ مجلد المشروع إلى:
   ```
   /storage/emulated/0/Download/meme-scan
   ```

2. في Termux:
   ```bash
   # الانتقال إلى مجلد التحميلات
   cd ~/storage/downloads/meme-scan
   
   # التحقق من وجود الملفات
   ls -la
   ```

---

## 🐍 الخطوة 5: إنشاء بيئة افتراضية (موصى به)

```bash
# التأكد من وجود pip
python -m pip install --upgrade pip

# إنشاء بيئة افتراضية
python -m venv venv

# تفعيل البيئة الافتراضية
source venv/bin/activate

# سيظهر (venv) قبل سطر الأوامر
```

---

## 📚 الخطوة 6: تثبيت المكتبات

```bash
# تثبيت جميع المكتبات المطلوبة
pip install -r requirements.txt

# إذا حدث خطأ، جرب:
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**⏱️ الوقت المتوقع:** 5-10 دقائق

### إذا واجهت مشاكل في التثبيت:

```bash
# تثبيت المكتبات الأساسية فقط
pip install aiohttp web3 eth-utils rich pyyaml tenacity python-dotenv

# ثم الباقي
pip install websockets tabulate cachetools orjson pytest pytest-asyncio
```

---

## ⚙️ الخطوة 7: إعداد التكوين

```bash
# إنشاء مجلد التكوين
mkdir -p ~/.config/meme-scan

# نسخ ملف التكوين النموذجي
cp config.example.yaml ~/.config/meme-scan/config.yaml

# تعديل التكوين (اختياري)
nano ~/.config/meme-scan/config.yaml
# أو
vim ~/.config/meme-scan/config.yaml
```

### إعداد مفاتيح API (اختياري لكن موصى به)

```bash
# إنشاء ملف المتغيرات البيئية
nano ~/.config/meme-scan/credentials

# أضف الأسطر التالية:
export GOPPLUS_API_KEY="your-goplus-api-key"
export COINGECKO_API_KEY="your-coingecko-api-key"

# حفظ الملف: Ctrl+O ثم Enter ثم Ctrl+X
```

---

## ✅ الخطوة 8: اختبار التثبيت

```bash
# اختبار syntax الكود
python -m py_compile src/cli.py

# عرض المساعدة
python src/cli.py --help

# اختبار التكوين
python src/cli.py config --show
```

---

## 🚀 الخطوة 9: التشغيل الأول

### اختبار سريع

```bash
# فحص سلسلة BSC (10 توكنات فقط للتجربة)
python src/cli.py scan --chain bsc --limit 10

# تحليل توكن محدد
python src/cli.py analyze --chain bsc --address 0x1234...
```

### تشغيل المراقبة المستمرة

```bash
# مراقبة BSC مع الإشعارات
python src/cli.py monitor --chains bsc --interval 60 --notify
```

---

## 🌙 الخطوة 10: التشغيل في الخلفية

### الطريقة A: باستخدام tmux (موصى به)

```bash
# تثبيت tmux
pkg install tmux -y

# إنشاء جلسة جديدة
tmux new -s scanner

# تشغيل الماسح
python src/cli.py monitor --chains bsc,eth --interval 30

# فصل الجلسة (البرنامج يظل يعمل): اضغط Ctrl+B ثم D

# للعودة للجلسة لاحقاً:
tmux attach -t scanner

# عرض جميع الجلسات
tmux ls

# إنهاء الجلسة
tmux kill-session -t scanner
```

### الطريقة B: باستخدام nohup

```bash
# تشغيل في الخلفية
nohup python src/cli.py monitor --chains bsc > scanner.log 2>&1 &

# معرفة رقم العملية
ps aux | grep python

# إيقاف العملية
kill <PID>
```

### الطريقة C: استخدام svc (تسريع الـ I/O)

```bash
# تقليل استخدام البطارية
termux-wake-lock  # منع النوم

# عند الانتهاء
termux-wake-unlock
```

---

## 📱 الخطوة 11: إنشاء اختصار سريع

```bash
# تحرير ملف bashrc
nano ~/.bashrc

# أضف الأسطر التالية في نهاية الملف:

# === Meme Scanner Shortcuts ===
alias mscan='cd ~/storage/downloads/meme-scan && source venv/bin/activate'
alias scan-bsc='python src/cli.py scan --chain bsc'
alias scan-eth='python src/cli.py scan --chain eth'
alias monitor-all='python src/cli.py monitor --chains bsc,eth,polygon'

# حفظ الملف ثم تفعيل:
source ~/.bashrc
```

---

## 🔧 استكشاف الأخطاء وإصلاحها

### مشكلة: "Permission denied"

```bash
# منح صلاحية التنفيذ
chmod +x src/cli.py

# منح صلاحيات التخزين مرة أخرى
termux-setup-storage
```

### مشكلة: "Module not found"

```bash
# التأكد من تفعيل البيئة الافتراضية
source venv/bin/activate

# إعادة تثبيت المكتبات
pip install -r requirements.txt --force-reinstall
```

### مشكلة: "Connection refused" أو "Network error"

```bash
# التحقق من الاتصال
ping google.com

# قد تحتاج لاستخدام VPN أو تغيير DNS
```

### مشكلة: الإشعارات لا تعمل

```bash
# التحقق من تثبيت Termux:API
pkg list-installed | grep termux-api

# إذا لم يكن مثبتاً:
pkg install termux-api

# اختبار الإشعارات
termux-notification --title "Test" --content "Hello"
```

### مشكلة: "Externally managed environment"

```bash
# في Termux الجديد، استخدم البيئة الافتراضية دائماً
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 جدول الأوامر السريعة

| الأمر | الوظيفة |
|-------|---------|
| `python src/cli.py scan --chain bsc --limit 50` | فحص 50 توكن على BSC |
| `python src/cli.py analyze --chain eth -a 0x...` | تحليل توكن محدد |
| `python src/cli.py monitor --chains bsc,eth` | مراقبة مستمرة |
| `python src/cli.py search "PEPE"` | البحث عن توكن |
| `python src/cli.py config --show` | عرض التكوين |
| `tmux attach -t scanner` | العودة للجلسة الخلفية |

---

## 🔋 توفير البطارية

```bash
# تقليل تكرار الفحص
python src/cli.py monitor --chains bsc --interval 120

# تقليل عدد التوكنات
python src/cli.py scan --chain bsc --limit 20

# إيقاف الاهتزاز والصوت
python src/cli.py monitor --chains bsc --no-sound
```

---

## 📌 نصائح مهمة

1. **التحديث الدوري**: قم بتحديث الحزم أسبوعياً
   ```bash
   pkg update && pkg upgrade -y
   ```

2. **النسخ الاحتياطي**: احتفظ بنسخة من ملف التكوين
   ```bash
   cp ~/.config/meme-scan/config.yaml ~/storage/downloads/config_backup.yaml
   ```

3. **مراقبة الموارد**: استخدم `htop` لمراقبة الاستخدام
   ```bash
   pkg install htop
   htop
   ```

4. **السجلات**: تحقق من السجلات عند وجود مشاكل
   ```bash
   tail -f logs/scan-$(date +%Y%m%d).log
   ```

---

## ✨ تهانينا!

المشروع جاهز للعمل على Termux. للتشغيل السريع:

```bash
cd ~/storage/downloads/meme-scan
source venv/bin/activate
python src/cli.py scan --chain bsc --limit 20 --notify
```

🚀 **ابدأ الآن واكتشف فرص التداول الآمن!**
