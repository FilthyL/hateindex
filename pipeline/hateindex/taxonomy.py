"""Lexicons and rules for detecting hostility toward Indians.

See docs/DEFINITION.md for the definitions these rules implement. Slurs are
listed here only so the classifier can detect them.
"""
import re

def rx(*parts):
    return re.compile("|".join(parts), re.I)

# --- Who is the target -------------------------------------------------------

# Indians as people. "Indian" as a bare adjective (Indian food, Indian army)
# is deliberately NOT a target on its own.
GROUP = rx(
    r"\bindians\b",
    r"\bindian(?:s)?\s+(?:people|persons?|men|women|guys|girls|dudes|immigrants?|migrants?|students?|"
    r"workers?|employees|engineers|devs|developers|coders|managers|bosses|colleagues|coworkers|"
    r"community|communities|diaspora|tourists?|famil(?:y|ies)|folks?|kids|population|nationals?|"
    r"origin|americans|canadians|australians|brits|uncles?|aunt(?:y|ie)s?|landlords?|drivers?|"
    r"neighbou?rs?|shop ?keepers?|doctors?|nurses?|visa holders?|h-?1bs?)\b",
    r"\bpeople (?:from|of) india\b", r"\bdesis?\b", r"\bjeets?\b",
    r"\b(?:every|all|these|those|typical|your average|another) indian\b", r"\banti-?indian\b",
    r"\bindian (?:guy|man|woman|girl|dude|person|immigrant|student|worker|kid|boss|manager|colleague|coworker)\b",
)

# Not about people of India.
GROUP_FALSE = rx(
    r"\b(?:american|native|red|cleveland|west|east|first nations?|plains|amazon|brazilian|mexican|foot|horse|caribbean)[\x22\u201d\x27]? indians?\b",
    r"\bindians? (?:tribes?|reservations?|nations?|casinos?)\b",
    r"\bindian (?:ocean|summer|ink|pale ale|motorcycles?|wells)\b",
)

# Slurs imply the target and are severity 2 on their own.
SLURS = rx(
    r"\bpajeets?\b", r"\bpoo+(?:\s|-)?in(?:\s|-)?(?:the\s)?loo+s?\b", r"\bstreet ?sh[i1]tt?ers?\b",
    r"\bcurry ?(?:munchers?|monkeys?|niggers?|n[i1]gg?as?|eaters?)\b", r"\bdot ?heads?\b",
    r"\bsaa+r\b(?=.*\b(?:needful|kindly|bobs|vagene|redeem|indian|pajeet)\b)",
    r"\bbobs? and vag(?:ene|ana|ina)\b", r"\bredeem\b.*\bsaa+r\b", r"\bsaa+rs\b",
    r"\bjeets?\b", r"\bcurry ?(?:land|stan)\b", r"\bpoojeets?\b",
)

# Pronouns that refer back to the group when the surrounding thread is about Indians.
PRONOUN_TARGET = rx(r"\bthey\b", r"\bthem\b", r"\btheir\b", r"\b(?:these|those) (?:people|guys|folks|ones)\b")

# Statements that generalise about the group ("Indians are…", "all Indians…").
GENERALISE = rx(
    r"\b(?:indians|desis|jeets|pajeets|they|these people)\s+(?:are|r|always|all|just|never|only|keep|can'?t|cannot|"
    r"won'?t|don'?t|do|have|smell|stink|love|need|will|literally|basically|seem|tend|refuse|ruin|ruined|"
    r"took|take|steal|bring|breed|flood|come)\b",
    r"\b(?:all|every|most|typical|these|those|so many|too many|why do|why are|why does|why is it always) "
    r"(?:the )?(?:indians?|desis?|jeets?)\b",
    r"\bindians (?:everywhere|again|lol|smh)\b",
    r"\b(?:that'?s|so|how) indian\b",
)

# --- Severity cues -----------------------------------------------------------

