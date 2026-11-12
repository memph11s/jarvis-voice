import json
import unittest

from jarvis_voice.session import SessionConfig, SessionState, VoiceSession


class FakeRecognizer:
    def __init__(self, events):
        self.events = iter(events)
        self.current = (False, {})
        self.reset_count = 0

    def AcceptWaveform(self, data):
        self.current = next(self.events, (False, {}))
        return self.current[0]

    def Result(self):
        return json.dumps(self.current[1], ensure_ascii=False)

    def PartialResult(self):
        return json.dumps(self.current[1], ensure_ascii=False)

    def Reset(self):
        self.reset_count += 1


class VoiceSessionTest(unittest.TestCase):
    def make_session(self, wake_events, speech_events, config=SessionConfig()):
        listened = []
        texts = []
        shutdowns = []
        session = VoiceSession(
            FakeRecognizer(wake_events),
            FakeRecognizer(speech_events),
            on_listen=lambda: listened.append(True),
            on_text=texts.append,
            on_shutdown=lambda: shutdowns.append(True),
            config=config,
        )
        return session, listened, texts, shutdowns

    def test_recording_stops_only_at_end_word(self):
        session, listened, texts, shutdowns = self.make_session(
            [(False, {"partial": "джарвис"})],
            [
                (False, {"partial": "привет"}),
                (False, {"partial": ""}),
                (False, {"partial": ""}),
                (True, {"text": "привет конец"}),
            ],
        )

        session.process(b"audio")
        self.assertEqual(session.state, SessionState.LISTENING)
        self.assertEqual(listened, [True])

        session.process(b"audio")
        session.process(b"audio")
        session.process(b"audio")
        self.assertEqual(session.state, SessionState.LISTENING)
        self.assertEqual(texts, [])

        session.process(b"audio")
        self.assertEqual(texts, ["привет"])
        self.assertEqual(shutdowns, [])
        self.assertEqual(session.state, SessionState.IDLE)

    def test_unrelated_speech_does_not_start_listening(self):
        session, listened, texts, shutdowns = self.make_session(
            [(True, {"text": "привет"})],
            [],
        )

        session.process(b"audio")

        self.assertEqual(session.state, SessionState.IDLE)
        self.assertEqual(listened, [])
        self.assertEqual(texts, [])
        self.assertEqual(shutdowns, [])

    def test_silence_does_not_finish_or_cancel_recording(self):
        session, listened, texts, shutdowns = self.make_session(
            [(False, {"partial": "джарвис"})],
            [(False, {"partial": ""})],
        )

        session.process(b"audio")
        for _ in range(100):
            session.process(b"audio")

        self.assertEqual(session.state, SessionState.LISTENING)
        self.assertEqual(texts, [])
        self.assertEqual(shutdowns, [])

    def test_end_word_inserts_partial_text(self):
        session, listened, texts, shutdowns = self.make_session(
            [(False, {"partial": "джарвис"})],
            [
                (False, {"partial": "открой документацию"}),
                (False, {"partial": "открой документацию конец"}),
            ],
        )

        session.process(b"audio")
        session.process(b"audio")
        session.process(b"audio")

        self.assertEqual(texts, ["открой документацию"])
        self.assertEqual(session.state, SessionState.IDLE)

    def test_final_parts_are_combined(self):
        session, listened, texts, shutdowns = self.make_session(
            [(False, {"partial": "джарвис"})],
            [
                (True, {"text": "первая часть"}),
                (True, {"text": "вторая часть"}),
                (False, {"partial": "конец"}),
            ],
        )

        session.process(b"audio")
        session.process(b"audio")
        session.process(b"audio")
        session.process(b"audio")

        self.assertEqual(texts, ["первая часть вторая часть"])

    def test_after_end_session_waits_for_next_wake_word(self):
        session, listened, texts, shutdowns = self.make_session(
            [
                (False, {"partial": "джарвис"}),
                (False, {"partial": "джарвис"}),
            ],
            [
                (False, {"partial": "первый текст конец"}),
                (False, {"partial": "второй текст конец"}),
            ],
        )

        session.process(b"audio")
        session.process(b"audio")
        session.process(b"audio")
        session.process(b"audio")

        self.assertEqual(listened, [True, True])
        self.assertEqual(texts, ["первый текст", "второй текст"])
        self.assertEqual(shutdowns, [])
        self.assertEqual(session.state, SessionState.IDLE)

    def test_shutdown_phrase_stops_session_while_idle(self):
        session, listened, texts, shutdowns = self.make_session(
            [(True, {"text": "пока джарвис"})],
            [],
        )

        session.process(b"audio")

        self.assertEqual(session.state, SessionState.STOPPED)
        self.assertEqual(shutdowns, [True])
        self.assertEqual(listened, [])

    def test_shutdown_phrase_stops_session_while_recording(self):
        session, listened, texts, shutdowns = self.make_session(
            [(False, {"partial": "джарвис"})],
            [(False, {"partial": "пока джарвис"})],
        )

        session.process(b"audio")
        session.process(b"audio")

        self.assertEqual(session.state, SessionState.STOPPED)
        self.assertEqual(shutdowns, [True])
        self.assertEqual(texts, [])


if __name__ == "__main__":
    unittest.main()
