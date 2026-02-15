"""
ニュースキャスター配信のステートマシン。

BroadcastPhase (Enum) と各フェーズのハンドラで構成されます。
各ハンドラは BroadcastContext を受け取り、次の BroadcastPhase を返します。
"""
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .config import logger, POLL_INTERVAL, MAX_WAIT_CYCLES
from .saint_graph import SaintGraph
from .news_service import NewsService
from .body_client import BodyClient


class BroadcastPhase(Enum):
    """配信のフェーズを表す列挙型。"""
    INTRO   = "intro"     # 開始挨拶
    NEWS    = "news"      # ニュース読み上げ中
    IDLE    = "idle"      # ニュース終了 → コメント待ち
    CLOSING = "closing"   # 締めの挨拶 → 配信停止


@dataclass
class BroadcastContext:
    """ハンドラ間で共有される配信コンテキスト。"""
    saint_graph: SaintGraph
    news_service: NewsService
    idle_counter: int = 0


# ---------------------------------------------------------------------------
# 共通ユーティリティ
# ---------------------------------------------------------------------------

async def _poll_and_respond(ctx: BroadcastContext) -> bool:
    """
    コメントをポーリングし、あれば応答します。全フェーズ共通。

    Returns:
        コメントがあり応答した場合 True
    """
    try:
        comments_data = await ctx.saint_graph.body.get_comments()

        if comments_data:
            comments_text = "\n".join(
                f"{c.get('author', 'User')}: {c.get('message', '')}"
                for c in comments_data
            )
            if comments_text:
                logger.info(f"Comments received: {comments_text}")
                await ctx.saint_graph.process_turn(comments_text)
                return True
    except Exception as e:
        logger.error(f"Error in polling/turn: {e}")
    return False


# ---------------------------------------------------------------------------
# フェーズハンドラ
# ---------------------------------------------------------------------------

async def handle_intro(ctx: BroadcastContext) -> BroadcastPhase:
    """INTRO: 配信開始の挨拶を行い、NEWS フェーズへ遷移する。"""
    await ctx.saint_graph.process_intro()
    return BroadcastPhase.NEWS


async def handle_news(ctx: BroadcastContext) -> BroadcastPhase:
    """
    NEWS: コメント優先で確認し、なければニュースを 1 本読み上げる。
    ニュースを全消化したら IDLE へ遷移する。
    """
    # コメント優先
    if await _poll_and_respond(ctx):
        ctx.idle_counter = 0
        return BroadcastPhase.NEWS

    # 次のニュースを読み上げ
    if ctx.news_service.has_next():
        item = ctx.news_service.get_next_item()
        logger.info(f"Reading news item: {item.title}")
        await ctx.saint_graph.process_news_reading(title=item.title, content=item.content)
        return BroadcastPhase.NEWS

    # ニュース全消化 → IDLE へ
    logger.info("All news items read. Waiting for final comments.")
    await ctx.saint_graph.process_news_finished()
    return BroadcastPhase.IDLE


async def handle_idle(ctx: BroadcastContext) -> BroadcastPhase:
    """
    IDLE: コメントを待ち、あれば応答してカウンタをリセットする。
    タイムアウトしたら CLOSING へ遷移する。
    """
    if await _poll_and_respond(ctx):
        ctx.idle_counter = 0
        return BroadcastPhase.IDLE

    ctx.idle_counter += 1
    if ctx.idle_counter > MAX_WAIT_CYCLES:
        logger.info(
            f"Silence timeout ({MAX_WAIT_CYCLES} cycles) reached. "
            "Finishing broadcast."
        )
        return BroadcastPhase.CLOSING

    return BroadcastPhase.IDLE


async def handle_closing(ctx: BroadcastContext) -> BroadcastPhase:
    """CLOSING: 締めの挨拶をしてリソースを解放する。None を返しループ終了。"""
    await ctx.saint_graph.process_closing()
    await asyncio.sleep(3)
    return None  # ループ終了のシグナル


# ---------------------------------------------------------------------------
# ディスパッチテーブル & メインループ
# ---------------------------------------------------------------------------

_HANDLERS = {
    BroadcastPhase.INTRO:   handle_intro,
    BroadcastPhase.NEWS:    handle_news,
    BroadcastPhase.IDLE:    handle_idle,
    BroadcastPhase.CLOSING: handle_closing,
}


async def run_broadcast_loop(ctx: BroadcastContext) -> None:
    """
    ステートマシンのメインループ。

    INTRO から始まり、各ハンドラが返す次フェーズに従って遷移します。
    ハンドラが None を返すとループを終了します。
    """
    phase = BroadcastPhase.INTRO
    logger.info("Entering Broadcast Loop (state machine)...")

    while phase is not None:
        try:
            handler = _HANDLERS[phase]
            next_phase = await handler(ctx)

            if next_phase is not None:
                if next_phase != phase:
                    logger.info(f"Phase transition: {phase.value} -> {next_phase.value}")
                phase = next_phase
                await asyncio.sleep(POLL_INTERVAL)
            else:
                # CLOSING ハンドラが None を返した → 終了
                logger.info(f"Phase {phase.value} completed. Exiting loop.")
                phase = None

        except Exception as e:
            logger.error(f"Unexpected error in phase {phase.value}: {e}", exc_info=True)
            await asyncio.sleep(5)
        except BaseException as e:
            logger.critical(f"Critical System Error in phase {phase.value}: {e}", exc_info=True)
            raise