CONTEMPT = rx(
    r"\bhate (?:indians|desis|them|these people|those people|jeets)\b", r"\bcan'?t stand\b",
    r"\b(?:sick|tired|fed up) of (?:indians|them|these people|desis)\b",
    r"\bdisgusting\b", r"\bgross\b", r"\brevolting\b", r"\bfilthy\b", r"\bnasty\b", r"\bugly\b",
    r"\bstupid\b", r"\bidiots?\b", r"\bmorons?\b", r"\bretard(?:s|ed)?\b", r"\btrash\b", r"\bgarbage\b",
    r"\bscum\b", r"\bpathetic\b", r"\binferior\b", r"\blowest (?:iq|caste)\b", r"\blow ?iq\b",
    r"\bworst people\b", r"\bdon'?t belong\b", r"\bnot welcome\b", r"\bunbearable\b", r"\bhorde\b",
)

DEHUMANISE = rx(
    r"\brats?\b", r"\bvermin\b", r"\bcockroach(?:es)?\b", r"\broaches\b", r"\bparasit(?:es|ic)\b",
    r"\banimals\b", r"\bsub-?humans?\b", r"\bapes\b", r"\bmonkeys\b", r"\blocusts?\b",
    r"\binfest(?:ation|ed|ing)\b", r"\bsavages?\b", r"\binsects\b", r"\bleeches\b",
    r"\bswarm(?:s|ing)?\b", r"\b(?:are|is|like|a|spread(?:ing)?) (?:a |the )?(?:cancer|disease|plague)\b", r"\bpests?\b", r"\bfilth\b", r"\bbugs\b", r"\bsewage\b",
)

EXCLUDE_VIOLENCE = rx(
    r"\bdeport (?:all |every |the |them|these|those|indians|desis|jeets|pajeets)", r"\bmass deport",
    r"\bsend (?:them|indians|all of them|these people|jeets|pajeets) (?:all )?(?:back|home)\b",
    r"\bgo back to (?:india|your country|your shithole)\b", r"\bban (?:all )?(?:the )?indians\b",
    r"\bkick (?:them|indians|all of them|these people) out\b", r"\bno more indians\b",
    r"\bremigrat(?:e|ion)\b", r"\bget (?:them|indians|these people) out\b", r"\bkeep (?:them|indians) out\b",
    r"\b(?:should|need to|must|deserve to|ought to) (?:be )?(?:killed|shot|hanged|hung|gassed|exterminated|"
    r"wiped out|burned|lynched|eradicated|purged|removed)\b",
    r"\bkill (?:all |every |the |them|these|those|indians|jeets|pajeets)", r"\bgas (?:them|the indians|all)\b",
    r"\bexterminat", r"\bethnic(?:ally)? cleans", r"\bday of the rope\b", r"\bhang (?:them|all)\b",
    r"\bstop (?:all )?indian (?:immigration|migration|visas)\b", r"\bclose the (?:borders?|gates?) to indians\b",
    r"\bexecut(?:e|ing) (?:all |the )?(?:indians|them|jeets|pajeets)\b", r"\bgenocid(?:e|ing)\b",
    r"\bhunt(?:ing)? (?:down )?(?:indians|them|jeets|pajeets)\b", r"\blynch", r"\bshoot (?:them|indians|jeets)\b",
)

# --- Reasons ("why") and stereotypes ("what") --------------------------------

REASONS = {
    "economic": "Jobs & economic competition",
    "immigration": "Immigration & demographic anxiety",
    "hygiene": "Disgust: hygiene & smell",
    "fraud": "Scams, fraud & crime",
    "workplace": "Workplace nepotism",
    "culture": "Culture & religion",
    "behaviour": "Manners & behaviour",
    "gender": "Gender & sexual stereotypes",
    "status": "Poverty & status contempt",
    "geopolitical": "Geopolitics & regional rivalry",
    "general": "General contempt (no specific reason)",
}

