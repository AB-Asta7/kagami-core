import pytest
from src.context import SlidingWindowContext


def test_buffer_addition_and_token_tracking():
    ctx = SlidingWindowContext(max_tokens=100)
    ctx.add_message(role="system", content="Init prompt", token_cost=30)
    ctx.add_message(role="user", content="Query 1", token_cost=40)

    assert len(ctx) == 2
    assert ctx.current_tokens == 70


def test_fifo_eviction_on_overflow():
    ctx = SlidingWindowContext(max_tokens=100)
    ctx.add_message(role="user", content="Msg 1", token_cost=50)
    ctx.add_message(role="assistant", content="Msg 2", token_cost=40)

    # Total actual: 90 tokens. Al meter uno de 30, excede 100 y debe expulsar Msg 1 (FIFO)
    ctx.add_message(role="user", content="Msg 3", token_cost=30)

    assert len(ctx) == 2
    assert ctx.current_tokens == 70
    messages = ctx.get_messages()
    assert messages[0]["content"] == "Msg 2"
    assert messages[1]["content"] == "Msg 3"


def test_message_exceeding_total_capacity_raises_error():
    ctx = SlidingWindowContext(max_tokens=50)
    with pytest.raises(ValueError):
        ctx.add_message(role="user", content="Huge message", token_cost=60)
