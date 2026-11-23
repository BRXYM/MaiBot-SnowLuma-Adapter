from importlib import import_module
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

codec_module = import_module("plugins.MaiBot-SnowLuma-Adapter.codecs.inbound.message_codec")


class QuotePreviewTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.query = SimpleNamespace(get_message_detail=AsyncMock())
        profile = SimpleNamespace(profile=SimpleNamespace(client_type="snowluma"))
        self.codec = codec_module.QQInboundCodec(Mock(), self.query, profile, Mock())

    async def test_quote_preview_does_not_load_attachment_data(self):
        self.query.get_message_detail.return_value = {
            "sender": {"user_id": "12345", "nickname": "测试"},
            "message": [{"type":"record","data":{"file":"song.amr"}},
                        {"type":"image","data":{"file":"photo"}},
                        {"type":"file","data":{"name":"歌单.txt"}},
                        {"type":"text","data":{"text":"备注"}}],
        }
        parts, _ = await self.codec.convert_segments(
            {"message":[{"type":"reply","data":{"id":"-12"}},
                        {"type":"text","data":{"text":"这个呢？"}}]}, "54321")
        self.assertEqual(parts[0]["data"]["target_message_content"], "[语音][图片][文件：歌单.txt]备注")
        self.assertEqual(parts[0]["data"]["target_message_id"], "-12")
        self.assertEqual(parts[1]["data"], "这个呢？")
        self.query.get_message_detail.assert_awaited_once_with("-12")

    async def test_missing_quote_detail_preserves_reference(self):
        self.query.get_message_detail.return_value = None
        part = await self.codec._build_reply_segment({"id":"-12"})
        self.assertEqual(part, {"type":"reply","data":{"target_message_id":"-12"}})