# id: (label, reason, pattern)
STEREOTYPES = {
    "smell": ("Indians smell / smell of curry", "hygiene",
              rx(r"\bsmell(?:s|y|ing)?\b", r"\bstink(?:s|y|ing)?\b", r"\bodou?r\b", r"\bb\.?o\.?\b", r"\breek")),
    "dirty": ("Indians are dirty / defecate in the street", "hygiene",
              rx(r"\bdirty\b", r"\bpoop(?:ing)?\b", r"\bsh[i1]t(?:ting)? (?:on|in) the (?:street|beach|road)",
                 r"\bopen defecation\b", r"\bunhygienic\b", r"\bhygiene\b", r"\bdon'?t (?:wash|shower|bathe)\b",
                 r"\bpoo in loo\b", r"\bstreet ?sh[i1]tt?ers?\b", r"\bsewage\b", r"\bganges\b", r"\bfilth")),
    "scam": ("Indians are scammers", "fraud",
             rx(r"\bscam(?:s|mer|mers|ming)?\b", r"\bfraud(?:s|sters?)?\b", r"\bcall ?cent(?:er|re)s?\b",
                r"\btech support\b", r"\bgift ?cards?\b", r"\bcon ?(?:men|artists)\b", r"\bredeem\b")),
    "jobs": ("Indians take our jobs / abuse H-1B", "economic",
             rx(r"\bjobs?\b", r"\bh-?1-?bs?\b", r"\bvisas?\b", r"\boutsourc", r"\bwages?\b", r"\bcheap labou?r\b",
                r"\breplac(?:e|ing|ed) (?:us|americans|workers|white)", r"\blayoffs?\b", r"\bopt\b", r"\bundercut")),
    "nepotism": ("Indians only hire other Indians", "workplace",
                 rx(r"\bnepotism\b", r"\bonly hire\b", r"\bhire (?:only )?(?:their own|other indians|each other)\b",
                    r"\bhiring (?:their own|other indians|only indians)\b", r"\btake over (?:the |a )?(?:company|team|department)",
                    r"\bethnic network", r"\bcaste (?:network|discrimination|bias)\b")),
    "invasion": ("Indians are overrunning / invading", "immigration",
                 rx(r"\binvasion\b", r"\binvad(?:e|ing|ers)\b", r"\boverrun\b", r"\bflood(?:ing|ed)?\b", r"\btoo many\b",
                    r"\btaking over\b", r"\breplacement\b", r"\bcolon(?:y|is|iz)", r"\bbrampton\b", r"\bdemographic",
                    r"\bswarm", r"\bhorde", r"\bimmigra", r"\bmigrants?\b", r"\binternational students\b")),
    "creep": ("Indian men are creeps / harass women", "gender",
              rx(r"\bcreeps?\b", r"\bcreepy\b", r"\bharass", r"\bperverts?\b", r"\brap(?:e|ists?)\b",
                 r"\bbobs? and vag", r"\bsend bobs\b", r"\bstar(?:e|ing) at (?:women|girls)\b", r"\bincels?\b")),
    "cheap": ("Indians are cheap / stingy", "status",
              rx(r"\bcheap(?:skates?)?\b(?! labou?r)", r"\bstingy\b", r"\btight ?fisted\b", r"\bhaggl", r"\bfrugal\b",
                 r"\bdon'?t tip\b", r"\bnever tip\b")),
    "poor": ("Indians are poor / third world", "status",
             rx(r"\bthird[- ]world\b", r"\bpoor\b", r"\bpoverty\b", r"\bslums?\b", r"\bshithole\b", r"\bbackward\b",
                r"\buncivili[sz]ed\b", r"\bprimitive\b")),
    "religion": ("Indians worship cows / are superstitious", "culture",
                 rx(r"\bcows?\b", r"\bcow (?:piss|urine|dung)\b", r"\bgomutra\b", r"\bsuperstiti", r"\bidols?\b",
                    r"\bpagans?\b", r"\bcaste\b", r"\bcurry\b", r"\bfood\b")),
    "rude": ("Indians are loud / rude / pushy", "behaviour",
             rx(r"\bloud\b", r"\brude\b", r"\bpushy\b", r"\bentitled\b", r"\barrogant\b", r"\bno manners\b",
                r"\b(?:cut|skip|jump)(?:ting)? (?:the )?(?:line|queue)\b", r"\bspit(?:ting)?\b", r"\bobnoxious\b")),
    "it": ("Indians are all tech support / IT", "economic",
           rx(r"\bit (?:guys|workers|sector|industry|people)\b", r"\bcod(?:ers|ing)\b", r"\bsoftware\b", r"\bcode monkeys?\b",
              r"\btcs\b", r"\binfosys\b", r"\bwipro\b", r"\bcognizant\b")),
    "drivers": ("Indians are bad drivers", "behaviour",
                rx(r"\bbad drivers?\b", r"\bcan'?t drive\b", r"\bdriving\b", r"\buber drivers?\b", r"\btruck(?:ers|ing)\b")),
    "fake_degree": ("Indian degrees/doctors are fake", "status",
                    rx(r"\bfake (?:degrees?|doctors?|engineers?|credentials|resumes?|cvs?)\b", r"\bdiploma mills?\b",
                       r"\bcheat(?:ed|ing)? (?:on )?(?:exams?|interviews?)\b", r"\bproxy interviews?\b")),
    "geo": ("Regional / geopolitical hostility", "geopolitical",
            rx(r"\bpakistan", r"\bbangladesh", r"\bkashmir\b", r"\bkhalistan", r"\bhindutva\b", r"\bsanghis?\b",
               r"\bbhakts?\b", r"\bbig brother\b", r"\bexpansionis", r"\bhegemon")),
}

