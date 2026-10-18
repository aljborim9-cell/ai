# AI Universe — Telegram Bot

نسخة Telegram من واجهة AI Universe HTML، تعمل كبوت Python على استضافة تدعم تشغيل Background Worker مثل Render أو VPS.

## الميزات
- دردشة عربية عبر Groq API.
- سجل محادثة مؤقت لكل مستخدم.
- اختيار نموذج باستخدام `/model`.
- توليد الصور عبر خدمة Pollinations باستخدام `/image`.
- أوامر `/start` و`/help` و`/new` و`/models`.

## التشغيل محلياً
1. أنشئ بوتاً من `@BotFather` وخذ `TELEGRAM_BOT_TOKEN`.
2. أنشئ مفتاحاً من لوحة Groq وخذ `GROQ_API_KEY`.
3. ثبّت Python 3.10 أو أحدث.
4. ثبّت الحزم:
   ```bash
   pip install -r requirements.txt
   ```
5. عيّن متغيرات البيئة ثم شغّل:
   ```bash
   python bot.py
   ```

## النشر على Render
1. ارفع محتويات هذا المجلد إلى مستودع GitHub.
2. في Render اختر **New + → Blueprint** وحدد المستودع الذي يحتوي `render.yaml`.
3. أضف `TELEGRAM_BOT_TOKEN` و`GROQ_API_KEY` في Environment، ولا تضع المفاتيح داخل الكود.
4. ابدأ النشر. الخدمة من نوع Worker ولا تحتاج رابط موقع.

## أوامر البوت
- `/start` — بدء الاستخدام
- `/new` — مسح سياق المحادثة الحالي
- `/models` — عرض النماذج
- `/model llama` — اختيار Llama 3.3 70B
- `/model fast` — اختيار Llama 3.1 8B
- `/model oss120` — اختيار GPT-OSS 120B
- `/model oss20` — اختيار GPT-OSS 20B
- `/image وصف الصورة` — توليد صورة

## ملاحظات مهمة
- سجل المحادثات محفوظ في الذاكرة فقط، ويُمسح عند إعادة تشغيل الخدمة. يمكن تطويره لاحقاً إلى SQLite أو PostgreSQL.
- توليد الصور يعتمد على خدمة خارجية، وقد تتغير إتاحتها أو حدودها.
- لا ترفع ملف `.env` أو مفاتيح API إلى GitHub.
- **الأمان:** ملف HTML الأصلي يحتوي مفاتيح API مكتوبة داخله. اعتبر المفاتيح مكشوفة، ألغِها/دوّرها من مزود الخدمة وأنشئ مفاتيح جديدة قبل النشر.
