"""Rule-based classifier that implements docs/DEFINITION.md."""
import html
import re
import unicodedata
from dataclasses import dataclass, field, asdict

from . import taxonomy as T

WEIGHTS = {0: 0.0, 1: 0.25, 2: 0.5, 3: 0.75, 4: 1.0}
SEVERITY_NAMES = {0: "Neutral / critique", 1: "Negative stereotyping", 2: "Contempt / slurs",
                  3: "Dehumanisation", 4: "Exclusion / violence"}

_TAG = re.compile(r"<[^>]+>")
_URL = re.compile(r"https?://\S+")
_QUOTE_LINK = re.compile(r">>\d+")  # 4chan reply links
_SENT = re.compile(r"(?<=[.!?\n])\s+")


def clean(text: str) -> str:
    text = html.unescape(text or "")
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<p>", "\n")
    text = _TAG.sub(" ", text)
    text = _URL.sub(" ", text)
    text = _QUOTE_LINK.sub(" ", text)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("‘", "'")
    return re.sub(r"[ \t]+", " ", text).strip()


@dataclass
class Result:
    targeted: bool = False      # about Indians as people
    sarcastic: bool = False     # excluded
    counter: bool = False       # counter-speech / reporting on racism; excluded from hate
    negated: bool = False
    state_only: bool = False    # only criticises the Indian state
    severity: int = 0
    slur: bool = False
    reasons: list = field(default_factory=list)
    stereotypes: list = field(default_factory=list)

    @property
    def weight(self):
        return WEIGHTS[self.severity]

    @property
    def hateful(self):
        return self.severity > 0

    def to_dict(self):
        d = asdict(self)
        d["weight"] = self.weight
        return d


def _targets(sentence: str, context_targeted: bool) -> bool:
    if T.GROUP_FALSE.search(sentence) and not T.SLURS.search(sentence):
        stripped = T.GROUP_FALSE.sub(" ", sentence)
    else:
        stripped = sentence
    if T.GROUP.search(stripped) or T.SLURS.search(stripped):
        return True
    return context_targeted and bool(T.PRONOUN_TARGET.search(stripped))


def classify(text: str, context: str = "") -> Result:
    """Classify one post. `context` is the thread title/subject, if any.

    If the context is about Indians, pronouns ("they", "these people") in
    the post are treated as referring to Indians.
    """
    r = Result()
    body = clean(text)
    low = body.lower()
    if not low:
        return r
    ctx = clean(context).lower()
    context_targeted = bool(ctx) and _targets(ctx, False)

    sentences = [s for s in _SENT.split(low) if s.strip()] or [low]
    # A sentence is "in scope" if it names the group, or follows one that did.
    scoped, prev = [], False
    for s in sentences:
        hit = _targets(s, context_targeted)
        if hit or (prev and T.PRONOUN_TARGET.search(s)):
            scoped.append(s)
        prev = hit
    if not scoped:
        if T.STATE_CRITIQUE.search(low):
            r.state_only = True
        return r
    r.targeted = True

    # Exclusions first.
    if (T.SARCASM.search(low)
            or (T.IRONY_EMOJI.search(body) and T.POSITIVE.search(low))
            or T.SCARE_QUOTED.search(body)):
        r.sarcastic = True
        return r
    if T.COUNTER_SPEECH.search(low) and not T.NOT_RACIST_BUT.search(low):
        r.counter = True
        return r

    scope = " \n ".join(scoped)
    if T.NEGATION.search(scope):
        r.negated = True

    generalises = bool(T.GENERALISE.search(scope)) or bool(T.NOT_RACIST_BUT.search(low)) or context_targeted
    sev = 0
    if T.SLURS.search(low):
        r.slur, sev = True, 2

    for sid, (_label, reason, pattern) in T.STEREOTYPES.items():
        if pattern.search(scope) and (generalises or r.slur):
            r.stereotypes.append(sid)
            if reason not in r.reasons:
                r.reasons.append(reason)

    if r.stereotypes and not r.negated:
        sev = max(sev, 1)
    if T.CONTEMPT.search(scope) and (generalises or r.slur):
        sev = max(sev, 2)
    if T.DEHUMANISE.search(scope) and (generalises or r.slur):
        sev = max(sev, 3)
    if T.EXCLUDE_VIOLENCE.search(scope):
        sev = 4
        if "immigration" not in r.reasons:
            r.reasons.append("immigration")

    if r.negated and sev <= 1:
        sev = 0
        r.stereotypes, r.reasons = [], []
    if sev == 0:
        r.stereotypes, r.reasons = [], []
    elif not r.reasons:
        r.reasons.append("general")
    r.severity = sev
    return r