# Loaded claims. A topic word above ("jobs", "visa", "immigration") only tags
# the reason once a post is already hostile; it takes one of these claims to
# make a post severity 1 on its own. Without this split, ordinary H-1B and
# immigration-policy debate counts as stereotyping.
CLAIMS = {
    "smell": rx(r"\bsmell(?:s|y|ing)?\b(?! (?:good|great|amazing|delicious))", r"\bstink(?:s|y|ing)?\b", r"\breek",
                r"\b(?:body )?odou?r\b"),
    "dirty": rx(r"\bdirty\b", r"\bfilthy\b", r"\bunhygienic\b", r"\bdon'?t (?:wash|shower|bathe)\b",
                r"\bsh[i1]t(?:ting)? (?:on|in) the (?:street|beach|road)", r"\bstreet ?sh[i1]tt?",
                r"\bpoo in (?:the )?loo\b"),
    "scam": rx(r"\bscam(?:mers?|s|ming)\b", r"\bfraudsters?\b", r"\bcon (?:men|artists)\b", r"\bliars?\b",
               r"\bdishonest\b", r"\bcan'?t be trusted\b", r"\buntrustworthy\b", r"\bcheaters?\b"),
    "jobs": rx(r"\b(?:steal|stealing|stole|take|taking|took|taken) (?:our|all the|all our|american|the good|white) (?:\w+ )?jobs\b",
               r"\breplac(?:e|ing|ed) (?:us|americans|american workers|native|white|local) ",
               r"\bundercut(?:ting)? (?:our |american |local )?wages\b", r"\bcheap (?:replacements?|scab)",
               r"\bh-?1-?bs? (?:scam|fraud|invasion|parasites)", r"\bvisa (?:scam|fraud|mills?)\b"),
    "nepotism": STEREOTYPES["nepotism"][2],
    "invasion": rx(r"\binvasion\b", r"\binvad(?:e|ing|ers)\b", r"\boverr(?:un|unning)\b",
                   r"\bflood(?:ing|ed)? (?:in|into|our|the country|the west)\b", r"\btoo many (?:of them|indians|jeets|desis)\b(?! (?:applicants|applying|in (?:the )?(?:line|queue)|waiting))",
                   r"\btaking over\b", r"\b(?:great )?replacement\b", r"\bcoloni[sz](?:e|ing|ation)\b", r"\bswarm", r"\bhordes?\b"),
    "creep": rx(r"\bcreeps?\b", r"\bcreepy\b", r"\bperverts?\b", r"\brapists?\b", r"\bbobs? and vag", r"\bsend bobs\b"),
    "cheap": rx(r"\bcheapskates?\b", r"\bstingy\b", r"\btight ?fisted\b", r"\b(?:don'?t|never) tip\b",
                r"\bcheap (?:people|bastards|asses|fucks)\b"),
    "poor": rx(r"\bshithole\b", r"\bbackward\b", r"\buncivili[sz]ed\b", r"\bprimitive\b",
               r"\bthird[- ]world (?:people|mentality|behaviou?r|shithole|trash)\b"),
    "religion": rx(r"\bcow (?:piss|urine|dung)\b", r"\bgomutra\b", r"\bworship(?:ping)? (?:cows|rats|idols)\b",
                   r"\bpiss drinkers?\b"),
    "rude": rx(r"\b(?:so |too |very )?(?:loud|rude|pushy|entitled|obnoxious)\b", r"\bno manners\b",
               r"\b(?:cut|skip|jump)(?:ting)? (?:the )?(?:line|queue)\b"),
    "it": rx(r"\bcode monkeys?\b", r"\b(?:bad|terrible|shit|crap|awful|garbage) (?:code|coders|developers|engineers|programmers)\b"),
    "drivers": rx(r"\bbad drivers?\b", r"\bcan'?t drive\b", r"\b(?:terrible|awful|worst) drivers\b"),
    "fake_degree": STEREOTYPES["fake_degree"][2],
    "geo": rx(r"\bsanghis?\b", r"\bbhakts?\b", r"\bexpansionis", r"\bhegemon"),
    "incompetent": rx(r"\b(?:indians|they|desis|jeets) (?:are|r) (?:so |all |just |really )?(?:bad|terrible|awful|incompetent|lazy|"
                      r"useless|horrible|the worst|inferior)\b", r"\bnot (?:very |inherently )?good at\b"),
}
STEREOTYPES["incompetent"] = ("Indians are incompetent / lazy", "workplace", CLAIMS["incompetent"])

