"""Body CLI - REST API Server Entry Point"""
import os
import uvicorn
from starlette.applications import Starlette
from .service import body_service
from .io_adapter import start_input_reader_thread
from ..rest import BodyApp

import logging

# ログ設定
logging.basicConfig(level=logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# CLI は標準の BodyApp を使用
body_app = BodyApp(body_service)
app = Starlette(routes=body_app.get_routes())


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    start_input_reader_thread()
    logger.warning(f"Starting Body CLI REST server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
