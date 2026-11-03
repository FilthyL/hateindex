import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hateindex.classify import classify


class Severity(unittest.TestCase):
    def sev(self, text, context=""):
        return classify(text, context).severity

    def test_neutral_news(self):
        r = classify("Indian students celebrate Diwali at the University of Toronto")
        self.assertTrue(r.targeted)
        self.assertEqual(r.severity, 0)

    def test_adjective_is_not_a_target(self):
        self.assertFalse(classify("Best Indian food in Leeds?").targeted)

    def test_native_americans_not_target(self):
        self.assertFalse(classify("American Indians were forced onto reservations").targeted)

    def test_state_critique_is_not_hate(self):
        r = classify("The Indian government's new farm policy is a disaster")
        self.assertFalse(r.targeted)
        self.assertTrue(r.state_only)

    def test_stereotype(self):
        r = classify("Indians are all scammers, every call centre is full of them")
        self.assertEqual(r.severity, 1)
        self.assertIn("scam", r.stereotypes)
        self.assertIn("fraud", r.reasons)

    def test_contempt(self):
        self.assertEqual(self.sev("I hate indians, they smell disgusting"), 2)

    def test_slur(self):
        r = classify("another pajeet in my team lol")
        self.assertTrue(r.slur)
        self.assertGreaterEqual(r.severity, 2)

    def test_dehumanisation(self):
        self.assertEqual(self.sev("Indians are like rats, they infest every city"), 3)

    def test_exclusion(self):
        r = classify("Deport all indians now")
        self.assertEqual(r.severity, 4)
        self.assertIn("immigration", r.reasons)

    def test_jobs(self):
        r = classify("Indians are taking all the tech jobs with H1B visas")
        self.assertIn("jobs", r.stereotypes)
        self.assertIn("economic", r.reasons)

    def test_not_racist_but(self):
        self.assertGreaterEqual(self.sev("I'm not racist but indians smell"), 1)

    def test_context_pronouns(self):
        r = classify("they are vermin, send them back", context="Why are there so many Indians in Canada now")
        self.assertEqual(r.severity, 4)


class Exclusions(unittest.TestCase):
    def test_sarcasm_marker(self):
        r = classify("Yeah right, Indians are the reason your rent is high /s")
        self.assertTrue(r.sarcastic)
        self.assertEqual(r.severity, 0)

    def test_sarcasm_phrase(self):
        self.assertTrue(classify("Oh sure, because all Indians are scammers").sarcastic)

    def test_irony_emoji(self):
        self.assertTrue(classify("Love how Indians are always blamed for everything 🙄").sarcastic)

    def test_counter_speech(self):
        r = classify("It's racist to say Indians smell. Stop spreading that stereotype.")
        self.assertTrue(r.counter)
        self.assertEqual(r.severity, 0)

    def test_news_about_racism(self):
        self.assertTrue(classify("Rising anti-Indian racism online alarms community leaders in Canada").counter)

    def test_negation(self):
        self.assertEqual(classify("Indians are not scammers, most are hardworking").severity, 0)
        self.assertEqual(classify("Not all Indians smell, that's silly").severity, 0)


if __name__ == "__main__":
    unittest.main()
