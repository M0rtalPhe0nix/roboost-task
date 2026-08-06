from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Intent


@dataclass(frozen=True)
class RuleDecision:
    intent: Intent
    is_urgent: bool
    rule_id: str


_SPAM = re.compile(
    r"(?:"
    r"\b(?:crypto|forex|guaranteed returns?|earn money|buy followers|seo services?)\b"
    r"|(?:زيادة|شراء)\s+(?:متابعين|لايكات)"
    r"|(?:استثمار|فوركس|عملات رقمية).{0,30}(?:مضمون|ارباح|أرباح)"
    r"|خدمات\s+(?:سيو|تسويق).{0,30}(?:نقدم|نعرض)"
    r")",
    re.IGNORECASE,
)

_LEGAL_OR_PUBLIC_ESCALATION = re.compile(
    r"(?:"
    r"\b(?:i(?:'ll| will| am going to)\s+(?:sue|call (?:the )?police|report (?:you|this)"
    r"|post (?:this|it) (?:online|on social media))|legal action|my lawyer|consumer protection)\b"
    r"|(?:سوف|راح|حـ?ا|ه)?(?:أرفع|ارفع|أقدم|اقدم)\s+(?:قضية|بلاغ|شكوى)"
    r"|(?:هكلم|سأتواصل مع|سابلغ|سأبلغ|ابلغ)\s+(?:الشرطة|المحامي|حماية المستهلك|الوزارة)"
    r"|(?:هنشر|سأنشر|سوف أنشر|افضح|هفضح).{0,40}(?:السوشيال|فيسبوك|تويتر|انستجرام|الناس)"
    r")",
    re.IGNORECASE,
)

_ACTUAL_HARM = re.compile(
    r"(?:"
    r"\b(?:food poisoning|poisoned|allergic reaction|anaphylaxis|went to (?:the )?hospital"
    r"|emergency room|data breach|leaked my (?:personal )?data|card details exposed)\b"
    r"|(?:تسمم|اتسمم|تسممنا|حساسية|اختناق).{0,45}(?:بعد|بسبب|من الأكل|من الطلب)"
    r"|(?:روحنا|ذهبت|رحت).{0,15}(?:المستشفى|الطوارئ)"
    r"|(?:سربتم|تسريب|انكشفت).{0,30}(?:بياناتي|بيانات شخصية|بطاقتي)"
    r")",
    re.IGNORECASE,
)

_REFUND = re.compile(
    r"\b(?:refund|money back|chargeback)\b|(?:استرجاع|استرداد|رجعوا|رجعولي).{0,20}(?:فلوس|المبلغ)?",
    re.IGNORECASE,
)


def rule_gate(text: str) -> RuleDecision | None:
    """Return only deliberately high-precision, complete decisions."""
    if _SPAM.search(text):
        return RuleDecision(Intent.SPAM, False, "spam_unsolicited_solicitation_v1")
    if _LEGAL_OR_PUBLIC_ESCALATION.search(text):
        intent = Intent.REFUND_REQUEST if _REFUND.search(text) else Intent.COMPLAINT
        return RuleDecision(intent, True, "urgent_explicit_escalation_v1")
    if _ACTUAL_HARM.search(text):
        intent = Intent.REFUND_REQUEST if _REFUND.search(text) else Intent.COMPLAINT
        return RuleDecision(intent, True, "urgent_credible_harm_v1")
    return None
