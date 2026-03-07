"""
PatternShield ML Detector v2.0
10 dark pattern categories, cookie consent, accessibility, sigmoid scoring.
"""
import re, math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False


@dataclass
class DetectionResult:
    detected_patterns: List[str] = field(default_factory=list)
    primary_pattern: Optional[str] = None
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    sentiment: Dict = field(default_factory=lambda: {"score": 0, "label": "neutral"})
    explanations: Dict[str, str] = field(default_factory=dict)
    severity: str = "none"
    text_analyzed: str = ""
    is_cookie_consent: bool = False
    accessibility_issues: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "detected_patterns": self.detected_patterns,
            "primary_pattern": self.primary_pattern,
            "confidence_scores": self.confidence_scores,
            "sentiment": self.sentiment,
            "explanations": self.explanations,
            "severity": self.severity,
            "text_analyzed": self.text_analyzed,
            "is_cookie_consent": self.is_cookie_consent,
            "accessibility_issues": self.accessibility_issues,
        }


class DarkPatternDetector:
    PATTERNS = {
        "Urgency/Scarcity": {
            "description": "Creates false sense of urgency or scarcity to pressure quick decisions",
            "severity_weight": 0.7,
            "keywords": [
                "only", "left", "stock", "hurry", "limited", "last", "soon",
                "now", "today", "hours", "minutes", "expires", "ends",
                "running out", "almost gone", "selling fast", "few items",
                "flash sale", "countdown", "timer", "act now", "quick",
                "don't miss", "while supplies", "almost sold out",
                "high demand", "popular item", "be quick", "last chance",
                "deal expires", "price increases", "one day sale", "secure yours",
            ],
            "patterns": [
                r"\d+\s*(left|remaining|available|in stock)",
                r"only\s+\d+",
                r"sale ends?\s*(in|at|on)",
                r"\d+\s*people\s*(viewing|bought|purchased|watching)",
                r"timer[:\s]*\d+[:\d]*",
                r"(ends?|expires?)\s*(in\s*)?\d+\s*(hour|minute|second|day|hr|min|sec)",
                r"(last|final)\s*(chance|day|hour|call)",
                r"price\s*(goes up|increases|changes)",
                r"(limited|exclusive)\s*(time|edition|offer|stock|quantity)",
            ],
            "negative_keywords": ["business hours", "opening hours", "store hours", "office hours"],
        },
        "Confirmshaming": {
            "description": "Uses guilt, shame or negative framing to manipulate decisions",
            "severity_weight": 0.8,
            "keywords": [
                "no thanks", "i don't want", "i don't like", "i prefer",
                "skip", "decline", "reject", "i'd rather", "i don't care",
                "miss out", "without", "i enjoy", "i don't deserve",
                "no,", "stay basic", "inferior", "overpaying",
                "i don't need", "not interested", "keep struggling",
                "waste time", "pay more", "prefer paying full",
                "don't deserve better", "enjoy overpaying",
            ],
            "patterns": [
                r"no\s*,?\s*thanks?\s*[,.]?\s*(i\s*(don.t|prefer|enjoy|like|rather))",
                r"no\s*,?\s*i\s*(don.t|prefer|enjoy|like|rather|am\s*not)",
                r"skip\s*(this|and|offer|\()",
                r"decline\s*(and|offer|this|the)",
                r"continue\s*without",
                r"proceed\s*without",
                r"(reject|refuse)\s*(and|this|the|savings?|offer|deal)",
                r"i.*(don.t|rather not)\s*(want|need|care|deserve)",
                r"(stay|remain|keep)\s*(basic|current|inferior|old)",
            ],
            "negative_keywords": [],
        },
        "Obstruction": {
            "description": "Makes it deliberately difficult to cancel, unsubscribe, or take desired actions",
            "severity_weight": 0.9,
            "keywords": [
                "mail", "written request", "headquarters", "contact",
                "customer service", "phone", "call", "fax", "days to process",
                "business days", "form", "visit store", "in person",
                "cancellation fee", "minimum", "certified mail",
                "notarized", "supervisor approval", "disabled until",
                "early termination", "penalty", "waiting period",
                "verification", "multiple steps", "speak to agent",
                "retention specialist", "chat with us first",
            ],
            "patterns": [
                r"(mail|send|fax)\s*(a\s*)?(written\s*)?(request|letter|form|notice)",
                r"contact\s*(customer\s*)?service",
                r"\d+\s*(business|working)\s*days",
                r"cancell?ation\s*(fee|charge|penalty)",
                r"(requires?|must)\s*(a\s*)?(phone\s*call|phone|calling|visit)",
                r"only\s*(available|by|through)\s*(calling|mail|fax|in\s*person|phone)",
                r"(in\s*person|in-person)\s*(visit|verification|only)",
                r"early\s*termination\s*(fee|charge|penalty)",
            ],
            "negative_keywords": ["contact us for help", "we're here to help"],
        },
        "Visual Interference": {
            "description": "Uses visual design tricks to manipulate attention and steer choices",
            "severity_weight": 0.6,
            "keywords": [
                "accept all", "yes please", "get started",
                "unlock", "upgrade", "premium", "claim", "start free",
                "maybe later", "dismiss", "skip for now",
            ],
            "visual_markers": [
                r"[✓✗★⚡🎉🔥💥⭐🏆💰🎁]+",
                r"[A-Z\s]{5,}",
                r"[!]{2,}",
                r"(?:FREE|SAVE|WIN|NEW|HOT|BEST|TOP|VIP|PRO|NOW)",
            ],
            "patterns": [
                r"(accept|agree)\s*all",
                r"(get|start|claim|unlock)\s*(your|free|now|today)",
            ],
            "negative_keywords": ["free delivery", "free shipping", "delivery by"],
        },
        "Hidden Costs": {
            "description": "Reveals additional fees or charges only at later stages",
            "severity_weight": 0.85,
            "keywords": [
                "processing fee", "service fee", "handling fee",
                "convenience fee", "booking fee", "platform fee",
                "additional charge", "surcharge", "shipping",
                "delivery fee", "insurance", "protection plan",
                "mandatory", "required fee", "admin fee",
                "setup fee", "activation fee", "restocking fee",
                "price does not include", "plus tax", "before tax",
                "fees apply", "charges may apply", "subject to",
            ],
            "patterns": [
                r"\+\s*(tax|shipping|handling|fee|surcharge)",
                r"(processing|service|handling|booking|convenience|platform|admin|setup|activation)\s*fee",
                r"(additional|extra|hidden)\s*(charge|cost|fee|payment)",
                r"price\s*(does\s*)?not\s*include",
                r"(fees?|charges?)\s*(may\s*)?apply",
                r"\$\d+\.?\d*\s*(fee|charge|surcharge)",
                r"\d[\d,.]*\s*%\s*surcharge",
                r"(mandatory|required|non.?refundable)\s*(fee|charge|deposit)",
            ],
            "negative_keywords": ["free shipping", "no hidden fees", "no additional charges", "tax included"],
        },
        "Forced Continuity": {
            "description": "Auto-enrolls users in recurring payments or traps them after free trials",
            "severity_weight": 0.9,
            "keywords": [
                "free trial", "auto-renew", "automatically renew",
                "recurring", "subscription", "billed", "charged",
                "cancel anytime", "automatic billing",
                "trial ends", "convert to paid", "continuous",
                "auto-charge", "unless cancelled", "will be charged",
                "renews at", "billing cycle", "annual plan",
            ],
            "patterns": [
                r"(free\s*)?trial\s*(will\s*)?(auto|convert|become|turn)",
                r"auto(matically)?[\s-]*(renew|charge|bill|debit|enroll)",
                r"(will|shall)\s*be\s*(automatically\s*)?(charged|billed|renewed)",
                r"unless\s*(you\s*)?(cancel|unsubscribe|opt[\s-]?out)",
                r"(renews?|charges?|bills?)\s*(at|for)\s*\$?\d+",
                r"(continuous|recurring|automatic)\s*(subscription|billing|payment|charge)",
            ],
            "negative_keywords": [],
        },
        "Sneaking": {
            "description": "Adds items, options or subscriptions without clear user consent",
            "severity_weight": 0.85,
            "keywords": [
                "added to cart", "selected for you", "recommended add",
                "pre-selected", "default", "opted in", "included",
                "bonus", "gift", "pre-checked", "already selected",
                "we've added", "best value", "most popular choice",
            ],
            "patterns": [
                r"(pre[\s-]?selected|pre[\s-]?checked|already\s*selected|auto[\s-]?selected)",
                r"(added|included|bundled)\s*(to|in|with)\s*(your\s*)?(cart|order|basket|bag)",
                r"(we.ve|we\s*have)\s*(added|included|selected)",
                r"(opt(ed)?[\s-]?in|enrolled)\s*(by\s*default|automatically)",
                r"(default|standard)\s*(selection|choice|option|plan)",
            ],
            "negative_keywords": ["you may add", "would you like to add", "optional"],
        },
        "Social Proof": {
            "description": "Uses potentially fake or misleading social validation",
            "severity_weight": 0.5,
            "keywords": [
                "people bought", "people viewing", "people purchased",
                "customers chose", "trending", "bestseller", "most popular",
                "top rated", "thousands", "millions", "trusted by",
                "verified", "just purchased", "bought this",
                "as seen on", "featured in",
            ],
            "patterns": [
                r"\d+[\s,+]*\s*(people|customers|users|buyers)\s*(bought|viewing|purchased|chose|love|trust)",
                r"(trusted|used|loved|chosen)\s*by\s*\d+[\s,+]*\s*(million|thousand|people|companies)",
                r"\w+\s*(just|recently)\s*(bought|purchased|signed up|ordered|joined)",
                r"(best[\s-]?seller|top[\s-]?rated|most\s*popular|highest[\s-]?rated)",
                r"(someone\s*in|a\s*customer\s*from)\s*\w+\s*(just\s*)?(bought|purchased|ordered)",
            ],
            "negative_keywords": [],
        },
        "Misdirection": {
            "description": "Draws attention toward or away from specific choices to steer behavior",
            "severity_weight": 0.65,
            "keywords": [
                "recommended", "best choice", "most popular",
                "best value", "our pick", "editor's choice",
                "suggested", "preferred", "optimal", "ideal",
                "smart choice", "top pick", "featured",
            ],
            "patterns": [
                r"(recommended|suggested|best|our)\s*(choice|pick|option|plan|value)",
                r"(most\s*)?(popular|chosen|selected)\s*(option|plan|choice|package)",
                r"(perfect|ideal|optimal|right)\s*(for\s*you|choice|plan|match)",
            ],
            "negative_keywords": [],
        },
        "Price Comparison Prevention": {
            "description": "Makes it hard to compare prices or understand true costs",
            "severity_weight": 0.7,
            "keywords": [
                "billed annually", "billed monthly", "starting at",
                "custom pricing", "contact for price", "call for quote",
                "personalized price", "request quote",
                "price varies", "see in cart", "added at checkout",
            ],
            "patterns": [
                r"\$[\d,.]+\s*/\s*(mo|month|yr|year|week|day|user|seat)",
                r"(billed|charged|paid)\s*(annually|monthly|quarterly|weekly)\s*(\(|\bat\b)",
                r"(starting|from)\s*(at\s*)?\$[\d,.]+",
                r"(custom|personalized|individual)\s*(pricing|quote|plan)",
                r"(contact|call|email)\s*(us\s*)?(for\s*)?(pricing|quote|rates)",
                r"price\s*(varies|depends|shown)\s*(at|in|during)\s*(checkout|cart)",
            ],
            "negative_keywords": ["compare plans", "see all prices", "price breakdown"],
        },
    }

    COOKIE_SIGNALS = ["cookie", "cookies", "consent", "gdpr", "tracking", "necessary", "functional", "analytical", "marketing"]
    COOKIE_PATTERNS_RAW = [
        r"(accept|reject|manage)\s*(all\s*)?(cookies?|tracking)",
        r"(cookie|privacy)\s*(policy|notice|settings|preferences|consent|banner)",
        r"(we\s*use|this\s*site\s*uses)\s*cookies?",
    ]

    def __init__(self):
        self._compiled = {}
        for ptype, rules in self.PATTERNS.items():
            cp = []
            for p in rules.get("patterns", []):
                try: cp.append(re.compile(p, re.IGNORECASE))
                except: pass
            cv = []
            for v in rules.get("visual_markers", []):
                try: cv.append(re.compile(v))
                except: pass
            self._compiled[ptype] = {"patterns": cp, "visual": cv}
        self._cookie_rx = []
        for p in self.COOKIE_PATTERNS_RAW:
            try: self._cookie_rx.append(re.compile(p, re.IGNORECASE))
            except: pass

    def analyze_element(self, text, element_type="div", color="#000000",
                        use_sentiment=True, use_enhanced=True, font_size=None,
                        opacity=None, position=None, parent_text=None):
        if not text or not text.strip():
            return DetectionResult(text_analyzed="").to_dict()
        text_clean = text.strip()
        text_lower = text_clean.lower()
        result = DetectionResult(text_analyzed=text_clean)
        result.is_cookie_consent = self._is_cookie(text_lower)

        for ptype, rules in self.PATTERNS.items():
            score, matches = self._score(text_clean, text_lower, ptype, rules)
            score = self._ctx_adjust(score, ptype, element_type, color, font_size, opacity)
            for nk in rules.get("negative_keywords", []):
                if nk in text_lower: score *= 0.3
            if score > 0:
                conf = self._sigmoid(score, 2.0, 1.5)
                result.confidence_scores[ptype] = round(conf, 4)
                if conf >= 0.3:
                    result.detected_patterns.append(ptype)
                    result.explanations[ptype] = self._explain(ptype, matches, conf)

        if use_sentiment and HAS_TEXTBLOB:
            result.sentiment = self._sentiment(text_clean, result)
        if result.is_cookie_consent:
            self._cookie_dp(text_lower, result, element_type, font_size)
        if use_enhanced:
            self._a11y(text_clean, element_type, color, font_size, opacity, result)
        if result.detected_patterns:
            primary = max(result.confidence_scores.items(), key=lambda x: x[1])
            result.primary_pattern = primary[0]
            result.severity = self._severity(result)
        return result.to_dict()

    def _score(self, text, text_lower, ptype, rules):
        score, matches = 0.0, []
        for kw in rules.get("keywords", []):
            if kw in text_lower:
                score += 1.0 + (len(kw.split()) - 1) * 0.5
                matches.append(kw)
        for rx in self._compiled.get(ptype, {}).get("patterns", []):
            if rx.search(text_lower):
                score += 2.5
                matches.append(f"regex:{rx.pattern[:30]}")
        for rx in self._compiled.get(ptype, {}).get("visual", []):
            if rx.search(text):
                score += 1.5
                matches.append(f"visual")
        return score, matches

    def _ctx_adjust(self, score, ptype, etype, color, font_size, opacity):
        if score == 0: return 0
        m = 1.0
        if ptype == "Confirmshaming" and etype in ("a", "span", "small"): m *= 1.2
        if ptype in ("Hidden Costs", "Sneaking") and etype in ("small", "span", "p"): m *= 1.15
        if color and color != "#000000":
            cl = color.lower()
            if ptype == "Urgency/Scarcity" and any(c in cl for c in ["#ef","#dc","#b9","#f9","#ea"]): m *= 1.15
            if ptype in ("Obstruction","Confirmshaming") and any(c in cl for c in ["#6b","#4b","#9c"]): m *= 1.1
        if font_size is not None:
            if ptype in ("Hidden Costs","Obstruction") and font_size < 12: m *= 1.2
        if opacity is not None and opacity < 0.7:
            if ptype in ("Obstruction","Confirmshaming","Hidden Costs"): m *= 1.2
        return score * m

    @staticmethod
    def _sigmoid(score, threshold=2.0, steepness=1.5):
        try: return 1.0 / (1.0 + math.exp(-steepness * (score - threshold)))
        except OverflowError: return 0.0 if score < threshold else 1.0

    def _sentiment(self, text, result):
        try:
            blob = TextBlob(text)
            p, s = blob.sentiment.polarity, blob.sentiment.subjectivity
            label = "negative" if p < -0.1 else ("positive" if p > 0.1 else "neutral")
            if label == "negative":
                for pt in ("Confirmshaming", "Obstruction"):
                    if pt in result.confidence_scores:
                        result.confidence_scores[pt] = min(result.confidence_scores[pt] * 1.15, 1.0)
            if s > 0.6 and label == "positive":
                for pt in ("Urgency/Scarcity", "Social Proof", "Misdirection"):
                    if pt in result.confidence_scores:
                        result.confidence_scores[pt] = min(result.confidence_scores[pt] * 1.1, 1.0)
            return {"score": round(p, 4), "label": label, "subjectivity": round(s, 4)}
        except: return {"score": 0, "label": "neutral", "subjectivity": 0}

    def _is_cookie(self, text_lower):
        if any(kw in text_lower for kw in self.COOKIE_SIGNALS):
            if any(rx.search(text_lower) for rx in self._cookie_rx): return True
        return False

    def _cookie_dp(self, text_lower, result, etype, font_size):
        if "accept" in text_lower and etype in ("button", "a", "input"):
            if font_size and font_size > 14:
                result.confidence_scores.setdefault("Visual Interference", 0)
                result.confidence_scores["Visual Interference"] = min(result.confidence_scores["Visual Interference"] + 0.3, 1.0)
                if "Visual Interference" not in result.detected_patterns:
                    result.detected_patterns.append("Visual Interference")
                result.explanations["Cookie: Asymmetric"] = "Accept button more prominent than reject"
        for sig in ["pre-selected", "pre-checked", "enabled by default"]:
            if sig in text_lower:
                result.confidence_scores.setdefault("Sneaking", 0)
                result.confidence_scores["Sneaking"] = min(result.confidence_scores["Sneaking"] + 0.5, 1.0)
                if "Sneaking" not in result.detected_patterns:
                    result.detected_patterns.append("Sneaking")
                result.explanations["Cookie: Preselected"] = "Non-essential cookies pre-selected"
                break

    def _a11y(self, text, etype, color, font_size, opacity, result):
        issues = []
        kws = ["cancel","unsubscribe","reject","opt out","decline","remove","delete","close"]
        if font_size is not None and font_size < 11:
            if any(kw in text.lower() for kw in kws):
                issues.append(f"Small text ({font_size}px) for important action")
        if opacity is not None and opacity < 0.5:
            issues.append(f"Very low opacity ({opacity})")
        result.accessibility_issues = issues

    def _severity(self, result):
        if not result.detected_patterns: return "none"
        max_s = 0
        for pt in result.detected_patterns:
            c = result.confidence_scores.get(pt, 0)
            w = self.PATTERNS.get(pt, {}).get("severity_weight", 0.5)
            max_s = max(max_s, c * w)
        n = len(result.detected_patterns)
        if n >= 3: max_s = min(max_s * 1.3, 1.0)
        elif n >= 2: max_s = min(max_s * 1.15, 1.0)
        if max_s >= 0.8: return "critical"
        elif max_s >= 0.6: return "high"
        elif max_s >= 0.4: return "medium"
        elif max_s >= 0.2: return "low"
        return "none"

    def _explain(self, ptype, matches, conf):
        desc = self.PATTERNS.get(ptype, {}).get("description", "")
        kws = [m for m in matches if not m.startswith(("regex:", "visual"))]
        if kws:
            trigger = ", ".join(f'"{m}"' for m in kws[:3])
            return f"{desc}. Triggered by: {trigger}. Confidence: {conf:.0%}"
        return f"{desc}. Confidence: {conf:.0%}"

    def get_pattern_explanation(self, pattern_type):
        return self.PATTERNS.get(pattern_type, {}).get("description", "Unknown")

    def get_all_pattern_types(self):
        return [{"type": pt, "description": r["description"], "severity_weight": r["severity_weight"]}
                for pt, r in self.PATTERNS.items()]

    @staticmethod
    def calculate_site_score(detections):
        if not detections:
            return {"score": 100, "grade": "A", "risk_level": "low",
                    "total_elements": 0, "flagged_elements": 0,
                    "pattern_breakdown": {}, "density": 0}
        total = len(detections)
        flagged = sum(1 for d in detections if d.get("primary_pattern"))
        counts, sev_sum = {}, 0
        for d in detections:
            pp = d.get("primary_pattern")
            if pp:
                counts[pp] = counts.get(pp, 0) + 1
                sev_sum += max(d.get("confidence_scores", {}).values(), default=0)
        density = flagged / total if total > 0 else 0
        score = max(0, 100 - int(sev_sum * 20) - int(density * 50))
        if score >= 90: grade, risk = "A", "low"
        elif score >= 75: grade, risk = "B", "low"
        elif score >= 60: grade, risk = "C", "medium"
        elif score >= 40: grade, risk = "D", "high"
        else: grade, risk = "F", "critical"
        return {"score": score, "grade": grade, "risk_level": risk,
                "total_elements": total, "flagged_elements": flagged,
                "pattern_breakdown": counts, "density": round(density, 4)}


def analyze_element(text, element_type="div", color="#000000", use_sentiment=True, use_enhanced=True):
    return DarkPatternDetector().analyze_element(text, element_type, color, use_sentiment, use_enhanced)
