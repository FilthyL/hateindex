import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hateindex.classify import classify


class Multilingual(unittest.TestCase):
    HOSTILE = [  # (text, lang, minimum severity)
        ("Los hindúes son unos estafadores", "es", 1),
        ("Deportar a los inmigrantes indios ya", "es", 4),
        ("Esses indianos fedem", "pt", 1),
        ("Les Indiens sont des rats", "fr", 3),
        ("Die Inder nehmen uns die Jobs", "de", 1),
        ("Inder abschieben, sofort", "de", 4),
        ("Gli indiani sono parassiti", "it", 3),
        ("Indiërs zijn oplichters", "nl", 1),
        ("Hindusi to oszuści", "pl", 1),
        ("Индусы понаехали, выгнать их", "ru", 4),
        ("الهنود حشرات", "ar", 3),
        ("Hintliler pis kokuyor", "tr", 1),
        ("Orang India ni penipu", "id", 1),
        ("インド人は汚い", "ja", 1),
        ("印度人太脏了", "zh", 1),
        ("又是阿三", "zh", 2),
    ]
    NEUTRAL = [
        ("Los indios de la Amazonía protegen la selva", None),        # indigenous, not Indians
        ("Die Indianer Nordamerikas", None),                          # Native Americans
        ("Os índios do Brasil", None),
        ("Muchos hindúes celebran Diwali en Madrid", "es"),
        ("Le racisme contre les Indiens augmente au Canada", "fr"),   # counter-speech
        ("Rassismus gegen Inder ist ein Problem", "de"),
        ("インド人のエンジニアが増えている", "ja"),
    ]

    def test_hostile(self):
        for text, lang, sev in self.HOSTILE:
            with self.subTest(text=text):
                r = classify(text)
                self.assertEqual(r.lang, lang)
                self.assertGreaterEqual(r.severity, sev)

    def test_neutral(self):
        for text, lang in self.NEUTRAL:
            with self.subTest(text=text):
                r = classify(text)
                self.assertEqual(r.severity, 0)
                if lang is None:
                    self.assertFalse(r.targeted)
                else:
                    self.assertEqual(r.lang, lang)

    def test_english_unchanged(self):
        r = classify("Indians are all scammers")
        self.assertEqual((r.lang, r.severity), ("en", 1))


if __name__ == "__main__":
    unittest.main()
