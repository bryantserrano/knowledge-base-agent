"""Run with: python -m unittest discover -s tests"""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.index import app


class ChatSwitchTests(unittest.TestCase):
    def test_disabled_chat_skips_providers_and_returns_503(self):
        for value in ("false", " FALSE ", "", "invalid"):
            with self.subTest(value=value), patch.dict(os.environ, {"CHAT_ENABLED": value}, clear=True):
                with patch("api.index.OpenAIEmbeddings") as embeddings, \
                     patch("api.index.PineconeVectorStore") as store, \
                     patch("api.index.ChatOpenAI") as llm:
                    with TestClient(app) as client:
                        self.assertEqual(client.get("/api/health").json(),
                                         {"status": "ok", "chat_enabled": False})
                        response = client.post("/api/chat", json={"question": "Hours?"})
                        self.assertEqual(response.status_code, 503)
                        self.assertEqual(response.json(), {"detail": "Chat is temporarily unavailable."})
                    embeddings.assert_not_called()
                    store.assert_not_called()
                    llm.assert_not_called()

    def test_enabled_and_default_chat_still_retrieve(self):
        credentials = dict(OPENAI_API_KEY="test", PINECONE_API_KEY="test", PINECONE_INDEX_NAME="test")
        for setting in ({}, {"CHAT_ENABLED": " TrUe "}):
            with self.subTest(setting=setting), patch.dict(os.environ, credentials | setting, clear=True):
                with patch("api.index.OpenAIEmbeddings"), \
                     patch("api.index.PineconeVectorStore") as store, \
                     patch("api.index.ChatOpenAI"):
                    retriever = store.return_value.as_retriever.return_value
                    retriever.invoke.return_value = []
                    with TestClient(app) as client:
                        self.assertTrue(client.get("/api/health").json()["chat_enabled"])
                        response = client.post("/api/chat", json={"question": "Hours?"})
                        self.assertEqual(response.status_code, 200)
                        retriever.invoke.assert_called_once_with("Hours?")


if __name__ == "__main__":
    unittest.main()