# Hostility expressed by comparison or sweeping blame, which has no single cue word.
COMPARATIVE = rx(
    r"\b(?:nowhere near|not even|not) as bad as (?:the )?(?:indians|jeets|pajeets|desis)\b",
    r"\bworse than (?:the )?(?:indians|jeets|pajeets)\b", r"\b(?:indians|jeets|pajeets) are (?:even )?worse\b",
    r"\bat least (?:they|we|i)?\s*use (?:a )?toilets?\b", r"\b(?:i )?(?:like|prefer) \w+ more th[ae]n (?:the )?(?:indians|jeets)\b",
    r"\bruin(?:s|ed|ing)? (?:everything|every (?:place|country|city|thing)|this country|the (?:country|neighbou?rhood|city))\b",
    r"\boutbreed", r"\bflood(?:ed|ing|s)? [\w ]{1,20} with (?:indians|jeets|pajeets|them)\b",
)

# Someone describing or rejecting a view, not holding it.
REPORTED = rx(
    r"\b(?:they|you|people|he|she|some|others|folks)(?:'re| are| is)? (?:saying|claiming|suggesting|implying|pretending)\b",
    r"\bthe (?:idea|notion|claim|myth|stereotype|trope|assumption) that\b", r"\btrash opinion\b",
    r"\bdeserves? (?:the )?downvotes\b", r"\bstupid (?:politics|to blame)\b", r"\b(?:wrong|unfair|lazy) to blame\b",
    r"\bblaming (?:indians|immigrants|them) for\b", r"\bget(?:ting)? attacked for\b", r"\bi am tired of it\b",
    r"\b(?:arrested|charged|convicted|sentenced|jailed|detained|indicted)\b",
)
# Insults addressed to the person being replied to, not to Indians
VOCATIVE = re.compile(r",\s*(?:you\s+)?(?:fucking\s+)?(?:retard(?:ed)?|idiot|moron|dumbass|faggot|nigger|cunt)s?\b", re.I)

# Other meanings of "Indians": Native Americans, sports teams, motorcycles.
OTHER_SENSE = rx(
    r"\btrib(?:e|es|al)\b", r"\bnative americans?\b", r"\breservations?\b", r"\bsettlers?\b", r"\bcolonists?\b",
    r"\b(?:cherokee|sioux|apache|navajo|shoshone|comanche|lakota|iroquois|mohawk|cree|ojibwe|atsina|naumkeag|kwaaymii)\b",
    r"\b(?:wigwams?|tepees?|tipis?|buffalo|cowboys?|thanksgiving|pilgrims|frontier|war party|smallpox|columbus|pocahontas)\b",
    r"\bland back\b", r"\bindigenous\b", r"\bfirst nations\b", r"\bamazon(?:ian)?\b",
    r"\b(?:mlb|baseball|innings?|final score|touchdown|quarterback|varsity|playoffs?|ballpark|pitcher|world series)\b",
    r"\b(?:tigers|white sox|yankees|vikings|red sox|guardians|braves|chiefs) \d", r"\b\d+-\d+\b(?=.*\b(?:win|loss|beat|defeat|game))",
    r"\bmotorcycles?\b", r"\bnortons?\b", r"\bharley\b", r"\bvincent\b",
    r"\bonly good indians\b", r"\b(?:17|18)\d\d\b",
)
# Things that tie a post to India despite those cues
INDIA_TIE = rx(r"\bindia\b", r"\bdesis?\b", r"\bhindus?\b", r"\bsikhs?\b", r"\bh-?1-?bs?\b", r"\bbollywood\b",
               r"\bdiwali\b", r"\bcurry\b", r"\bmodi\b", r"\bindian[- ]americans?\b", r"\bsouth asians?\b",
               r"\bjeets?\b", r"\bpajeets?\b", r"\bsaa+r", r"\bcaste\b", r"\bbangalore\b", r"\bdelhi\b", r"\bmumbai\b")

