import unittest

from jarvis_voice.text_processing import extract_local_question, punctuate_text


class TextProcessingTest(unittest.TestCase):
    def test_sentence_is_capitalized_and_finished(self):
        self.assertEqual(punctuate_text("  проверь   этот тест "), "Проверь этот тест.")

    def test_question_gets_question_mark(self):
        self.assertEqual(punctuate_text("почему падает тест"), "Почему падает тест?")

    def test_existing_punctuation_is_preserved(self):
        self.assertEqual(punctuate_text("готово!"), "Готово!")

    def test_local_question_is_extracted_without_rewriting(self):
        self.assertEqual(
            extract_local_question("спроси почему небо голубое"),
            "почему небо голубое",
        )
        self.assertEqual(extract_local_question("спроси"), "")

    def test_regular_dictation_is_not_an_ollama_question(self):
        self.assertIsNone(extract_local_question("напиши привет"))
        self.assertIsNone(extract_local_question("спросить его"))


if __name__ == "__main__":
    unittest.main()
