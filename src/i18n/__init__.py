"""i18n catalogs: English, Persian (Farsi), Arabic."""

from __future__ import annotations

from typing import Any

SUPPORTED = ("en", "fa", "ar")

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "help": (
            "*Quran Recitation Sharing Bot*\n"
            "Share the Quran in this group by page, surah, hizb, or juz.\n\n"
            "*Everyone*\n"
            "• `/help` — this message\n"
            "• `/lang en|fa|ar` — set group language\n"
            "• `/status` — cycle progress\n"
            "• `/available` — free portions\n"
            "• `/claim <n>` — claim a portion\n"
            "• `/release <n>` — release your claim\n"
            "• `/done <n>` — mark portion complete\n"
            "• `/mine` — your claims\n"
            "• `/settings` — group settings\n"
            "• `/plan …` — personal recitation plan (DM)\n\n"
            "*Admins*\n"
            "• `/startcycle` — open a new cycle\n"
            "• `/granularity page|surah|hizb|juz|quran` — recitation unit\n"
            "• `/cycle daily|weekly|monthly|<N>d` — cycle length\n"
            "• `/reminders off|daily|<N>h|<N>d` — completion reminders\n"
            "• `/advertise off|daily|<N>h|<N>d` — open-spot announcements\n"
            "• `/niyyah [text]` — set/clear intention (نیت)\n"
            "• `/admin add|remove <@user|id>` — manage admins\n"
            "• `/admins` — list admins"
        ),
        "cycle_started": "New cycle *#{cycle}* started — {total} × {unit}. Claim with /claim.",
        "niyyah_set": "Intention (نیت) set:\n_{niyyah}_",
        "niyyah_cleared": "Intention (نیت) cleared.",
        "niyyah_current": "Current intention (نیت):\n_{niyyah}_",
        "niyyah_none": "No intention (نیت) set for this cycle.",
        "claim_ok": "You claimed {unit} *{num}*. May Allah accept it.\nRead: {link}",
        "claim_taken": "{unit} *{num}* is already claimed by {name}.",
        "claim_invalid": "Please choose a {unit} number from 1 to {total}.",
        "claim_no_cycle": "No active cycle. An admin should run /startcycle.",
        "release_ok": "Released {unit} *{num}*.",
        "release_not_yours": "You do not hold {unit} *{num}*.",
        "done_ok": "Marked {unit} *{num}* as done. جزاكم الله خيراً",
        "done_not_yours": "You can only mark your own claimed portions as done.",
        "available_header": "*Available {unit}* ({count}/{total} free):",
        "available_none": "All {total} portions are claimed this cycle.",
        "status_header": "*Cycle #{cycle}* — {claimed} claimed, {done} done, {free} free",
        "status_niyyah": "نیت: _{niyyah}_",
        "status_claims": "*Claims:*\n{lines}",
        "status_empty": "No claims yet. Use /claim.",
        "mine_header": "*Your claims this cycle:*\n{lines}",
        "mine_empty": "You have nothing claimed this cycle.",
        "lang_set": "Group language set to *English*.",
        "lang_invalid": "Supported languages: `en`, `fa`, `ar`.",
        "admin_only": "Only group admins can run this command.",
        "admin_added": "Added admin: {id}",
        "admin_removed": "Removed admin: {id}",
        "admin_list": "*Admins:*\n{lines}",
        "admin_need_id": "Usage: `/admin add|remove <whatsapp_user_id>`",
        "unknown": "Unknown command. Send `/help`.",
        "claim_line": "• {unit} {num} — {name} ({status})",
        "status_claimed": "claimed",
        "status_done": "done",
        "bootstrapped": "You are now an admin for this group.",
        # Units
        "unit_page": "Page",
        "unit_surah": "Surah",
        "unit_hizb": "Hizb",
        "unit_juz": "Juz",
        "unit_quran": "Quran",
        # Settings
        "granularity_set": "Recitation unit set to *{unit}* ({total} portions). Applies from the next cycle.",
        "granularity_invalid": "Usage: `/granularity page|surah|hizb|juz|quran`",
        "cycle_spec_set": "Cycle length set to *{spec}*. Applies from the next cycle.",
        "cycle_spec_invalid": "Usage: `/cycle daily|weekly|monthly|<N>d`",
        "reminders_set": "Completion reminders enabled: every *{spec}*.",
        "reminders_off": "Completion reminders turned off.",
        "reminders_invalid": "Usage: `/reminders off|daily|weekly|<N>h|<N>d`",
        "advertise_set": "Open-spot announcements enabled: every *{spec}*.",
        "advertise_off": "Open-spot announcements turned off.",
        "advertise_invalid": "Usage: `/advertise off|daily|weekly|<N>h|<N>d`",
        "settings_overview": (
            "*Group settings*\n"
            "• Unit: {unit} ({total} portions)\n"
            "• Cycle: {cycle_spec}\n"
            "• Reminders: {reminder_spec}\n"
            "• Open-spot ads: {ad_spec}"
        ),
        # Scheduled messages
        "reminder_message": "Reminder — pending recitation this cycle:\n{lines}\nMark complete with `/done <n>`.",
        "reminder_line": "• {unit} {num} — {link}",
        "ad_message": "*Open spots* ({count} free):\n{lines}\nClaim with `/claim <n>`.",
        "cycle_rollover": "Cycle *#{cycle}* has started — {total} × {unit} available. Claim with /claim.",
        # Personal plans
        "plan_usage": (
            "Personal plan commands:\n"
            "• `/plan start <count> <page|surah|hizb|juz> <daily|weekly|monthly|Nd>` — e.g. `/plan start 1 juz daily`\n"
            "• `/plan status` — your progress\n"
            "• `/plan done` — complete current portion\n"
            "• `/plan stop` — stop the plan"
        ),
        "plan_started": "Personal plan started: {count} × {unit} every {spec}.\nFirst portion: {unit} {range} of {total}.\nRead: {link}",
        "plan_status": "*Personal plan*: {done}/{total} {unit} done (khatms: {khatm}).\nCurrent portion: {unit} {range}.\nRead: {link}\nComplete with `/plan done`.",
        "plan_done": "Portion complete, may Allah accept it. Next: {unit} {range} of {total}.\nRead: {link}",
        "plan_khatm": "Takbir! You completed a full khatm (total: {khatm}). Starting again from {unit} 1.",
        "plan_stopped": "Personal plan stopped.",
        "plan_none": "No active personal plan. Start one with `/plan start 1 juz daily`.",
        "plan_checkin": "Your recitation portion: {unit} {range}.\nRead: {link}\nReply `/plan done` when complete.",
    },
    "fa": {
        "help": (
            "*ربات تقسیم تلاوت قرآن*\n"
            "تقسیم قرآن در این گروه بر اساس صفحه، سوره، حزب یا جزء.\n\n"
            "*همه*\n"
            "• `/help` یا `/راهنما` — این پیام\n"
            "• `/lang en|fa|ar` — زبان گروه\n"
            "• `/status` یا `/وضعیت` — پیشرفت دوره\n"
            "• `/available` یا `/آزاد` — بخش‌های آزاد\n"
            "• `/claim <n>` یا `/رزرو <n>` — رزرو بخش\n"
            "• `/release <n>` یا `/آزادسازی <n>` — لغو رزرو\n"
            "• `/done <n>` یا `/تمام <n>` — تکمیل بخش\n"
            "• `/mine` یا `/من` — رزروهای شما\n"
            "• `/settings` یا `/تنظیمات` — تنظیمات گروه\n"
            "• `/plan …` یا `/برنامه …` — برنامه شخصی تلاوت\n\n"
            "*مدیران*\n"
            "• `/startcycle` یا `/دوره‌جدید` — شروع دوره جدید\n"
            "• `/granularity` یا `/واحد صفحه|سوره|حزب|جزء|قرآن` — واحد تلاوت\n"
            "• `/cycle` یا `/دوره روزانه|هفتگی|ماهانه|<N>d` — طول دوره\n"
            "• `/reminders` یا `/یادآوری خاموش|روزانه|<N>h|<N>d` — یادآوری\n"
            "• `/advertise` یا `/اعلان خاموش|روزانه|<N>h|<N>d` — اعلان جای خالی\n"
            "• `/niyyah [متن]` یا `/نیت [متن]` — تنظیم/پاک کردن نیت\n"
            "• `/admin add|remove <id>` — مدیریت مدیران\n"
            "• `/admins` — فهرست مدیران"
        ),
        "cycle_started": "دوره *#{cycle}* شروع شد — {total} × {unit}. با /رزرو رزرو کنید.",
        "niyyah_set": "نیت ثبت شد:\n_{niyyah}_",
        "niyyah_cleared": "نیت پاک شد.",
        "niyyah_current": "نیت فعلی:\n_{niyyah}_",
        "niyyah_none": "برای این دوره نیتی ثبت نشده است.",
        "claim_ok": "{unit} *{num}* برای شما رزرو شد. قبول حق.\nمتن: {link}",
        "claim_taken": "{unit} *{num}* قبلاً توسط {name} گرفته شده است.",
        "claim_invalid": "شماره {unit} باید بین 1 تا {total} باشد.",
        "claim_no_cycle": "دوره فعالی نیست. مدیر باید /startcycle بزند.",
        "release_ok": "{unit} *{num}* آزاد شد.",
        "release_not_yours": "{unit} *{num}* در اختیار شما نیست.",
        "done_ok": "{unit} *{num}* تکمیل شد. جزاكم الله خيراً",
        "done_not_yours": "فقط بخش‌های خودتان را می‌توانید تکمیل کنید.",
        "available_header": "*{unit}های آزاد* ({count}/{total}):",
        "available_none": "هر {total} بخش این دوره گرفته شده‌اند.",
        "status_header": "*دوره #{cycle}* — {claimed} رزرو، {done} تمام، {free} آزاد",
        "status_niyyah": "نیت: _{niyyah}_",
        "status_claims": "*رزروها:*\n{lines}",
        "status_empty": "هنوز رزروی نیست. /رزرو",
        "mine_header": "*رزروهای شما در این دوره:*\n{lines}",
        "mine_empty": "در این دوره چیزی رزرو نکرده‌اید.",
        "lang_set": "زبان گروه روی *فارسی* تنظیم شد.",
        "lang_invalid": "زبان‌های پشتیبانی‌شده: `en`، `fa`، `ar`.",
        "admin_only": "فقط مدیران گروه می‌توانند این دستور را اجرا کنند.",
        "admin_added": "مدیر اضافه شد: {id}",
        "admin_removed": "مدیر حذف شد: {id}",
        "admin_list": "*مدیران:*\n{lines}",
        "admin_need_id": "نحوه استفاده: `/admin add|remove <whatsapp_user_id>`",
        "unknown": "دستور ناشناخته. `/راهنما` را بفرستید.",
        "claim_line": "• {unit} {num} — {name} ({status})",
        "status_claimed": "رزرو",
        "status_done": "تمام",
        "bootstrapped": "شما اکنون مدیر این گروه هستید.",
        # Units
        "unit_page": "صفحه",
        "unit_surah": "سوره",
        "unit_hizb": "حزب",
        "unit_juz": "جزء",
        "unit_quran": "قرآن",
        # Settings
        "granularity_set": "واحد تلاوت روی *{unit}* تنظیم شد ({total} بخش). از دوره بعد اعمال می‌شود.",
        "granularity_invalid": "نحوه استفاده: `/واحد صفحه|سوره|حزب|جزء|قرآن`",
        "cycle_spec_set": "طول دوره روی *{spec}* تنظیم شد. از دوره بعد اعمال می‌شود.",
        "cycle_spec_invalid": "نحوه استفاده: `/دوره روزانه|هفتگی|ماهانه|<N>d`",
        "reminders_set": "یادآوری تکمیل فعال شد: هر *{spec}*.",
        "reminders_off": "یادآوری تکمیل خاموش شد.",
        "reminders_invalid": "نحوه استفاده: `/یادآوری خاموش|روزانه|هفتگی|<N>h|<N>d`",
        "advertise_set": "اعلان جای خالی فعال شد: هر *{spec}*.",
        "advertise_off": "اعلان جای خالی خاموش شد.",
        "advertise_invalid": "نحوه استفاده: `/اعلان خاموش|روزانه|هفتگی|<N>h|<N>d`",
        "settings_overview": (
            "*تنظیمات گروه*\n"
            "• واحد: {unit} ({total} بخش)\n"
            "• دوره: {cycle_spec}\n"
            "• یادآوری: {reminder_spec}\n"
            "• اعلان جای خالی: {ad_spec}"
        ),
        # Scheduled messages
        "reminder_message": "یادآوری — تلاوت باقی‌مانده این دوره:\n{lines}\nبا `/تمام <n>` تکمیل کنید.",
        "reminder_line": "• {unit} {num} — {link}",
        "ad_message": "*جاهای خالی* ({count} آزاد):\n{lines}\nبا `/رزرو <n>` رزرو کنید.",
        "cycle_rollover": "دوره *#{cycle}* شروع شد — {total} × {unit} آزاد است. با /رزرو رزرو کنید.",
        # Personal plans
        "plan_usage": (
            "دستورهای برنامه شخصی:\n"
            "• `/plan start <تعداد> <صفحه|سوره|حزب|جزء> <روزانه|هفتگی|ماهانه|Nd>` — مثال: `/plan start 1 جزء روزانه`\n"
            "• `/plan status` — پیشرفت شما\n"
            "• `/plan done` — تکمیل بخش فعلی\n"
            "• `/plan stop` — توقف برنامه"
        ),
        "plan_started": "برنامه شخصی شروع شد: {count} × {unit} هر {spec}.\nبخش اول: {unit} {range} از {total}.\nمتن: {link}",
        "plan_status": "*برنامه شخصی*: {done}/{total} {unit} تمام (ختم‌ها: {khatm}).\nبخش فعلی: {unit} {range}.\nمتن: {link}\nبا `/plan done` تکمیل کنید.",
        "plan_done": "بخش تکمیل شد، قبول حق. بعدی: {unit} {range} از {total}.\nمتن: {link}",
        "plan_khatm": "الله اکبر! یک ختم کامل کردید (مجموع: {khatm}). دوباره از {unit} ۱ شروع می‌شود.",
        "plan_stopped": "برنامه شخصی متوقف شد.",
        "plan_none": "برنامه شخصی فعالی ندارید. با `/plan start 1 جزء روزانه` شروع کنید.",
        "plan_checkin": "بخش تلاوت شما: {unit} {range}.\nمتن: {link}\nپس از اتمام `/plan done` بفرستید.",
    },
    "ar": {
        "help": (
            "*بوت تقسيم تلاوة القرآن*\n"
            "مشاركة القرآن في هذه المجموعة بالصفحة أو السورة أو الحزب أو الجزء.\n\n"
            "*للجميع*\n"
            "• `/help` أو `/مساعدة` — هذه الرسالة\n"
            "• `/lang en|fa|ar` — لغة المجموعة\n"
            "• `/status` أو `/حالة` — تقدم الدورة\n"
            "• `/available` أو `/متاح` — الأقسام المتاحة\n"
            "• `/claim <n>` أو `/حجز <n>` — حجز قسم\n"
            "• `/release <n>` أو `/إلغاء <n>` — إلغاء الحجز\n"
            "• `/done <n>` أو `/تم <n>` — إتمام القسم\n"
            "• `/mine` أو `/لي` — حجوزاتك\n"
            "• `/settings` أو `/إعدادات` — إعدادات المجموعة\n"
            "• `/plan …` أو `/خطة …` — خطة تلاوة شخصية\n\n"
            "*المشرفون*\n"
            "• `/startcycle` أو `/دورة-جديدة` — بدء دورة جديدة\n"
            "• `/granularity` أو `/وحدة صفحة|سورة|حزب|جزء|قرآن` — وحدة التلاوة\n"
            "• `/cycle` أو `/دورة يومي|أسبوعي|شهري|<N>d` — طول الدورة\n"
            "• `/reminders` أو `/تذكير إيقاف|يومي|<N>h|<N>d` — التذكير\n"
            "• `/advertise` أو `/إعلان إيقاف|يومي|<N>h|<N>d` — إعلان الأماكن المتاحة\n"
            "• `/niyyah [نص]` أو `/نية [نص]` — تعيين/مسح النية\n"
            "• `/admin add|remove <id>` — إدارة المشرفين\n"
            "• `/admins` — قائمة المشرفين"
        ),
        "cycle_started": "بدأت الدورة *#{cycle}* — {total} × {unit}. احجز بـ /حجز.",
        "niyyah_set": "تم تعيين النية:\n_{niyyah}_",
        "niyyah_cleared": "تم مسح النية.",
        "niyyah_current": "النية الحالية:\n_{niyyah}_",
        "niyyah_none": "لا توجد نية لهذه الدورة.",
        "claim_ok": "حجزت {unit} *{num}*. تقبّل الله.\nالنص: {link}",
        "claim_taken": "{unit} *{num}* محجوز بواسطة {name}.",
        "claim_invalid": "اختر رقم {unit} من 1 إلى {total}.",
        "claim_no_cycle": "لا توجد دورة نشطة. على المشرف تشغيل /startcycle.",
        "release_ok": "أُلغي حجز {unit} *{num}*.",
        "release_not_yours": "{unit} *{num}* ليس لديك.",
        "done_ok": "أُتم {unit} *{num}*. جزاكم الله خيراً",
        "done_not_yours": "يمكنك إتمام أقسامك فقط.",
        "available_header": "*{unit} المتاحة* ({count}/{total}):",
        "available_none": "جميع الأقسام الـ{total} محجوزة هذه الدورة.",
        "status_header": "*الدورة #{cycle}* — {claimed} محجوز، {done} مكتمل، {free} متاح",
        "status_niyyah": "النية: _{niyyah}_",
        "status_claims": "*الحجوزات:*\n{lines}",
        "status_empty": "لا حجوزات بعد. استخدم /حجز.",
        "mine_header": "*حجوزاتك هذه الدورة:*\n{lines}",
        "mine_empty": "ليس لديك حجوزات هذه الدورة.",
        "lang_set": "لغة المجموعة: *العربية*.",
        "lang_invalid": "اللغات المدعومة: `en`، `fa`، `ar`.",
        "admin_only": "هذا الأمر للمشرفين فقط.",
        "admin_added": "أُضيف مشرف: {id}",
        "admin_removed": "أُزيل مشرف: {id}",
        "admin_list": "*المشرفون:*\n{lines}",
        "admin_need_id": "الاستخدام: `/admin add|remove <whatsapp_user_id>`",
        "unknown": "أمر غير معروف. أرسل `/مساعدة`.",
        "claim_line": "• {unit} {num} — {name} ({status})",
        "status_claimed": "محجوز",
        "status_done": "مكتمل",
        "bootstrapped": "أصبحت مشرفًا لهذه المجموعة.",
        # Units
        "unit_page": "صفحة",
        "unit_surah": "سورة",
        "unit_hizb": "حزب",
        "unit_juz": "الجزء",
        "unit_quran": "القرآن",
        # Settings
        "granularity_set": "وحدة التلاوة الآن *{unit}* ({total} قسمًا). تُطبق من الدورة القادمة.",
        "granularity_invalid": "الاستخدام: `/وحدة صفحة|سورة|حزب|جزء|قرآن`",
        "cycle_spec_set": "طول الدورة الآن *{spec}*. يُطبق من الدورة القادمة.",
        "cycle_spec_invalid": "الاستخدام: `/دورة يومي|أسبوعي|شهري|<N>d`",
        "reminders_set": "تم تفعيل التذكير: كل *{spec}*.",
        "reminders_off": "تم إيقاف التذكير.",
        "reminders_invalid": "الاستخدام: `/تذكير إيقاف|يومي|أسبوعي|<N>h|<N>d`",
        "advertise_set": "تم تفعيل إعلان الأماكن المتاحة: كل *{spec}*.",
        "advertise_off": "تم إيقاف إعلان الأماكن المتاحة.",
        "advertise_invalid": "الاستخدام: `/إعلان إيقاف|يومي|أسبوعي|<N>h|<N>d`",
        "settings_overview": (
            "*إعدادات المجموعة*\n"
            "• الوحدة: {unit} ({total} قسمًا)\n"
            "• الدورة: {cycle_spec}\n"
            "• التذكير: {reminder_spec}\n"
            "• إعلان الأماكن: {ad_spec}"
        ),
        # Scheduled messages
        "reminder_message": "تذكير — تلاوتك المتبقية هذه الدورة:\n{lines}\nأتمم بـ `/تم <n>`.",
        "reminder_line": "• {unit} {num} — {link}",
        "ad_message": "*أماكن متاحة* ({count} متاح):\n{lines}\nاحجز بـ `/حجز <n>`.",
        "cycle_rollover": "بدأت الدورة *#{cycle}* — {total} × {unit} متاح. احجز بـ /حجز.",
        # Personal plans
        "plan_usage": (
            "أوامر الخطة الشخصية:\n"
            "• `/plan start <عدد> <صفحة|سورة|حزب|جزء> <يومي|أسبوعي|شهري|Nd>` — مثال: `/plan start 1 جزء يومي`\n"
            "• `/plan status` — تقدمك\n"
            "• `/plan done` — إتمام القسم الحالي\n"
            "• `/plan stop` — إيقاف الخطة"
        ),
        "plan_started": "بدأت الخطة الشخصية: {count} × {unit} كل {spec}.\nالقسم الأول: {unit} {range} من {total}.\nالنص: {link}",
        "plan_status": "*الخطة الشخصية*: {done}/{total} {unit} مكتمل (الختمات: {khatm}).\nالقسم الحالي: {unit} {range}.\nالنص: {link}\nأتمم بـ `/plan done`.",
        "plan_done": "اكتمل القسم، تقبّل الله. التالي: {unit} {range} من {total}.\nالنص: {link}",
        "plan_khatm": "الله أكبر! أتممت ختمة كاملة (المجموع: {khatm}). نبدأ من جديد من {unit} 1.",
        "plan_stopped": "توقفت الخطة الشخصية.",
        "plan_none": "لا توجد خطة شخصية نشطة. ابدأ بـ `/plan start 1 جزء يومي`.",
        "plan_checkin": "قسم تلاوتك: {unit} {range}.\nالنص: {link}\nأرسل `/plan done` عند الإتمام.",
    },
}


def normalize_lang(code: str | None) -> str:
    if not code:
        return "en"
    c = code.strip().lower()
    if c in ("fa", "farsi", "persian", "فارسی", "فارسي"):
        return "fa"
    if c in ("ar", "arabic", "عربي", "عربی", "العربية"):
        return "ar"
    if c in ("en", "english", "انگلیسی"):
        return "en"
    return "en" if c not in SUPPORTED else c


def t(lang: str, key: str, **kwargs: Any) -> str:
    catalog = STRINGS.get(normalize_lang(lang), STRINGS["en"])
    template = catalog.get(key) or STRINGS["en"].get(key, key)
    return template.format(**kwargs) if kwargs else template


def unit_label(lang: str, granularity: str) -> str:
    return t(lang, f"unit_{granularity}")
