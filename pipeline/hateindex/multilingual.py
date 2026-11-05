"""Non-English rules, so the index isn't limited to English speakers.

Same ladder as English (docs/DEFINITION.md): claim → 1, contempt/slur → 2,
dehumanisation → 3, exclusion/violence → 4. Each language has its own terms
for Indians, cue words and counter-speech words.

These rules are cruder than the English ones: there's no generalisation
check, so a cue only counts in the same sentence as a term for Indians.
Words that usually mean someone else are left out on purpose:
Spanish "indios" / Portuguese "índios" (indigenous peoples), German
"Indianer" (Native Americans), Dutch "Indische" (Indonesian-Dutch).

Slurs are listed only so they can be detected.
"""
import re


def rx(*parts, cjk=False):
    # CJK has no spaces, so \b is meaningless there
    return re.compile("|".join(parts), re.I)


LANGS = {
    "es": dict(
        group=rx(r"\bhind[úu]es\b", r"\b(?:inmigrantes|trabajadores|estudiantes|migrantes) indios\b",
                 r"\bindios de la india\b", r"\bpersonas de la india\b"),
        slurs=None,
        claims={"smell": rx(r"\bhuelen\b", r"\bapestan\b", r"\bmal olor\b"),
                "dirty": rx(r"\bsucios\b", r"\bcochinos\b", r"\bcagan en la calle\b"),
                "scam": rx(r"\bestafadores\b", r"\btimadores\b"),
                "invasion": rx(r"\binvasi[óo]n\b", r"\bnos invaden\b", r"\bdemasiados\b"),
                "jobs": rx(r"\b(?:roban|quitan) (?:nuestros |los )?(?:trabajos|empleos)\b")},
        contempt=rx(r"\basco\b", r"\basquerosos\b", r"\bodio a los\b", r"\bbasura\b", r"\bescoria\b"),
        dehumanise=rx(r"\bratas\b", r"\bcucarachas\b", r"\bplaga\b", r"\bpar[áa]sitos\b", r"\banimales\b", r"\balima[ñn]as\b"),
        exclude=rx(r"\bdeportar(?:los)?\b", r"\bque se vayan\b", r"\bexpulsar(?:los)?\b", r"\bvuelvan a su pa[íi]s\b",
                   r"\bmatar(?:los)?\b", r"\bfuera de (?:aqu[íi]|nuestro pa[íi]s)\b"),
        counter=rx(r"\bracis(?:mo|ta)\b", r"\bxen[óo]fob", r"\bdiscriminaci[óo]n\b", r"\bestereotipo"),
    ),
    "pt": dict(
        group=rx(r"\bindianos\b", r"\bindianas\b"),
        slurs=None,
        claims={"smell": rx(r"\bfedem\b", r"\bcheiram mal\b", r"\bfedor\b"),
                "dirty": rx(r"\bsujos\b", r"\bimundos\b"),
                "scam": rx(r"\bgolpistas\b", r"\bvigaristas\b", r"\bestelionat"),
                "invasion": rx(r"\binvas[ãa]o\b", r"\binvadindo\b"),
                "jobs": rx(r"\b(?:roubam|tiram) (?:nossos |os )?(?:empregos|trabalhos)\b")},
        contempt=rx(r"\bnojo\b", r"\bnojentos\b", r"\bodeio\b", r"\blixo\b", r"\besc[óo]ria\b"),
        dehumanise=rx(r"\bratos\b", r"\bbaratas\b", r"\bpraga\b", r"\bparasitas\b", r"\banimais\b"),
        exclude=rx(r"\bdeportar\b", r"\bvoltem para (?:a [íi]ndia|o seu pa[íi]s)\b", r"\bfora daqui\b",
                   r"\bexpulsar\b", r"\bmatar\b"),
        counter=rx(r"\bracis", r"\bxen[óo]fob", r"\bdiscrimina[çc]", r"\bestere[óo]tipo"),
    ),
    "fr": dict(
        group=rx(r"\bindiens\b(?! d'am[ée]rique)", r"\bindiennes\b"),
        slurs=None,
        claims={"smell": rx(r"\bpuent\b", r"\bsentent mauvais\b", r"\bodeur\b"),
                "dirty": rx(r"\bsales\b", r"\bcrasseux\b", r"\bchient dans la rue\b"),
                "scam": rx(r"\barnaqueurs\b", r"\bescrocs\b"),
                "invasion": rx(r"\binvasion\b", r"\benvahi", r"\bgrand remplacement\b", r"\btrop nombreux\b"),
                "jobs": rx(r"\bvolent (?:nos |les )?(?:emplois|boulots)\b")},
        contempt=rx(r"\bd[ée]go[ûu]tants?\b", r"\bje d[ée]teste les\b", r"\bd[ée]chets\b", r"\bracaille\b"),
        dehumanise=rx(r"\brats\b", r"\bcafards\b", r"\bvermine\b", r"\bparasites\b", r"\banimaux\b", r"\bfl[ée]au\b"),
        exclude=rx(r"\bexpulse[rz]\b", r"\bqu'ils rentrent chez eux\b", r"\brenvoye[rz]\b", r"\bretournez en inde\b",
                   r"\btue[rz]\b", r"\bdehors\b"),
        counter=rx(r"\bracis", r"\bx[ée]nophob", r"\bdiscrimin", r"\bst[ée]r[ée]otype"),
    ),
    "de": dict(
        group=rx(r"\binder(?:innen|n)?\b", r"\bindische (?:einwanderer|migranten|arbeiter|studenten|fachkr[äa]fte)\b"),
        slurs=None,
        claims={"smell": rx(r"\bstinken\b", r"\bgestank\b"),
                "dirty": rx(r"\bdreckig\b", r"\bschmutzig\b"),
                "scam": rx(r"\bbetr[üu]ger\b", r"\babzocker\b"),
                "invasion": rx(r"\binvasion\b", r"\b[üu]berflute", r"\b[üu]berschwemm", r"\b[üu]berfremdung\b",
                               r"\bumvolkung\b", r"\bzu viele\b"),
                "jobs": rx(r"\b(?:nehmen|klauen|stehlen) (?:uns )?(?:die |unsere )?(?:jobs|arbeitspl[äa]tze)\b")},
        contempt=rx(r"\beklig\b", r"\bwiderlich\b", r"\bich hasse\b", r"\babschaum\b", r"\bgesindel\b"),
        dehumanise=rx(r"\bratten\b", r"\bkakerlaken\b", r"\bungeziefer\b", r"\bparasiten\b", r"\btiere\b", r"\bplage\b"),
        exclude=rx(r"\babschieben\b", r"\bausweisen\b", r"\braus mit\b", r"\bgeht zur[üu]ck\b", r"\bremigration\b",
                   r"\bumbringen\b"),
        counter=rx(r"\brassis", r"\bfremdenfeindlich", r"\bdiskriminier", r"\bhetze gegen\b", r"\bklischee"),
    ),
    "it": dict(
        group=rx(r"\bindiani\b(?! d'america)", r"\bindiane\b"),
        slurs=None,
        claims={"smell": rx(r"\bpuzzano\b", r"\bfetore\b"),
                "dirty": rx(r"\bsporchi\b", r"\bluridi\b"),
                "scam": rx(r"\btruffatori\b", r"\bimbroglioni\b"),
                "invasion": rx(r"\binvasione\b", r"\binvadono\b", r"\bsostituzione etnica\b", r"\btroppi\b"),
                "jobs": rx(r"\b(?:rubano|tolgono) (?:il |i |nostro |nostri )?(?:lavoro|lavori|posti di lavoro)\b")},
        contempt=rx(r"\bschifosi\b", r"\bfanno schifo\b", r"\bodio gli\b", r"\bfeccia\b", r"\bspazzatura\b"),
        dehumanise=rx(r"\bratti\b", r"\bscarafaggi\b", r"\bparassiti\b", r"\banimali\b", r"\bpiaga\b"),
        exclude=rx(r"\brimpatri", r"\bespell", r"\btornate(?:ne)? a casa\b", r"\bcacciarli\b", r"\bammazzarli\b"),
        counter=rx(r"\brazzis", r"\bxenofob", r"\bdiscrimin", r"\bstereotip"),
    ),
    "nl": dict(
        group=rx(r"\bindi[ëe]rs\b"),
        slurs=None,
        claims={"smell": rx(r"\bstinken\b", r"\bstank\b"),
                "dirty": rx(r"\bvies\b", r"\bsmerig\b"),
                "scam": rx(r"\boplichters\b", r"\bfraudeurs\b"),
                "invasion": rx(r"\binvasie\b", r"\boverspoeld\b", r"\bomvolking\b", r"\bte veel\b"),
                "jobs": rx(r"\b(?:pikken|stelen|nemen) (?:onze |de )?banen\b")},
        contempt=rx(r"\bwalgelijk\b", r"\bik haat\b", r"\btuig\b", r"\buitschot\b"),
        dehumanise=rx(r"\bratten\b", r"\bkakkerlakken\b", r"\bongedierte\b", r"\bparasieten\b", r"\bbeesten\b", r"\bplaag\b"),
        exclude=rx(r"\buitzetten\b", r"\bdeporteren\b", r"\boprotten\b", r"\bterug naar (?:india|hun land)\b"),
        counter=rx(r"\bracis", r"\bdiscrimin", r"\bxenofob", r"\bstereotype"),
    ),
    "pl": dict(
        group=rx(r"\bhindus(?:i|[óo]w|om|ami)\b", r"\bindyjczy(?:cy|k[óo]w)\b"),
        slurs=None,
        claims={"smell": rx(r"\bśmierdz", r"\bsmr[óo]d\b"),
                "dirty": rx(r"\bbrudni\b", r"\bbrudasy\b"),
                "scam": rx(r"\boszuści\b", r"\boszust"),
                "invasion": rx(r"\binwazja\b", r"\bzalewaj", r"\bza du[żz]o\b"),
                "jobs": rx(r"\bzabieraj[ąa] (?:nam )?prac")},
        contempt=rx(r"\bobrzydliw", r"\bnienawidz", r"\bścierwo\b"),
        dehumanise=rx(r"\bszczury\b", r"\bkaraluchy\b", r"\brobactwo\b", r"\bpaso[żz]yty\b", r"\bzwierz[ęe]ta\b"),
        exclude=rx(r"\bdeportowa", r"\bwypierdala", r"\bwyrzuci[ćc]\b", r"\bwon do\b"),
        counter=rx(r"\brasizm", r"\brasist", r"\bksenofob", r"\bdyskrymin", r"\bstereotyp"),
    ),
    "ru": dict(
        group=rx(r"\bиндийц(?:ы|ев|ам|ами)\b", r"\bинду(?:сы|сов|сам|сами)\b"),
        slurs=None,
        claims={"smell": rx(r"\bвоня", r"\bвонь\b"),
                "dirty": rx(r"\bгрязн", r"\bсрут на улиц"),
                "scam": rx(r"\bмошенник", r"\bобманщик"),
                "invasion": rx(r"\bвторжени", r"\bнаводнили\b", r"\bпонаехали\b", r"\bслишком много\b"),
                "jobs": rx(r"\b(?:отбирают|забирают|крадут) (?:наши |у нас )?(?:работу|рабочие места)")},
        contempt=rx(r"\bотвратительн", r"\bненавижу\b", r"\bмерзк", r"\bбыдло\b", r"\bотброс"),
        dehumanise=rx(r"\bкрысы\b", r"\bтараканы\b", r"\bпаразиты\b", r"\bживотные\b", r"\bскоты\b"),
        exclude=rx(r"\bдепортир", r"\bвыгнать\b", r"\bпусть едут обратно\b", r"\bубить\b"),
        counter=rx(r"\bрасизм", r"\bрасист", r"\bксенофоб", r"\bдискриминац", r"\bстереотип"),
    ),
    "ar": dict(
        # Arabic attaches "al-"/"wa-" prefixes, so no leading \b
        group=rx(r"(?:ال)?هنود\b", r"العمالة الهندية"),
        slurs=None,
        claims={"smell": rx(r"رائحت?هم", r"ريحتهم", r"نتنين"),
                "dirty": rx(r"قذرين", r"وسخين", r"وساخة"),
                "scam": rx(r"نصابين", r"محتالين"),
                "invasion": rx(r"غزو", r"اجتاحوا"),
                "jobs": rx(r"(?:يسرقون|ياخذون|يأخذون) (?:وظائفنا|شغلنا)")},
        contempt=rx(r"مقرفين", r"مقرف", r"أكره", r"اكره", r"حثالة"),
        dehumanise=rx(r"فئران", r"صراصير", r"حشرات", r"حيوانات", r"طفيليات"),
        exclude=rx(r"ترحيلهم", r"طردهم", r"يرجعون لبلادهم", r"اقتلوهم"),
        counter=rx(r"عنصري", r"عنصرية", r"تمييز"),
    ),
    "tr": dict(
        group=rx(r"\bhintli(?:ler|leri|lere|lerin)?\b"),
        slurs=None,
        claims={"smell": rx(r"\bkokuyor", r"\bkokarlar\b", r"\bpis koku\b"),
                "dirty": rx(r"\bkirli\b", r"\bpis\b"),
                "scam": rx(r"\bdoland[ıi]r[ıi]c[ıi]"),
                "invasion": rx(r"\bistila\b", r"\bi[şs]gal\b", r"\b[çc]ok fazla\b"),
                "jobs": rx(r"\bi[şs]lerimizi (?:[çc]al[ıi]yor|al[ıi]yor)")},
        contempt=rx(r"\bi[ğg]ren[çc]\b", r"\bnefret ediyorum\b", r"\bpislik\b"),
        dehumanise=rx(r"\bfareler\b", r"\bhamamb[öo]cek", r"\bparazit", r"\bhayvanlar\b"),
        exclude=rx(r"\bs[ıi]n[ıi]r d[ıi][şs][ıi]\b", r"\bdefolsunlar\b", r"\b[üu]lkelerine d[öo]ns[üu]nler\b"),
        counter=rx(r"\b[ıi]rk[çc][ıi]", r"\bayr[ıi]mc[ıi]l[ıi]k\b"),
    ),
    "id": dict(  # Indonesian and Malay
        group=rx(r"\borang(?:-orang)? india\b", r"\bwarga india\b", r"\bkaum india\b"),
        slurs=rx(r"\bkeling\b"),
        claims={"smell": rx(r"\bbau\b", r"\bbusuk\b"),
                "dirty": rx(r"\bjorok\b", r"\bkotor\b"),
                "scam": rx(r"\bpenipu\b"),
                "invasion": rx(r"\bmenyerbu\b", r"\bterlalu banyak\b"),
                "jobs": rx(r"\b(?:rampas|ambil|curi) (?:pekerjaan|kerja) kita\b")},
        contempt=rx(r"\bjijik\b", r"\bbenci\b", r"\bsampah\b"),
        dehumanise=rx(r"\btikus\b", r"\bkecoak\b", r"\blipas\b", r"\bbinatang\b", r"\bparasit\b"),
        exclude=rx(r"\busir\b", r"\bbalik ke india\b", r"\bhantar balik\b"),
        counter=rx(r"\brasis", r"\bperkauman\b", r"\bdiskriminasi\b", r"\bstereotip"),
    ),
    "ja": dict(
        group=rx(r"インド人"),
        slurs=None,
        claims={"smell": rx(r"臭い", r"くさい"),
                "dirty": rx(r"汚い", r"不潔"),
                "scam": rx(r"詐欺"),
                "invasion": rx(r"侵略", r"多すぎ"),
                "jobs": rx(r"仕事を奪")},
        contempt=rx(r"気持ち悪い", r"大嫌い", r"ゴミ"),
        dehumanise=rx(r"ゴキブリ", r"害虫", r"寄生虫"),
        exclude=rx(r"追い出せ", r"強制送還", r"国へ帰れ", r"帰れ", r"殺せ"),
        counter=rx(r"差別", r"ヘイト", r"偏見"),
    ),
    "zh": dict(
        group=rx(r"印度人", r"三哥"),
        slurs=rx(r"阿三"),
        claims={"smell": rx(r"咖喱味", r"很臭", r"臭"),
                "dirty": rx(r"脏", r"不卫生", r"随地大小便"),
                "scam": rx(r"骗子", r"诈骗"),
                "invasion": rx(r"入侵", r"太多了"),
                "jobs": rx(r"抢(?:我们的)?工作")},
        contempt=rx(r"恶心", r"讨厌", r"垃圾"),
        dehumanise=rx(r"老鼠", r"蟑螂", r"害虫", r"寄生虫", r"畜生"),
        exclude=rx(r"滚回", r"驱逐", r"遣返"),
        counter=rx(r"种族歧视", r"歧视", r"偏见"),
    ),
}

