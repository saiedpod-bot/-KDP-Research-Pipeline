# 🚀 KDP Research Pipeline — أنبوب أبحاث النشر الذاتي على أمازون

**منصة متكاملة لاكتشاف وتحليل الفرص الربحية في سوق Kindle Direct Publishing (KDP)**  
تجميع بيانات ⇒ تحليل ذكي ⇒ تصدير ⇒ لوحة تحكم تفاعلية ⇒ محرك اكتشاف متقدم

---

## 📋 المحتويات

- [عن الأداة](#-عن-الأداة)
- [الميزات الرئيسية](#-الميزات-الرئيسية)
- [البنية المعمارية](#-البنية-المعمارية)
- [طريقة التثبيت](#-طريقة-التثبيت)
- [طريقة الاستخدام](#-طريقة-الاستخدام)
  - [سطر الأوامر (CLI)](#-سطر-الأوامر-cli)
  - [لوحة التحكم (Dashboard)](#-لوحة-التحكم-streamlit-dashboard)
- [شرح المكونات](#-شرح-المكونات)
  - [Tier 1 — Scraper (التجميع)](#tier-1--scraper-التجميع)
  - [Tier 2 — Analyzer (التحليل)](#tier-2--analyzer-التحليل)
  - [Tier 3 — Exporter (التصدير)](#tier-3--exporter-التصدير)
  - [Tier 4 — Database & Config (قاعدة البيانات)](#tier-4--database--config-قاعدة-البيانات)
  - [Tier 5 — Dashboard (لوحة التحكم)](#tier-5--dashboard-لوحة-التحكم)
- [SmartScore — مقياس الفرصة الذكية](#-smartscore--مقياس-الفرصة-الذكية)
- [Gold Mine — منجم الفرص](#-gold-mine--منجم-الفرص)
- [الميزات المتقدمة](#-الميزات-المتقدمة)
  - [Smart Niche Discovery](#-smart-niche-discovery)
  - [New Release Mode](#-new-release-mode)
  - [Multi-Niche Tunneling](#-multi-niche-tunneling)
  - [Search Filters (rh)](#-search-filters-rh)
  - [Developer Mode](#-developer-mode)
  - [Settings Tab](#-settings-tab)
  - [History Tab](#-history-tab)
- [نظام Multi-Agent Pipeline](#-نظام-multi-agent-pipeline)
- [مخطوطة الكتاب](#-مخطوطة-الكتاب)
- [المصادر والمراجع](#-المصادر-والمراجع)
- [طرق الربط والتكامل](#-طرق-الربط-والتكامل)
- [هيكل المشروع](#-هيكل-المشروع)
- [الترخيص](#-الترخيص)

---

## 🎯 عن الأداة

**KDP Research Pipeline** هي منصة مفتوحة المصدر مصممة لمساعدة مؤلفي KDP (Kindle Direct Publishing) في:

1. **اكتشاف المجالات الربحية** — تحليل آلاف المنتجات وتحديد الفجوات في السوق
2. **تحليل المنافسين** — قياس المنافسة بذكاء عبر SmartScore
3. **تخطيط الكتب** — بمساعدة نظام Multi-Agent Orchestrator (33 وكيل ذكي)
4. **كتابة المحتوى** — توليد مخطوطات كاملة (مثال: 33,879 كلمة، 68 وصفة)
5. **مراقبة الأداء** — تتبع عمليات البحث السابقة واكتشاف المجالات الجديدة

> الأداة موجهة لمؤلفي KDP الجدد والمحترفين، تركز على **Low-FODMAP Kids' Cookbook** كدراسة حالة أولى.

---

## ✨ الميزات الرئيسية

| الميزة | الوصف |
|--------|-------|
| 🔍 **بحث متقدم** | 3 طرق بحث: كلمة مفتاحية، URL كامل (Tunneling)، منتجات محددة |
| 🧠 **SmartScore** | مقياس فرصة ذكي يجمع بين المبيعات والمنافسة |
| 💎 **Gold Mine** | كشف المنتجات ذات الطلب العالي والمنافسة المنخفضة |
| 📊 **لوحة تحكم** | Streamlit Dashboard مع 3 تبويبات وتصميم داكن |
| 🗄️ **SQLite** | حفظ سجل البحث والإعدادات محلياً (لا يحتاج سيرفر) |
| 🚀 **New Release Mode** | تصفية فقط الإصدارات الجديدة (آخر 30 يوم) |
| 🕳️ **Tunneling** | إدخال رابط أمازون مباشرة واستخراج البيانات |
| 🔗 **Smart Discovery** | اكتشاف كلمات مفتاحية ومجالات جديدة من المنتجات الحالية |
| 🔧 **Developer Mode** | إخفاء السجلات التقنية في لوحة التحكم |
| 🤖 **Multi-Agent** | 33 وكيل ذكي لتخطيط وكتابة الكتاب كاملاً |

---

## 🏗️ البنية المعمارية

```
┌─────────────────────────────────────────────────────────┐
│                    main.py / app.py                      │
│         (Orchestrator CLI + Streamlit UI)                │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ scraper  │→│ analyzer │→│ exporter │  │database │ │
│  │ .py      │  │ .py      │  │ .py      │  │ .py     │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐ │
│  │config_   │  │__init__  │  │  manuscript-*.md       │ │
│  │manager.py│  │.py       │  │  (8 files, 68 recipes) │ │
│  └──────────┘  └──────────┘  └───────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  SerpApi API  ←→  Amazon Search / Product API          │
└─────────────────────────────────────────────────────────┘
```

### مسار البيانات

```
بحث (SerpApi) → تصفية وتحليل → SmartScore → تصدير (Sheets/JSON) → Dashboard
```

---

## 📦 طريقة التثبيت

### المتطلبات الأساسية

- Python 3.9+
- مفتاح SerpApi (مجاني: 100 بحث/شهر) — [serpapi.com](https://serpapi.com)

### 1. تنزيل المشروع

```bash
git clone https://github.com/saiedpod-bot/-KDP-Research-Pipeline.git
cd KDP-Research-Pipeline
```

### 2. تثبيت المكتبات

```bash
pip install streamlit pandas serpapi requests gspread google-auth
```

### 3. إعداد مفتاح SerpApi

أنشئ ملف `.env` في مجلد المشروع:

```env
SERPAPI_KEY=your_serpapi_key_here
```

أو أدخله لاحقاً من واجهة Settings في Dashboard.

---

## 💻 طريقة الاستخدام

### ▶️ سطر الأوامر CLI

#### بحث سريع (صفحة واحدة)

```bash
python main.py "low fodmap cookbook for kids"
```

#### بحث عميق (5 صفحات)

```bash
python main.py "coloring books for adults" --max-pages 5 --min-price 7.00
```

#### تصدير إلى Google Sheets

```bash
python main.py "adhd planner" --max-pages 5 --sheet-id "1abc123..."
```

#### باراميترات سطر الأوامر

| الباراميتر | النوع | الافتراضي | الشرح |
|-----------|------|----------|-------|
| `query` | نص | إجباري | كلمة البحث على أمازون |
| `--max-pages` | رقم | 3 | عدد الصفحات (كل صفحة ≈ 20-50 منتج) |
| `--min-price` | رقم | 5.00 | أقل سعر للتصفية |
| `--sheet-id` | نص | — | معرف Google Sheet للتصدير |
| `--creds` | نص | credentials.json | مسار ملف المفاتيح |

---

### 🖥️ لوحة التحكم Streamlit Dashboard

```bash
streamlit run app.py
```

![Dashboard](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)

#### تبويبات Dashboard

##### 📊 تبويب Dashboard (الرئيسي)
- إدخال كلمة البحث
- اختيار عدد الصفحات (1-10)
- تحديد أقل سعر
- **New Release Mode** — checkbox لتصفية آخر 30 يوم
- **Search Filters (rh)** — حقل نصي لباراميترات أمازون المتقدمة
- **Multi-Niche Tunneling** — إدخال رابط أمازون مباشرة
- **Discover More** — اكتشاف مجالات جديدة من النتائج
- نتائج مع:
  - ASIN كرابط قابل للضغط
  - Est. Daily Sales (10000/BSR)
  - السعر بتنسيق $
  - SmartScore ملون

##### ⚙️ تبويب Settings
- **SerpApi Key** — حقل إدخال مشفر (Password)
- **Sheet ID** — معرف Google Sheet
- **Clear History** — مسح كل السجل
- الحفظ التلقائي في SQLite

##### 📜 تبويب History
- آخر 50 بحث مع التاريخ وعدد النتائج
- **Load Results** — تحميل نتائج بحث سابق
- **Delete** — حذف بحث
- **Discovery Queue** — عرض المجالات المكتشفة (قيد الانتظار / تم البحث)

##### 🔧 Developer Mode
- checkbox في الشريط الجانبي
- يخفي البطاقات الفنية وسجل الأخطاء
- يتم حفظ التفضيل في SQLite

---

## 🔬 شرح المكونات

### Tier 1 — Scraper (التجميع)

**الملف:** `core/scraper.py`

وظيفته: جلب البيانات من أمازون عبر SerpApi.

#### الدوال الرئيسية

| الدالة | الوظيفة |
|--------|---------|
| `fetch_amazon_data(query, api_key, page)` | جلب صفحة واحدة من نتائج البحث |
| `fetch_all_pages(query, api_key, max_pages, filter_params)` | جلب عدة صفحات مع إزالة التكرارات |
| `fetch_amazon_data_paginated(query, api_key, max_pages, filter_params)` | جلب مع ترقيم متسلسل |
| `search_and_format(query, api_key, max_pages, filter_params)` | جلب + تنسيق في خطوة واحدة |
| `fetch_product_details(asin, api_key)` | جلب تفاصيل منتج محدد (يكلف 1 رصيد) |
| `fetch_category_url(url, api_key)` | جلب بيانات من رابط أمازون مباشرة |
| `tunnel_category_pages(url, api_key, max_pages)` | تمرير عدة صفحات من رابط واحد |

**آلية التكرار (Backoff):** عند فشل الطلب، ينتظر 1 ثانية، ثم 2، ثم 4، ثم 8 — حتى 5 محاولات.

### Tier 2 — Analyzer (التحليل)

**الملف:** `core/analyzer.py`

وظيفته: تحليل البيانات وتحديد الفرص.

#### الدوال الرئيسية

| الدالة | الوظيفة |
|--------|---------|
| `run_analysis(rows)` | تحميل -> تصفية -> تسجيل -> حفظ |
| `find_gems_dataframe(df)` | كشف الجواهر باستخدام pandas |
| `find_low_competition_gems(rows)` | كشف الجواهر بدون pandas |
| `filter_by_price(rows, min_price)` | تصفية حسب السعر |

**شروط الجوهرة (Gem):**
- BSR < 50,000 (المنتج يبيع)
- ReviewCount < 30 (المنافسة منخفضة)

### Tier 3 — Exporter (التصدير)

**الملف:** `core/exporter.py`

وظيفته: تصدير النتائج إلى Google Sheets.

| الدالة | الوظيفة |
|--------|---------|
| `run_export(rows, sheet_id, creds_path)` | توثيق -> رفع -> كتابة |
| `export_with_service_account(rows, sheet_id, creds_path)` | رفع بحساب خدمة Google |

**مطلوب:** حساب خدمة Google مع تفعيل Google Sheets API.

### Tier 4 — Database & Config (قاعدة البيانات)

**الملف:** `core/database.py` + `core/config_manager.py`

#### SQLite Tables

| الجدول | الوظيفة |
|--------|---------|
| `search_history` | سجل عمليات البحث (50 إدخال) |
| `settings` | إعدادات (SerpApi key, Sheet ID, Developer Mode) |
| `discovery_queue` | قائمة الاكتشاف (مصطلحات + مصادر + نتائج) |

#### Config Manager — أولوية الإعدادات

1. **SQLite DB** — القيمة المحفوظة من واجهة Settings
2. **`.env`** — ملف البيئة
3. **Environment Variable** — متغير النظام
4. **الافتراضي** — قيمة فارغة

### Tier 5 — Dashboard (لوحة التحكم)

**الملف:** `app.py`

واجهة تفاعلية مبنية بـ **Streamlit** مع:
- تصميم داكن (`.streamlit/config.toml`)
- 3 تبويبات (Dashboard / Settings / History)
- شريط جانبي مع Developer Mode
- أعمدة تفاعلية: ASIN كرابط، ألوان حسب القيمة

---

## 🧠 SmartScore — مقياس الفرصة الذكية

```
SmartScore = ReviewCount / (BSR + 1)
```

- **ReviewCount عالي** = طلب قوي / دليل اجتماعي
- **BSR منخفض** = سرعة مبيعات عالية
- القسمة على `(BSR + 1)` تعاقب المنافسين الراسخين
- **النتيجة:** كلما زاد الرقم = فرصة أكبر

> ⚠️ **ملاحظة:** BSR حالياً 0 لجميع المنتجات (يحتاج API متقدم). حالياً SmartScore = ReviewCount.

---

## 💎 Gold Mine — منجم الفرص

بعد التحليل، يطبع النظام جدول **GOLD MINE** لأفضل 5 فرص:

```
+==========================================================+
|  GOLD MINE -- Top 5 Low-Competition Opportunities        |
+==========================================================+
| Rank ASIN               Score   Price  Reviews Rating |
|----- -------------- --------- ------- -------- ------ |
|    1 B0DZY2V81Z        0.0000    8.49        0    4.7 |
+==========================================================+
```

**ما هي الجوهرة؟**
1. **BSR < 50,000** — المنتج يبيع
2. **ReviewCount < 30** — قلة مراجعات = المجال غير مشبع

---

## 🚀 الميزات المتقدمة

### 🔍 Smart Niche Discovery

اكتشاف آلي لكلمات مفتاحية ومجالات جديدة من المنتجات الحالية.

**آلية العمل:**
1. `fetch_product_details(asin)` — يجلب تفاصيل 3 منتجات (يكلف 3 رصيد SerpApi)
2. `extract_discovery_terms(query, top_asins)` — يستخرج:
   - **Categories** (الدرجة: 90) — تصنيفات أمازون
   - **Bought Together** (الدرجة: 70) — منتجات تُشترى معاً
   - **Also Bought** (الدرجة: 40) — منتجات ذات صلة
3. يحفظ في `discovery_queue` مع مصدر كل مصطلح
4. يظهر في Dashboard مع أزرار "Search This" لكل مصطلح

### 🆕 New Release Mode

**تفعيل:** checkbox في Dashboard

```
filter_params = {"rh": "p_n_publication_date:1250226011"}
```

يُمرر مباشرة إلى SerpApi — يظهر فقط المنتجات المنشورة في آخر 30 يوم.

### 🕳️ Multi-Niche Tunneling

إدخال رابط أمازون مباشرة بدلاً من كلمة بحث:

```
https://www.amazon.com/gp/bestsellers/books/...  ← يدعمه
```

- `fetch_category_url(url, api_key)` — يجلب أي رابط أمازون عبر SerpApi `url` parameter
- `tunnel_category_pages(url, api_key, max_pages)` — يمرر صفحات متعددة

### 🔧 Search Filters (rh)

حقل نصي يمرر باراميترات `rh` مباشرة إلى SerpApi بدون تعديل:

```
p_n_publication_date:1250226011|p_n_condition-type:6350179011
```

يدعم **أي** فلتر متصفح أمازون.

### 👨‍💻 Developer Mode

checkbox في الشريط الجانبي:
- **ON:** يظهر كل شيء (بطاقات الحالة، سجل الأخطاء)
- **OFF:** يخفي التفاصيل التقنية
- يُحفظ التفضيل في SQLite

---

## 🤖 نظام Multi-Agent Pipeline

**الملفات:** `multi-agent-full-pipeline.md`, `multi-agent-niche-research.md`

نظام تخطيط وإنتاج كامل بـ **33 وكيل ذكي** موزعين على 8 مراحل:

| المرحلة | عدد الوكلاء | الوظيفة |
|---------|-------------|---------|
| 1. Niche Research | 6+1 | أبحاث السوق المتعمقة |
| 2. Content Creation | 3 | تخطيط + كتابة + مراجعة |
| 3. Formatting & Layout | 2 | تنسيق إلكتروني + طباعي |
| 4. Cover Design | 4 | تصميم الغلاف الأمامي + الخلفي |
| 5. Listing Optimization | 4 | عنوان + وصف + كلمات مفتاحية + A+ |
| 6. Amazon Ads | 6 | إعلانات أمازون المُدارة |
| 7. Launch Strategy | 4 | خطة إطلاق متكاملة |
| 8. Post-Launch Monitoring | 4 | مراقبة + تحديثات |

### نموذج دراسة الحالة: Low-FODMAP Kids' Cookbook

**تم إنجاز:** المرحلة 1 (Niche Research) + المرحلة 2 (Content Creation)
- **26 فصلاً** في 8 أجزاء
- **68 وصفة** (33,879 كلمة)
- **استهداف:** 10-15% من الأطفال المصابين بـ IBS
- **المنافس الوحيد:** "The Kid-Friendly ADHD & Autism Cookbook" (742 مراجعة، 4.5★)

---

## 📖 مخطوطة الكتاب

**8 ملفات مخطوطة كاملة:**

| الملف | المحتوى |
|-------|---------|
| `manuscript-frontmatter-part1.md` | المقدمة + الجزء 1: أساسيات Low-FODMAP |
| `manuscript-part2-breakfasts.md` | الجزء 2: وجبات الإفطار |
| `manuscript-part3-lunchbox.md` | الجزء 3: وجبات المدرسة |
| `manuscript-part4-dinner.md` | الجزء 4: وجبات العشاء |
| `manuscript-part5-snacks.md` | الجزء 5: الوجبات الخفيفة |
| `manuscript-part6-desserts.md` | الجزء 6: الحلويات |
| `manuscript-part7-drinks.md` | الجزء 7: المشروبات |
| `manuscript-part8-backmatter.md` | الجزء 8: الخاتمة + الملاحق |

**الطول التقديري:** 200-250 صفحة مطبوعة

---

## 📚 المصادر والمراجع

### APIs المستخدمة

| المصدر | النوع | التكلفة | الاستخدام |
|--------|------|---------|-----------|
| [SerpApi](https://serpapi.com) | Amazon Search API | مجاني: 100/شهر | بحث أمازون |
| [SerpApi Product API](https://serpapi.com/product-search) | Amazon Product API | 1 رصيد/ASIN | تفاصيل المنتج |
| [Google Sheets API](https://console.cloud.google.com) | Google API | مجاني | تصدير البيانات |

### المكتبات

| المكتبة | الاستخدام |
|---------|-----------|
| `streamlit` | لوحة التحكم |
| `pandas` | تحليل البيانات |
| `serpapi` | واجهة أمازون |
| `requests` | اتصالات HTTP |
| `gspread` | Google Sheets |

### مراجع KDP

- [KDP Help](https://kdp.amazon.com/en_US/help)
- [KDP Royalty Calculator](https://kdp.amazon.com/en_US/royalty-calculator)
- [Amazon Bestsellers Rank](https://www.amazon.com/gp/bestsellers/books)

---

## 🔗 طرق الربط والتكامل

### 1. مع Google Sheets

```
python main.py "بحث" --sheet-id "1abc..."
```

**التحضير:**
1. حساب خدمة في Google Cloud Console
2. تفعيل Google Sheets API
3. رفع `credentials.json` في جذر المشروع

### 2. مع SerpApi

مباشر عبر متغير البيئة أو واجهة Settings:
- `.env` → `SERPAPI_KEY=...`
- Dashboard → Settings → SerpApi Key

### 3. PyInstaller (تطبيق مستقل)

```bash
pip install pyinstaller
pyinstaller build.spec
```

النتيجة:
- `dist/KDP_Pipeline.exe` — بدون كونسول
- `dist/KDP_Pipeline_DEBUG.exe` — مع كونسول للتصحيح

---

## 📁 هيكل المشروع

```
.
├── app.py                          # Streamlit Dashboard
├── main.py                         # CLI Pipeline
├── build.spec                      # PyInstaller config
├── config.json                     # API safety lock
├── .env                            # SerpApi key (gitignored)
├── .gitignore
├── README.md
│
├── core/                           # ⭐ الحزمة الأساسية
│   ├── __init__.py                 # تصدير الحزمة
│   ├── scraper.py                  # التجميع من أمازون
│   ├── analyzer.py                 # التحليل والتسجيل
│   ├── exporter.py                 # التصدير لـ Google Sheets
│   ├── database.py                 # SQLite
│   └── config_manager.py           # إدارة الإعدادات
│
├── src/                            # الإصدار القديم (احتياطي)
│   ├── scraper.py
│   ├── analyzer.py
│   └── exporter.py
│
├── manuscript-*.md                 # 8 ملفات مخطوطة (68 وصفة)
├── system-prompt-kdp.md            # دليل الخبير KDP
├── multi-agent-full-pipeline.md    # 33 وكيل ذكي
├── multi-agent-niche-research.md   # 6 وكلاء أبحاث
├── memory-repository.md            # مستودع الذاكرة
├── project_state.json              # حالة المشروع
│
├── database/                       # SQLite (gitignored)
├── output/                         # نتائج (gitignored)
└── .streamlit/
    └── config.toml                 # ثيم داكن
```

---

## 📜 الترخيص

**MIT License** — استخدم، عدل، وزع بحرية.

---

> **تم التطوير بواسطة [saiedpod-bot](https://github.com/saiedpod-bot)**
> 
> لأي استفسار: افتح Issue في GitHub
>
> *آخر تحديث: يونيو 2026*
