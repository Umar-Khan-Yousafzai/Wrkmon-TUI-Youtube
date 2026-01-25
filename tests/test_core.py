"""Tests for core modules."""

import pytest
from wrkmon.core.queue import PlayQueue, QueueItem


class TestPlayQueue:
    """Tests for PlayQueue."""

    def test_empty_queue(self):
        queue = PlayQueue()
        assert queue.is_empty
        assert queue.length == 0
        assert queue.current is None

    def test_add_item(self):
        queue = PlayQueue()
        item = QueueItem(
            video_id="test123",
            title="Test Track",
            channel="Test Channel",
            duration=180,
        )
        pos = queue.add(item)
        assert pos == 0
        assert queue.length == 1
        assert not queue.is_empty

    def test_next_previous(self):
        queue = PlayQueue()
        for i in range(3):
            queue.add(QueueItem(
                video_id=f"test{i}",
                title=f"Track {i}",
                channel="Channel",
                duration=100,
            ))

        # Start at beginning
        queue.jump_to(0)
        assert queue.current.video_id == "test0"

        # Next
        queue.next()
        assert queue.current.video_id == "test1"

        # Previous
        queue.previous()
        assert queue.current.video_id == "test0"

    def test_shuffle(self):
        queue = PlayQueue()
        for i in range(5):
            queue.add(QueueItem(
                video_id=f"test{i}",
                title=f"Track {i}",
                channel="Channel",
                duration=100,
            ))

        queue.shuffle()
        assert queue.shuffle_mode
        assert len(queue._shuffle_order) == 5

        queue.unshuffle()
        assert not queue.shuffle_mode

    def test_repeat_modes(self):
        queue = PlayQueue()
        assert queue.repeat_mode == "none"

        queue.cycle_repeat()
        assert queue.repeat_mode == "one"

        queue.cycle_repeat()
        assert queue.repeat_mode == "all"

        queue.cycle_repeat()
        assert queue.repeat_mode == "none"

    def test_clear(self):
        queue = PlayQueue()
        queue.add(QueueItem(
            video_id="test",
            title="Track",
            channel="Channel",
            duration=100,
        ))
        assert queue.length == 1

        queue.clear()
        assert queue.is_empty


class TestQueueItem:
    """Tests for QueueItem."""

    def test_url_property(self):
        item = QueueItem(
            video_id="abc123",
            title="Test",
            channel="Channel",
            duration=60,
        )
        assert item.url == "https://www.youtube.com/watch?v=abc123"