# Political/state critique: legitimate and never by itself hate.
STATE_CRITIQUE = rx(r"\b(?:modi|bjp|congress party|indian (?:government|govt|state|army|military|policy|"
                    r"foreign ministry|embassy|high commission)|new delhi|government of india)\b")

# --- Exclusions ----------------------------------------------------------------

SARCASM = rx(
    r"(?:^|\s)/s\b", r"#sarcasm\b", r"\(sarcasm\)", r"\byeah,? right\b", r"\boh,? sure\b", r"\bsure,? because\b",
    r"\bas if\b", r"\bsaid no one ever\b", r"\btotally not racist\b", r"\bnot racist at all\b",
    r"\bbecause that'?s (?:totally|definitely) how\b", r"\bwow,? (?:so|such) (?:original|brave|smart)\b",
    r"\bclearly the (?:real )?problem\b", r"\bgreat take\b.*\b(?:genius|bro)\b",
)
IRONY_EMOJI = re.compile("[\U0001F644\U0001F643\U0001F60F\U0001F921]")
POSITIVE = rx(r"\b(?:love|great|wonderful|amazing|brilliant|genius|fantastic|so smart|best)\b")
SCARE_QUOTED = re.compile(r"[\"“”']\s*(?:scam\w*|smell\w*|dirty|invad\w*|creeps?|cheap)\s*[\"“”']", re.I)

COUNTER_SPEECH = rx(
    r"\b(?:is|that'?s|so|how|this is|that is|being|pure|blatant|casual|openly|rampant|rising|growing|anti-indian) racis(?:t|m)\b",
    r"\bracism (?:against|towards?|toward) (?:indians|south asians|desis)\b",
    r"\banti-?indian (?:racism|hate|hatred|sentiment|bigotry|rhetoric|abuse|attacks?|slurs?|posts?)\b",
    r"\bstereotyp", r"\bbigot", r"\bxenophob", r"\bstop (?:saying|calling|spreading|being racist)\b",
    r"\bhate crimes? (?:against|targeting)\b", r"\bdiscriminat(?:ion|ed|ing) (?:against|toward)\b",
    r"\btargeted (?:for|because)\b", r"\bslurs? (?:against|at|toward)\b", r"\bracial abuse\b",
    r"\bcondemn", r"\bunacceptable\b", r"\bcalled (?:it|this) out\b",
    r"\b(?:vile|disgusting|your|such|this) (?:,\s*)?racis(?:t|m)\b", r"\bracist (?:shit|crap|nonsense|garbage|bs|bullshit)\b",
    r"\bnot going to tolerate\b", r"\bnothing (?:in .{0,40})?(?:that )?could reasonably be interpreted as racist\b", r"\bracist slurs?\b", r"\bnew slur\b", r"\bslur (?:targets|aimed|used against)\b",
)
# "I'm not racist but…" is the opposite of counter-speech.
NOT_RACIST_BUT = rx(r"\b(?:i'?m|im|i am) not (?:a )?racist,? but\b", r"\bnot (?:to be|trying to be) racist,? but\b")

NEGATION = rx(
    r"\bnot all (?:indians|desis|of them)\b",
    r"\b(?:indians|desis|they) (?:are not|aren'?t|arent|r not|do not|don'?t|don't|never)\s+(?:all\s+)?"
    r"(?:scam|smell|dirty|creep|cheap|stealing|taking|invad|bad)",
    r"\bit'?s (?:a )?(?:myth|lie|false)\b", r"\bnothing to do with being indian\b", r"\bmost indians (?:are|aren'?t)\b",
)
