# 🔍 Meme Token Scanner

**ماسح أمني شامل لعملات الميم - اكتشف المخاطر قبل التداول**

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ المميزات

### 🔐 التحليلات الأمنية
- **كشف Honeypot** - تحليل ثابت + ديناميكي
- **كشف Mint Function** - تحديد مخاطر التضخم
- **تحليل الضرائب** - كشف الضرائب الخفية
- **التحقق من الملكية** - التأكد من renounceOwnership
- **فحص قفل LP** - التحقق من قفل السيولة
- **تحليل تركيز الحيازات** - كشف السيطرة

### 🌐 الشبكات المدعومة
- Ethereum (ETH)
- BNB Smart Chain (BSC)
- Polygon
- Base
- Arbitrum
- Solana
- Avalanche

### 📊 مصادر البيانات
- **GoPlus Security** - API أمني احترافي
- **DEXScreener** - بيانات DEX الفورية
- **GeckoTerminal** - بيانات السوق

### 📱 دعم Termux
- إشعارات النظام
- تنبيهات صوتية
- TTS

## ⚡ التثبيت السريع

```bash
# على Termux
pkg update && pkg install python git -y
git clone https://github.com/albarahayham/meme-scan.git
cd meme-scan
pip install -r requirements.txt
python src/cli.py --help
```

## 🚀 أمثلة الاستخدام

```bash
# فحص سلسلة BSC
python src/cli.py scan --chain bsc --limit 50

# تحليل توكن محدد
python src/cli.py analyze --chain eth --address 0x...

# مراقبة مستمرة
python src/cli.py monitor --chains bsc,eth,polygon

# البحث عن توكن
python src/cli.py search "PEPE"
```

## 📊 مخرجات

| التنسيق | الوصف |
|---------|-------|
| JSON | تصدير كامل لجميع البيانات |
| CSV | جدول بيانات للتحليل |
| CLI | جداول ملونة في الطرفية |

## ⚠️ تنبيه قانوني

**هذه الأداة للتحليل فقط. لا تنفذ أي معاملات on-chain.**
المستخدم مسؤول عن امتلاكه للقوانين المحلية.

## 📜 الرخصة

MIT License - انظر ملف LICENSE

---

**⚠️ تذكر: هذا البرنامج للتحليل فقط. لا تستثمر أكثر مما تستطيع خسارته. DYOR!**