LANG_NAMES = {"en": "English", "es": "Spanish", "pt": "Portuguese", "fr": "French", "de": "German",
              "it": "Italian", "nl": "Dutch", "pl": "Polish", "ru": "Russian", "ar": "Arabic", "tr": "Turkish",
              "id": "Indonesian / Malay", "ja": "Japanese", "zh": "Chinese"}

# Sentence ends, including CJK and Arabic punctuation.
SENT = re.compile(r"(?<=[.!?\n。！？؟])\s*")


def detect(text):
    """Return (lang, sentences that mention Indians) for the first language whose group terms match."""
    for code, L in LANGS.items():
        if L["group"].search(text) or (L["slurs"] and L["slurs"].search(text)):
            sents = [s for s in SENT.split(text) if s.strip()]
            hits = [s for s in sents if L["group"].search(s) or (L["slurs"] and L["slurs"].search(s))]
            return code, hits
    return None, []


def score(code, sentences, whole):
    """Severity, stereotypes and flags for a non-English post."""
    L = LANGS[code]
    out = {"severity": 0, "stereotypes": [], "slur": False, "counter": False}
    if L["counter"].search(whole):
        out["counter"] = True
        return out
    scope = " \n ".join(sentences)
    sev = 0
    if L["slurs"] and L["slurs"].search(whole):
        out["slur"], sev = True, 2
    claims = [sid for sid, c in L["claims"].items() if c.search(scope)]
    if claims:
        sev = max(sev, 1)
        out["stereotypes"] = claims
    if L["contempt"].search(scope):
        sev = max(sev, 2)
    if L["dehumanise"].search(scope):
        sev = max(sev, 3)
    if L["exclude"].search(scope):
        sev = 4
    out["severity"] = sev
    return out
